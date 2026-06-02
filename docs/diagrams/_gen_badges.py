"""Generate consistent letter-badge PNGs for platforms without official simpleicons logos.

Output: 256×256 transparent-background PNG with a rounded color square + initials.
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Badge spec: (slug, "Initials", "#background_hex")
BADGES = [
    # Internal services
    ("auth", "🔐", "#475569"),      # slate
    ("biz_svc", "BS", "#3B82F6"),   # blue
    ("agent_svc", "AS", "#A855F7"), # purple
    ("brain", "AI", "#EC4899"),     # pink

    # Data sources without simpleicons logos
    ("dv360", "DV", "#34A853"),
    ("stackadapt", "SA", "#FF5C39"),
    ("leadrx", "LX", "#0EA5E9"),
    ("liveramp", "LR", "#00B5AB"),
    ("quorum", "QR", "#1F4F8B"),
    ("trade_desk", "TTD", "#FF7100"),
    ("placeriq", "PIQ", "#005F87"),
    ("experian", "EX", "#0A3F77"),
    ("salesforce", "SF", "#00A1E0"),
    ("netsuite", "NS", "#FF6600"),
    ("adobe_firefly", "FF", "#FF003D"),
    ("canva", "CV", "#00C4CC"),

    # External SaaS without good simpleicons
    ("bedrock", "AWS", "#FF9900"),
    ("aws_s3", "S3", "#E25444"),
    ("langfuse", "LF", "#7C3AED"),
    ("smtp", "✉", "#64748B"),
    ("helicone", "🍯", "#F59E0B"),
]

OUT_DIR = "icons"
os.makedirs(OUT_DIR, exist_ok=True)

# Try to find a bold sans-serif font
FONT_PATHS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
font_path = next((p for p in FONT_PATHS if os.path.exists(p)), None)


def make_badge(slug: str, text: str, bg_hex: str, size: int = 256, radius: int = 48):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded square background
    bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5)) + (255,)
    draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=bg)

    # Decide font size by text length
    fs = 128 if len(text) <= 2 else (96 if len(text) == 3 else 72)

    if font_path:
        try:
            font = ImageFont.truetype(font_path, fs)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    out = os.path.join(OUT_DIR, f"{slug}.png")
    img.save(out, "PNG")
    print(f"  ✓ {out}")


if __name__ == "__main__":
    print(f"Font: {font_path or 'default'}")
    for slug, text, hex_ in BADGES:
        make_badge(slug, text, hex_)
    print(f"\nGenerated {len(BADGES)} badges in {OUT_DIR}/")
