"""
VORN DB update script: mark new arrivals, add women's perfumes, update images.
Run: python manage.py shell < seed_updates.py
Or: python seed_updates.py (if called from correct Django environment)
"""
import django
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vorn_project.settings')
django.setup()

from store.models import Product, Category, ProductImage
from django.core.files.base import ContentFile

# ── 1. Mark products as new arrivals ──────────────────────────────────
new_arrival_slugs = [
    'asymmetric-satin-gown',
    'mulberry-silk-slip-dress',
    'monarch-silk-draped-blouse',
    'elysian-wide-leg-silk-pant',
    'cashmere-belted-wrap-coat',
    'vorn-bergamote-noble',
    'vorn-imperial-sandalwood',
    'vorn-vetiver-ancestral',
    'ivory-linen-shirt',
    'charcoal-slim-trouser',
    'savile-row-double-breasted-suit',
    'merino-shawl-collar-cardigan',
    'asymmetric-silk-satin-slip-dress',
    'heritage-tweed-overcoat',
]
count = Product.objects.filter(slug__in=new_arrival_slugs).update(
    is_new_arrival=True,
    is_featured=True
)
print(f'[1] Marked {count} products as new arrivals + featured')

# ── 2. Add Women's Perfumes ─────────────────────────────────────────
perfumes_cat = Category.objects.get(slug='perfumes')

women_perfumes = [
    {
        'name': 'VORN Neroli Lumière',
        'slug': 'vorn-neroli-lumiere',
        'short_description': 'A radiant citrus floral — bergamot, neroli blossom, and white musk on a warm amber base.',
        'description': 'Neroli Lumière opens with a burst of Sicilian bergamot and sun-kissed neroli blossom, cascading into a heart of jasmine sambac and tuberose. The dry-down settles on warm white musk and ambrette, leaving a luminous, skin-close sillage. A fragrance of effortless femininity.',
        'price': '4200',
        'compare_price': '5200',
        'gender': 'W',
        'material': '100ml · Eau de Parfum',
        'care_instructions': 'Spray on pulse points. Keep away from direct sunlight.',
        'image_path': 'static/images/products/perfume_neroli_lumiere_women.png',
        'image_name': 'perfume_neroli_lumiere_women.png',
    },
    {
        'name': 'VORN Rose Oud Elixir',
        'slug': 'vorn-rose-oud-elixir',
        'short_description': 'A heady rose oud for evenings — Turkish rose, aged oud, and smoky vetiver.',
        'description': 'Rose Oud Elixir is an intoxicating blend of Bulgarian and Turkish rose absolute, entwined with precious aged oud and dark patchouli. A base of smoky vetiver and labdanum resin gives depth and tenacity. Rich, enigmatic, and unmistakably feminine.',
        'price': '5800',
        'compare_price': '6500',
        'gender': 'W',
        'material': '100ml · Eau de Parfum',
        'care_instructions': 'Spray on pulse points. A little goes a long way.',
        'image_path': 'static/images/products/perfume_rose_oud_elixir_women.png',
        'image_name': 'perfume_rose_oud_elixir_women.png',
    },
    {
        'name': 'VORN Fleur de Cashmere',
        'slug': 'vorn-fleur-de-cashmere',
        'short_description': 'Soft, powdery cashmere florals — iris, violet leaf, and warm sandalwood.',
        'description': 'Fleur de Cashmere is the scent of warmth and intimacy. A soft, enveloping floral built around iris root, violet leaves, and peony petals. The base of creamy sandalwood and tonka bean wraps the skin in a velvety, cashmere-like warmth that lasts through the day.',
        'price': '3800',
        'compare_price': '4500',
        'gender': 'W',
        'material': '100ml · Eau de Parfum',
        'care_instructions': 'Spray on pulse points. Store at room temperature.',
        'image_path': 'static/images/products/perfume_fleur_cashmere_women.png',
        'image_name': 'perfume_fleur_cashmere_women.png',
    },
]

for p_data in women_perfumes:
    if Product.objects.filter(slug=p_data['slug']).exists():
        print(f'[2] Already exists: {p_data["name"]}')
        continue

    p = Product.objects.create(
        name=p_data['name'],
        slug=p_data['slug'],
        category=perfumes_cat,
        short_description=p_data['short_description'],
        description=p_data['description'],
        price=p_data['price'],
        compare_price=p_data['compare_price'],
        gender=p_data['gender'],
        material=p_data['material'],
        care_instructions=p_data['care_instructions'],
        is_active=True,
        is_new_arrival=True,
        is_featured=True,
        stock=50,
    )

    img_path = p_data['image_path']
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            pi = ProductImage(product=p, is_primary=True, sort_order=0, alt_text=p.name)
            pi.image.save(p_data['image_name'], ContentFile(f.read()), save=True)
        print(f'[2] Created with image: {p.name}')
    else:
        print(f'[2] Created (no image at {img_path}): {p.name}')

# ── 3. Add editorial images to women's products that lack a primary image ──
women_image_map = {
    'Cashmere Belted Wrap Coat': ('static/images/products/womens_outerwear_editorial.png', 'womens_outerwear_editorial.png'),
    'Asymmetric Satin Gown': ('static/images/products/womens_silk_dress_editorial.png', 'womens_silk_dress_editorial.png'),
    'Monarch Silk Draped Blouse': ('static/images/products/womens_cashmere_top_editorial.png', 'womens_cashmere_top_editorial.png'),
}

for prod_name, (img_path, img_name) in women_image_map.items():
    if not os.path.exists(img_path):
        print(f'[3] Image not found: {img_path}')
        continue
    products = Product.objects.filter(name=prod_name)
    if not products.exists():
        print(f'[3] Product not found: {prod_name}')
        continue
    prod = products.first()
    existing = prod.images.filter(is_primary=True).first()
    if existing:
        print(f'[3] Already has primary image: {prod_name}')
        continue
    with open(img_path, 'rb') as f:
        pi = ProductImage(product=prod, is_primary=True, sort_order=0, alt_text=prod.name)
        pi.image.save(img_name, ContentFile(f.read()), save=True)
    print(f'[3] Added editorial image: {prod_name}')

print('\nAll DB updates complete!')
print(f'New arrivals total: {Product.objects.filter(is_new_arrival=True, is_active=True).count()}')
print(f'Women perfumes: {Product.objects.filter(gender="W", category__slug="perfumes").count()}')
