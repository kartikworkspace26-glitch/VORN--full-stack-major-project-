from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile, Address, Wishlist, NewsletterSubscriber
from orders.models import Order


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


# ── Register ──────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        errors = []
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username is already taken.')
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if len(password1) < 8:
            errors.append('Password must be at least 8 characters.')
        if password1 != password2:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accounts/register.html', {
                'first_name': first_name, 'last_name': last_name,
                'username': username, 'email': email,
            })

        user = User.objects.create_user(
            username=username, email=email, password=password1,
            first_name=first_name, last_name=last_name
        )
        # Create profile
        get_or_create_profile(user)

        login(request, user)
        messages.success(request, f'Welcome to VORN, {first_name or username}! Your account has been created.')
        return redirect('home')

    return render(request, 'accounts/register.html')


# ── Login ─────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Allow login with email
        if '@' in username:
            try:
                user_obj = User.objects.get(email__iexact=username)
                username = user_obj.username
            except User.DoesNotExist:
                pass

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            get_or_create_profile(user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.POST.get('next') or request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials. Please try again.')

    next_url = request.GET.get('next', '')
    return render(request, 'accounts/login.html', {'next': next_url})


# ── Logout ────────────────────────────────────────────────────────────────────
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out. See you soon.')
    return redirect('home')


# ── Profile ───────────────────────────────────────────────────────────────────
@login_required
def profile_view(request):
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        action = request.POST.get('action', 'update_profile')

        if action == 'update_profile':
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name  = request.POST.get('last_name', user.last_name).strip()
            user.email      = request.POST.get('email', user.email).strip()
            user.save()

            profile.phone  = request.POST.get('phone', profile.phone).strip()
            profile.gender = request.POST.get('gender', profile.gender)
            dob = request.POST.get('date_of_birth')
            if dob:
                try:
                    from datetime import date
                    parts = dob.split('-')
                    profile.date_of_birth = date(int(parts[0]), int(parts[1]), int(parts[2]))
                except Exception:
                    pass
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')

        elif action == 'change_password':
            old_pw = request.POST.get('old_password', '')
            new_pw1 = request.POST.get('new_password1', '')
            new_pw2 = request.POST.get('new_password2', '')

            if not request.user.check_password(old_pw):
                messages.error(request, 'Current password is incorrect.')
            elif len(new_pw1) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
            elif new_pw1 != new_pw2:
                messages.error(request, 'New passwords do not match.')
            else:
                request.user.set_password(new_pw1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
            return redirect('profile')

    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    addresses = Address.objects.filter(user=request.user)
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product').prefetch_related('product__images')[:30]

    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': profile,
        'recent_orders': orders,
        'addresses': addresses,
        'wishlist_items': wishlist_items,
        'tab': request.GET.get('tab', 'profile'),
    })


# ── Address CRUD ──────────────────────────────────────────────────────────────
@login_required
def add_address(request):
    if request.method == 'POST':
        addr = Address(
            user=request.user,
            label=request.POST.get('label', 'home'),
            full_name=request.POST.get('full_name', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            address_line1=request.POST.get('address_line1', '').strip(),
            address_line2=request.POST.get('address_line2', '').strip(),
            city=request.POST.get('city', '').strip(),
            state=request.POST.get('state', '').strip(),
            pincode=request.POST.get('pincode', '').strip(),
            is_default=request.POST.get('is_default') == 'on',
        )
        addr.save()
        messages.success(request, 'Address added successfully.')
    return redirect('profile')


@login_required
def delete_address(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr.delete()
    messages.success(request, 'Address removed.')
    return redirect('profile')


@login_required
def set_default_address(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    addr.is_default = True
    addr.save()
    messages.success(request, 'Default address updated.')
    return redirect('profile')


# ── Newsletter Subscribe ───────────────────────────────────────────────────────
def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        name  = request.POST.get('name', '').strip()
        if email:
            NewsletterSubscriber.objects.get_or_create(email=email, defaults={'name': name})
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, "You're subscribed! Welcome to The VORN Edit.")
    return redirect('home')
