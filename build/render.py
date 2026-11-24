#!/usr/bin/env python3
"""Biscuit Isle: parchment chart of the last biscuit."""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
S = 2048
CX, CY = 1044.0, 1172.0
R = 630.0
BITE_DIST = 636.0
BITE_ANG = -math.pi / 4.05
BX = CX + BITE_DIST * math.cos(BITE_ANG)
BY = CY + BITE_DIST * math.sin(BITE_ANG)
RB = 324.0

FONT_DIR = Path("/usr/share/fonts/truetype/sand-box/google")
FONT_PLACE = FONT_DIR / "IM Fell English SC" / "IMFellEnglishSC-Regular.ttf"
FONT_NOTE = FONT_DIR / "Patrick Hand" / "PatrickHand-Regular.ttf"
FONT_TITLE = FONT_DIR / "Pirata One" / "PirataOne-Regular.ttf"

INK = (62, 36, 22, 255)
INK_SOFT = (86, 54, 34, 150)
HALO = (246, 234, 208, 235)
RED = (158, 36, 28, 255)


def wobble(ang):
    return (
        22 * math.sin(3 * ang + 0.40)
        + 14 * math.sin(7 * ang + 1.15)
        + 8 * math.sin(12 * ang + 2.20)
        + 5 * math.sin(18 * ang + 0.35)
        + 3.5 * math.sin(27 * ang + 1.70)
    )


def tooth(bang):
    return (
        26 * math.sin(15 * bang + 0.35)
        + 12 * math.sin(22 * bang + 1.15)
        + 7 * math.sin(8 * bang + 0.2)
    )


def coast_points(expand=0.0, n=980):
    """Closed coastline. expand > 0 shifts the shore seaward."""
    angs = [(-math.pi + 2 * math.pi * i / n) for i in range(n)]
    outer, bitten = [], []
    for ang in angs:
        rr = R + wobble(ang) + expand
        x = CX + rr * math.cos(ang)
        y = CY + rr * math.sin(ang)
        bang = math.atan2(y - BY, x - BX)
        br = RB + tooth(bang) - expand * 0.9
        bitten.append(math.hypot(x - BX, y - BY) < br)
        outer.append((x, y))
    idx = bitten.index(False)
    order = list(range(idx, n)) + list(range(idx))
    run = [bitten[i] for i in order]
    a = run.index(True)
    b = a
    while b < n and run[b]:
        b += 1
    j1 = outer[order[a - 1]]
    j2 = outer[order[b % n]]
    raw = []
    for k in range(520):
        bang = -math.pi + 2 * math.pi * k / 520
        br = RB + tooth(bang) - expand * 0.9
        x = BX + br * math.cos(bang)
        y = BY + br * math.sin(bang)
        ang = math.atan2(y - CY, x - CX)
        if math.hypot(x - CX, y - CY) < R + wobble(ang) + expand - 1.5:
            raw.append((bang, x, y))
    raw.sort()
    chains, cur = [], [raw[0]]
    for p in raw[1:]:
        if p[0] - cur[-1][0] > 0.25:
            chains.append(cur)
            cur = [p]
        else:
            cur.append(p)
    chains.append(cur)
    if len(chains) > 1 and chains[0][0][0] + 2 * math.pi - chains[-1][-1][0] < 0.25:
        chains[0] = chains[-1] + chains[0]
        chains.pop()

    def cost(ch):
        a1, a2 = (ch[0][1], ch[0][2]), (ch[-1][1], ch[-1][2])
        fwd = math.hypot(a1[0] - j1[0], a1[1] - j1[1]) + math.hypot(a2[0] - j2[0], a2[1] - j2[1])
        rev = math.hypot(a2[0] - j1[0], a2[1] - j1[1]) + math.hypot(a1[0] - j2[0], a1[1] - j2[1])
        return fwd, rev

    best = min(chains, key=lambda ch: min(cost(ch)))
    fwd, rev = cost(best)
    arc = [(p[1], p[2]) for p in best]
    if rev < fwd:
        arc = arc[::-1]
    coast = [outer[i] for i in order[:a]] + arc + [outer[i] for i in order[b:]]
    return cut_with_circle(coast, SAUCER[0], SAUCER[1], lambda bang: SAUCER[2] - expand * 0.85 + 12 * math.sin(3 * bang + 0.4))


# South coast, just outside the shore, so the circle scoops a round bay.
SA_ANG = math.pi / 2 + 0.06
SAUCER = (
    CX + (R + 36) * math.cos(SA_ANG),
    CY + (R + 36) * math.sin(SA_ANG),
    248.0,
)


def cut_with_circle(pts, ox, oy, rad_fn):
    """Replace the run of pts that falls inside the circle with that circle's inner arc."""
    n = len(pts)
    inside = []
    for x, y in pts:
        ang = math.atan2(y - oy, x - ox)
        inside.append(math.hypot(x - ox, y - oy) < rad_fn(ang) - 1.2)
    if not any(inside) or all(inside):
        return pts
    start = inside.index(False)
    order = list(range(start, n)) + list(range(start))
    run = [inside[i] for i in order]
    a = run.index(True)
    b = a
    while b < n and run[b]:
        b += 1
    if b >= n:
        return pts
    j1 = pts[order[a - 1]]
    j2 = pts[order[b]]
    raw = []
    for k in range(560):
        bang = -math.pi + 2 * math.pi * k / 560
        br = rad_fn(bang)
        x = ox + br * math.cos(bang)
        y = oy + br * math.sin(bang)
        ang = math.atan2(y - CY, x - CX)
        if math.hypot(x - CX, y - CY) >= R + wobble(ang) - 2:
            continue
        bite_a = math.atan2(y - BY, x - BX)
        if math.hypot(x - BX, y - BY) < RB + tooth(bite_a) - 2:
            continue
        raw.append((bang, x, y))
    if len(raw) < 8:
        return pts
    raw.sort()
    chains, cur = [], [raw[0]]
    for p in raw[1:]:
        gap = p[0] - cur[-1][0]
        if gap > 0.35:
            chains.append(cur)
            cur = [p]
        else:
            cur.append(p)
    chains.append(cur)
    if len(chains) > 1 and chains[0][0][0] + 2 * math.pi - chains[-1][-1][0] < 0.35:
        chains[0] = chains[-1] + chains[0]
        chains.pop()

    def cost(ch):
        a1, a2 = (ch[0][1], ch[0][2]), (ch[-1][1], ch[-1][2])
        fwd = math.hypot(a1[0] - j1[0], a1[1] - j1[1]) + math.hypot(a2[0] - j2[0], a2[1] - j2[1])
        rev = math.hypot(a2[0] - j1[0], a2[1] - j1[1]) + math.hypot(a1[0] - j2[0], a1[1] - j2[1])
        return fwd, rev

    best = min(chains, key=lambda ch: min(cost(ch)))
    fwd, rev = cost(best)
    arc = [(p[1], p[2]) for p in best]
    if rev < fwd:
        arc = arc[::-1]
    return [pts[i] for i in order[:a]] + arc + [pts[i] for i in order[b:]]


