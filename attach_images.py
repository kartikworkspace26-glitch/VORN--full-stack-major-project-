import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vorn_project.settings')
django.setup()

from store.models import Product, ProductImage, ProductVariant

# Map: product slug -> image filename (inside media/products/)
image_map = {
    'obsidian-oxford-shirt':  'products/oxford_shirt.png',
    'ivory-linen-shirt':      'products/linen_shirt.png',
    'charcoal-slim-trouser':  'products/charcoal_trouser.png',
    'camel-overcoat':         'products/camel_overcoat.png',
    'midnight-merino-crewneck':'products/merino_crewneck.png',
    'leather-card-wallet':    'products/leather_wallet.png',
}

for slug, img_path in image_map.items():
    try:
        p = Product.objects.get(slug=slug)
        # Remove old images first
        p.images.all().delete()
        pi = ProductImage(product=p, image=img_path, is_primary=True, sort_order=0,
                          alt_text=f'{p.name} - VORN')
        # Save without calling watermark (image already exists)
        ProductImage.objects.create(product=p, image=img_path,
                                    is_primary=True, sort_order=0,
                                    alt_text=f'{p.name} - VORN')
        print(f'[OK] {p.name} -> {img_path}')
    except Product.DoesNotExist:
        print(f'[SKIP] No product with slug: {slug}')

# Add size variants to clothing products
clothing_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
clothing_slugs = ['obsidian-oxford-shirt', 'ivory-linen-shirt',
                  'charcoal-slim-trouser', 'camel-overcoat', 'midnight-merino-crewneck']
shoe_sizes = ['6', '7', '8', '9', '10', '11']

for slug in clothing_slugs:
    try:
        p = Product.objects.get(slug=slug)
        if not p.variants.exists():
            for s in clothing_sizes:
                ProductVariant.objects.create(product=p, size=s, color='', stock=20)
            print(f'[SIZES] {p.name}: {", ".join(clothing_sizes)}')
    except Product.DoesNotExist:
        pass

try:
    boot = Product.objects.get(slug='desert-sand-chelsea-boot')
    if not boot.variants.exists():
        for s in shoe_sizes:
            ProductVariant.objects.create(product=boot, size=s, color='', stock=8)
        print(f'[SIZES] {boot.name}: {", ".join(shoe_sizes)}')
except Product.DoesNotExist:
    pass

print('\nDone! Images and variants attached.')
