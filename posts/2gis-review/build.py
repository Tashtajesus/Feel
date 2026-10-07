"""Draw the «Дарим лакомства за отзыв в 2ГИС» creative in the ZooGarden identity.

Usage (from the repo root):
  python3 posts/2gis-review/build.py   # draft SVGs in posts/2gis-review/draft/
  node posts/2gis-review/render.cjs    # final Figma-ready SVGs + PNGs

Identity (from the ZooGarden brand board): orange #FF8A00, green #4CAF3B,
dark green #1D4B2A, cream #F6F1E8, sage #DEE4D9; Montserrat ExtraBold for
headlines, Montserrat Medium/Bold for text, Caveat for handwritten stickers;
white die-cut stickers, speech bubbles, leaves, paws and hearts.

The SVG is both the PNG source and the Figma import, so it keeps to what
Figma's SVG import turns into editable layers: shapes, a clip path for the
photo, inline presentation attributes and one <text> per line. The photo is
embedded as JPEG; the @font-face block only matters for rendering (in Figma
Montserrat and Caveat come from Google Fonts).
"""

import base64
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = "../assets/fonts"  # relative to draft/; render.cjs rewrites it for the final files
PHOTO = HERE / "assets" / "titbit-treats.jpg"  # 740x820 crop of the shop's photo

ORANGE, GREEN, DARK = "#FF8A00", "#4CAF3B", "#1D4B2A"
CREAM, SAGE, WHITE = "#F6F1E8", "#DEE4D9", "#FFFFFF"
PHOTO_RATIO = 820 / 740


def font_faces():
    faces = [("Montserrat", w) for w in (500, 700, 800)] + [("Caveat", 700)]
    ranges = {
        "cyrillic": "U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116",
        "latin": "U+0000-00FF, U+0131, U+0152-0153, U+2000-206F, U+20AC, U+2122, U+2212",
    }
    return "\n".join(
        f'@font-face{{font-family:"{fam}";font-weight:{w};'
        f'src:url("{FONTS}/{fam.lower()}-{sub}-{w}-normal.woff2") format("woff2");unicode-range:{rng};}}'
        for fam, w in faces
        for sub, rng in ranges.items()
    )


def text(x, y, s, size, family="Montserrat", weight=800, fill=WHITE, anchor="start", ident=None, extra=""):
    id_attr = f' id="{ident}"' if ident else ""
    return (
        f'<text{id_attr} x="{x}" y="{y}" font-family="{family}" font-weight="{weight}" font-size="{size}"'
        f' fill="{fill}" text-anchor="{anchor}"{extra}>{s}</text>'
    )


def hand(x, y, s, size, fill=DARK, anchor="middle", ident=None):
    return text(x, y, s, size, family="Caveat", weight=700, fill=fill, anchor=anchor, ident=ident)


def heart(cx, cy, size, fill=ORANGE, stroke=None, width=0, rot=0):
    k = size / 100
    d = "M0 -28 C -18 -58 -66 -48 -64 -12 C -62 18 -30 38 0 62 C 30 38 62 18 64 -12 C 66 -48 18 -58 0 -28 Z"
    paint = f'fill="none" stroke="{stroke}" stroke-width="{width / k:.1f}" stroke-linejoin="round"' if stroke else f'fill="{fill}"'
    return f'<path transform="translate({cx} {cy}) rotate({rot}) scale({k:.3f})" d="{d}" {paint}/>'


def paw(cx, cy, scale, rot, fill):
    toes = [(0, 12, 26, 21), (-29, -14, 9, 12), (-10, -30, 9.5, 13), (10, -30, 9.5, 13), (29, -14, 9, 12)]
    shapes = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}"/>' for x, y, rx, ry in toes)
    return f'<g transform="translate({cx} {cy}) rotate({rot}) scale({scale})" fill="{fill}">{shapes}</g>'