def _noise(rng, n):
    small = rng.random((n, n), dtype=np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8), "L").resize((S, S), Image.Resampling.BICUBIC)
    return np.asarray(img).astype(np.float32) / 255.0


def parchment():
    """Warm cream sheet: stains, burnt corners, faint fibres. Fixed seed."""
    rng = np.random.default_rng(1752)
    arr = np.empty((S, S, 4), np.float32)
    arr[..., 0] = 239
    arr[..., 1] = 224
    arr[..., 2] = 189
    arr[..., 3] = 255
    fine = rng.normal(0, 4.2, (S, S)).astype(np.float32)
    fibre = Image.new("L", (S, S), 0)
    fd = ImageDraw.Draw(fibre)
    for _ in range(1400):
        x = float(rng.uniform(0, S))
        y = float(rng.uniform(0, S))
        ang = float(rng.uniform(0, math.pi))
        length = float(rng.uniform(10, 36))
        shade = int(rng.integers(40, 110))
        fd.line(
            [(x, y), (x + math.cos(ang) * length, y + math.sin(ang) * length)],
            fill=shade,
            width=1,
        )
    threads = np.asarray(fibre.filter(ImageFilter.GaussianBlur(0.4))).astype(np.float32)
    arr[..., 0] += fine - threads * 0.09
    arr[..., 1] += fine * 0.78 - threads * 0.07
    arr[..., 2] += fine * 0.42 - threads * 0.04
    stain = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stain)
    for _ in range(20):
        x = int(rng.integers(-40, S - 40))
        y = int(rng.integers(-40, S - 40))
        rx, ry = int(rng.integers(110, 460)), int(rng.integers(80, 320))
        col = (
            int(rng.integers(128, 176)),
            int(rng.integers(82, 124)),
            int(rng.integers(42, 78)),
            int(rng.integers(22, 48)),
        )
        sd.ellipse([x - rx, y - ry, x + rx, y + ry], fill=col)
    stain_a = np.asarray(stain.filter(ImageFilter.GaussianBlur(26))).astype(np.float32)
    sa = stain_a[..., 3:4] / 255.0
    arr[..., :3] = arr[..., :3] * (1 - sa) + stain_a[..., :3] * sa
    return np.clip(arr, 0, 255)


