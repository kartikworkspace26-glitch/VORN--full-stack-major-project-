import os
import sys
import shutil
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vorn_project.settings')
django.setup()

from store.models import Category, Product, ProductImage, ProductVariant
from django.core.files import File

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
PRODUCTS_MEDIA_DIR = os.path.join(MEDIA_DIR, 'products')
CATEGORIES_MEDIA_DIR = os.path.join(MEDIA_DIR, 'categories')

# Create media directories if they don't exist
os.makedirs(PRODUCTS_MEDIA_DIR, exist_ok=True)
os.makedirs(CATEGORIES_MEDIA_DIR, exist_ok=True)

# Active conversation artifact directory for Gemini images
ARTIFACT_DIRS = [
    r"C:\Users\puran\.gemini\antigravity-ide\brain\53629429-e16e-42be-8fd0-90d0f57017aa",
    r"C:\Users\puran\.gemini\antigravity-ide\brain\24db8a02-57f5-4a9f-8ee2-717fe738c102"
]
STATIC_PRODUCTS_DIR = os.path.join(BASE_DIR, 'static', 'images', 'products')


# Import image generator fallback
try:
    from generate_product_images import generate_product_image
except ImportError:
    generate_product_image = None

# Category assets mapping (copied if exist)
category_images_mapping = {
    'cat-shirts.png': os.path.join(BASE_DIR, 'static', 'images', 'mens_shirt_linen_editorial.jpg'),
    'cat-trousers.png': os.path.join(BASE_DIR, 'static', 'images', 'womens_silk_dress_editorial.jpg'),
    'cat-outerwear.png': os.path.join(BASE_DIR, 'static', 'images', 'mens_outerwear_camel.jpg'),
    'cat-knitwear.png': os.path.join(BASE_DIR, 'static', 'images', 'mens_knitwear_navy.jpg'),
    'cat-accessories.png': os.path.join(BASE_DIR, 'static', 'images', 'mens_accessories_leather.jpg'),
    'cat-footwear.png': os.path.join(BASE_DIR, 'static', 'images', 'womens_outerwear_coat.jpg'),
    'cat-perfumes.png': os.path.join(BASE_DIR, 'static', 'images', 'womens_silk_blouse_editorial.jpg'),
}

def copy_category_assets():
    print("--- Copying Category Image Assets ---")
    for dest_name, src_path in category_images_mapping.items():
        if os.path.exists(src_path):
            shutil.copy(src_path, os.path.join(CATEGORIES_MEDIA_DIR, dest_name))
            print(f"Copied category image: {dest_name}")
        else:
            print(f"Warning: Source not found for category image {dest_name}")