def leaf(cx, cy, size, rot, fill, vein="#FFFFFF"):
    k = size / 100
    return (
        f'<g transform="translate({cx} {cy}) rotate({rot}) scale({k:.3f})">'
        f'<path d="M0 -100 C 62 -70 70 30 0 100 C -70 30 -62 -70 0 -100 Z" fill="{fill}"/>'
        f'<path d="M0 -70 Q 6 0 0 92" fill="none" stroke="{vein}" stroke-opacity="0.35" stroke-width="7" stroke-linecap="round"/>'
        "</g>"
    )


def sparks(cx, cy, size, rot, color=WHITE):
    rays = [(-40, 0.55), (0, 0.75), (40, 0.55)]
    lines = []
    for angle, length in rays:
        a = math.radians(angle - 90)
        r0, r1 = size * 0.35, size * (0.35 + length)
        lines.append(
            f'<line x1="{r0 * math.cos(a):.1f}" y1="{r0 * math.sin(a):.1f}" x2="{r1 * math.cos(a):.1f}" y2="{r1 * math.sin(a):.1f}"'
            f' stroke="{color}" stroke-width="{size * 0.09:.1f}" stroke-linecap="round"/>'
        )
    return f'<g transform="translate({cx} {cy}) rotate({rot})">{"".join(lines)}</g>'


def wordmark(x, y, size, ident):
    return text(x, y, "ZooGarden", size, ident=ident, extra=' letter-spacing="-1"')


def headline(x, y1, y2, size, rot):
    return (
        f'<g id="headline" transform="rotate({rot} {x} {y1})">'
        + text(x, y1, "Дарим лакомства", size, ident="headline-1")
        + f'<text id="headline-2" x="{x}" y="{y2}" font-family="Montserrat" font-weight="800" font-size="{size}" fill="{WHITE}">'
        f'за отзыв в <tspan fill="{DARK}">2ГИС</tspan></text>'
        "</g>"
    )


def photo_card(x, y, w, rot, href):
    h = round(w * PHOTO_RATIO)
    b = 14  # white sticker border
    cx, cy = x + w / 2, y + h / 2
    return (
        f'<g id="photo" transform="rotate({rot} {cx} {cy})">'
        f'<rect x="{x - b}" y="{y - b + 16}" width="{w + 2 * b}" height="{h + 2 * b}" rx="{44 + b}" fill="{DARK}" fill-opacity="0.22"/>'
        f'<rect x="{x - b}" y="{y - b}" width="{w + 2 * b}" height="{h + 2 * b}" rx="{44 + b}" fill="{WHITE}"/>'
        f'<clipPath id="photo-clip"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="44"/></clipPath>'
        f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"'
        f' href="{href}" xlink:href="{href}" clip-path="url(#photo-clip)"/>'
        "</g>"
    )


def speech_bubble(x, y, w, h, rot, lines, size):
    cx, cy = x + w / 2, y + h / 2
    tail = f"M{x + w - 70} {y + h - 8} L{x + w + 26} {y + h + 34} L{x + w - 26} {y + h - 30} Z"
    out = [
        f'<g id="bubble" transform="rotate({rot} {cx} {cy})">',
        f'<path d="{tail}" fill="{WHITE}"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2.3:.0f}" fill="{WHITE}"/>',
    ]
    top = cy - (len(lines) - 1) * size * 0.5 + size * 0.32
    for i, line in enumerate(lines):
        out.append(hand(cx - 14, top + i * size, line, size, ident=f"bubble-{i + 1}"))
    out.append(heart(x + w - 52, y + 42, 28, rot=12))
    out.append("</g>")
    return "".join(out)


def round_sticker(cx, cy, r, rot, lines, size):
    top = cy - (len(lines) - 1) * size * 0.5 + size * 0.32
    return (
        f'<g id="sticker" transform="rotate({rot} {cx} {cy})">'
        f'<circle cx="{cx}" cy="{cy}" r="{r + 10}" fill="{WHITE}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GREEN}"/>'
        + "".join(hand(cx, top + i * size, line, size, fill=WHITE, ident=f"sticker-{i + 1}") for i, line in enumerate(lines))
        + "</g>"
    )


