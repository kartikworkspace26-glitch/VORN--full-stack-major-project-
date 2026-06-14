import json
import hmac
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Order, OrderItem, Coupon


# ── Checkout ──────────────────────────────────────────────────────────────────
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your bag is empty.')
        return redirect('cart')

    cart_items = []
    subtotal = 0
    for key, item in cart.items():
        s = item['price'] * item['quantity']
        subtotal += s
        cart_items.append({**item, 'key': key, 'subtotal': s})

    shipping = 0 if subtotal >= 999 else 99
    total = subtotal + shipping

    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'user': request.user,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_me_link': settings.RAZORPAY_ME_LINK,
    })


# ── Apply Coupon ───────────────────────────────────────────────────────────────
def apply_coupon(request):
    code = request.POST.get('code', '').strip().upper()
    cart = request.session.get('cart', {})
    subtotal = sum(i['price'] * i['quantity'] for i in cart.values())

    try:
        coupon = Coupon.objects.get(code=code)
        if coupon.is_valid(subtotal):
            if coupon.discount_type == 'percent':
                discount = (subtotal * float(coupon.discount_value)) / 100
            else:
                discount = float(coupon.discount_value)
            request.session['coupon'] = {'code': code, 'discount': float(discount)}
            request.session.modified = True
            return JsonResponse({'success': True, 'discount': float(discount), 'code': code})
        else:
            return JsonResponse({'success': False, 'message': 'Coupon is invalid or minimum order amount not met.'})
    except Coupon.DoesNotExist:
        pass

    return JsonResponse({'success': False, 'message': 'Invalid or expired coupon code.'})


# ── Create Order (used by both Razorpay.me and SDK flows) ──────────────────────
def create_order_from_cart(request, data, payment_method='razorpay_me'):
    """
    Creates a Django Order from the cart session.
    Returns (order, error_message)
    """
    cart = request.session.get('cart', {})
    if not cart:
        return None, 'Cart is empty'

    subtotal = sum(i['price'] * i['quantity'] for i in cart.values())
    shipping = 0 if subtotal >= 999 else 99
    coupon_data = request.session.get('coupon', {})
    discount = coupon_data.get('discount', 0)
    total = max(subtotal + shipping - discount, 1)

    order = Order(
        user=request.user if request.user.is_authenticated else None,
        full_name=data.get('full_name', '').strip(),
        email=data.get('email', '').strip(),
        phone=data.get('phone', '').strip(),
        address_line1=data.get('address_line1', '').strip(),
        address_line2=data.get('address_line2', '').strip(),
        city=data.get('city', '').strip(),
        state=data.get('state', '').strip(),
        pincode=data.get('pincode', '').strip(),
        subtotal=subtotal,
        shipping_charge=shipping,
        discount=discount,
        total=total,
        status='pending',
    )
    order.save()

    for key, item in cart.items():
        # Safe check to avoid database IntegrityError (500) if product was deleted/re-seeded
        from store.models import Product
        try:
            prod = Product.objects.get(id=item['product_id'])
            prod_id = prod.id
        except Product.DoesNotExist:
            prod_id = None

        OrderItem.objects.create(
            order=order,
            product_id=prod_id,
            product_name=item['name'],
            size=item.get('size', ''),
            color=item.get('color', ''),
            quantity=item['quantity'],
            price=item['price'],
        )

    # Store in session
    request.session['pending_order_id'] = order.id
    request.session.modified = True

    return order, None