def seed_database():
    print("\n--- Seeding Database ---")
    
    # 1. Update Categories
    cats_data = [
        {'name': 'Shirts', 'slug': 'shirts', 'sort_order': 1, 'image': 'categories/cat-shirts.png', 'description': 'Precision-cut shirts in the finest cottons and linens.'},
        {'name': 'Trousers', 'slug': 'trousers', 'sort_order': 2, 'image': 'categories/cat-trousers.png', 'description': 'Tailored trousers that redefine refined dressing.'},
        {'name': 'Outerwear', 'slug': 'outerwear', 'sort_order': 3, 'image': 'categories/cat-outerwear.png', 'description': 'Coats and jackets for the commanding entrance.'},
        {'name': 'Knitwear', 'slug': 'knitwear', 'sort_order': 4, 'image': 'categories/cat-knitwear.png', 'description': 'Fine-gauge knits that layer beautifully.'},
        {'name': 'Accessories', 'slug': 'accessories', 'sort_order': 5, 'image': 'categories/cat-accessories.png', 'description': 'The final touch — wallets, pocket squares, and more.'},
        {'name': 'Footwear', 'slug': 'footwear', 'sort_order': 6, 'image': 'categories/cat-footwear.png', 'description': 'Handcrafted shoes and boots of exceptional quality.'},
        {'name': 'Perfumes', 'slug': 'perfumes', 'sort_order': 7, 'image': 'categories/cat-perfumes.png', 'description': 'Refined luxury fragrances crafted for deliberate presence.'},
        {'name': 'Suits', 'slug': 'suits', 'sort_order': 8, 'image': 'categories/cat-outerwear.png', 'description': 'Structured suits tailored for modern presence.'},
        {'name': 'Dresses', 'slug': 'dresses', 'sort_order': 9, 'image': 'categories/cat-trousers.png', 'description': 'Luxury dresses with exceptional flow and drape.'},
        {'name': 'Tops', 'slug': 'tops', 'sort_order': 10, 'image': 'categories/cat-shirts.png', 'description': 'Sophisticated tops in fine silk and knit structures.'},
    ]
    
    categories = {}
    for c in cats_data:
        obj, created = Category.objects.update_or_create(
            slug=c['slug'],
            defaults={'name': c['name'], 'sort_order': c['sort_order'], 'image': c['image'], 'description': c['description']}
        )
        categories[c['slug']] = obj
        print(f"Category: {obj.name} -> Image: {obj.image}")

    # Clear existing products to ensure clean seed of the new collection
    print("Clearing old products...")
    Product.objects.all().delete()

    # Sizing guides mapping
    clothing_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    trouser_sizes = ['28', '30', '32', '34', '36', '38']
    shoe_sizes = ['6', '7', '8', '9', '10', '11']
    acc_sizes = ['One Size']
    perfume_sizes = ['50ml', '100ml']

    def get_sizes_for_category(cat_slug):
        if cat_slug == 'shirts': return clothing_sizes
        if cat_slug == 'trousers': return trouser_sizes
        if cat_slug == 'outerwear': return clothing_sizes
        if cat_slug == 'knitwear': return clothing_sizes
        if cat_slug == 'footwear': return shoe_sizes
        if cat_slug == 'perfumes': return perfume_sizes
        if cat_slug in ('suits', 'dresses', 'tops'): return clothing_sizes
        return acc_sizes

    # Overhauled collection of 20 ultra-premium products
    products_data = [
        # === PERFUMES ===
        dict(name="VORN Vetiver Ancestral", slug="vorn-vetiver-ancestral", category=categories['perfumes'],
             description="A deep, hypnotic scent layered with rich Haitian vetiver, smoked cedarwood, and aged patchouli. It opens with sharp black pepper and frankincense, settling into a warm amber and dry leather base.",
             short_description="A deep, smoky blend of Haitian vetiver and aged patchouli.",
             price=4800, compare_price=5800, gender='U', material='Eau de Parfum', is_featured=True,
             base_filename=None),

        dict(name="VORN Imperial Sandalwood", slug="vorn-imperial-sandalwood", category=categories['perfumes'],
             description="Woven from pure Mysore sandalwood, saffron, and crushed cardamom. A creamy, majestic fragrance with a skin-like texture that lingers throughout the day.",
             short_description="Creamy Mysore sandalwood layered with warm saffron.",
             price=4600, compare_price=None, gender='U', material='Eau de Parfum Extract', is_featured=True,
             base_filename=None),

        dict(name="VORN Bergamote Noble", slug="vorn-bergamote-noble", category=categories['perfumes'],
             description="A bright, noble opening of cold-pressed Calabrian bergamot and Tunisian neroli, resting on a base of white ambergris and soft musk. Clean, commanding, and timeless.",
             short_description="Crisp Calabrian bergamot and Tunisian neroli.",
             price=4200, compare_price=None, gender='U', material='Eau de Parfum', is_featured=False,
             base_filename=None),

        # === WOMEN'S COLLECTION ===
        dict(name="Monarch Silk Draped Blouse", slug="monarch-silk-draped-blouse", category=categories['tops'],
             description="Cut from 22momme mulberry silk, this blouse features an architectural cowl drape, dropped shoulders, and double-button cuffs. A statement of fluid, quiet luxury.",
             short_description="Heavy mulberry silk blouse with an architectural drape.",
             price=5200, compare_price=6800, gender='W', material='100% Mulberry Silk', is_featured=True,
             base_filename='womens_silk_blouse_editorial.jpg'),

        dict(name="Elysian Wide-Leg Silk Pant", slug="elysian-wide-leg-silk-pant", category=categories['trousers'],
             description="Flowing wide-leg trousers designed with an ultra-high waist, clean front zip closure, and deep side pockets. Cut from heavyweight fluid sand silk crepe de chine.",
             short_description="Heavyweight fluid silk crepe wide-leg trousers.",
             price=6800, compare_price=8900, gender='W', material='100% Silk Crepe de Chine', is_featured=True,
             base_filename=None),

        dict(name="Cashmere Belted Wrap Coat", slug="cashmere-belted-wrap-coat", category=categories['outerwear'],
             description="A luxurious open-front wrap coat hand-stitched from double-faced cashmere and virgin wool. Styled with a shawl collar and loose self-tie belt in soft alabaster bone.",
             short_description="Double-faced cashmere-blend wrap coat in alabaster.",
             price=14800, compare_price=18900, gender='W', material='70% Merino Wool, 30% Cashmere', is_featured=True,
             base_filename='womens_cashmere_knitwear.jpg'),

        dict(name="Asymmetric Silk Satin Slip Dress", slug="asymmetric-silk-satin-slip-dress", category=categories['dresses'],
             description="Bias-cut dress in high-lustre silk satin. Features an asymmetric one-shoulder strap, draped cowl neck, and a delicate side slit in deep obsidian.",
             short_description="Bias-cut silk satin slip dress in deep obsidian.",
             price=8500, compare_price=11000, gender='W', material='100% Silk Satin', is_featured=False,
             base_filename=None),

        # === MEN'S COLLECTION ===
        dict(name="Savile Row Double-Breasted Suit", slug="savile-row-double-breasted-suit", category=categories['suits'],
             description="A timeless three-piece suit tailored from structured chalkstripe English wool. Features a sharp peak lapel blazer, matching vest, and classic double-pleated trousers.",
             short_description="Navy chalkstripe English wool double-breasted suit.",
             price=16800, compare_price=22000, gender='M', material='100% English Wool', is_featured=True,
             base_filename='mens_suit_editorial.jpg'),

        dict(name="Heritage Tweed Overcoat", slug="heritage-tweed-overcoat", category=categories['outerwear'],
             description="Classic long double-breasted overcoat tailored from heavy salt-and-pepper Scottish tweed. Features structured shoulders, real horn buttons, and deep welt pockets.",
             short_description="Heavy salt-and-pepper Scottish tweed overcoat.",
             price=13800, compare_price=17500, gender='M', material='100% Scottish Tweed, Cupro Lining', is_featured=True,
             base_filename='mens_outerwear_camel.jpg'),

        dict(name="Merino Shawl-Collar Cardigan", slug="merino-shawl-collar-cardigan", category=categories['knitwear'],
             description="A heavy-gauge cardigan cable-knit from 100% merino wool. Styled with a thick shawl collar, leather-wrapped buttons, and patch pockets in heather oatmeal.",
             short_description="Heavy-gauge merino wool shawl-collar cardigan.",
             price=7200, compare_price=9500, gender='M', material='100% Merino Wool', is_featured=False,
             base_filename=None),

        dict(name="Heritage Calfskin Oxford Shoe", slug="heritage-calfskin-oxford-shoe", category=categories['footwear'],
             description="Blake-stitched cap-toe Oxfords crafted from hand-burnished cognac calfskin. Featuring a stacked leather heel, leather outsoles, and durable wax laces. Premium footwear for the modern man.",
             short_description="Blake-stitched hand-burnished calfskin Oxfords.",
             price=8900, compare_price=11500, gender='M', material='100% Calfskin Upper, Leather Sole', is_featured=True,
             base_filename=None),

        # === FOOTWEAR ADDITIONS (MEN & WOMEN) ===
        dict(name="Desert Sand Chelsea Boot", slug="desert-sand-chelsea-boot", category=categories['footwear'],
             description="Blake-stitched Chelsea boot in desert sand nubuck leather. A clean, unfussy silhouette that works equally with tailored trousers and dark denim. The leather sole is Goodyear-welted for resoling.",
             short_description="Nubuck leather Chelsea boot — Blake-stitched sole, immaculate silhouette.",
             price=6999, compare_price=8999, gender='M', material='Nubuck Leather Upper, Goodyear-Welted Leather Sole', is_featured=True,
             base_filename=None),

        dict(name="Elysian Suede Ankle Boot", slug="elysian-suede-ankle-boot", category=categories['footwear'],
             description="Handcrafted in Italy from ultra-soft taupe suede, featuring a comfortable block heel and clean pointed-toe silhouette. A perfect choice for effortless day-to-night styling.",
             short_description="Premium Italian suede ankle boots with a refined block heel.",
             price=7999, compare_price=9999, gender='W', material='100% Suede Leather, Leather Sole', is_featured=True,
             base_filename='womens_outerwear_coat.jpg'),

        # === MENSWEAR / UNISEX FOUNDATIONS ===
        dict(name="Obsidian Oxford Shirt", slug="obsidian-oxford-shirt", category=categories['shirts'],
             description="A precision-cut Oxford shirt in 100% Egyptian cotton. The collar sits perfectly without stiffeners. The weave is a two-ply 200-thread-count that softens with every wash. A foundational piece for the discerning wardrobe.",
             short_description="Egyptian cotton Oxford shirt with a razor-sharp silhouette.",
             price=2499, compare_price=3499, gender='M', material='100% Egyptian Cotton, 200 Thread Count', is_featured=False,
             base_filename=None),

        dict(name="Ivory Linen Shirt", slug="ivory-linen-shirt", category=categories['shirts'],
             description="Woven from Portuguese linen, this shirt breathes beautifully in any climate. The slightly relaxed fit allows for effortless layering. The ivory tone works as a canvas for your accessories.",
             short_description="Portuguese linen shirt in off-white — breathes beautifully.",
             price=1999, compare_price=None, gender='U', material='100% Portuguese Linen', is_featured=False,
             base_filename='mens_shirt_linen_editorial.jpg'),

        dict(name="Charcoal Slim Trouser", slug="charcoal-slim-trouser", category=categories['trousers'],
             description="Tailored in a premium Italian mill from a refined wool-blend fabric. A slim leg that breaks at the ankle for the modern silhouette. The side-adjusters replace the belt entirely.",
             short_description="Italian wool-blend slim trouser in charcoal — ankle break perfection.",
             price=3999, compare_price=5499, gender='M', material='70% Merino Wool, 30% Polyester', is_featured=False,
             base_filename=None),

        dict(name="Camel Overcoat", slug="camel-overcoat", category=categories['outerwear'],
             description="The iconic camel overcoat, cut in a double-faced cashmere-wool blend. The silhouette is elongating and authoritative. Horn buttons, double-vent, and a structured shoulder that requires no tailoring.",
             short_description="Double-faced cashmere-blend overcoat in camel. Timeless, authoritative.",
             price=12999, compare_price=16999, gender='U', material='60% Cashmere, 40% Merino Wool — Italian double-face', is_featured=False,
             base_filename='mens_outerwear_camel.jpg'),

        dict(name="Midnight Merino Crewneck", slug="midnight-merino-crewneck", category=categories['knitwear'],
             description="Extra-fine 18-gauge merino wool knit in deep midnight navy. The weight is perfect for layering without bulk. The ribbed hem and cuffs stay true to shape through repeated wear.",
             short_description="Extra-fine 18-gauge merino crewneck — layers without bulk.",
             price=4499, compare_price=5999, gender='U', material='100% Extra-Fine Merino Wool, 18 Gauge', is_featured=False,
             base_filename='mens_knitwear_navy.jpg'),

        dict(name="Leather Card Wallet", slug="leather-card-wallet", category=categories['accessories'],
             description="Slim bifold wallet in full-grain vegetable-tanned leather sourced from a 150-year-old Italian tannery. Holds 6 cards and notes. The leather develops a rich patina with age — a companion for life.",
             short_description="Full-grain Italian vegetable-tanned leather — gets better with age.",
             price=1499, compare_price=None, gender='U', material='Full-grain Vegetable-Tanned Leather, Italian origin', is_featured=False,
             base_filename='mens_accessories_leather.jpg'),

        dict(name="Silk Pocket Square", slug="silk-pocket-square", category=categories['accessories'],
             description="Hand-rolled edges, printed in Como, Italy. 100% pure silk, 33x33cm. Each fold tells a different story. The final gesture of a considered outfit — effortless, yet deliberate.",
             short_description="Hand-rolled Como silk — the detail that elevates everything.",
             price=799, compare_price=None, gender='U', material='100% Pure Silk, Como Italy, 33×33cm', is_featured=False,
             base_filename=None),

        # === MENSWEAR ADDITIONS ===
        dict(name="VORN Signature Heavyweight Tee", slug="vorn-signature-heavyweight-tee", category=categories['tops'],
             description="A boxy, relaxed-fit heavy organic cotton t-shirt. Cut from custom 300gsm double-knit combed cotton with an drop-shoulder construction. The perfect basic foundational item.",
             short_description="Custom 300gsm heavyweight organic cotton drop-shoulder tee.",
             price=1499, compare_price=1999, gender='M', material='100% Organic Cotton', is_featured=True,
             base_filename=None),

        dict(name="Linen Henley Top", slug="linen-henley-top", category=categories['tops'],
             description="Cut from 100% fine French linen with a classic three-button placket and relaxed band collar. Crisp, highly breathable structure perfect for warm weather styling.",
             short_description="Breathable French linen Henley top with band collar.",
             price=2299, compare_price=2999, gender='M', material='100% French Linen', is_featured=False,
             base_filename=None),

        dict(name="Classic Oversized Poplin Shirt", slug="classic-oversized-poplin-shirt", category=categories['tops'],
             description="Tailored with an oversized boxy drape from crisp, high-thread-count cotton poplin. Features dropped shoulders, premium mother-of-pearl buttons, and a clean curved hem.",
             short_description="Crisp oversized cotton poplin button-down shirt.",
             price=2899, compare_price=None, gender='M', material='100% Cotton Poplin', is_featured=False,
             base_filename=None),

        # === WOMENSWEAR ADDITIONS ===
        dict(name="Mulberry Silk Camisole", slug="mulberry-silk-camisole", category=categories['tops'],
             description="Flowing silhouette with delicate adjustable spaghetti straps and a gentle V-neckline. Cut from premium high-lustre mulberry silk satin for beautiful drape and movement.",
             short_description="Feminine, high-lustre pure mulberry silk camisole top.",
             price=2499, compare_price=None, gender='W', material='100% Mulberry Silk Satin', is_featured=True,
             base_filename=None),

        dict(name="Draped Asymmetric Top", slug="draped-asymmetric-top", category=categories['tops'],
             description="An architectural one-shoulder draped top in heavyweight fluid viscose-silk crepe. Features elegant asymmetric gathers at the waist and shoulder for a refined, modern silhouette.",
             short_description="Architectural one-shoulder fluid crepe draped top.",
             price=3400, compare_price=4500, gender='W', material='75% Viscose, 25% Silk Crepe', is_featured=True,
             base_filename=None),

        dict(name="High-Neck Ribbed Top", slug="high-neck-ribbed-top", category=categories['tops'],
             description="A body-conscious, sleek high-neck top in fine-ribbed organic stretch cotton. Perfect for standalone elegance or effortless layering under lightweight blazers.",
             short_description="Sleek fine-ribbed high-neck organic cotton top.",
             price=1899, compare_price=2499, gender='W', material='95% Organic Cotton, 5% Elastane', is_featured=False,
             base_filename=None),

        dict(name="Fine-Knit Polo Top", slug="fine-knit-polo-top", category=categories['tops'],
             description="A beautifully lightweight knit polo with a modern three-button placket and slim ribbed collar. Woven from high-twist fine linen-cotton yarn for unique breathability and texture.",
             short_description="Lightweight fine-knit linen-cotton polo top.",
             price=2499, compare_price=3299, gender='W', material='55% Linen, 45% Cotton', is_featured=False,
             base_filename=None),

        dict(name="Organic Cotton Tank Top", slug="organic-cotton-tank-top", category=categories['tops'],
             description="A relaxed, high-neck racerback tank top in premium soft organic rib-knit cotton. Designed with flat-locked raw seams for a clean, sustainable minimalist aesthetic.",
             short_description="Minimalist high-neck racerback organic cotton tank.",
             price=1299, compare_price=1699, gender='W', material='100% Combed Organic Cotton', is_featured=False,
             base_filename=None),

        dict(name="VORN Signature Oversized Suit", slug="vorn-signature-oversized-suit", category=categories['suits'],
             description="A deconstructed, modern double-breasted suit with slouchy trousers and fluid blazer. Tailored from a premium sand wool-blend crepe that drops beautifully with effortless ease.",
             short_description="Deconstructed sand double-breasted suit with relaxed wide trousers.",
             price=18500, compare_price=24500, gender='W', material='85% Wool, 15% Viscose Crepe', is_featured=True,
             base_filename=None),

        dict(name="Ivory Silk Tuxedo Suit", slug="ivory-silk-tuxedo-suit", category=categories['suits'],
             description="A majestic evening tuxedo suit. The single-button blazer features glossy satin lapels and matching high-waisted silk cigarette trousers. An epitome of luxury womenswear.",
             short_description="Feminine ivory pure silk tuxedo suit with satin lapels.",
             price=19800, compare_price=26000, gender='W', material='100% Silk Satin, Silk Lining', is_featured=True,
             base_filename=None),

        dict(name="Mulberry Silk Slip Dress", slug="mulberry-silk-slip-dress", category=categories['dresses'],
             description="Classic bias-cut slip dress in fluid 22momme mulberry silk. Designed with spaghetti straps, a soft cowl neck, and a delicate side slit. It slides down the body like liquid gold.",
             short_description="Bias-cut pure mulberry silk slip dress with cowl neckline.",
             price=9200, compare_price=12000, gender='W', material='100% Mulberry Silk', is_featured=True,
             base_filename='womens_silk_dress_editorial.jpg'),

        dict(name="Linen Tiered Maxi Dress", slug="linen-tiered-maxi-dress", category=categories['dresses'],
             description="A beautiful, tiered maxi dress in breezy, lightweight washed linen. Styled with a gathered neckline and raw-edged tiers that drape gracefully down to the floor.",
             short_description="Breezy tier-draped washed linen maxi dress.",
             price=6999, compare_price=8999, gender='W', material='100% Washed Linen', is_featured=False,
             base_filename=None),

        dict(name="Asymmetric Satin Gown", slug="asymmetric-satin-gown", category=categories['dresses'],
             description="An exquisite floor-length evening gown cut from high-lustre emerald green silk satin. Features a draped, asymmetric one-shoulder design and a high dramatic leg slit.",
             short_description="Exquisite one-shoulder high-lustre emerald satin gown.",
             price=11500, compare_price=15000, gender='W', material='100% Silk Satin', is_featured=True,
             base_filename='womens_evening_gown.jpg'),
    ]

    for idx, p in enumerate(products_data):
        base_filename = p.pop('base_filename')
        slug = p['slug']
        cat_slug = p['category'].slug
        
        unique_img_name = f"product_{slug}.png"
        dest_path = os.path.join(PRODUCTS_MEDIA_DIR, unique_img_name)
        
        # 1. Determine image source
        src_path = None
        if base_filename:
            static_cand = os.path.join(BASE_DIR, 'static', 'images', base_filename)
            if os.path.exists(static_cand):
                src_path = static_cand
        
        # 2. Check for local high-quality AI images in products directory if any
        if not src_path:
            local_candidates = [
                os.path.join(STATIC_PRODUCTS_DIR, f"{slug}.jpg"),
                os.path.join(STATIC_PRODUCTS_DIR, f"{slug}.png"),
            ]
            for cand in local_candidates:
                if os.path.exists(cand):
                    src_path = cand
                    break
        
        # 3. Copy image if found
        has_image = False
        if src_path:
            shutil.copy(src_path, dest_path)
            print(f"   [IMG] Copied high-quality image for: {slug} from {os.path.basename(src_path)}")
            has_image = True
        else:
            print(f"   [INFO] No high-quality image source for: {slug}. Falling back to elegant VORN text placeholder in UI.")

        obj, created = Product.objects.update_or_create(
            slug=slug,
            defaults=p
        )
        print(f"{'[CREATED]' if created else '[UPDATED]'} Product: {obj.name} (Rs. {obj.price})")

        # Attach image to product model ONLY if we copied a real image
        obj.images.all().delete()
        if has_image:
            relative_img_path = f"products/{unique_img_name}"
            pi = ProductImage(product=obj, image=relative_img_path, is_primary=True, sort_order=0, alt_text=obj.name)
            pi.save()
            print(f"   Attached unique image: {relative_img_path}")
        else:
            print(f"   No product image attached (uses CSS placeholder)")

        # Generate variants (sizes)
        sizes = get_sizes_for_category(cat_slug)
        for size in sizes:
            ProductVariant.objects.get_or_create(
                product=obj,
                size=size,
                color='',
                defaults={'stock': 15, 'sku': f"VRN-{obj.id}-{size}"}
            )

    print(f"\nCompleted! Seeded {Product.objects.count()} products across {Category.objects.count()} categories.")

if __name__ == '__main__':
    copy_category_assets()
    seed_database()
