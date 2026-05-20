import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vorn_project.settings')
django.setup()

from store.models import Category, Product, ProductImage, ProductVariant
from orders.models import Coupon
from django.utils import timezone
from datetime import timedelta
from django.core.files import File

BASE = os.path.dirname(os.path.abspath(__file__))

PRODUCT_IMAGES = {
    'obsidian-oxford-shirt': 'media/products/obsidian-oxford-shirt.jpg',
    'ivory-linen-shirt': 'media/products/ivory-linen-shirt.jpg',
    'charcoal-slim-trouser': 'media/products/charcoal-slim-trouser.jpg',
    'camel-overcoat': 'media/products/camel-overcoat.jpg',
    'midnight-merino-crewneck': 'media/products/midnight-merino-crewneck.jpg',
    'leather-card-wallet': 'media/products/leather-card-wallet.jpg',
    'desert-sand-chelsea-boot': 'media/products/desert-sand-chelsea-boot.jpg',
    'silk-pocket-square': 'media/products/silk-pocket-square.jpg',
}

SIZES = {
    'shirts': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
    'trousers': ['28', '30', '32', '34', '36', '38'],
    'outerwear': ['XS', 'S', 'M', 'L', 'XL'],
    'knitwear': ['XS', 'S', 'M', 'L', 'XL'],
    'accessories': ['One Size'],
    'footwear': ['6', '7', '8', '9', '10', '11'],
}