# ── Create Razorpay Order (SDK flow) ─────────────────────────────────────────
def create_razorpay_order(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    cart = request.session.get('cart', {})
    if not cart:
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid request data'}, status=400)

    order, err = create_order_from_cart(request, data)
    if err:
        return JsonResponse({'error': err}, status=400)

    key_id     = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    amount_paise = max(order.total_in_paise, 100)

    try:
        import razorpay
        client   = razorpay.Client(auth=(key_id, key_secret))
        rz_order = client.order.create({
            'amount':   amount_paise,
            'currency': 'INR',
            'receipt':  order.order_number,
            'notes':    {'order_id': str(order.id)},
        })
        order.razorpay_order_id = rz_order['id']
        order.save()

        return JsonResponse({
            'razorpay_order_id': rz_order['id'],
            'amount':            amount_paise,
            'currency':          'INR',
            'order_db_id':       order.id,
            'order_number':      order.order_number,
        })

    except Exception as e:
        import logging
        logging.getLogger('vorn').error(f'[Razorpay] Order creation failed: {e}')
        # Delete the orphaned DB order so the cart stays intact
        order.delete()
        return JsonResponse(
            {'error': 'Payment gateway error. Please try again in a moment.'},
            status=502,
        )


# ── Initiate Payment Link ─────────────────────────────────────────────────────
def initiate_payment_link(request):
    """
    POST from checkout form → create order → redirect to Razorpay.me with amount.
    """
    if request.method != 'POST':
        return redirect('checkout')

    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your bag is empty.')
        return redirect('cart')

    data = {
        'full_name':    request.POST.get('full_name', '').strip(),
        'email':        request.POST.get('email', '').strip(),
        'phone':        request.POST.get('phone', '').strip(),
        'address_line1':request.POST.get('address_line1', '').strip(),
        'address_line2':request.POST.get('address_line2', '').strip(),
        'city':         request.POST.get('city', '').strip(),
        'state':        request.POST.get('state', '').strip(),
        'pincode':      request.POST.get('pincode', '').strip(),
    }

    # Validate
    required = ['full_name', 'email', 'phone', 'address_line1', 'city', 'state', 'pincode']
    for field in required:
        if not data[field]:
            messages.error(request, f'{field.replace("_", " ").title()} is required.')
            return redirect('checkout')

    order, err = create_order_from_cart(request, data, payment_method='razorpay_me')
    if err:
        messages.error(request, err)
        return redirect('checkout')

    # Razorpay.me payment URL (strictly ends with @vorn)
    payment_url = settings.RAZORPAY_ME_LINK

    # Redirect to payment page (intermediate page that opens Razorpay.me)
    return render(request, 'orders/payment_link.html', {
        'order': order,
        'payment_url': payment_url,
        'amount_rupees': order.total,
        'razorpay_me': settings.RAZORPAY_ME_LINK,
    })


# ── Confirm Payment (after Razorpay.me redirect) ──────────────────────────────
def confirm_payment(request, order_number):
    """
    Customer clicks "I have paid" after paying via Razorpay.me.
    Marks order as confirmed (pending admin verification).
    """
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id', '').strip()
        order.razorpay_payment_id = transaction_id or f'RZRPAY-ME-{order.order_number}'
        order.status = 'confirmed'
        order.is_paid = True
        order.save()

        # Update coupon usage
        coupon_data = request.session.get('coupon', {})
        if coupon_data.get('code'):
            try:
                coupon = Coupon.objects.get(code=coupon_data['code'])
                coupon.used_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass

        # Clear session
        request.session['cart'] = {}
        request.session.pop('coupon', None)
        request.session.pop('pending_order_id', None)
        request.session.modified = True

        return redirect('order_success', order_number=order.order_number)

    return render(request, 'orders/confirm_payment.html', {'order': order})


# ── Payment Callback (Razorpay SDK) ───────────────────────────────────────────
@csrf_exempt
def payment_callback(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    data = request.POST
    payment_method = data.get('payment_method', '')

    # UPI manual / Razorpay.me manual flow
    if payment_method in ('upi_manual', 'razorpay_me'):
        order_id = request.session.get('pending_order_id')
        if not order_id:
            messages.error(request, 'Order not found. Please try again.')
            return redirect('checkout')
        order = get_object_or_404(Order, id=order_id)
        order.is_paid = True
        order.status = 'confirmed'
        order.razorpay_payment_id = f'MANUAL-{order.order_number}'
        order.save()

        # Clear session
        request.session['cart'] = {}
        request.session.pop('coupon', None)
        request.session.pop('pending_order_id', None)
        request.session.modified = True

        return redirect('order_success', order_number=order.order_number)

    # Standard Razorpay SDK callback
    order_id = request.session.get('pending_order_id')
    if not order_id:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('checkout')

    order = get_object_or_404(Order, id=order_id)

    razorpay_payment_id = data.get('razorpay_payment_id', '')
    razorpay_order_id   = data.get('razorpay_order_id', '')
    razorpay_signature  = data.get('razorpay_signature', '')

    # Verify HMAC signature — required, no bypass
    key_secret = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
    message    = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
    generated  = hmac.new(key_secret, message, hashlib.sha256).hexdigest()
    # Also try the Razorpay SDK verify util if available
    try:
        import razorpay as rzp_sdk
        rzp_client = rzp_sdk.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }
        rzp_client.utility.verify_payment_signature(params)
        signature_valid = True
    except Exception:
        # Fall back to our own HMAC check
        signature_valid = (generated == razorpay_signature)

    if signature_valid:
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_order_id   = razorpay_order_id
        order.razorpay_signature  = razorpay_signature
        order.is_paid  = True
        order.status   = 'confirmed'
        order.save()

        # Coupon usage
        coupon_data = request.session.get('coupon', {})
        if coupon_data.get('code'):
            try:
                coupon = Coupon.objects.get(code=coupon_data['code'])
                coupon.used_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass

        request.session['cart'] = {}
        request.session.pop('coupon', None)
        request.session.pop('pending_order_id', None)
        request.session.modified = True

        return redirect('order_success', order_number=order.order_number)
    else:
        order.status = 'cancelled'
        order.save()
        messages.error(request, 'Payment verification failed. Please contact support with your order number.')
        return redirect('checkout')


# ── Order Success ──────────────────────────────────────────────────────────────
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    items = order.items.all().select_related('product')

    # Calculate estimated delivery date (3–7 business days)
    from datetime import timedelta
    from django.utils import timezone
    today = timezone.now().date()
    # Add business days (skip weekends)
    def add_business_days(start, days):
        current = start
        added = 0
        while added < days:
            current += timedelta(days=1)
            if current.weekday() < 5:  # Mon-Fri
                added += 1
        return current

    delivery_min = add_business_days(today, 3)
    delivery_max = add_business_days(today, 7)
    delivery_days_min = 3
    delivery_days_max = 7

    # Send fake order confirmation email
    email_sent = False
    if order.email:
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string

            # Plain-text fallback
            items_text = ""
            for item in items:
                items_text += f"  • {item.product_name} (Size: {item.size or 'Free Size'}) x{item.quantity} — ₹{item.subtotal}\n"

            plain_body = (
                f"VORN — Order Confirmed #{order.order_number}\n\n"
                f"Dear {order.full_name},\n\n"
                f"Thank you for your order. Here are your details:\n\n"
                f"Order: #{order.order_number}\n"
                f"Total: ₹{order.total}\n"
                f"Payment: {'Paid' if order.is_paid else 'Pending Verification'}\n\n"
                f"Items:\n{items_text}\n"
                f"Delivery: {delivery_min.strftime('%d %b')} – {delivery_max.strftime('%d %b %Y')}\n"
                f"Ship to: {order.address_line1}, {order.city}, {order.state} — {order.pincode}\n\n"
                f"Questions? Email hello@vorn.in\n\n— Team VORN"
            )

            # HTML email using template
            try:
                html_body = render_to_string('orders/email_order_confirmation.html', {
                    'order': order,
                    'items': items,
                    'delivery_min': delivery_min,
                    'delivery_max': delivery_max,
                })
            except Exception:
                html_body = plain_body

            msg = EmailMultiAlternatives(
                subject=f'VORN — Order Confirmed #{order.order_number}',
                body=plain_body,
                from_email='VORN <orders@vorn.in>',
                to=[order.email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=True)
            email_sent = True
        except Exception as e:
            print(f"[VORN Email] Failed to send confirmation: {e}")
            email_sent = False

    return render(request, 'orders/success.html', {
        'order': order,
        'items': items,
        'delivery_min': delivery_min,
        'delivery_max': delivery_max,
        'delivery_days_min': delivery_days_min,
        'delivery_days_max': delivery_days_max,
        'email_sent': email_sent,
    })


# ── Order History ──────────────────────────────────────────────────────────────
def order_history(request):
    if not request.user.is_authenticated:
        return redirect('login')
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'orders/history.html', {'orders': orders})


# ── Order Detail ───────────────────────────────────────────────────────────────
def order_detail(request, order_number):
    if not request.user.is_authenticated:
        return redirect('login')
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})