def paint_washes(arr, coast):
    """Even teal watercolour: pale at the shore, deeper offshore, paper still showing."""
    rng = np.random.default_rng(1753)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(coast, fill=255)
    land = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    land_soft = np.asarray(mask.filter(ImageFilter.GaussianBlur(7))).astype(np.float32) / 255.0
    # Broad, smooth depth. Built on a small mask so the falloff cannot clot into clouds.
    small = mask.resize((384, 384), Image.Resampling.BOX)
    b_far = np.asarray(
        small.filter(ImageFilter.GaussianBlur(32)).resize((S, S), Image.Resampling.BICUBIC)
    ).astype(np.float32) / 255.0
    b_mid = np.asarray(
        small.filter(ImageFilter.GaussianBlur(12)).resize((S, S), Image.Resampling.BICUBIC)
    ).astype(np.float32) / 255.0
    b_near = np.asarray(mask.filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255.0
    shore = np.clip(b_near * 0.50 + b_mid * 0.70 + b_far * 0.95, 0, 1)
    depth = np.clip(1.0 - shore, 0, 1) ** 0.85
    n1 = _noise(rng, 36)
    n2 = _noise(rng, 14)
    # Fine grain only: a tight high-frequency field, a few percent at most.
    grit = np.random.default_rng(1761).normal(0, 28, (720, 720)).astype(np.float32)
    grit = np.clip(grit + 128, 0, 255).astype(np.uint8)
    grain = (np.asarray(Image.fromarray(grit, "L").resize((S, S), Image.Resampling.BILINEAR)).astype(np.float32) - 128) / 128.0
    streaks = Image.new("L", (S, S), 0)
    sd = ImageDraw.Draw(streaks)
    pen = np.random.default_rng(1760)
    for i in range(5):
        y0 = float(pen.uniform(120, S - 140))
        phase = float(pen.uniform(0, 6.2))
        amp = float(pen.uniform(8, 16))
        pts = [
            (x, y0 + amp * math.sin(x / 340.0 + phase) + 6 * math.sin(x / 120.0 + i))
            for x in range(40, S - 40, 28)
        ]
        sd.line(pts, fill=int(pen.integers(70, 120)), width=int(pen.integers(8, 14)))
    streak = np.asarray(streaks.filter(ImageFilter.GaussianBlur(9))).astype(np.float32) / 255.0
    streak *= 1.0 - land_soft
    shallow = np.array([158, 204, 194], np.float32)
    deep = np.array([42, 118, 126], np.float32)
    tone = np.clip(depth * 0.90 + grain * 0.035 + streak * 0.08, 0, 1)
    sea_col = shallow * (1 - tone)[..., None] + deep * tone[..., None]
    sea_a = np.clip(0.16 + 0.32 * depth + grain * 0.018 + streak * 0.05, 0.0, 0.52)
    sea_a *= 1.0 - land_soft
    paper = arr[..., :3]
    out = paper * (1 - sea_a)[..., None] + sea_col * sea_a[..., None]
    yy, xx = np.mgrid[0:S, 0:S]
    nL = _noise(rng, 42)
    nG = _noise(rng, 18)
    gold = np.array([226, 178, 104], np.float32)
    toast = np.array([188, 132, 68], np.float32)
    land_col = gold * (0.88 + 0.22 * nL)[..., None] * (0.96 + 0.08 * (n1 - 0.5))[..., None]
    land_col = land_col * (1 - 0.22 * n2)[..., None] + toast * (0.22 * n2)[..., None]
    green_m = np.clip((nG - 0.62) * 4.0, 0, 1)
    lowland = np.clip((yy - (CY - 220)) / 640.0, 0, 1) * np.clip((CX + 80 - xx) / 820.0 + 0.35, 0, 1)
    green_m *= lowland
    green = np.array([112, 138, 74], np.float32)
    land_col = land_col * (1 - 0.5 * green_m)[..., None] + green * (0.5 * green_m)[..., None]
    rim_blur = np.asarray(mask.filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255.0
    rim = np.clip((0.90 - rim_blur) * 3.6, 0, 1)
    baked = np.array([122, 70, 34], np.float32)
    land_col = land_col * (1 - 0.7 * rim)[..., None] + baked * (0.7 * rim)[..., None]
    wash_land = paper * 0.18 + land_col * 0.82
    out = out * (1 - land)[..., None] + wash_land * land[..., None]
    nx = (xx - S / 2) / (S * 0.5)
    ny = (yy - S / 2) / (S * 0.5)
    v = np.clip((nx * nx + ny * ny - 0.28) / 0.95, 0, 1) ** 1.25
    burn = np.array([98, 52, 26], np.float32)
    out = out * (1 - 0.58 * v)[..., None] + burn * (0.58 * v)[..., None]
    arr = arr.copy()
    arr[..., :3] = np.clip(out, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def draw_waves(img, coast):
    """A few hand-drawn wave ticks in open water, clear of the shore."""
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(coast, fill=255)
    near = np.asarray(mask.filter(ImageFilter.GaussianBlur(18)))
    rng = np.random.default_rng(9)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    placed = 0
    for _ in range(700):
        if placed >= 16:
            break
        x = int(rng.integers(70, S - 90))
        y = int(rng.integers(300, S - 90))
        if near[y, x] > 12:
            continue
        if y < 320 and 380 < x < 1680:
            continue
        w = int(rng.integers(16, 34))
        h = int(rng.integers(7, 14))
        draw.arc([x, y, x + w, y + h], 200, 340, fill=(36, 64, 74, 150), width=2)
        if rng.random() > 0.55:
            draw.arc([x + w + 6, y + 2, x + w + 6 + w, y + h + 2], 200, 340, fill=(36, 64, 74, 120), width=2)
        placed += 1
    img.alpha_composite(overlay)


def stroke(draw, pts, fill, width):
    draw.line(pts + [pts[0]], fill=fill, width=width, joint="curve")


def smooth_ring(pts, win):
    n = len(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    out = []
    span = 2 * win + 1
    for i in range(n):
        sx = sy = 0.0
        for k in range(-win, win + 1):
            j = (i + k) % n
            sx += xs[j]
            sy += ys[j]
        out.append((sx / span, sy / span))
    return out


def stroke_open(draw, pts, fill, width, max_step):
    """Draw a polyline, breaking it where a fold would jump across the water."""
    if len(pts) < 2:
        return
    cur = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - cur[-1][0], p[1] - cur[-1][1]) > max_step:
            if len(cur) > 10:
                draw.line(cur, fill=fill, width=width, joint="curve")
            cur = [p]
        else:
            cur.append(p)
    if len(cur) > 10:
        draw.line(cur, fill=fill, width=width, joint="curve")


def draw_coast_ripples(draw, coast):
    """Parallel ink ripples. The bite is three smooth arcs; the rest follow the shore."""
    bite = []
    for x, y in coast:
        bang = math.atan2(y - BY, x - BX)
        bite.append(abs(math.hypot(x - BX, y - BY) - (RB + tooth(bang))) < 42)
    # Close small gaps so the bay reads as one run, and include the two junctions.
    flagged = bite[:]
    for i, on in enumerate(bite):
        if on:
            for k in range(-8, 9):
                flagged[(i + k) % len(bite)] = True
    ring = smooth_ring(coast, 14)
    for gap, alpha in ((16, 150), (34, 115), (54, 82), (76, 56)):
        off = offset_outward(ring, gap)
        kept = []
        for p, on in zip(off, flagged):
            kept.append(None if on else p)
        cur = []
        for p in kept:
            if p is None:
                stroke_open(draw, cur, (36, 72, 82, alpha), 3, max_step=22)
                cur = []
            else:
                cur.append(p)
        stroke_open(draw, cur, (36, 72, 82, alpha), 3, max_step=22)
    # Bite Bay: two or three neat arcs parallel to the bitten shore, no tooth fans.
    for inset, alpha in ((28, 160), (52, 120), (76, 84)):
        pts, runs = [], []
        for k in range(480):
            bang = -math.pi + 2 * math.pi * k / 480
            br = RB - inset
            x = BX + br * math.cos(bang)
            y = BY + br * math.sin(bang)
            ang = math.atan2(y - CY, x - CX)
            in_bay = math.hypot(x - CX, y - CY) < R + wobble(ang) - 10
            if in_bay:
                pts.append((x, y))
            elif len(pts) > 16:
                runs.append(pts)
                pts = []
            else:
                pts = []
        if len(pts) > 16:
            runs.append(pts)
        if not runs:
            continue
        arc = max(runs, key=len)
        draw.line(arc, fill=(36, 72, 82, alpha), width=3, joint="curve")


def offset_outward(pts, dist):
    out = []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[(i - 1) % n]
        x1, y1 = pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        if (x - CX) * nx + (y - CY) * ny < 0:
            nx, ny = -nx, -ny
        out.append((x + nx * dist, y + ny * dist))
    return out


def halo_text(draw, xy, text, font, fill, anchor="mm"):
    x, y = xy
    for ox in (-3, 0, 3):
        for oy in (-3, 0, 3):
            if ox or oy:
                draw.text((x + ox, y + oy), text, font=font, fill=HALO, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


def fill_poly(img, pts, color):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).polygon(pts, fill=color)
    img.alpha_composite(overlay)


def offset_band(pts, width):
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == len(pts) - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            dx = pts[i + 1][0] - pts[i - 1][0]
            dy = pts[i + 1][1] - pts[i - 1][1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        left.append((x + nx * width, y + ny * width))
        right.append((x - nx * width, y - ny * width))
    return left + right[::-1]


def organic(cx, cy, rx, ry, phase, n=96):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        w = 1 + 0.075 * math.sin(3 * a + phase) + 0.04 * math.sin(5 * a + 0.8) + 0.02 * math.sin(8 * a + phase)
        pts.append((cx + math.cos(a) * rx * w, cy + math.sin(a) * ry * w * (1 + 0.03 * math.sin(2 * a))))
    return pts


def sample_curve(controls, steps=10):
    pts = []
    padded = [controls[0]] + list(controls) + [controls[-1]]
    for i in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[i - 1], padded[i], padded[i + 1], padded[i + 2]
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            wob = 7 * math.sin(t * 4.2 + i * 1.2)
            pts.append((x + wob, y + wob * 0.25))
    pts.append(controls[-1])
    return pts


def river_points():
    # Foot of Mount Kettle, waving down into the north shore of the lagoon.
    # South past the lagoon's west side, then east into the lagoon, so the
    # walk can cross it before turning up the west shore.
    return sample_curve(
        [(972, 1088), (1068, 1184), (1148, 1296), (1224, 1384), (1312, 1436), (1384, 1424)],
        steps=12,
    )


def draw_tree(draw, x, y, scale=1.0):
    s = scale
    draw.line([(x, y + 4 * s), (x + 1 * s, y - 20 * s)], fill=INK, width=max(2, int(2 * s)))
    draw.ellipse([x - 11 * s, y - 36 * s, x + 12 * s, y - 14 * s], outline=INK, width=2)
    draw.arc([x - 6 * s, y - 30 * s, x + 7 * s, y - 16 * s], 210, 20, fill=INK, width=2)


def draw_land_marks(draw, coast):
    """Fork pricks, slope hatching, and a few tree doodles on the biscuit."""
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(coast, fill=255)
    px = mask.load()
    # Three rows of shortbread fork-pricks on the open middle ground.
    for row, y in enumerate((1288, 1336, 1384)):
        for col in range(4):
            x = 800 + col * 50 + (6 if row == 1 else 0)
            if px[x, y] < 200:
                continue
            draw.ellipse([x - 5, y - 4, x + 5, y + 4], outline=INK, width=2)
            draw.ellipse([x - 2, y - 1, x + 2, y + 2], fill=(120, 74, 40, 255))
    # Light hatching on the south-east slope, clear of the lagoon.
    for i in range(6):
        for j in range(5):
            x = 1472 + i * 24
            y = 1110 + j * 22 + (i % 2) * 5
            if px[x, y] < 200 or px[min(S - 1, x + 16), min(S - 1, y + 12)] < 200:
                continue
            draw.line([(x, y), (x + 16, y + 11)], fill=(86, 54, 34, 150), width=2)
    clusters = (
        [(588, 1364), (626, 1392), (560, 1408), (618, 1426)],
        [(760, 900), (798, 926), (734, 948)],
        [(1504, 1168), (1540, 1196), (1472, 1212), (1520, 1232)],
    )
    for group in clusters:
        for i, (x, y) in enumerate(group):
            if px[int(x), int(y)] > 200:
                draw_tree(draw, x, y, 1.15 if i % 2 == 0 else 0.9)


def jam_jar(draw, x, y):
    draw.rounded_rectangle([x, y, x + 26, y + 34], radius=4, fill=(186, 46, 48, 235), outline=INK, width=2)
    draw.rectangle([x - 3, y - 7, x + 29, y + 2], fill=(236, 214, 176, 255), outline=INK, width=2)
    draw.ellipse([x + 8, y - 14, x + 18, y - 5], fill=(90, 56, 36, 255), outline=INK)


def draw_features(img, coast):
    draw = ImageDraw.Draw(img)
    # Jammy Marsh: a soft jam wash, reeds, two jars.
    marsh = organic(690, 1504, 156, 96, 0.6)
    fill_poly(img, marsh, (176, 42, 48, 150))
    rim = organic(690, 1504, 138, 82, 0.6)
    draw = ImageDraw.Draw(img)
    draw.line(rim + [rim[0]], fill=(120, 28, 36, 180), width=3, joint="curve")
    for x, y in ((600, 1496), (660, 1540), (730, 1484), (790, 1544), (640, 1460), (760, 1510)):
        draw.line([(x, y + 26), (x - 7, y + 4), (x + 2, y - 10), (x + 11, y - 18)], fill=INK, width=3, joint="curve")
    jam_jar(draw, 628, 1556)
    jam_jar(draw, 734, 1572)
    # Dunking Lagoon: tea in an oval hollow, lighter rim, two ripple rings.
    lagoon = organic(1396, 1364, 168, 122, 1.4)
    fill_poly(img, lagoon, (118, 78, 44, 210))
    inner = organic(1396, 1364, 132, 92, 1.4)
    fill_poly(img, inner, (86, 52, 30, 230))
    draw = ImageDraw.Draw(img)
    draw.line(lagoon + [lagoon[0]], fill=(214, 176, 120, 220), width=6, joint="curve")
    draw.line(lagoon + [lagoon[0]], fill=INK, width=3, joint="curve")
    draw.ellipse([1336, 1324, 1456, 1404], outline=(62, 40, 26, 200), width=2)
    draw.ellipse([1360, 1344, 1432, 1386], outline=(62, 40, 26, 160), width=2)
    # The Steeping River, narrow at the kettle, wider where it meets the lagoon.
    spine = river_points()
    left, right = [], []
    for i, (x, y) in enumerate(spine):
        t = i / (len(spine) - 1)
        w = 5 + 11 * t
        if i == 0:
            dx, dy = spine[1][0] - x, spine[1][1] - y
        elif i == len(spine) - 1:
            dx, dy = x - spine[i - 1][0], y - spine[i - 1][1]
        else:
            dx = spine[i + 1][0] - spine[i - 1][0]
            dy = spine[i + 1][1] - spine[i - 1][1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    fill_poly(img, left + right[::-1], (156, 104, 58, 230))
    draw = ImageDraw.Draw(img)
    draw.line(left, fill=INK, width=2, joint="curve")
    draw.line(right, fill=INK, width=2, joint="curve")
    # Mount Kettle: a lumpy hand-inked cone, hatched on the shadow side.
    apex, left_b, right_b, foot = (968, 892), (828, 1078), (1092, 1064), (980, 1086)

    def lumpy(a, b, phase, amp, n=9):
        pts = []
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        for i in range(n + 1):
            t = i / n
            bulge = math.sin(t * math.pi) * amp * math.sin(phase + t * 8.5)
            pts.append((a[0] + dx * t + nx * bulge, a[1] + dy * t + ny * bulge))
        return pts

    left_edge = lumpy(apex, left_b, 0.4, 11)
    right_edge = lumpy(apex, right_b, 1.8, 13)
    draw.polygon(left_edge + [foot], fill=(226, 186, 122, 255), outline=INK)
    draw.polygon(right_edge + [foot], fill=(150, 96, 52, 255), outline=INK)
    draw.line([apex, foot], fill=(96, 58, 34, 180), width=2)
    for i in range(6):
        t = 0.28 + i * 0.11
        draw.line(
            [
                (apex[0] + (foot[0] - apex[0]) * t + 4, apex[1] + (foot[1] - apex[1]) * t),
                (apex[0] + (right_b[0] - apex[0]) * t - 6, apex[1] + (right_b[1] - apex[1]) * t + 2),
            ],
            fill=(78, 46, 28, 175),
            width=2,
        )
    draw.ellipse([apex[0] - 36, apex[1] - 16, apex[0] + 30, apex[1] + 18], fill=(36, 22, 16, 255), outline=INK, width=3)
    draw.ellipse([apex[0] - 16, apex[1] - 4, apex[0] + 12, apex[1] + 10], fill=(16, 10, 8, 255))
    # A kettle spout on the shadowed flank, steam curling up toward the note.
    spout = [(1024, 990), (1076, 958), (1062, 922)]
    draw.line(spout, fill=(186, 132, 74, 255), width=9, joint="curve")
    draw.line(spout, fill=INK, width=3, joint="curve")
    draw.ellipse([1044, 904, 1078, 932], fill=(232, 198, 146, 255), outline=INK, width=3)
    for sx, sy, rad in ((1052, 894, 14), (1020, 864, 11), (1048, 836, 9)):
        draw.ellipse(
            [sx - rad, sy - rad * 0.8, sx + rad, sy + rad * 0.8],
            fill=(248, 244, 234, 225),
            outline=INK,
            width=2,
        )
    draw = ImageDraw.Draw(img)
    # Sugarloaf Hill, a cube of sugar.
    sx, sy, s = 820, 760, 72
    top = [(sx, sy), (sx + s * 0.55, sy - s * 0.38), (sx + s * 1.1, sy), (sx + s * 0.55, sy + s * 0.36)]
    left = [(sx, sy), (sx + s * 0.55, sy + s * 0.36), (sx + s * 0.55, sy + s * 0.95), (sx, sy + s * 0.58)]
    right = [(sx + s * 1.1, sy), (sx + s * 0.55, sy + s * 0.36), (sx + s * 0.55, sy + s * 0.95), (sx + s * 1.1, sy + s * 0.58)]
    draw.polygon(top, fill=(246, 240, 224, 255), outline=INK)
    draw.polygon(left, fill=(214, 196, 160, 255), outline=INK)
    draw.polygon(right, fill=(232, 214, 176, 255), outline=INK)
    # Crumbling Cliffs, hatched along the west shore.
    for i, (x, y) in enumerate(coast):
        if x < CX - 340 and 1040 < y < 1320 and i % 5 == 0:
            dx, dy = CX - x, CY - y
            length = math.hypot(dx, dy) or 1
            draw.line([(x, y), (x + dx / length * 36, y + dy / length * 34)], fill=INK, width=3)
    # A small hollow north of the lagoon, where the last biscuit waits.
    hollow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hollow)
    hd.ellipse([1228, 1068, 1472, 1228], fill=(148, 96, 48, 70))
    img.alpha_composite(hollow.filter(ImageFilter.GaussianBlur(6)))
    draw = ImageDraw.Draw(img)
    draw.arc([1248, 1100, 1452, 1216], 10, 170, fill=INK, width=2)
    draw.arc([1276, 1124, 1424, 1204], 15, 165, fill=(90, 56, 34, 180), width=2)
    # Twin Custard Creams, offshore south-east.
    for x, y in ((1548, 1768), (1662, 1816)):
        draw.rounded_rectangle([x, y, x + 92, y + 58], radius=12, fill=(214, 170, 104, 255), outline=INK, width=3)
        draw.line([(x + 10, y + 29), (x + 82, y + 29)], fill=(248, 230, 186, 255), width=6)
        for h in range(3):
            draw.ellipse([x + 18 + h * 22, y + 12, x + 30 + h * 22, y + 24], fill=(120, 78, 40, 255))
    # Fork-prick rocks, just off the bitten edge and the east shore.
    for x, y, rad in ((1688, 1040, 14), (1740, 1105, 11), (1712, 980, 9), (1775, 1188, 13), (1810, 1260, 8), (1816, 1688, 10), (1872, 1748, 8)):
        draw.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(188, 156, 110, 255), outline=INK, width=2)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(90, 60, 36, 255))


def bay_label():
    hits = []
    for y in range(520, 1100, 10):
        for x in range(1200, 1900, 10):
            ang = math.atan2(y - CY, x - CX)
            if math.hypot(x - CX, y - CY) > R + wobble(ang) - 30:
                continue
            bang = math.atan2(y - BY, x - BX)
            if math.hypot(x - BX, y - BY) < RB + tooth(bang) - 36:
                hits.append((x, y))
    if not hits:
        return (1520, 760)
    return (sum(p[0] for p in hits) / len(hits), sum(p[1] for p in hits) / len(hits))


def draw_labels(draw):
    font = ImageFont.truetype(str(FONT_PLACE), 74)
    small = ImageFont.truetype(str(FONT_PLACE), 68)
    treasure = ImageFont.truetype(str(FONT_PLACE), 52)
    bx, by = bay_label()
    labels = [
        # In the open water of the bay, just left of the ship. Two lines so
        # the name fits the scoop and stays clear of the hull.
        ("Saucer", (948, 1818), font),
        ("Bay", (948, 1898), font),
        ("Bite Bay", (bx - 10, by - 46), font),
        ("Mount", (648, 984), small),
        ("Kettle", (648, 1052), small),
        # On the lagoon's right rim, below the slope hatch and above the bridge name.
        ("Dunking", (1504, 1336), treasure),
        ("Lagoon", (1504, 1390), treasure),
        ("Jammy Marsh", (800, 1460), small),
        ("Crumbling", (600, 1144), small),
        ("Cliffs", (600, 1212), small),
        ("Sugarloaf", (640, 760), small),
        ("Hill", (640, 828), small),
        # Stacked in the sea directly above the two biscuit rocks.
        ("The Custard", (1692, 1628), small),
        ("Creams", (1656, 1704), small),
        # Centred above the X, clear of the dotted slope hatch.
        ("The Last Biscuit", (1368, 1048), treasure),
    ]
    for text, xy, fnt in labels:
        halo_text(draw, xy, text, fnt, RED if text == "The Last Biscuit" else INK)


def dashed(draw, pts, fill, width=5, dash=18, gap=13):
    samples = []
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(2, int(dist / 4))
        for s in range(steps):
            t = s / steps
            samples.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    samples.append(pts[-1])
    on, run, seg = True, 0, []
    for p in samples:
        seg.append(p)
        run += 4
        if run >= (dash if on else gap):
            if on and len(seg) > 1:
                draw.line(seg, fill=fill, width=width, joint="curve")
            seg, run, on = [p], 0, not on
    if on and len(seg) > 1:
        draw.line(seg, fill=fill, width=width)


def draw_cup(draw, x, y):
    draw.ellipse([x - 16, y - 4, x + 16, y + 8], outline=INK, width=2)
    draw.arc([x - 12, y - 16, x + 12, y + 6], 200, 340, fill=INK, width=2)
    draw.line([(x - 12, y - 6), (x - 12, y + 8), (x + 12, y + 8), (x + 12, y - 6)], fill=INK, width=2)
    draw.arc([x + 10, y - 8, x + 24, y + 8], 280, 80, fill=INK, width=2)
    draw.arc([x - 4, y - 28, x + 2, y - 16], 200, 40, fill=INK, width=2)


def draw_rowboat(draw, x, y):
    draw.polygon([(x - 34, y), (x + 32, y - 2), (x + 22, y + 12), (x - 22, y + 12)], fill=(122, 74, 40, 255), outline=INK, width=2)
    draw.line([(x - 10, y - 2), (x - 28, y - 20)], fill=INK, width=2)
    draw.line([(x + 8, y - 2), (x + 28, y - 18)], fill=INK, width=2)


def draw_route(draw):
    """Beach, tea, bridge, west of the lagoon, a napkin loop, the X."""
    spine = river_points()
    i = min(range(len(spine) - 1), key=lambda k: (spine[k][0] - 1260) ** 2 + (spine[k][1] - 1410) ** 2)
    bx, by = spine[i]
    dx, dy = spine[i + 1][0] - bx, spine[i + 1][1] - by
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    span = 34
    draw.line([(bx + nx * span, by + ny * span), (bx - nx * span, by - ny * span)], fill=(236, 214, 164, 255), width=16)
    draw.line([(bx + nx * span, by + ny * span), (bx - nx * span, by - ny * span)], fill=INK, width=3)
    draw.line([(bx + nx * (span - 8), by + ny * (span - 8)), (bx - nx * (span - 8), by - ny * (span - 8))], fill=INK, width=2)
    path = [
        (1010, 1564),
        (1124, 1504),
        (bx, by),
        (1296, 1360),
        (1264, 1292),
        (1192, 1252),
        (1136, 1204),
        (1196, 1160),
        (1260, 1192),
        (1228, 1244),
        (1304, 1200),
        (1368, 1160),
    ]
    dashed(draw, path, RED, width=6, dash=22, gap=12)
    xx, yy = 1368, 1160
    draw.line([(xx - 28, yy - 28), (xx + 28, yy + 28)], fill=RED, width=8)
    draw.line([(xx + 28, yy - 28), (xx - 28, yy + 28)], fill=RED, width=8)
    draw_rowboat(draw, 1010, 1556)
    draw_cup(draw, 1124, 1456)
    bridge = ImageFont.truetype(str(FONT_PLACE), 46)
    halo_text(draw, (bx + 188, by + 58), "Sugar Lump Bridge", bridge, INK)
    note = ImageFont.truetype(str(FONT_NOTE), 46)
    ink = (92, 48, 36, 255)
    halo_text(draw, (1124, 1416), "tea break", note, ink)
    halo_text(draw, (980, 1308), "turned back for napkins", note, ink)


def draw_ship(draw):
    x, y = 1124, 1752
    draw.polygon([(x - 50, y), (x + 54, y - 6), (x + 34, y + 20), (x - 32, y + 18)], fill=(104, 62, 38, 255), outline=INK)
    draw.line([(x + 6, y), (x + 6, y - 56)], fill=INK, width=3)
    draw.polygon([(x + 6, y - 54), (x + 40, y - 32), (x + 6, y - 16)], fill=(244, 236, 214, 255), outline=INK)
    draw.line([(x - 16, y + 10), (x - 8, y + 36)], fill=INK, width=3)
    draw.line([(x - 22, y + 34), (x + 6, y + 40)], fill=INK, width=3)


def draw_notes(draw):
    note = ImageFont.truetype(str(FONT_NOTE), 46)
    ink = (92, 48, 36, 255)
    halo_text(draw, (560, 1296), "Do not lean", note, ink)
    bx, by = bay_label()
    vx, vy = BX - bx, BY - by
    dist = math.hypot(vx, vy) or 1.0
    bx += vx / dist * 36
    by += vy / dist * 24
    halo_text(draw, (bx, by + 28), "Someone got here first.", note, ink)
    halo_text(draw, (1020, 748), "Boils at four", note, ink)
    halo_text(draw, (1020, 800), "o'clock sharp", note, ink)
    halo_text(draw, (1368, 1744), "Anchor here.", note, ink)
    halo_text(draw, (1368, 1800), "Mind the saucer.", note, ink)


def draw_compass(draw):
    """Eight-point rose, about 150px across once reduced. North is a teaspoon."""
    cx, cy, r = 250, 470, 132
    draw.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6], fill=(244, 232, 206, 235), outline=INK, width=4)
    for i in range(8):
        if i == 0:
            continue
        ang = -math.pi / 2 + i * math.pi / 4
        reach = r * (0.90 if i % 2 == 0 else 0.68)
        tip = (cx + math.cos(ang) * reach, cy + math.sin(ang) * reach)
        base = 28 if i % 2 == 0 else 20
        left = (cx + math.cos(ang + 0.42) * base, cy + math.sin(ang + 0.42) * base)
        right = (cx + math.cos(ang - 0.42) * base, cy + math.sin(ang - 0.42) * base)
        fill = (148, 42, 34, 255) if i % 2 == 0 else (92, 58, 36, 255)
        draw.polygon([tip, left, right], fill=fill, outline=INK)
    draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(244, 232, 206, 255), outline=INK, width=2)
    # Teaspoon standing in for the north point.
    draw.polygon(
        [(cx - 7, cy + 6), (cx + 7, cy + 6), (cx + 5, cy - r + 36), (cx - 5, cy - r + 36)],
        fill=(196, 160, 108, 255),
        outline=INK,
    )
    draw.ellipse([cx - 22, cy - r - 18, cx + 22, cy - r + 46], fill=(226, 198, 146, 255), outline=INK, width=3)
    draw.arc([cx - 12, cy - r + 2, cx + 12, cy - r + 28], 200, 340, fill=INK, width=2)
    rose = ImageFont.truetype(str(FONT_PLACE), 40)
    for lab, xy in (
        ("N", (cx, cy - r - 48)),
        ("E", (cx + r + 32, cy)),
        ("S", (cx, cy + r + 34)),
        ("W", (cx - r - 34, cy)),
    ):
        halo_text(draw, xy, lab, rose, INK)


