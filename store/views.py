from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Avg
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from .models import Product, Category, Review


# ── Homepage ──────────────────────────────────────────────────────────────────
def homepage(request):
    featured = Product.objects.filter(is_featured=True, is_active=True)[:8]
    new_arrivals = Product.objects.filter(is_new_arrival=True, is_active=True)[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    return render(request, 'store/home.html', {
        'featured': featured,
        'featured_products': featured,
        'new_arrivals': new_arrivals,
        'categories': categories,
    })


# ── Catalog ───────────────────────────────────────────────────────────────────
def catalog(request):
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    categories = Category.objects.filter(is_active=True)

    # Filters
    category_slug = request.GET.get('category')
    gender = request.GET.get('gender')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', '-created_at')
    q = request.GET.get('q', '')

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)
    if gender:
        if gender in ['M', 'W']:
            products = products.filter(Q(gender=gender) | Q(gender='U'))
        else:
            products = products.filter(gender=gender)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    is_new = request.GET.get('is_new')
    if is_new:
        products = products.filter(is_new_arrival=True)

    sort_options = {
        '-created_at': 'Newest First',
        'price': 'Price: Low to High',
        '-price': 'Price: High to Low',
        'name': 'Name A–Z',
    }
    if sort in sort_options:
        products = products.order_by(sort)

    return render(request, 'store/catalog.html', {
        'products': products,
        'categories': categories,
        'active_category': active_category,
        'sort_options': sort_options,
        'current_sort': sort,
        'query': q,
        'gender_filter': gender,
        'max_price': max_price,
        'is_new': is_new,
    })


# ── Product Detail ────────────────────────────────────────────────────────────
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()
    variants = product.variants.all()
    reviews = product.reviews.filter().select_related('user')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]

    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'images': images,
        'variants': variants,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'related': related,
        'user_review': user_review,
    })


# ── Cart ──────────────────────────────────────────────────────────────────────
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for key, item in cart.items():
        subtotal = item['price'] * item['quantity']
        total += subtotal
        cart_items.append({**item, 'key': key, 'subtotal': subtotal})
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


def cart_json_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    count = 0
    for key, item in cart.items():
        subtotal = item['price'] * item['quantity']
        total += subtotal
        count += item['quantity']
        items.append({
            'key': key,
            'product_id': item['product_id'],
            'name': item['name'],
            'price': float(item['price']),
            'size': item.get('size', ''),
            'color': item.get('color', ''),
            'quantity': item['quantity'],
            'image': item.get('image', ''),
            'subtotal': float(subtotal),
        })
    return JsonResponse({
        'items': items,
        'total': float(total),
        'subtotal': float(total),
        'count': count,
    })


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    size = request.POST.get('size', 'Free Size')
    color = request.POST.get('color', '')
    quantity = int(request.POST.get('quantity', 1))

    cart = request.session.get('cart', {})
    key = f"{product_id}_{size}_{color}"

    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'product_id': product_id,
            'name': product.name,
            'price': float(product.price),
            'size': size,
            'color': color,
            'quantity': quantity,
            'image': product.primary_image.image.url if product.primary_image else '',
        }

    request.session['cart'] = cart
    request.session.modified = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        count = sum(i.get('quantity', 0) for i in cart.values())
        return JsonResponse({'success': True, 'cart_count': count, 'message': f'{product.name} added to bag!'})

    messages.success(request, f'"{product.name}" added to your bag.')
    return redirect('cart')


def remove_from_cart(request, key):
    cart = request.session.get('cart', {})
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Item removed from bag.')
    return redirect('cart')


def update_cart(request, key):
    quantity = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})
    if key in cart:
        if quantity > 0:
            cart[key]['quantity'] = quantity
        else:
            del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')


# ── Search ────────────────────────────────────────────────────────────────────
def search(request):
    q = request.GET.get('q', '')
    products = []
    if q:
        products = Product.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q),
            is_active=True
        ).select_related('category').prefetch_related('images')

    if request.GET.get('format') == 'json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        products_json = []
        for p in products[:8]:
            primary_img = p.primary_image
            image_url = primary_img.image.url if primary_img else ''
            products_json.append({
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'image': image_url,
                'url': f'/product/{p.slug}/',
            })
        return JsonResponse({'products': products_json})

    return render(request, 'store/search.html', {'products': products, 'query': q})


# ── Wishlist (session-based) ───────────────────────────────────────────────────
def wishlist(request):
    ids = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=ids, is_active=True).prefetch_related('images')
    return render(request, 'store/wishlist.html', {'products': products})


def toggle_wishlist(request, product_id):
    wishlist = request.session.get('wishlist', [])
    if product_id in wishlist:
        wishlist.remove(product_id)
        added = False
    else:
        wishlist.append(product_id)
        added = True
    request.session['wishlist'] = wishlist
    request.session.modified = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'added': added, 'count': len(wishlist)})
    return redirect('wishlist')