def steps_card(x, y, w, row_h, size):
    rows = [
        ("1", "Найдите ZooGarden в 2ГИС"),
        ("2", "Напишите честный отзыв"),
        ("3", "Покажите его на кассе — лакомство ваше"),
    ]
    pad = 30
    note_h = 52
    h = pad * 2 + row_h * len(rows) + note_h
    out = [f'<g id="steps"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="36" fill="{CREAM}"/>']
    for i, (n, label) in enumerate(rows):
        cy = y + pad + row_h * i + row_h / 2
        out.append(f'<circle cx="{x + 62}" cy="{cy}" r="27" fill="{GREEN}"/>')
        out.append(text(x + 62, cy + 10, n, 28, anchor="middle", ident=f"step-{n}-num"))
        out.append(text(x + 108, cy + size * 0.36, label, size, weight=700, fill=DARK, ident=f"step-{n}-text"))
    line_y = y + pad + row_h * len(rows) + 6
    out.append(f'<rect x="{x + 36}" y="{line_y}" width="{w - 72}" height="3" rx="1.5" fill="{SAGE}"/>')
    out.append(
        text(x + w / 2, line_y + 38, "Подарок — за любой честный отзыв, оценка не важна", size * 0.78,
             weight=500, fill=DARK, anchor="middle", ident="note")
    )
    out.append("</g>")
    return "".join(out), h


def defs():
    return f"<defs><style>{font_faces()}</style></defs>"


def svg(w, h, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'
        f' width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        + defs()
        + f'<rect id="background" width="{w}" height="{h}" fill="{ORANGE}"/>'
        + body
        + "</svg>\n"
    )


def photo_href():
    return "data:image/jpeg;base64," + base64.b64encode(PHOTO.read_bytes()).decode("ascii")


def post():
    w, h = 1080, 1350
    href = photo_href()
    top = 972
    steps, steps_h = steps_card(80, top, 920, 62, 32)
    body = (
        '<g id="decor">'
        + leaf(1028, 78, 150, 38, GREEN)
        + leaf(948, 40, 78, -18, DARK)
        + paw(1046, 640, 0.95, -18, GREEN)
        + paw(1000, 742, 0.7, 12, GREEN)
        + sparks(858, 262, 58, 40)
        + heart(330, 420, 46, stroke=WHITE, width=6, rot=-12)
        + "</g>"
        + wordmark(80, 104, 40, "wordmark")
        + headline(80, 222, 314, 82, -3)
        + photo_card(412, 368, 480, 4, href)
        + speech_bubble(54, 486, 330, 176, -6, ["Это вам", "за отзыв!"], 60)
        + round_sticker(330, 860, 84, 12, ["оценка", "любая!"], 42)
        + steps
    )
    assert top + steps_h <= h - 70, "steps card too close to the bottom"
    return svg(w, h, body)


def story():
    w, h = 1080, 1920
    href = photo_href()
    steps, steps_h = steps_card(80, 1318, 920, 70, 32)
    body = (
        '<g id="decor">'
        + leaf(1040, 236, 150, 38, GREEN)
        + leaf(962, 196, 80, -18, DARK)
        + paw(1046, 980, 1.0, -18, GREEN)
        + paw(996, 1090, 0.74, 12, GREEN)
        + sparks(922, 446, 62, 40)
        + heart(330, 640, 50, stroke=WHITE, width=6, rot=-12)
        + "</g>"
        + wordmark(80, 268, 44, "wordmark")
        + headline(80, 400, 496, 84, -3)
        + photo_card(372, 584, 580, 4, href)
        + speech_bubble(46, 712, 350, 190, -6, ["Это вам", "за отзыв!"], 64)
        + round_sticker(320, 1186, 92, 12, ["оценка", "любая!"], 46)
        + steps
    )
    # Instagram's reply bar and link sticker need the bottom ~260 px.
    assert 1318 + steps_h <= h - 260, "steps card runs into the story's bottom zone"
    return svg(w, h, body)


if __name__ == "__main__":
    out = HERE / "draft"
    out.mkdir(exist_ok=True)
    (out / "2gis-review-post.svg").write_text(post(), encoding="utf-8")
    (out / "2gis-review-story.svg").write_text(story(), encoding="utf-8")
    print("wrote", ", ".join(p.name for p in sorted(out.glob("*.svg"))))