def draw_kraken(draw):
    """Teapot kraken in the south-west sea, about 220px wide on the finished chart."""
    x, y = 318, 1504
    teal = (156, 198, 190, 255)
    deep = (64, 122, 128, 255)
    # Five open curls under the pot, tips turning outward so they stay apart.
    controls = (
        [(x - 78, y + 28), (x - 156, y + 8), (x - 188, y + 86), (x - 150, y + 168)],
        [(x - 34, y + 60), (x - 96, y + 128), (x - 120, y + 206), (x - 48, y + 236)],
        [(x + 10, y + 70), (x + 2, y + 150), (x + 36, y + 226), (x + 108, y + 246)],
        [(x + 50, y + 48), (x + 96, y + 96), (x + 112, y + 156), (x + 78, y + 204)],
        [(x + 100, y + 20), (x + 168, y + 52), (x + 196, y + 128), (x + 154, y + 188)],
    )
    halves = (18, 22, 20, 19, 16)
    for pts, half in zip(controls, halves):
        curve = sample_curve(pts, steps=8)
        band = offset_band(curve, half)
        draw.polygon(band, fill=deep)
        n = len(curve)
        draw.line(band[:n], fill=INK, width=3, joint="curve")
        draw.line(band[n:], fill=INK, width=3, joint="curve")
        tx, ty = curve[-1]
        draw.ellipse([tx - half, ty - half * 0.75, tx + half, ty + half * 0.75], fill=deep, outline=INK, width=3)
    draw.ellipse([x - 116, y - 82, x + 116, y + 90], fill=teal, outline=INK, width=4)
    draw.ellipse([x - 82, y - 128, x + 82, y - 46], fill=(214, 232, 224, 255), outline=INK, width=4)
    draw.arc([x - 82, y - 108, x + 82, y - 58], 12, 168, fill=INK, width=2)
    draw.ellipse([x - 16, y - 158, x + 16, y - 122], fill=(102, 64, 40, 255), outline=INK, width=3)
    draw.arc([x - 172, y - 58, x - 78, y + 48], 70, 290, fill=INK, width=11)
    spout = [(x + 28, y - 86), (x + 70, y - 150), (x + 36, y - 198)]
    draw.line(spout, fill=teal, width=20, joint="curve")
    draw.line(spout, fill=INK, width=4, joint="curve")
    draw.ellipse([x + 8, y - 226, x + 62, y - 182], fill=(220, 236, 228, 255), outline=INK, width=4)
    for sx, sy, rad in ((x + 4, y - 258, 17), (x + 46, y - 296, 13), (x + 8, y - 330, 10)):
        draw.ellipse(
            [sx - rad, sy - rad * 0.8, sx + rad, sy + rad * 0.8],
            fill=(248, 244, 234, 230),
            outline=INK,
            width=3,
        )
    for ex in (x - 42, x + 40):
        draw.ellipse([ex - 28, y - 26, ex + 28, y + 28], fill=(250, 246, 238, 255), outline=INK, width=3)
        draw.ellipse([ex - 11, y - 6, ex + 11, y + 16], fill=INK)
        draw.ellipse([ex - 3, y - 2, ex + 7, y + 6], fill=(250, 246, 238, 255))
    draw.arc([x - 38, y + 16, x + 42, y + 58], 18, 162, fill=INK, width=4)
    for dy, rx in ((62, 132), (84, 176), (104, 108)):
        draw.arc([x - rx, y + dy, x + rx, y + dy + 30], 18, 162, fill=(28, 72, 80, 190), width=3)
    name = ImageFont.truetype(str(FONT_PLACE), 38)
    warn = ImageFont.truetype(str(FONT_NOTE), 40)
    halo_text(draw, (x + 16, y + 308), "The Great Teapot Kraken", name, INK)
    halo_text(draw, (x + 16, y + 356), "Here Be Dunkers", warn, INK)


