"""
VORN — Clean Product Image Generator
Generates elegant flat-lay / product-only images (no models).
Each product gets a unique, premium-looking image with:
  - Warm neutral / luxury background gradient
  - Subtle fabric texture overlay
  - Product color swatch
  - Brand watermark
  - Category-specific composition
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vorn_project.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from store.models import Product, ProductImage
import math, random

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR  = os.path.join(BASE_DIR, 'media', 'products')
os.makedirs(MEDIA_DIR, exist_ok=True)

# ── Colour palettes per category ────────────────────────────────────────────
PALETTES = {
    'shirts': [
        [(245,240,232),(210,195,175)],  # Ivory / cream
        [(28,28,32),(45,43,50)],        # Obsidian
        [(235,228,215),(195,183,162)],  # Sand linen
        [(240,234,222),(200,188,168)],  # Warm white
        [(220,215,205),(185,178,165)],  # Muted stone
        [(38,42,58),(55,60,82)],        # Navy
    ],
    'trousers': [
        [(52,50,54),(35,33,36)],        # Charcoal
        [(210,198,175),(175,163,140)],  # Sand
        [(38,42,58),(28,32,48)],        # Navy
        [(245,238,225),(215,208,192)],  # Cream
        [(95,80,65),(72,60,48)],        # Warm brown
        [(160,155,148),(135,130,122)],  # Greige
    ],
    'outerwear': [
        [(180,158,112),(145,122,78)],   # Camel
        [(45,50,42),(30,35,28)],        # Olive
        [(28,28,32),(18,18,22)],        # Black
        [(185,175,162),(155,145,132)],  # Bone
        [(65,68,78),(48,52,62)],        # Slate
        [(120,95,75),(88,68,50)],       # Cognac
    ],
    'knitwear': [
        [(38,42,58),(28,32,48)],        # Midnight navy
        [(210,198,175),(175,163,140)],  # Sand
        [(245,240,232),(215,210,200)],  # Cream
        [(95,80,65),(72,60,48)],        # Camel
        [(160,80,80),(130,55,55)],      # Burgundy
        [(80,100,80),(60,78,60)],       # Forest green
    ],
    'accessories': [
        [(28,22,16),(18,14,8)],         # Dark leather
        [(200,175,140),(165,138,102)],  # Tan leather
        [(85,75,65),(62,54,46)],        # Dark brown
        [(235,228,215),(200,192,178)],  # Cream
        [(45,50,42),(30,35,28)],        # Olive
        [(28,28,32),(18,18,22)],        # Black
    ],
    'footwear': [
        [(210,195,170),(175,158,130)],  # Desert sand
        [(28,24,22),(16,14,12)],        # Glossy black
        [(245,245,245),(228,228,228)],  # White
        [(195,178,158),(158,140,118)],  # Suede tan
        [(22,18,14),(14,10,8)],         # Midnight black
        [(115,85,60),(88,62,40)],       # Rich brown
    ],
    'perfumes': [
        [(18,12,8),(8,4,2)],            # Oud noir
        [(38,42,28),(28,32,18)],        # Vetiver green
        [(240,225,200),(210,190,165)],  # Neroli light
    ],
    'suits': [
        [(38,38,42),(28,28,32)],        # Charcoal
        [(28,32,48),(18,22,38)],        # Navy
        [(245,238,225),(215,208,192)],  # Ivory
        [(52,48,44),(38,34,30)],        # Dark grey
        [(22,20,18),(12,10,8)],         # Black
    ],
    'dresses': [
        [(245,235,220),(215,200,180)],  # Ivory
        [(28,28,32),(18,18,22)],        # Black
        [(180,160,140),(148,128,108)],  # Camel
        [(200,185,210),(168,152,178)],  # Lilac
        [(210,195,180),(175,158,142)],  # Blush
    ],
    'tops': [
        [(245,240,232),(215,210,200)],  # Cream
        [(28,28,32),(18,18,22)],        # Black
        [(38,42,58),(28,32,48)],        # Navy
        [(235,220,200),(200,185,162)],  # Warm white
        [(180,160,140),(148,128,108)],  # Sand
    ],
}

SHAPES = {
    'shirts':      'folded_shirt',
    'trousers':    'folded_trouser',
    'outerwear':   'hanging_coat',
    'knitwear':    'folded_knit',
    'accessories': 'flat_accessory',
    'footwear':    'shoe_pair',
    'perfumes':    'perfume_bottle',
    'suits':       'hanging_coat',
    'dresses':     'hanging_dress',
    'tops':        'folded_shirt',
}


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i]-c1[i])*t) for i in range(3))


def draw_luxury_background(draw, w, h, bg1, bg2):
    """Premium warm gradient background."""
    for y in range(h):
        t = y / h
        # Slightly non-linear for depth
        t = t * t * (3 - 2*t)
        c = lerp_color(bg1, bg2, t)
        draw.line([(0, y), (w, y)], fill=c)


def draw_subtle_grid(draw, w, h, color):
    """Ultra-subtle linen texture lines."""
    for x in range(0, w, 18):
        draw.line([(x, 0), (x, h)], fill=(*color[:3], 8), width=1)
    for y in range(0, h, 18):
        draw.line([(0, y), (w, y)], fill=(*color[:3], 8), width=1)


def draw_folded_shirt(draw, w, h, c1, c2, shadow_c):
    """Clean flat-lay folded shirt / top."""
    cx, cy = w//2, h//2
    sw, sh = int(w*0.56), int(h*0.48)

    # Shadow
    draw.rectangle([cx-sw//2+6, cy-sh//2+8, cx+sw//2+6, cy+sh//2+8], fill=(*shadow_c, 60))

    # Body
    body = [cx-sw//2, cy-sh//4, cx+sw//2, cy+sh//2]
    draw.rectangle(body, fill=c1)

    # Collar area
    col_pts = [
        cx-sw//8, cy-sh//4,
        cx+sw//8, cy-sh//4,
        cx+sw//16, cy-sh//4 + sh//8,
        cx-sw//16, cy-sh//4 + sh//8,
    ]
    draw.polygon(col_pts, fill=c2)

    # Shoulder seams
    for side in [-1, 1]:
        sx = cx + side*(sw//2)
        sx2 = cx + side*(sw//8)
        draw.line([(sx2, cy-sh//4), (sx, cy-sh//5)], fill=c2, width=2)

    # Fold crease lines
    for i in range(1, 4):
        y_crease = cy - sh//4 + i*(sh*3//4)//4
        draw.line([(cx-sw//2+8, y_crease), (cx+sw//2-8, y_crease)],
                  fill=(*c2[:3], 80), width=1)


def draw_folded_trouser(draw, w, h, c1, c2, shadow_c):
    """Clean flat-lay folded trousers."""
    cx, cy = w//2, h//2
    tw, th = int(w*0.44), int(h*0.6)

    draw.rectangle([cx-tw//2+5, cy-th//2+7, cx+tw//2+5, cy+th//2+7], fill=(*shadow_c, 55))

    # Waistband
    wb = [cx-tw//2, cy-th//2, cx+tw//2, cy-th//2+th//8]
    draw.rectangle(wb, fill=c2)

    # Left leg
    ll = [cx-tw//2, cy-th//2+th//8, cx, cy+th//2]
    draw.polygon([ll[0], ll[1], ll[2], ll[1], ll[2], ll[3], ll[0]+tw//16, ll[3]], fill=c1)

    # Right leg
    rl = [cx, cy-th//2+th//8, cx+tw//2, cy-th//2+th//8, cx+tw//2-tw//16, cy+th//2, cx, cy+th//2]
    draw.polygon(rl, fill=c1)

    # Centre crease
    draw.line([(cx, cy-th//2+th//8), (cx, cy+th//2)], fill=(*c2[:3], 90), width=2)

    # Fold line
    y_fold = cy + th//6
    draw.line([(cx-tw//2+6, y_fold), (cx+tw//2-6, y_fold)], fill=(*c2[:3], 70), width=1)


def draw_hanging_coat(draw, w, h, c1, c2, shadow_c):
    """Coat/blazer hanging (front-facing flat)."""
    cx, cy = w//2, h//2+h//16
    cw, ch = int(w*0.52), int(h*0.70)

    draw.rectangle([cx-cw//2+6, cy-ch//2+8, cx+cw//2+6, cy+ch//2+8], fill=(*shadow_c, 55))

    # Main body
    body = [
        cx-cw//2,   cy-ch//2+ch//10,
        cx+cw//2,   cy-ch//2+ch//10,
        cx+cw//2,   cy+ch//2,
        cx+cw//5,   cy+ch//2,
        cx,         cy+ch//2 - ch//8,
        cx-cw//5,   cy+ch//2,
        cx-cw//2,   cy+ch//2,
    ]
    draw.polygon(body, fill=c1)

    # Lapels
    left_lapel = [cx-cw//12, cy-ch//2+ch//10, cx-cw//5, cy-ch//6, cx-cw//8, cy-ch//10, cx-cw//12, cy-ch//12]
    right_lapel = [cx+cw//12, cy-ch//2+ch//10, cx+cw//5, cy-ch//6, cx+cw//8, cy-ch//10, cx+cw//12, cy-ch//12]
    draw.polygon(left_lapel, fill=c2)
    draw.polygon(right_lapel, fill=c2)

    # Collar
    draw.line([(cx-cw//12, cy-ch//2+ch//10), (cx+cw//12, cy-ch//2+ch//10)], fill=c2, width=3)

    # Buttons
    for i in range(3):
        by = cy + i*(ch//8)
        draw.ellipse([cx-8, by-8, cx+8, by+8], fill=c2)


def draw_hanging_dress(draw, w, h, c1, c2, shadow_c):
    """Elegant dress hanging flat."""
    cx, cy = w//2, h//2+h//16
    dw, dh = int(w*0.46), int(h*0.72)

    draw.rectangle([cx-dw//2+5, cy-dh//2+7, cx+dw//2+5, cy+dh//2+7], fill=(*shadow_c, 50))

    # Bodice
    bodice = [
        cx-dw//3, cy-dh//2+dh//10,
        cx+dw//3, cy-dh//2+dh//10,
        cx+dw//2, cy-dh//2+dh//3,
        cx-dw//2, cy-dh//2+dh//3,
    ]
    draw.polygon(bodice, fill=c1)

    # Skirt (flared)
    skirt = [
        cx-dw//2, cy-dh//2+dh//3,
        cx+dw//2, cy-dh//2+dh//3,
        cx+dw//2+dw//5, cy+dh//2,
        cx-dw//2-dw//5, cy+dh//2,
    ]
    draw.polygon(skirt, fill=c1)

    # Neckline
    neck_pts = [cx-dw//6, cy-dh//2+dh//10, cx+dw//6, cy-dh//2+dh//10, cx, cy-dh//2+dh//6]
    draw.polygon(neck_pts, fill=c2)

    # Waist seam
    y_waist = cy - dh//2 + dh//3
    draw.line([(cx-dw//2+4, y_waist), (cx+dw//2-4, y_waist)], fill=(*c2[:3], 80), width=2)


def draw_folded_knit(draw, w, h, c1, c2, shadow_c):
    """Folded knitwear with texture lines."""
    cx, cy = w//2, h//2
    kw, kh = int(w*0.54), int(h*0.46)

    draw.rectangle([cx-kw//2+5, cy-kh//2+7, cx+kw//2+5, cy+kh//2+7], fill=(*shadow_c, 55))
    draw.rectangle([cx-kw//2, cy-kh//2, cx+kw//2, cy+kh//2], fill=c1)

    # Ribbed texture lines
    for i in range(8):
        x_rib = cx - kw//2 + 6 + i*(kw-12)//8
        draw.line([(x_rib, cy-kh//2+4), (x_rib, cy+kh//2-4)],
                  fill=(*c2[:3], 55), width=2)

    # Collar rectangle
    col = [cx-kw//5, cy-kh//2, cx+kw//5, cy-kh//2+kh//6]
    draw.rectangle(col, fill=c2)

    # Fold shadow
    draw.rectangle([cx-kw//2+2, cy-2, cx+kw//2-2, cy+4], fill=(*shadow_c, 40))


def draw_flat_accessory(draw, w, h, c1, c2, shadow_c):
    """Wallet / accessory flat lay."""
    cx, cy = w//2, h//2
    aw, ah = int(w*0.50), int(h*0.32)

    draw.rectangle([cx-aw//2+5, cy-ah//2+6, cx+aw//2+5, cy+ah//2+6], fill=(*shadow_c, 60))
    draw.rectangle([cx-aw//2, cy-ah//2, cx+aw//2, cy+ah//2], fill=c1)

    # Stitching border
    margin = 10
    for i in range(0, aw - margin*2, 8):
        draw.line([(cx-aw//2+margin+i, cy-ah//2+margin),
                   (cx-aw//2+margin+i+4, cy-ah//2+margin)], fill=c2, width=1)
        draw.line([(cx-aw//2+margin+i, cy+ah//2-margin),
                   (cx-aw//2+margin+i+4, cy+ah//2-margin)], fill=c2, width=1)

    # Card slots
    for i in range(3):
        y_slot = cy - ah//4 + i*(ah//6)
        draw.rectangle([cx-aw//2+15, y_slot, cx, y_slot+ah//8], fill=c2)

    # Logo emboss
    draw.rectangle([cx+aw//8, cy-ah//8, cx+aw//3, cy+ah//8], fill=c2)


def draw_shoe_pair(draw, w, h, c1, c2, shadow_c):
    """Minimalist shoe pair flat-lay."""
    cx, cy = w//2, h//2

    for side, x_off in [(-1, -w//8), (1, w//8)]:
        sx = cx + x_off
        sw_s, sh_s = int(w*0.30), int(h*0.20)

        # Shadow
        draw.ellipse([sx-sw_s//2+4, cy-sh_s//4+8, sx+sw_s//2+4, cy+sh_s//2+8],
                     fill=(*shadow_c, 50))

        # Sole
        draw.ellipse([sx-sw_s//2, cy-sh_s//4, sx+sw_s//2, cy+sh_s//4+sh_s//2], fill=c2)

        # Upper
        upper = [
            sx-sw_s//2, cy,
            sx+sw_s//2, cy,
            sx+sw_s//2-sw_s//8, cy-sh_s,
            sx-sw_s//2+sw_s//8, cy-sh_s,
        ]
        draw.polygon(upper, fill=c1)

        # Toe cap
        draw.ellipse([sx-sw_s//2, cy-sh_s//2, sx+sw_s//5, cy+sh_s//5], fill=c1)


def draw_perfume_bottle(draw, w, h, c1, c2, shadow_c):
    """Elegant tall perfume bottle."""
    cx, cy = w//2, h//2
    bw, bh = int(w*0.24), int(h*0.58)

    # Bottle shadow
    draw.rectangle([cx-bw//2+6, cy-bh//2+10, cx+bw//2+6, cy+bh//2+10], fill=(*shadow_c, 60))

    # Bottle body — slight taper
    body = [
        cx-bw//2,     cy-bh//2+bh//6,
        cx+bw//2,     cy-bh//2+bh//6,
        cx+bw//2+bw//8, cy+bh//2,
        cx-bw//2-bw//8, cy+bh//2,
    ]
    draw.polygon(body, fill=c1)

    # Neck
    neck_w, neck_h = bw//3, bh//8
    draw.rectangle([cx-neck_w//2, cy-bh//2, cx+neck_w//2, cy-bh//2+bh//6], fill=c2)

    # Cap/stopper
    cap_w = int(neck_w*1.6)
    draw.rectangle([cx-cap_w//2, cy-bh//2-bh//12, cx+cap_w//2, cy-bh//2], fill=c2)

    # Label on bottle
    lbl = [cx-bw//3, cy-bh//8, cx+bw//3, cy+bh//5]
    draw.rectangle(lbl, fill=(*c2[:3], 40))

    # Liquid level (gradient suggestion)
    liquid_y = cy + bh//4
    draw.line([(cx-bw//2+2, liquid_y), (cx+bw//2-2, liquid_y)],
              fill=(*c2[:3], 80), width=1)

    # Glass highlight
    draw.rectangle([cx-bw//2+4, cy-bh//2+bh//6+4, cx-bw//2+14, cy+bh//2-4],
                   fill=(255, 255, 255, 40))


def add_brand_watermark(img, text='VORN'):
    """Add subtle VORN watermark."""
    draw = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size

    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except:
        font = ImageFont.load_default()

    txt_w = len(text) * 7
    x = w - txt_w - 14
    y = h - 22
    draw.text((x, y), text, fill=(120, 108, 90, 80), font=font)


def add_corner_accent(draw, w, h, c):
    """Subtle gold corner lines for premium feel."""
    accent = (*c, 60)
    sz = 28
    draw.line([(10, 10), (10+sz, 10)], fill=accent, width=1)
    draw.line([(10, 10), (10, 10+sz)], fill=accent, width=1)
    draw.line([(w-10, 10), (w-10-sz, 10)], fill=accent, width=1)
    draw.line([(w-10, 10), (w-10, 10+sz)], fill=accent, width=1)
    draw.line([(10, h-10), (10+sz, h-10)], fill=accent, width=1)
    draw.line([(10, h-10), (10, h-10-sz)], fill=accent, width=1)
    draw.line([(w-10, h-10), (w-10-sz, h-10)], fill=accent, width=1)
    draw.line([(w-10, h-10), (w-10, h-10-sz)], fill=accent, width=1)


DRAW_FUNCS = {
    'folded_shirt':    draw_folded_shirt,
    'folded_trouser':  draw_folded_trouser,
    'hanging_coat':    draw_hanging_coat,
    'folded_knit':     draw_folded_knit,
    'flat_accessory':  draw_flat_accessory,
    'shoe_pair':       draw_shoe_pair,
    'perfume_bottle':  draw_perfume_bottle,
    'hanging_dress':   draw_hanging_dress,
}


def generate_product_image(slug, cat_slug, palette_idx, w=800, h=1000):
    """Generate a clean flat-lay product image."""
    palette = PALETTES.get(cat_slug, PALETTES['shirts'])
    colors = palette[palette_idx % len(palette)]

    bg1 = tuple(min(c + 20, 255) for c in colors[0])  # Slightly lighter bg
    bg2 = tuple(max(c - 10, 0) for c in colors[0])
    c1  = colors[0]
    c2  = colors[1]
    shadow_c = (max(c1[0]-40, 0), max(c1[1]-40, 0), max(c1[2]-40, 0))

    # Background image (RGBA for compositing)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    bg_layer = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    bg_draw  = ImageDraw.Draw(bg_layer)

    # Warm neutral background base
    neutral_bg = (248, 244, 238)
    neutral_bg2 = (235, 228, 218)
    draw_luxury_background(bg_draw, w, h, neutral_bg, neutral_bg2)

    # Merge bg
    img = bg_layer.copy()
    draw = ImageDraw.Draw(img, 'RGBA')

    # Subtle grid texture
    draw_subtle_grid(draw, w, h, (180, 168, 150))

    # Draw the product shape
    shape = SHAPES.get(cat_slug, 'folded_shirt')
    draw_fn = DRAW_FUNCS.get(shape, draw_folded_shirt)
    draw_fn(draw, w, h, c1, c2, shadow_c)

    # Corner accents (gold tone)
    add_corner_accent(draw, w, h, (172, 138, 83))

    # Apply slight blur to shadow layer for realism
    img_rgb = img.convert('RGB')
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.1)

    # Add watermark
    img_rgba = img_rgb.convert('RGBA')
    add_brand_watermark(img_rgba)

    # Save
    dest = os.path.join(MEDIA_DIR, f"product_{slug}.png")
    img_rgba.convert('RGB').save(dest, 'PNG', quality=95, optimize=True)
    return dest


def regenerate_all():
    products = Product.objects.filter(is_active=True).select_related('category')
    print(f"Regenerating {products.count()} product images (clean flat-lay, no models)...")

    for idx, p in enumerate(products):
        cat_slug = p.category.slug
        dest = generate_product_image(p.slug, cat_slug, idx)
        print(f"  OK {p.name[:45]} -> product_{p.slug}.png")

        # Update DB record
        relative_path = f"products/product_{p.slug}.png"
        p.images.filter(is_primary=True).update(image=relative_path)

    print(f"\nDONE: All {products.count()} product images regenerated - clean flat-lay style, no models.")


if __name__ == '__main__':
    regenerate_all()
