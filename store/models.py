from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
import os


class ProductTag(models.Model):
    """Editorial tags: 'BESTSELLER', 'STAFF PICK', 'EXCLUSIVE', etc."""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)
    color = models.CharField(max_length=20, default='gold', help_text='CSS color name or hex')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    GENDER_CHOICES = [
        ('M', 'Men'),
        ('W', 'Women'),
        ('U', 'Unisex'),
    ]
    SIZE_XS = 'XS'
    SIZE_S = 'S'
    SIZE_M = 'M'
    SIZE_L = 'L'
    SIZE_XL = 'XL'
    SIZE_XXL = 'XXL'

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                        help_text="Original price (for showing discount)")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    material = models.CharField(max_length=200, blank=True)
    care_instructions = models.TextField(blank=True)
    shipping_info = models.TextField(blank=True, help_text='Shipping & returns info shown on PDP')
    weight_grams = models.PositiveIntegerField(null=True, blank=True, help_text='Product weight in grams')
    dimensions = models.CharField(max_length=100, blank=True, help_text='e.g. 30cm x 20cm x 5cm')
    tags = models.ManyToManyField('ProductTag', blank=True, related_name='products')
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    stock = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return None

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img

    @property
    def price_in_paise(self):
        return int(self.price * 100)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Add VORN watermark to uploaded images
        if self.image:
            self._add_watermark()

    def _add_watermark(self):
        try:
            img_path = self.image.path
            img = Image.open(img_path).convert('RGBA')
            width, height = img.size
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            text = 'VORN'
            font_size = max(width // 20, 24)
            try:
                font = ImageFont.truetype('arial.ttf', font_size)
            except Exception:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = width - text_width - 20
            y = height - text_height - 20
            draw.text((x, y), text, font=font, fill=(201, 169, 110, 100))
            combined = Image.alpha_composite(img, watermark)
            combined.convert('RGB').save(img_path, 'JPEG', quality=95)
        except Exception:
            pass


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50, blank=True)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True)

    class Meta:
        unique_together = ['product', 'size', 'color']

    def __str__(self):
        return f"{self.product.name} - {self.size} {self.color}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"VORN-{self.product.id}-{self.size}-{self.color[:3].upper() if self.color else 'NA'}"
        super().save(*args, **kwargs)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    body = models.TextField()
    image = models.ImageField(upload_to='reviews/', null=True, blank=True, help_text='Optional photo review')
    helpful_count = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}★"


# ── CMS / Homepage Content Models ─────────────────────────────────────────────

class HeroBanner(models.Model):
    """Admin-managed homepage hero (video or image)."""
    MEDIA_CHOICES = [('video', 'Video'), ('image', 'Image')]

    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True)
    eyebrow = models.CharField(max_length=100, blank=True, help_text='Small caps label above title')
    media_type = models.CharField(max_length=10, choices=MEDIA_CHOICES, default='image')
    video = models.FileField(upload_to='banners/', null=True, blank=True)
    image = models.ImageField(upload_to='banners/', null=True, blank=True)
    cta_text = models.CharField(max_length=80, blank=True, default='Explore Collection')
    cta_url = models.CharField(max_length=200, blank=True, default='/shop/')
    cta2_text = models.CharField(max_length=80, blank=True)
    cta2_url = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']
        verbose_name = 'Hero Banner'
        verbose_name_plural = 'Hero Banners'

    def __str__(self):
        return self.title


class EditorialSection(models.Model):
    """Flexible homepage content block manageable from admin."""
    POSITION_CHOICES = [
        ('manifesto', 'Brand Manifesto'),
        ('lookbook', 'Lookbook Strip'),
        ('edit', 'The VORN Edit'),
        ('usp', 'USP Strip'),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True)
    image = models.ImageField(upload_to='editorial/', null=True, blank=True)
    position = models.CharField(max_length=30, choices=POSITION_CHOICES)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.get_position_display()} — {self.title}"


class LookbookPage(models.Model):
    """Editorial lookbook campaign."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    season = models.CharField(max_length=50, blank=True, help_text='e.g. SS26, AW26')
    cover_image = models.ImageField(upload_to='lookbooks/')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
