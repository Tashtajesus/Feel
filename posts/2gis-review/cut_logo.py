"""Cut the ZooGarden logo out of the brand board as transparent PNGs.

Usage (from the repo root):
  python3 posts/2gis-review/cut_logo.py posts/2gis-review/assets/zoogarden-brandboard.jpg

Writes assets/zoogarden-mark.png (dog and cat in the ring) and
assets/zoogarden-logo.png (mark, wordmark and tagline). The board is a
1212x1297 raster, so these are raster stand-ins until a vector logo arrives.

The background is removed by flooding the board's cream from the crop edges:
the white faces inside the mark are fenced by dark outlines, so they stay.
Anything that is not attached to the logo itself (board captions, the
handwritten note, the leaf at the edge) is dropped by connected components.
"""

import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent

# Boxes on the 1212x1297 board: (left, top, right, bottom).
MARK_BOX = (138, 30, 342, 201)
LOGO_BOX = (42, 30, 462, 306)
# Board captions near the logo that must not survive (in LOGO_BOX coordinates).
LOGO_DROP = [(0, 0, 105, 66), (286, 0, 420, 72)]


def flood_background(rgb, tol):
    h, w, _ = rgb.shape
    edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(edge, axis=0)
    close = np.linalg.norm(rgb - bg, axis=2) < tol
    seen = np.zeros((h, w), bool)
    q = deque((y, x) for y in range(h) for x in (0, w - 1)) + deque((y, x) for x in range(w) for y in (0, h - 1))
    while q:
        y, x = q.popleft()
        if seen[y, x] or not close[y, x]:
            continue
        seen[y, x] = True
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]:
                q.append((ny, nx))
    return seen, bg


def components(mask):
    h, w = mask.shape
    labels = np.zeros((h, w), int)
    sizes, boxes = [0], [None]
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or labels[sy, sx]:
                continue
            n = len(sizes)
            labels[sy, sx] = n
            q, count, box = deque([(sy, sx)]), 0, [sx, sy, sx, sy]
            while q:
                y, x = q.popleft()
                count += 1
                box = [min(box[0], x), min(box[1], y), max(box[2], x), max(box[3], y)]
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not labels[ny, nx]:
                            labels[ny, nx] = n
                            q.append((ny, nx))
            sizes.append(count)
            boxes.append(box)
    return labels, sizes, boxes


def shift_or(mask, r):
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            shifted = np.zeros_like(mask)
            ys = slice(max(dy, 0), mask.shape[0] + min(dy, 0))
            yd = slice(max(-dy, 0), mask.shape[0] + min(-dy, 0))
            xs = slice(max(dx, 0), mask.shape[1] + min(dx, 0))
            xd = slice(max(-dx, 0), mask.shape[1] + min(-dx, 0))
            shifted[ys, xs] = mask[yd, xd]
            out |= shifted
    return out


def silhouette(keep, r):
    """Close small gaps in the outline, then fill everything the outline encloses."""
    pad = r + 2  # without a margin the closing sticks to the image edge
    padded = np.pad(keep, pad)
    closed = ~shift_or(~shift_or(padded, r), r)
    outside, _ = flood_background(np.dstack([closed * 255.0] * 3), tol=1)
    return (~outside)[pad:-pad, pad:-pad] | keep


def cutout(board, box, drop=(), tol=26, min_size=40, fill_rows=None):
    rgb = np.asarray(board.crop(box).convert("RGB")).astype(float)
    bg_mask, bg = flood_background(rgb, tol)
    labels, sizes, boxes = components(~bg_mask)
    h, w = labels.shape
    keep = np.zeros((h, w), bool)
    for n in range(1, len(sizes)):
        x0, y0, x1, y1 = boxes[n]
        touches_edge = x0 == 0 or y0 == 0 or x1 == w - 1 or y1 == h - 1
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dropped = any(a <= cx <= c and b <= cy <= d for a, b, c, d in drop)
        if sizes[n] >= min_size and not touches_edge and not dropped:
            keep |= labels == n
    # The dog's outline is open near the nose, so the flood also takes its white face:
    # inside fill_rows, everything the mark encloses is put back.
    if fill_rows:
        y0, y1 = fill_rows
        sil = silhouette(keep, r=6)
        keep[y0:y1] |= sil[y0:y1]
    # Soft edge: one-pixel band around the kept area, alpha from distance to the background colour.
    dist = np.linalg.norm(rgb - bg, axis=2)
    alpha = keep.astype(float)
    grown = keep.copy()
    grown[1:] |= keep[:-1]
    grown[:-1] |= keep[1:]
    grown[:, 1:] |= keep[:, :-1]
    grown[:, :-1] |= keep[:, 1:]
    band = grown & ~keep
    alpha[band] = np.clip((dist[band] - 6) / 40, 0, 1)
    # Remove the cream that is mixed into semi-transparent edge pixels.
    a = np.clip(alpha, 1e-3, 1)[..., None]
    colour = np.clip((rgb - (1 - a) * bg) / a, 0, 255)
    rgba = np.dstack([colour, alpha * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    return img.crop(img.getbbox())


def main(board_path):
    board = Image.open(board_path)
    assert board.size == (1212, 1297), f"unexpected board size {board.size}"
    out = HERE / "assets"
    mark = cutout(board, MARK_BOX, fill_rows=(0, MARK_BOX[3] - MARK_BOX[1]))
    # Only the mark part of the full logo is filled; letter counters stay transparent.
    logo = cutout(board, LOGO_BOX, drop=LOGO_DROP, min_size=12, fill_rows=(0, 170))
    mark.save(out / "zoogarden-mark.png")
    logo.save(out / "zoogarden-logo.png")
    print("mark", mark.size, "logo", logo.size)


if __name__ == "__main__":
    main(sys.argv[1])