def draw_scale(draw):
    x, y = 160, 1936
    draw.line([(x, y), (x + 270, y)], fill=INK, width=4)
    for i in range(4):
        draw.line([(x + i * 90, y - 12), (x + i * 90, y + 12)], fill=INK, width=3)
    for i in range(3):
        cx, cy, rad = x + 45 + i * 90, y - 28, 16
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(214, 170, 104, 255), outline=INK, width=2)
        for h in range(3):
            draw.ellipse([cx - 8 + h * 6, cy - 3, cx - 4 + h * 6, cy + 1], fill=(110, 70, 40, 255))
    small = ImageFont.truetype(str(FONT_PLACE), 32)
    halo_text(draw, (x + 135, y + 36), "1 league = 3 biscuits", small, INK)


def draw_legend(draw):
    x, y = 1568, 286
    draw.rounded_rectangle([x, y, x + 420, y + 168], radius=8, fill=(244, 232, 206, 235), outline=INK, width=3)
    small = ImageFont.truetype(str(FONT_PLACE), 32)
    draw.line([(x + 18, y + 38), (x + 70, y + 38)], fill=RED, width=4)
    draw.line([(x + 18, y + 84), (x + 70, y + 84)], fill=(110, 70, 40, 255), width=6)
    draw.line([(x + 32, y + 112), (x + 56, y + 136)], fill=RED, width=4)
    draw.line([(x + 56, y + 112), (x + 32, y + 136)], fill=RED, width=4)
    draw.text((x + 86, y + 38), "the walk", font=small, fill=INK, anchor="lm")
    draw.text((x + 86, y + 84), "the Steeping River", font=small, fill=INK, anchor="lm")
    draw.text((x + 86, y + 128), "the last biscuit", font=small, fill=INK, anchor="lm")