def run():
    # Categories
    cats_data = [
        {'name': 'Shirts', 'slug': 'shirts', 'sort_order': 1,
         'description': 'Precision-cut shirts in the finest cottons and linens.'},
        {'name': 'Trousers', 'slug': 'trousers', 'sort_order': 2,
         'description': 'Tailored trousers that redefine refined dressing.'},
        {'name': 'Outerwear', 'slug': 'outerwear', 'sort_order': 3,
         'description': 'Coats and jackets for the commanding entrance.'},
        {'name': 'Knitwear', 'slug': 'knitwear', 'sort_order': 4,
         'description': 'Fine-gauge knits that layer beautifully.'},
        {'name': 'Accessories', 'slug': 'accessories', 'sort_order': 5,
         'description': 'The final touch — wallets, pocket squares, and more.'},
        {'name': 'Footwear', 'slug': 'footwear', 'sort_order': 6,
         'description': 'Handcrafted shoes and boots of exceptional quality.'},
    ]
    cats = {}
    for c in cats_data:
        obj, created = Category.objects.get_or_create(slug=c['slug'], defaults=c)
        cats[c['slug']] = obj
        print(f"{'[CREATED]' if created else '[EXISTS]'} Category: {obj.name}")

    # Products
    products_data = [
        dict(name='Obsidian Oxford Shirt', slug='obsidian-oxford-shirt',
             category=cats['shirts'],
             description='A precision-cut Oxford shirt in 100% Egyptian cotton. The collar sits perfectly without stiffeners. The weave is a two-ply 200-thread-count that softens with every wash. A foundational piece for the discerning wardrobe.',
             short_description='Egyptian cotton Oxford shirt with a razor-sharp silhouette.',
             price=2499, compare_price=3499, gender='M',
             material='100% Egyptian Cotton, 200 Thread Count',
             care_instructions='Machine wash cold, 30°C. Hang dry. Iron on medium heat. Do not bleach.',
             is_featured=True, is_new_arrival=True, stock=50),
        dict(name='Ivory Linen Shirt', slug='ivory-linen-shirt',
             category=cats['shirts'],
             description='Woven from Portuguese linen, this shirt breathes beautifully in any climate. The slightly relaxed fit allows for effortless layering. The ivory tone works as a canvas for your accessories.',
             short_description='Portuguese linen shirt in off-white — breathes beautifully.',
             price=1999, compare_price=None, gender='U',
             material='100% Portuguese Linen',
             care_instructions='Hand wash in cold water. Do not tumble dry. Iron on low heat while damp.',
             is_featured=True, is_new_arrival=False, stock=35),
        dict(name='Charcoal Slim Trouser', slug='charcoal-slim-trouser',
             category=cats['trousers'],
             description='Tailored in a premium Italian mill from a refined wool-blend fabric. A slim leg that breaks at the ankle for the modern silhouette. The side-adjusters replace the belt entirely.',
             short_description='Italian wool-blend slim trouser in charcoal — ankle break perfection.',
             price=3999, compare_price=5499, gender='M',
             material='70% Merino Wool, 30% Polyester',
             care_instructions='Dry clean recommended. Steam press only. Do not iron directly on fabric.',
             is_featured=True, is_new_arrival=True, stock=28),
        dict(name='Camel Overcoat', slug='camel-overcoat',
             category=cats['outerwear'],
             description='The iconic camel overcoat, cut in a double-faced cashmere-wool blend. The silhouette is elongating and authoritative. Horn buttons, double-vent, and a structured shoulder that requires no tailoring.',
             short_description='Double-faced cashmere-blend overcoat in camel. Timeless, authoritative.',
             price=12999, compare_price=16999, gender='U',
             material='60% Cashmere, 40% Merino Wool — Italian double-face',
             care_instructions='Dry clean only. Store on a wide cedar hanger. Brush with a horsehair brush after wear.',
             is_featured=True, is_new_arrival=True, stock=15),
        dict(name='Midnight Merino Crewneck', slug='midnight-merino-crewneck',
             category=cats['knitwear'],
             description='Extra-fine 18-gauge merino wool knit in deep midnight navy. The weight is perfect for layering without bulk. The ribbed hem and cuffs stay true to shape through repeated wear.',
             short_description='Extra-fine 18-gauge merino crewneck — layers without bulk.',
             price=4499, compare_price=5999, gender='U',
             material='100% Extra-Fine Merino Wool, 18 Gauge',
             care_instructions='Hand wash cold. Dry flat on a clean towel. Do not hang. Do not tumble dry.',
             is_featured=False, is_new_arrival=True, stock=40),
        dict(name='Leather Card Wallet', slug='leather-card-wallet',
             category=cats['accessories'],
             description='Slim bifold wallet in full-grain vegetable-tanned leather sourced from a 150-year-old Italian tannery. Holds 6 cards and notes. The leather develops a rich patina with age — a companion for life.',
             short_description='Full-grain Italian vegetable-tanned leather — gets better with age.',
             price=1499, compare_price=None, gender='U',
             material='Full-grain Vegetable-Tanned Leather, Italian origin',
             care_instructions='Condition with natural leather balm every 6 months. Keep away from moisture.',
             is_featured=False, is_new_arrival=False, stock=100),
        dict(name='Desert Sand Chelsea Boot', slug='desert-sand-chelsea-boot',
             category=cats['footwear'],
             description='Blake-stitched Chelsea boot in desert sand nubuck leather. A clean, unfussy silhouette that works equally with tailored trousers and dark denim. The leather sole is Goodyear-welted for resoling.',
             short_description='Nubuck leather Chelsea boot — Blake-stitched sole, immaculate silhouette.',
             price=6999, compare_price=8999, gender='M',
             material='Nubuck Leather Upper, Goodyear-Welted Leather Sole',
             care_instructions='Brush gently with suede brush after each wear. Apply waterproofing spray monthly.',
             is_featured=True, is_new_arrival=False, stock=20),
        dict(name='Silk Pocket Square', slug='silk-pocket-square',
             category=cats['accessories'],
             description='Hand-rolled edges, printed in Como, Italy. 100% pure silk, 33x33cm. Each fold tells a different story. The final gesture of a considered outfit — effortless, yet deliberate.',
             short_description='Hand-rolled Como silk — the detail that elevates everything.',
             price=799, compare_price=None, gender='U',
             material='100% Pure Silk, Como Italy, 33×33cm',
             care_instructions='Dry clean only. Store folded in tissue paper. Keep away from direct sunlight.',
             is_featured=False, is_new_arrival=True, stock=200),
    ]

    created_products = []
    for p in products_data:
        obj, created = Product.objects.get_or_create(slug=p['slug'], defaults=p)
        created_products.append(obj)
        print(f"{'[CREATED]' if created else '[EXISTS]'} Product: {obj.name} - Rs.{obj.price}")

        # Add product images
        if not obj.images.exists():
            img_path = PRODUCT_IMAGES.get(obj.slug, '')
            if img_path:
                full_path = os.path.join(BASE, img_path)
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        fname = f'products/{obj.slug}.jpg'
                        pi = ProductImage(product=obj, alt_text=obj.name, is_primary=True, sort_order=0)
                        pi.image.save(fname, File(f), save=True)
                    print(f"   [IMG] Image attached: {obj.name}")
                else:
                    print(f"   [WARN] Image file not found: {full_path}")

        # Add variants
        cat_slug = obj.category.slug
        sizes = SIZES.get(cat_slug, ['One Size'])
        for i, size in enumerate(sizes):
            ProductVariant.objects.get_or_create(
                product=obj, size=size, color='',
                defaults={'stock': 10, 'sku': f'VRN-{obj.id}-{size}'}
            )

    # Coupons
    now = timezone.now()
    coupons_data = [
        {'code': 'VORN10', 'discount_type': 'percent', 'discount_value': 10,
         'min_order_amount': 1000, 'max_uses': 500, 'is_active': True,
         'valid_from': now, 'valid_until': now + timedelta(days=365)},
        {'code': 'WELCOME20', 'discount_type': 'percent', 'discount_value': 20,
         'min_order_amount': 2000, 'max_uses': 100, 'is_active': True,
         'valid_from': now, 'valid_until': now + timedelta(days=90)},
        {'code': 'FLAT500', 'discount_type': 'fixed', 'discount_value': 500,
         'min_order_amount': 3000, 'max_uses': 200, 'is_active': True,
         'valid_from': now, 'valid_until': now + timedelta(days=180)},
    ]
    for coup in coupons_data:
        obj, created = Coupon.objects.get_or_create(code=coup['code'], defaults=coup)
        print(f"{'[CREATED]' if created else '[EXISTS]'} Coupon: {obj.code}")

    print(f'\nVORN seeded: {Product.objects.count()} products, {Category.objects.count()} categories, {Coupon.objects.count()} coupons')


if __name__ == '__main__':
    run()
