"""Draw the «Дарим корм за отзыв в 2ГИС» creative as SVG (post and story).

Usage (from the repo root):
  python3 posts/2gis-review/build.py   # writes draft SVGs to posts/2gis-review/draft/
  node posts/2gis-review/render.cjs    # final Figma-ready SVGs + PNGs

The SVG is the source for both the PNG and the Figma import, so it sticks to
what Figma's SVG import keeps as editable layers: plain shapes, linear/radial
gradients, inline presentation attributes and one <text> per line. No filters,
no <pattern>, no CSS classes. The @font-face block only matters for rendering;
in Figma the same fonts (Unbounded, Rubik, Oswald) come from Google Fonts.
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = "../../../videos/dog-bags-parade/assets/fonts"

INK, PAPER, CREAM, PAW_FILL = "#221C17", "#FFFDF8", "#FFF4E4", "#F6DFC0"
MUTED, GREEN, GREEN_SOFT = "#5E554D", "#17A34A", "#DDF3E4"
RIBBON, RIBBON_DARK, STAR = "#DE3A2B", "#A92A1F", "#F2A20C"
BAG, BAG_DARK = "#2347A8", "#152E70"


def font_faces():
    faces = [
        ("Unbounded", 800, "unbounded-cyrillic-800-normal", "cyr"),
        ("Unbounded", 800, "unbounded-latin-800-normal", "lat"),
        ("Rubik", 700, "rubik-cyrillic-700-normal", "cyr"),
        ("Rubik", 700, "rubik-latin-700-normal", "lat"),
        ("Rubik", 600, "rubik-cyrillic-600-normal", "cyr"),
        ("Rubik", 600, "rubik-latin-600-normal", "lat"),
        ("Oswald", 700, "oswald-cyrillic-700-normal", "cyr"),
        ("Oswald", 700, "oswald-latin-700-normal", "lat"),
    ]
    ranges = {
        "cyr": "U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116",
        "lat": "U+0000-00FF, U+0131, U+0152-0153, U+2000-206F, U+20AC, U+2122, U+2212",
    }
    return "\n".join(
        f'@font-face{{font-family:"{fam}";font-weight:{w};src:url("{FONTS}/{f}.woff2") format("woff2");unicode-range:{ranges[r]};}}'
        for fam, w, f, r in faces
    )


def text(x, y, s, size, family="Rubik", weight=700, fill=INK, anchor="middle", ident=None, extra=""):
    id_attr = f' id="{ident}"' if ident else ""
    return (
        f'<text{id_attr} x="{x}" y="{y}" font-family="{family}" font-weight="{weight}" font-size="{size}"'
        f' fill="{fill}" text-anchor="{anchor}"{extra}>{s}</text>'
    )


def paw(cx, cy, scale, rot, fill):
    toes = [(0, 12, 26, 21), (-29, -14, 9, 12), (-10, -30, 9.5, 13), (10, -30, 9.5, 13), (29, -14, 9, 12)]
    shapes = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}"/>' for x, y, rx, ry in toes)
    return f'<g transform="translate({cx} {cy}) rotate({rot}) scale({scale})" fill="{fill}">{shapes}</g>'


def background(w, h):
    paws = "".join(
        paw(tx + 60, ty + 70, 0.6, -18, PAW_FILL) + paw(tx + 180, ty + 190, 0.6, 16, PAW_FILL)
        for ty in range(0, h, 240)
        for tx in range(0, w, 240)
    )
    return (
        f'<rect id="background" width="{w}" height="{h}" fill="{CREAM}"/>'
        f'<g id="paws">{paws}</g>'
        f'<rect id="glow" width="{w}" height="{h}" fill="url(#glow-grad)"/>'
    )


def chip(cx, y, h, label, size, fill, color, ident, pad=30):
    """Pill around a centered label; render.cjs sizes the pill to the measured text."""
    return (
        f'<g id="{ident}">'
        f'<rect x="{cx - 100}" y="{y}" width="200" height="{h}" rx="{h / 2}" fill="{fill}" data-chip-for="{ident}-text" data-pad="{pad}"/>'
        + text(cx, y + h / 2 + size * 0.36, label, size, fill=color, ident=f"{ident}-text", extra=' letter-spacing="2"')
        + "</g>"
    )


def gift_bag(x, y, scale):
    """Food bag with a ribbon and bow, drawn in a 400x540 box."""
    body = "M44 58 C36 200 30 380 30 478 C30 510 52 524 84 524 L316 524 C348 524 370 510 370 478 C370 380 364 200 356 58 Z"
    teeth = "M36 30" + "".join(" l10.25 -12 l10.25 12" for _ in range(16)) + " L364 74 Q200 84 36 74 Z"
    return (
        f'<g id="gift-bag" transform="translate({x} {y}) scale({scale})">'
        f'<ellipse cx="200" cy="532" rx="190" ry="22" fill="{INK}" fill-opacity="0.16"/>'
        f'<path d="{body}" fill="{BAG}"/>'
        f'<path d="{body}" fill="url(#sheen)"/>'
        f'<rect x="184" y="70" width="32" height="454" fill="{RIBBON}"/>'
        f'<rect x="33" y="404" width="334" height="32" fill="{RIBBON}"/>'
        f'<path d="{teeth}" fill="{BAG_DARK}"/>'
        f'<line x1="52" y1="56" x2="348" y2="56" stroke="{PAPER}" stroke-opacity="0.45" stroke-width="3" stroke-dasharray="10 8"/>'
        f'<rect x="72" y="138" width="256" height="206" rx="28" fill="{PAPER}"/>'
        + paw(200, 192, 0.6, 0, BAG)
        + text(200, 282, "КОРМ", 64, family="Oswald", weight=700, fill=BAG_DARK, ident="bag-name")
        + text(200, 322, "В ПОДАРОК", 22, fill=MUTED, ident="bag-sub", extra=' letter-spacing="3"')
        # Bow on the top seal.
        + '<g transform="translate(200 36)">'
        f'<path d="M-6 6 L-58 74 L-34 70 L-22 92 L-2 14 Z" fill="{RIBBON_DARK}"/>'
        f'<path d="M6 6 L58 74 L34 70 L22 92 L2 14 Z" fill="{RIBBON_DARK}"/>'
        f'<ellipse cx="-44" cy="-18" rx="48" ry="27" transform="rotate(-24 -44 -18)" fill="{RIBBON}"/>'
        f'<ellipse cx="44" cy="-18" rx="48" ry="27" transform="rotate(24 44 -18)" fill="{RIBBON}"/>'
        f'<ellipse cx="-40" cy="-16" rx="22" ry="10" transform="rotate(-24 -40 -16)" fill="{RIBBON_DARK}"/>'
        f'<ellipse cx="40" cy="-16" rx="22" ry="10" transform="rotate(24 40 -16)" fill="{RIBBON_DARK}"/>'
        f'<circle cx="0" cy="-4" r="20" fill="{RIBBON}"/>'
        "</g></g>"
    )


def star(cx, cy, r):
    import math

    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 0.45
        a = math.radians(-90 + i * 36)
        pts.append(f"{cx + rad * math.cos(a):.1f},{cy + rad * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{PAPER}" stroke="{STAR}" stroke-width="4" stroke-linejoin="round"/>'


def review_card(x, y, w, h, rot):
    """Generic review being written: empty stars, a pencil, text lines. Not a copy of the 2GIS UI."""
    cx, cy = x + w / 2, y + h / 2
    stars = "".join(star(x + 58 + i * 52, y + 132, 20) for i in range(5))
    lines = "".join(
        f'<rect x="{x + 36}" y="{y + 178 + i * 30}" width="{lw}" height="14" rx="7" fill="#E9E2D8"/>'
        for i, lw in enumerate((w - 72, w - 120, w - 190))
    )
    return (
        f'<g id="review-card" transform="rotate({rot} {cx} {cy})">'
        f'<rect x="{x}" y="{y + 10}" width="{w}" height="{h}" rx="30" fill="{INK}" fill-opacity="0.10"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="30" fill="{PAPER}"/>'
        f'<circle cx="{x + 64}" cy="{y + 62}" r="30" fill="{GREEN_SOFT}"/>'
        f'<circle cx="{x + 64}" cy="{y + 54}" r="11" fill="{GREEN}"/>'
        f'<path d="M{x + 44} {y + 82} Q{x + 64} {y + 60} {x + 84} {y + 82} Z" fill="{GREEN}"/>'
        + text(x + 110, y + 74, "Ваш отзыв", 34, anchor="start", ident="review-title")
        + stars
        # Pencil writing the review.
        + f'<g transform="translate({x + w - 72} {y + 130}) rotate(40)">'
        f'<rect x="-9" y="-46" width="18" height="70" rx="3" fill="#FFD60A"/>'
        f'<rect x="-9" y="-56" width="18" height="12" rx="3" fill="{RIBBON}"/>'
        f'<path d="M-9 24 L9 24 L0 42 Z" fill="#F3D9B1"/><path d="M-3 36 L3 36 L0 42 Z" fill="{INK}"/>'
        "</g>"
        + lines
        + "</g>"
    )


def map_pin(cx, cy, s):
    return (
        f'<g id="map-pin" transform="translate({cx} {cy}) scale({s})">'
        f'<path d="M0 58 C-12 40 -44 14 -44 -12 A44 44 0 1 1 44 -12 C44 14 12 40 0 58 Z" fill="{GREEN}"/>'
        f'<circle cx="0" cy="-12" r="27" fill="{PAPER}"/>'
        + paw(0, -10, 0.42, 0, GREEN)
        + "</g>"
    )


def steps_card(x, y, w, row_h, size):
    rows = [
        ("1", "Найдите Zoogarden в 2ГИС"),
        ("2", "Напишите честный отзыв"),
        ("3", "Покажите его на кассе — корм ваш"),
    ]
    pad = 34
    h = pad * 2 + row_h * len(rows)
    out = [f'<g id="steps"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="34" fill="{PAPER}"/>']
    for i, (n, label) in enumerate(rows):
        cy = y + pad + row_h * i + row_h / 2
        out.append(f'<circle cx="{x + 66}" cy="{cy}" r="30" fill="{GREEN}"/>')
        out.append(text(x + 66, cy + 11, n, 30, family="Unbounded", weight=800, fill=PAPER, ident=f"step-{n}-num"))
        out.append(text(x + 118, cy + size * 0.36, label, size, anchor="start", ident=f"step-{n}-text"))
    out.append("</g>")
    return "".join(out), h


def defs():
    return (
        "<defs>"
        '<radialGradient id="glow-grad" cx="0.5" cy="0.42" r="0.62">'
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.85"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>'
        "</radialGradient>"
        '<linearGradient id="sheen" x1="0" x2="1" y1="0" y2="0">'
        '<stop offset="0" stop-color="#000000" stop-opacity="0.28"/>'
        '<stop offset="0.13" stop-color="#000000" stop-opacity="0"/>'
        '<stop offset="0.28" stop-color="#FFFFFF" stop-opacity="0.22"/>'
        '<stop offset="0.4" stop-color="#FFFFFF" stop-opacity="0"/>'
        '<stop offset="0.86" stop-color="#000000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000000" stop-opacity="0.3"/>'
        "</linearGradient>"
        f"<style>{font_faces()}</style>"
        "</defs>"
    )


def headline(cx, y1, y2, s1, s2):
    return (
        '<g id="headline">'
        + text(cx, y1, "Дарим корм", s1, family="Unbounded", weight=800, ident="headline-1")
        + f'<text id="headline-2" x="{cx}" y="{y2}" font-family="Unbounded" font-weight="800" font-size="{s2}" fill="{INK}" text-anchor="middle">'
        f'за отзыв в <tspan fill="{GREEN}">2ГИС</tspan></text>'
        "</g>"
    )


def svg(w, h, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        + defs()
        + background(w, h)
        + body
        + "</svg>\n"
    )


def post():
    w, h = 1080, 1350
    top = 848
    steps, steps_h = steps_card(80, top, 920, 72, 38)
    body = (
        chip(540, 70, 64, "АКЦИЯ", 32, INK, PAPER, "tag")
        + headline(540, 256, 344, 100, 62)
        + gift_bag(165, 410, 0.74)
        + review_card(548, 436, 432, 290, -4)
        + map_pin(948, 452, 1.0)
        + steps
        + text(540, top + steps_h + 52, "Подарок — за любой честный отзыв, оценка не важна", 28, weight=600, fill=MUTED, ident="note")
        + chip(540, top + steps_h + 80, 62, "Zoogarden · Павлодар", 32, INK, PAPER, "footer", pad=40)
    )
    return svg(w, h, body)


def story():
    w, h = 1080, 1920
    top = 1150
    steps, steps_h = steps_card(80, top, 920, 84, 40)
    body = (
        chip(540, 250, 66, "АКЦИЯ", 34, INK, PAPER, "tag")
        + headline(540, 450, 546, 106, 66)
        + gift_bag(140, 630, 0.86)
        + review_card(560, 660, 440, 296, -4)
        + map_pin(960, 676, 1.08)
        + steps
        + text(540, top + steps_h + 62, "Подарок — за любой честный отзыв, оценка не важна", 30, weight=600, fill=MUTED, ident="note")
        + chip(540, top + steps_h + 96, 66, "Zoogarden · Павлодар", 34, INK, PAPER, "footer", pad=42)
    )
    return svg(w, h, body)


if __name__ == "__main__":
    out = HERE / "draft"
    out.mkdir(exist_ok=True)
    (out / "2gis-review-post.svg").write_text(post(), encoding="utf-8")
    (out / "2gis-review-story.svg").write_text(story(), encoding="utf-8")
    print("wrote", ", ".join(p.name for p in sorted(out.glob("*.svg"))))