def draw_gull(draw, x, y):
    draw.arc([x, y, x + 22, y + 14], 200, 20, fill=INK, width=2)
    draw.arc([x + 18, y, x + 40, y + 14], 160, 340, fill=INK, width=2)


def draw_bottle(draw):
    x, y = 1892, 668
    draw.arc([x - 40, y + 58, x + 40, y + 86], 10, 170, fill=(32, 68, 76, 170), width=2)
    draw.arc([x - 58, y + 70, x + 58, y + 102], 16, 164, fill=(32, 68, 76, 120), width=2)
    draw.ellipse([x - 24, y + 10, x + 24, y + 74], fill=(176, 206, 198, 230), outline=INK, width=3)
    draw.polygon([(x - 8, y + 12), (x + 8, y + 12), (x + 6, y - 10), (x - 6, y - 10)], fill=(198, 220, 212, 255), outline=INK)
    draw.rounded_rectangle([x - 7, y - 24, x + 7, y - 8], radius=2, fill=(146, 90, 48, 255), outline=INK)
    draw.arc([x - 8, y + 28, x + 10, y + 46], 200, 30, fill=(244, 232, 206, 255), width=3)
    draw.line([(x - 6, y + 36), (x + 12, y + 52)], fill=(244, 232, 206, 255), width=2)


