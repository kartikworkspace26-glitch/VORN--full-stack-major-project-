"""
VORN Security Middleware
Adds comprehensive HTTP security headers to every response.
"""

from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Injects security headers on every response:
      - Content-Security-Policy
      - Referrer-Policy
      - Permissions-Policy
      - X-Content-Type-Options
      - X-Frame-Options
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ── Content-Security-Policy ─────────────────────────────────────────
        # Allow our own origin, Google Fonts, Razorpay, Font Awesome CDN,
        # and the Groq API (backend only — no direct browser calls).
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://checkout.razorpay.com https://cdnjs.cloudflare.com https://ka-f.fontawesome.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://ka-f.fontawesome.com; "
            "font-src 'self' https://fonts.gstatic.com https://ka-f.fontawesome.com data:; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://checkout.razorpay.com; "
            "frame-src https://checkout.razorpay.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self' https://api.razorpay.com;"
        )
        response["Content-Security-Policy"] = csp

        # ── Referrer-Policy ─────────────────────────────────────────────────
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ── Permissions-Policy ──────────────────────────────────────────────
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(self), usb=(), magnetometer=(), gyroscope=()"
        )

        # ── X-Content-Type-Options ──────────────────────────────────────────
        response["X-Content-Type-Options"] = "nosniff"

        # ── X-Frame-Options ─────────────────────────────────────────────────
        response["X-Frame-Options"] = "SAMEORIGIN"

        # ── Remove server fingerprinting ────────────────────────────────────
        if "Server" in response:
            del response["Server"]
        if "X-Powered-By" in response:
            del response["X-Powered-By"]

        return response


class RateLimitMiddleware:
    """
    Simple in-memory rate limiter for sensitive endpoints.
    Uses Django's cache backend (LocMemCache or Redis in production).
    Limits: 10 requests / 60 s per IP on protected paths.
    """
    PROTECTED_PATHS = [
        '/accounts/login/',
        '/accounts/register/',
        '/api/ai-stylist/',
        '/orders/create-razorpay-order/',
        '/orders/payment-callback/',
    ]
    LIMIT = 20       # max requests
    WINDOW = 60      # seconds

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in self.PROTECTED_PATHS):
            from django.core.cache import cache
            from django.http import HttpResponse

            ip = self._get_client_ip(request)
            cache_key = f'rl:{request.path}:{ip}'
            count = cache.get(cache_key, 0)

            if count >= self.LIMIT:
                return HttpResponse(
                    '<h1>429 Too Many Requests</h1><p>Please slow down.</p>',
                    status=429,
                    content_type='text/html',
                )

            cache.set(cache_key, count + 1, timeout=self.WINDOW)

        return self.get_response(request)

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