# ── Review Submit ─────────────────────────────────────────────────────────────
def submit_review(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        title = request.POST.get('title', '')
        body = request.POST.get('body', '')
        Review.objects.update_or_create(
            product=product, user=request.user,
            defaults={'rating': rating, 'title': title, 'body': body}
        )
        messages.success(request, 'Your review has been submitted.')
    return redirect('product_detail', slug=product.slug)


# ── Lookbook & Size Guide ─────────────────────────────────────────────────────
def lookbook(request):
    return render(request, 'store/lookbook.html')


def size_guide(request):
    return render(request, 'store/size_guide.html')


def contact_view(request):
    return render(request, 'store/contact.html')


def legal_view(request):
    return render(request, 'store/legal.html')


@csrf_exempt
def ai_stylist(request):
    """
    VORN AI Personal Stylist — powered by Groq (llama-3.3-70b-versatile).
    Accepts POST { "message": "...", "model": "..." } and returns { "reply": "..." }.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        selected_model = data.get('model', 'gemini-nano-banana-pro').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not user_message:
        return JsonResponse({
            'reply': (
                'Welcome to VORN\'s styling parlour. I am your personal AI stylist. '
                'Ask me anything — outfits, sizing, fragrances, or occasion dressing. '
                'How may I assist you today?'
            )
        })

    # ── Build catalog context (last 80 products to stay within token limit) ────
    active_products = (
        Product.objects.filter(is_active=True)
        .select_related('category')
        .order_by('-created_at')[:80]
    )
    catalog_lines = []
    for p in active_products:
        gender_label = {'M': 'Men', 'W': 'Women', 'U': 'Unisex'}.get(p.gender, p.gender)
        catalog_lines.append(
            f"• {p.name} | {p.category.name} | ₹{p.price} | {gender_label} | "
            f"Material: {p.material or 'Premium'} | /product/{p.slug}/"
        )
    catalog_context = "\n".join(catalog_lines)

    # Customise based on model
    if selected_model == 'gemini-nano-banana-pro':
        model_name_for_prompt = "Gemini Nano Banana Pro model"
    else:
        model_name_for_prompt = "Groq LLaMA 3.3 70B model"

    system_prompt = f"""You are the VORN AI Personal Stylist — a sophisticated, refined, and knowledgeable luxury fashion assistant for VORN, a high-fashion minimalist clothing and fragrance brand from India. You are powered by the {model_name_for_prompt}.

Your personality:
- Eloquent, warm, and exclusive — like a personal shopper at a luxury boutique
- Knowledgeable about fabrics, silhouettes, fits, colour coordination, and fragrance
- Concise but rich in detail — never verbose, always intentional

VORN's SS26 Catalog (use ONLY these products in recommendations):
{catalog_context}

Instructions:
1. Recommend actual VORN products from the catalog above that match the user's request
2. Format product links as markdown: [Product Name](/product/slug/)
3. Always mention price in ₹
4. For clothing, mention material, fit, and how to style it
5. For fragrance, describe the scent character and occasion
6. If asked something unrelated to fashion/styling, gently redirect to VORN's collection
7. Never mention Groq, LLaMA, or any AI/technical details (other than acknowledging you are powered by the {model_name_for_prompt} if asked)
8. Keep responses under 300 words — curated, not exhaustive"""

    # ── Groq API call ─────────────────────────────────────────────────────────
    from django.conf import settings as django_settings
    groq_key = getattr(django_settings, 'GROQ_API_KEY', '')

    if groq_key:
        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {groq_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user',   'content': user_message},
                    ],
                    'max_tokens': 500,
                    'temperature': 0.72,
                    'stream': False,
                },
                timeout=15,
            )
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                return JsonResponse({'reply': reply})
            else:
                print(f"[VORN AI] Groq API error {response.status_code}: {response.text[:200]}")
        except Exception as exc:
            print(f"[VORN AI] Groq request failed: {exc}")

    # ── Local smart fallback ──────────────────────────────────────────────────
    message_lower = user_message.lower()
    stopwords = {'show', 'find', 'style', 'with', 'what', 'wear', 'want', 'need',
                 'give', 'like', 'some', 'look', 'best', 'have', 'does', 'that',
                 'this', 'from', 'which', 'your', 'vorn'}
    keywords = [w.strip(',.!?') for w in message_lower.split()
                if len(w.strip(',.!?')) > 2 and w.strip(',.!?') not in stopwords]

    matched = []
    if keywords:
        q_filter = Q()
        for kw in keywords:
            q_filter |= (
                Q(name__icontains=kw) |
                Q(description__icontains=kw) |
                Q(category__name__icontains=kw) |
                Q(material__icontains=kw)
            )
        matched = list(Product.objects.filter(q_filter, is_active=True).select_related('category')[:5])

    if not matched:
        for cat in Category.objects.filter(is_active=True):
            if cat.name.lower() in message_lower:
                matched = list(Product.objects.filter(category=cat, is_active=True)[:5])
                break

    if matched:
        lines = [
            "Based on your request, here are my curated picks from VORN's SS26 collection:\n"
        ]
        for p in matched:
            lines.append(
                f"- **[{p.name}](/product/{p.slug}/)** — ₹{p.price}  \n"
                f"  *{p.material or 'Premium fabric'} · {p.category.name}*  \n"
                f"  {p.short_description or ''}"
            )
        lines.append(
            "\nWould you like styling advice on any of these pieces, or shall I suggest a complete look?"
        )
        return JsonResponse({'reply': "\n".join(lines)})

    # Generic greeting fallback
    return JsonResponse({'reply': (
        "I would be delighted to help you discover VORN's collection. "
        "Tell me about the occasion, your preferred silhouette, or a colour palette — "
        "and I will curate a look just for you."
    )})