def draw_title(draw):
    title = ImageFont.truetype(str(FONT_TITLE), 118)
    sub = ImageFont.truetype(str(FONT_PLACE), 42)
    credit = ImageFont.truetype(str(FONT_NOTE), 36)
    draw.rounded_rectangle([430, 58, 1618, 268], radius=46, fill=(236, 220, 186, 235), outline=INK, width=4)
    draw.arc([470, 78, 620, 150], 200, 20, fill=INK, width=2)
    draw.arc([1420, 78, 1570, 150], 160, 340, fill=INK, width=2)
    halo_text(draw, (1024, 128), "BISCUIT ISLE", title, INK)
    halo_text(draw, (1024, 198), "A True Chart of the Last Biscuit", sub, INK)
    halo_text(draw, (1024, 242), "drawn by Capt. Hob Crumbsworth, 1752 · bring milk", credit, (92, 48, 36, 255))


def draw_border(draw):
    def loop(inset, amp):
        pts = []
        n = 70
        edges = (
            lambda t: (inset + (S - 2 * inset) * t, inset + amp * math.sin(t * 16)),
            lambda t: (S - inset + amp * math.sin(t * 14), inset + (S - 2 * inset) * t),
            lambda t: (S - inset - (S - 2 * inset) * t, S - inset + amp * math.sin(t * 16)),
            lambda t: (inset + amp * math.sin(t * 14), S - inset - (S - 2 * inset) * t),
        )
        for edge in edges:
            for i in range(n):
                pts.append(edge(i / n))
        return pts

    draw.line(loop(32, 5) + [loop(32, 5)[0]], fill=INK, width=5, joint="curve")
    draw.line(loop(52, 3) + [loop(52, 3)[0]], fill=INK, width=2, joint="curve")


def draw_furniture(draw):
    draw_title(draw)
    draw_compass(draw)
    draw_kraken(draw)
    draw_scale(draw)
    draw_legend(draw)
    draw_bottle(draw)
    draw_gull(draw, 1328, 348)
    draw_gull(draw, 1416, 390)
    draw_border(draw)


def main():
    coast = coast_points(0.0)
    img = paint_washes(parchment(), coast)
    draw = ImageDraw.Draw(img)
    draw_coast_ripples(draw, coast)
    draw_waves(img, coast)
    draw = ImageDraw.Draw(img)
    stroke(draw, coast, INK, 6)
    draw_land_marks(draw, coast)
    draw_features(img, coast)
    draw = ImageDraw.Draw(img)
    draw_route(draw)
    draw_ship(draw)
    draw_notes(draw)
    draw_labels(draw)
    draw_furniture(ImageDraw.Draw(img))
    out = img.convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
    dest = ROOT / "entry.png"
    out.save(dest, "PNG", optimize=True)
    if dest.stat().st_size > 980_000:
        q = out.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        q.convert("RGB").save(dest, "PNG", optimize=True)
    print(f"wrote {dest} {dest.stat().st_size} bytes")


if __name__ == "__main__":
    main()
