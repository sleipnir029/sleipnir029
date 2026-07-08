"""One day on the road — 16-bit pixel art edition.

The same journey as journey_scene.py (kept as the ASCII draft), rebuilt as
a low-res pixel scene: 246x113 canvas, x3 nearest-neighbor upscale.

Route (world is 960 px, wraps): morning fields (a rabbit bolts) -> lake ->
pine forest -> golden-hour hills -> the suspension bridge at night (stop,
breathe, a star falls, an owl watches, fireflies drift) -> dawn mist ->
morning again.

Rules carried over from the ASCII cuts:
 - scroll a constant 3 px/frame when cruising (constant step = no judder);
   ease by dwell and whole-px steps, never fractional
 - lighting is f(world position), so the loop closes seamlessly
 - parallax strips tile the scroll distance exactly
 - every canvas row is painted by some layer (gaps render as black)

  python3 pixel_journey.py --still 50 320 560 680 850   stills at world s
  python3 pixel_journey.py                              full animation
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'

PW, PH = 246, 113
SCALE = 3
FPS = 10
L = 960                     # world length in px; s wraps mod L

HORIZON = 66
ROAD_TOP, ROAD_BOT = 72, 76
RIDER_X = 80                # rider's fixed screen x (front wheel center)

# world zones
LAKE_L, LAKE_R = 253, 400
FOREST_L, FOREST_R = 413, 573
BRIDGE_L, BRIDGE_R = 653, 840
TOWER_A, TOWER_B = 680, 813
TOWER_TOP = 21
STOP_S = (TOWER_A + TOWER_B) // 2 - RIDER_X
PAUSE_FRAMES = 84

# ------------------------------------------------------------ palettes

SKY_TOP = [(96, 158, 214), (64, 84, 160), (24, 22, 66), (11, 13, 34)]
SKY_HOR = [(186, 216, 232), (244, 158, 96), (168, 74, 96), (32, 30, 68)]
KEYS = [0.0, 0.42, 0.7, 1.0]           # day, golden, dusk, night


def blend4(colors, d):
    for k in range(3):
        if d <= KEYS[k + 1]:
            f = (d - KEYS[k]) / (KEYS[k + 1] - KEYS[k])
            a, b = colors[k], colors[k + 1]
            return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
    return colors[-1]


def lerp(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def pal(day, night, d, g=0.0):
    """Day/night lerp with an optional golden-hour warm push."""
    c = lerp(day, night, d)
    if g > 0:
        warm = (min(255, c[0] + 60), c[1] + 8, max(0, c[2] - 30))
        c = lerp(c, warm, g * 0.55)
    return c


P_FAR = ((104, 128, 158), (15, 17, 42))
P_FAR_LIT = ((128, 150, 176), (20, 23, 52))
P_HILL = ((78, 126, 84), (11, 13, 32))
P_GROUND = ((104, 152, 74), (15, 17, 32))
P_ROAD = ((186, 172, 152), (58, 56, 76))
P_TREE = ((52, 112, 60), (9, 12, 28))
P_TREE_LIT = ((84, 150, 82), (14, 18, 36))
P_TRUNK = ((84, 66, 48), (16, 14, 26))
P_WATER = ((70, 132, 180), (24, 22, 56))
P_WATER_DEEP = ((38, 84, 130), (9, 9, 24))
P_BRIDGE = ((240, 232, 208), (238, 230, 205))
P_CLOUD = ((244, 246, 250), (96, 100, 126))
P_CLOUD_SH = ((208, 214, 226), (76, 80, 104))
SUN_C = (255, 214, 100)
SUN_LOW = (255, 140, 60)
MOON_C = (255, 238, 200)
FIREFLY = (255, 226, 120)

# rider colors (day -> night moonlit versions)
P_JERSEY = ((214, 64, 54), (120, 76, 92))
P_SKIN = ((168, 114, 70), (134, 122, 128))    # brown skin, moonlit at night
P_BIKE = ((40, 46, 60), (140, 150, 170))
P_SHORTS = ((36, 38, 52), (96, 104, 126))
P_HAIR = ((26, 22, 24), (92, 98, 118))        # black hair, catches moonlight


def darkness(x):
    x = x % L
    if x < 520:
        return 0.0
    if x < 653:
        return (x - 520) / 133
    if x < 880:
        return 1.0
    return max(0.0, 1.0 - (x - 880) / 75)


def golden(d):
    return max(0.0, 1.0 - abs(d - 0.45) / 0.3)   # peaks mid-transition

# ------------------------------------------------------------ timeline

def build_offsets():
    steps = []
    ease_in = [2, 2, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0]   # 3 -> rolling stop
    ease_out = [1, 0, 0, 1, 0, 1, 1, 2, 2]
    n1, r1 = divmod(STOP_S - sum(ease_in), 3)
    ease_in = ([r1] if r1 else []) + ease_in
    steps += [3] * n1 + ease_in
    pause_start = len(steps)
    steps += [0] * PAUSE_FRAMES
    rest = L - STOP_S - sum(ease_out)
    n2, r2 = divmod(rest, 3)
    steps += ease_out + ([r2] if r2 else []) + [3] * n2
    s, out = 0, []
    for v in steps:
        out.append(s)
        s += v
    assert s == L, s
    return out, pause_start


OFFSETS, PAUSE_START = build_offsets()
TOTAL_FRAMES = len(OFFSETS)
PAUSE_END = PAUSE_START + PAUSE_FRAMES

# ------------------------------------------------------------ world data

RNG = random.Random(29)

STARS = [(RNG.randrange(PW), RNG.randrange(50), RNG.random()) for _ in range(42)]

CLOUDS = [(20, 11), (130, 21), (300, 7), (440, 16)]       # 0.5x strip, 480

FAR_PEAKS = [(-14, 35), (33, 21), (80, 40), (127, 27), (173, 37), (220, 24)]
FAR_LEN = 240                                             # 0.25x strip


def far_ridge(x):
    y = HORIZON
    for px_, h in FAR_PEAKS:
        for rep in (-FAR_LEN, 0, FAR_LEN):
            y = min(y, HORIZON - h + abs(x - px_ - rep) * 2 // 3)
    return y


HILL_LEN = 480                                            # 0.5x strip


def hill_ridge(x):
    a = math.sin(x * 2 * math.pi / HILL_LEN * 3)
    b = math.sin(x * 2 * math.pi / HILL_LEN * 7 + 1.7)
    return int(62 - 5 * a - 3 * b)


TREES = [(40, 'leafy'), (127, 'leafy'), (213, 'leafy'),
         (424, 'pine'), (448, 'pine'), (469, 'pine'), (499, 'pine'),
         (525, 'pine'), (549, 'pine'), (597, 'leafy'), (629, 'leafy'),
         (869, 'leafy'), (933, 'pine')]
BUSHES = [72, 168, 245, 415, 583, 615, 852, 906, 944]
FENCES = [(11, 240), (853, 952)]
REEDS = [LAKE_L - 5, LAKE_L + 4, LAKE_R - 4, LAKE_R + 5,
         BRIDGE_L - 8, BRIDGE_R + 8]

MEADOW = [(RNG.randrange(L), RNG.randrange(ROAD_BOT + 1, PH),
           RNG.uniform(-0.25, 0.3)) for _ in range(4600)]
FLOWER_COLS = [(235, 160, 170), (245, 240, 210), (250, 210, 120)]
FLOWERS = [(RNG.randrange(L), RNG.randrange(ROAD_BOT + 2, ROAD_BOT + 19),
            RNG.randrange(3)) for _ in range(170)]

FIREFLIES = [(665 + RNG.randrange(290), RNG.randrange(77, 101),
              RNG.randrange(40)) for _ in range(11)]

WATER_NOISE = [(RNG.randrange(960), RNG.randrange(PH), RNG.random())
               for _ in range(2600)]

ROAD_MARKS = [(RNG.randrange(L), RNG.randrange(1, 4)) for _ in range(70)]

WIND_FLECKS = [(RNG.randrange(L), RNG.randrange(ROAD_TOP - 22, ROAD_TOP + 8),
                RNG.uniform(0, 6.3)) for _ in range(12)]

RABBIT_X = 200


def water_cell(wc, y):
    wc = wc % L
    if y <= ROAD_BOT:
        return False
    if BRIDGE_L + 5 <= wc <= BRIDGE_R - 5:
        return True
    if y > ROAD_BOT + 24:
        return False
    inset = (y - ROAD_BOT - 1) * 4
    return LAKE_L + 8 + inset <= wc <= LAKE_R - 8 - inset

# ------------------------------------------------------------ drawing

def make_frame(t):
    s = OFFSETS[t]
    d = darkness(s + RIDER_X)
    g = golden(d)
    img = Image.new('RGB', (PW, PH))
    px = img.load()

    # --- sky: banded vertical gradient with checker dither
    top = blend4(SKY_TOP, d)
    hor = blend4(SKY_HOR, d)
    bands = 11
    for y in range(HORIZON + 1):
        f = y / HORIZON * (bands - 1)
        i, frac = int(f), f - int(f)
        c1 = lerp(top, hor, i / (bands - 1))
        c2 = lerp(top, hor, min(i + 1, bands - 1) / (bands - 1))
        for x in range(PW):
            if frac < 0.35:
                c = c1
            elif frac > 0.65:
                c = c2
            else:
                c = c2 if (x + y) % 2 else c1
            px[x, y] = c

    # --- horizon haze, thickest in daylight
    haze = (1 - d) * 0.3
    if haze > 0.03:
        hz = lerp(hor, (255, 255, 255), 0.25)
        for y in range(HORIZON - 6, HORIZON + 1):
            f2 = (y - (HORIZON - 6)) / 6 * haze
            for x in range(PW):
                px[x, y] = lerp(px[x, y], hz, f2)

    # --- stars
    if d > 0.5:
        for i, (x, y, thr) in enumerate(STARS):
            if d > 0.5 + thr * 0.5:
                tw = (t // 6 + i) % 5
                if tw:
                    px[x, y] = (216, 220, 235) if tw > 1 else (150, 155, 175)

    # --- sun / moon
    if d < 0.8:
        sy = 13 + d * 69
        sc = lerp(SUN_C, SUN_LOW, min(1.0, max(0.0, (d - 0.3) * 2.2)))
        for yy in range(max(0, int(sy) - 10), min(HORIZON + 1, int(sy) + 11)):
            for xx in range(175, 199):
                dd = math.hypot(xx - 187, (yy - sy) * 1.1)
                if dd < 5.6:
                    px[xx, yy] = sc
                elif dd < 8 and (xx + yy) % 2:
                    px[xx, yy] = lerp(px[xx, yy], sc, 0.18)
    if d > 0.55:
        my = 53 - (d - 0.55) / 0.45 * 37
        for yy in range(max(0, int(my) - 10), min(HORIZON + 1, int(my) + 11)):
            for xx in range(191, 214):
                dd = math.hypot(xx - 202, yy - my)
                d2 = math.hypot(xx - 206, yy - my + 1.3)
                if dd < 6.6 and d2 > 5.6:
                    px[xx, yy] = MOON_C
                elif 6.6 <= dd < 9 and (xx + yy) % 2:
                    px[xx, yy] = lerp(px[xx, yy], MOON_C, 0.12)

    # --- clouds (0.5x): puffy top, shaded underside
    ccol = pal(*P_CLOUD, d, g)
    csh = pal(*P_CLOUD_SH, d, g)
    for cx, cy in CLOUDS:
        x0 = int(cx - s * 0.5) % HILL_LEN - 55
        for ddx in range(-8, 9):
            for ddy in range(-2, 3):
                if ddx * ddx + ddy * ddy * 14 < 62 and 0 <= cy + ddy <= HORIZON:
                    xx = x0 + ddx
                    if 0 <= xx < PW:
                        px[xx, cy + ddy] = csh if ddy == 2 else ccol

    # --- birds in the morning air (0.5x layer)
    if d < 0.4:
        wing = (t // 6) % 2
        bcol2 = lerp((40, 48, 66), (140, 150, 170), d)
        for bxw, byw in ((115, 26), (122, 29), (365, 20)):
            x0 = int(bxw - s * 0.5) % HILL_LEN - 55
            if 0 <= x0 < PW:
                px[x0, byw] = bcol2
                for dx2 in (-1, 1):
                    xx = x0 + dx2
                    if 0 <= xx < PW:
                        px[xx, byw - wing] = bcol2

    # --- far mountains (0.25x), lit on the sunward slope
    fcol = pal(*P_FAR, d, g * 0.5)
    flit = pal(*P_FAR_LIT, d, g * 0.5)
    off_f = int(s * 0.25) % FAR_LEN
    for x in range(PW):
        wx = (x + off_f) % FAR_LEN
        top_y = far_ridge(wx)
        lit = far_ridge(wx + 1) < top_y      # right-descending = lit edge
        snow = pal((236, 242, 250), (110, 118, 142), d)
        tall = HORIZON - top_y > 30
        for y in range(top_y, HORIZON + 1):
            if tall and y - top_y < 3:
                px[x, y] = snow
            else:
                px[x, y] = flit if lit and y < top_y + 3 else fcol

    # --- distant ground band fills the horizon-to-road gap
    hcol = pal(*P_HILL, d, g * 0.35)
    gcol = pal(*P_GROUND, d, g * 0.3)
    dg = lerp(hcol, gcol, 0.5)
    for y in range(HORIZON + 1, ROAD_TOP):
        for x in range(PW):
            px[x, y] = dg

    # --- hills (0.5x)
    off_h = int(s * 0.5) % HILL_LEN
    for x in range(PW):
        for y in range(hill_ridge((x + off_h) % HILL_LEN), ROAD_TOP):
            px[x, y] = hcol

    # --- ground + road
    rcol = pal(*P_ROAD, d, g * 0.4)
    redge = lerp(rcol, (255, 255, 255), 0.22)
    off = s % L
    for x in range(PW):
        wc = (x + off) % L
        for y in range(ROAD_TOP, PH):
            if water_cell(wc, y):
                depth = (y - ROAD_BOT) / (PH - ROAD_BOT)
                wcol = lerp(pal(*P_WATER, d), pal(*P_WATER_DEEP, d), depth)
                if y == ROAD_BOT + 1:            # bright waterline
                    wcol = lerp(wcol, (235, 240, 245), 0.22)
                px[x, y] = wcol
            elif ROAD_TOP <= y <= ROAD_BOT:
                px[x, y] = redge if y == ROAD_TOP else rcol
            else:
                fade = (y - ROAD_BOT) / (PH - ROAD_BOT)
                px[x, y] = lerp(gcol, (int(gcol[0] * 0.4),
                                       int(gcol[1] * 0.4),
                                       int(gcol[2] * 0.45)), fade)

    # --- road texture: faint patches and cracks
    rdark = lerp(rcol, (0, 0, 0), 0.12)
    for wx, dy in ROAD_MARKS:
        x = (wx - off) % L
        if 0 <= x < PW:
            px[x, ROAD_TOP + dy] = rdark
            if wx % 3 == 0 and x + 1 < PW:
                px[x + 1, ROAD_TOP + dy] = rdark

    # --- meadow speckles + flowers
    for wx, y, dv in MEADOW:
        x = (wx - off) % L
        if 0 <= x < PW and not water_cell(wx, y) and y > ROAD_BOT:
            b = px[x, y]
            px[x, y] = tuple(max(0, min(255, int(v * (1 + dv)))) for v in b)
    if d < 0.85:
        for wx, y, ci in FLOWERS:
            x = (wx - off) % L
            if 0 <= x < PW and not water_cell(wx, y):
                px[x, y] = lerp(FLOWER_COLS[ci], (110, 105, 125), d)

    # --- water shimmer + reflections
    for wx, y, r in WATER_NOISE:
        wxs = (wx + int(t * 0.7)) % L
        if water_cell(wxs, y):
            x = (wxs - off) % L
            if 0 <= x < PW and r < 0.5:
                px[x, y] = lerp(px[x, y], (200, 215, 230), 0.18)
    if d < 0.5:                        # sun glints on the lake
        gx = (LAKE_L + LAKE_R) // 2
        for y in range(ROAD_BOT + 1, ROAD_BOT + 21):
            wob = int(math.sin(y * 0.7 + t * 0.35) * 3)
            wxc = gx + wob
            if water_cell(wxc, y) and y % 2:
                x = (wxc - off) % L
                if 0 <= x < PW:
                    px[x, y] = lerp(px[x, y], SUN_C, 0.5)
    if d > 0.75:                       # the moon on the river
        for y in range(ROAD_BOT + 1, PH):
            wob = int(math.sin(y * 0.6 + t * 0.3) * 3)
            wxc = 767 + wob
            if water_cell(wxc, y) and y % 2:
                x = (wxc - off) % L
                if 0 <= x < PW:
                    px[x, y] = lerp(px[x, y], MOON_C, 0.6)
                    if x + 1 < PW:
                        px[x + 1, y] = lerp(px[x + 1, y], MOON_C, 0.25)

    def plot(x, y, c):
        if 0 <= x < PW and 0 <= y < PH:
            px[x, y] = c

    # --- lake banks
    bank = lerp(gcol, (0, 0, 0), 0.25)
    for y in range(ROAD_BOT + 1, ROAD_BOT + 25):
        inset = (y - ROAD_BOT - 1) * 4
        for wxb in (LAKE_L + 8 + inset - 1, LAKE_R - 8 - inset + 1):
            x = (wxb - off) % L
            if 0 <= x < PW:
                plot(x, y, bank)

    # --- fences (kept light so they don't dominate the day)
    fcol2 = pal((172, 152, 124), (44, 44, 62), d, g * 0.4)
    for lo, hi in FENCES:
        for wx in range(lo, hi, 18):
            x = (wx - off) % L
            if -2 <= x < PW:
                for yy in range(ROAD_TOP - 8, ROAD_TOP):
                    plot(x, yy, fcol2)
        for wx in range(lo, hi):
            x = (wx - off) % L
            if 0 <= x < PW:
                plot(x, ROAD_TOP - 5, fcol2)

    # --- trees: two-tone canopies
    tcol = pal(*P_TREE, d, g * 0.3)
    tlit = pal(*P_TREE_LIT, d, g * 0.3)
    kcol = pal(*P_TRUNK, d)
    for wx, kind in TREES:
        x = (wx - off) % L
        if not -12 <= x < PW + 12:
            continue
        if kind == 'leafy':
            for yy in range(ROAD_TOP - 7, ROAD_TOP):
                plot(x, yy, kcol)
                plot(x + 1, yy, kcol)
            cy = ROAD_TOP - 11
            for ddx in range(-7, 9):
                for ddy in range(-5, 6):
                    if (ddx - 0.5) ** 2 / 1.7 + ddy * ddy <= 23:
                        lit = ddy < -1 or (ddx < -2 and ddy < 1)
                        plot(x + ddx, cy + ddy, tlit if lit else tcol)
        else:
            h = 15 + (wx * 7) % 8            # every pine its own height
            for i in range(h):
                yy = ROAD_TOP - h + i
                w = 1 + i * 5 // h
                for ddx in range(-w, w + 1):
                    lit = ddx < -w // 2 and i > 2
                    plot(x + ddx, yy, tlit if lit else tcol)
            plot(x, ROAD_TOP - 1, kcol)
            plot(x, ROAD_TOP - 2, kcol)

    # --- bushes: low tufts along the roadside
    for wx in BUSHES:
        x = (wx - off) % L
        if -4 <= x < PW + 4:
            for ddx in range(-3, 4):
                for ddy in range(0, 3):
                    if ddx * ddx + (ddy - 1) ** 2 * 3 <= 9:
                        plot(x + ddx, ROAD_TOP - 1 - ddy,
                             tlit if ddy == 2 else tcol)

    # --- reeds, leaning with the wind
    sway = 1 if (t // 7 + 1) % 3 == 0 else 0
    for wx in REEDS:
        x = (wx - off) % L
        if 0 <= x < PW:
            for yy in range(ROAD_BOT + 1, ROAD_BOT + 5):
                plot(x + (sway if yy < ROAD_BOT + 3 else 0), yy, tcol)
            plot(x + 1 + sway, ROAD_BOT + 1, tlit)

    # --- the bridge
    bcol = P_BRIDGE[0] if d < 0.5 else P_BRIDGE[1]
    bdim = lerp(bcol, (40, 40, 60), 0.45)
    mid, half = (TOWER_A + TOWER_B) / 2, (TOWER_B - TOWER_A) / 2
    for wx in range(TOWER_A + 1, TOWER_B):
        x = (wx - off) % L
        if not 0 <= x < PW:
            continue
        y = TOWER_TOP + ((ROAD_TOP - 11) - TOWER_TOP) * (1 - ((wx - mid) / half) ** 2)
        plot(x, int(y), bcol)
        if wx % 16 == 8:
            for sy in range(int(y) + 1, ROAD_TOP):
                plot(x, sy, bdim)
    for anchor, tower in ((BRIDGE_L, TOWER_A), (BRIDGE_R, TOWER_B)):
        n = abs(tower - anchor)
        stp = 1 if anchor < tower else -1
        for i in range(n):
            wx = anchor + i * stp
            x = (wx - off) % L
            if not 0 <= x < PW:
                continue
            y = ROAD_TOP - 1 - (ROAD_TOP - 1 - TOWER_TOP) * (i / n) ** 2
            plot(x, int(y), bcol)
    for tw in (TOWER_A, TOWER_B):
        x = (tw - off) % L
        if -4 <= x < PW + 4:
            for yy in range(TOWER_TOP - 3, ROAD_BOT + 13):
                plot(x - 1, yy, bcol)
                plot(x, yy, bcol)
                plot(x + 1, yy, bdim)
            for yy in range(ROAD_BOT + 13, PH):
                if (yy + tw) % 3:
                    wob = 1 if (yy // 3) % 2 else -1
                    plot(x + wob, yy, lerp(pal(*P_WATER_DEEP, d), (0, 0, 0), 0.3))
    for x in range(PW):
        wc = (x + off) % L
        if BRIDGE_L <= wc <= BRIDGE_R:
            plot(x, ROAD_TOP - 1, bdim)
            if wc % 5 == 0:
                plot(x, ROAD_TOP - 2, bdim)
                plot(x, ROAD_TOP - 3, bdim)
            plot(x, ROAD_BOT + 1, lerp(bdim, (0, 0, 0), 0.4))
            if wc % 3 == 0:                       # deck planks
                plot(x, ROAD_BOT, lerp(rcol, (0, 0, 0), 0.15))

    # --- beacon on the near tower, blinking red at night
    if d > 0.8:
        x = (TOWER_A - off) % L
        if 0 <= x < PW and (t // 9) % 3 != 2:
            plot(x, TOWER_TOP - 4, (255, 70, 56))
            px_c = px[x, TOWER_TOP - 5]
            px[x, TOWER_TOP - 5] = lerp(px_c, (255, 70, 56), 0.3)

    # --- owl perched on the far tower top, watching (night)
    if d > 0.9:
        x = (TOWER_B - off) % L
        if 0 <= x < PW:
            body = (74, 68, 88)
            for oy in (TOWER_TOP - 4, TOWER_TOP - 5, TOWER_TOP - 6):
                plot(x, oy, body)
                plot(x + 1, oy, body)
            plot(x - 1, TOWER_TOP - 6, body)      # ear tufts
            plot(x + 2, TOWER_TOP - 6, body)
            if (t // 26) % 7:
                plot(x, TOWER_TOP - 5, (222, 206, 148))
                plot(x + 1, TOWER_TOP - 5, (222, 206, 148))

    # --- rabbit in the morning fields: sits, then bolts as you near
    rider_w = s + RIDER_X
    if rider_w < RABBIT_X + 80:
        dist = RABBIT_X - rider_w
        hop = max(0, 45 - dist) if dist < 45 else 0
        rx = RABBIT_X + hop * 2
        x = int(rx - off) % L
        bob = (t // 2) % 2 if hop else 0
        if 0 <= x < PW and dist > -40:
            rcol2 = pal((196, 178, 150), (70, 70, 90), d)
            y0 = ROAD_BOT + 5
            plot(x, y0 - 1 - bob, rcol2)          # body
            plot(x + 1, y0 - 1 - bob, rcol2)
            plot(x + 2, y0 - 1 - bob, rcol2)
            plot(x + 2, y0 - 2 - bob, rcol2)      # head
            plot(x + 3, y0 - 2 - bob, rcol2)
            plot(x + 2, y0 - 3 - bob, rcol2)      # ears
            plot(x + 3, y0 - 4 - bob, rcol2)

    # --- fireflies in the night meadow
    if d > 0.85:
        for i, (fx, fy, ph) in enumerate(FIREFLIES):
            if (t + ph) % 44 < 16:
                wobx = int(math.sin((t + ph) * 0.2 + i) * 4)
                woby = int(math.cos((t + ph) * 0.15 + i * 2) * 2)
                x = (fx + wobx - off) % L
                y = fy + woby
                if 0 <= x < PW and not water_cell(fx + wobx, y):
                    plot(x, y, FIREFLY)
                    if (t + ph) % 44 < 8:
                        for hx, hy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            xx, yy = x + hx, y + hy
                            if 0 <= xx < PW and 0 <= yy < PH:
                                px[xx, yy] = lerp(px[xx, yy], FIREFLY, 0.45)

    # --- the wind: small flecks drifting through, day and night
    fleck_day = (168, 148, 96)
    fleck_night = (96, 102, 124)
    fcolw = lerp(fleck_day, fleck_night, d)
    for wxf, yf, ph in WIND_FLECKS:
        x = int(wxf - off - t * 1.4) % L
        if 0 <= x < PW:
            y = yf + int(math.sin(t * 0.25 + ph) * 2)
            if 0 <= y < PH and not water_cell((x + off) % L, y):
                px[x, y] = fcolw

    # --- dawn mist over the last fields
    rw = rider_w % L
    mist = 0.0
    if rw > 853:
        mist = max(0.0, d * (1 - d) * 3) * min(1.0, (rw - 853) / 40)
    if mist > 0.05:
        mcol = (188, 196, 210)
        for wx, y, r in WATER_NOISE[:700]:
            yy = 61 + (y % 16)
            wxs = (wx + int(t * 0.4)) % L
            x = (wxs - off) % L
            if 0 <= x < PW and r < mist * 0.55:
                px[x, yy] = lerp(px[x, yy], mcol, 0.35)

    # --- rider
    draw_rider(px, plot, t, d, g)

    return img


# ------------------------------------------------------------ the rider

def rider_pal(d):
    n = max(0.0, (d - 0.55) * 2.2)
    return {k: lerp(day, night, min(1.0, n)) for k, (day, night) in
            {'jersey': P_JERSEY, 'skin': P_SKIN, 'bike': P_BIKE,
             'shorts': P_SHORTS, 'hair': P_HAIR}.items()}


def draw_rider(px, plot, t, d, g):
    c = rider_pal(d)
    wy = ROAD_TOP - 5                  # wheel centers
    bx = RIDER_X                       # front wheel center
    rx = bx - 14                       # rear wheel center
    paused = PAUSE_START <= t < PAUSE_END
    tt = t - PAUSE_START

    # shadow, stretched at golden hour
    if d < 0.9:
        sh_len = 10 + int(12 * g)
        for i in range(sh_len):
            x = rx - 3 + i + int(8 * g)
            for yy in (ROAD_TOP, ROAD_TOP + (1 if sh_len // 3 < i < 2 * sh_len // 3 else 0)):
                if 0 <= x < PW:
                    px[x, yy] = lerp(px[x, yy], (10, 14, 10), 0.45)

    def wheel(cx):
        for a in range(16):
            ang = a * math.pi / 8
            plot(int(round(cx + 4 * math.cos(ang))),
                 int(round(wy + 4 * math.sin(ang))), c['bike'])
        plot(cx, wy, c['bike'])
        sp = (t // 2) % 4 * math.pi / 4
        for r_ in (2, 3):
            plot(int(round(cx + r_ * math.cos(sp))),
                 int(round(wy + r_ * math.sin(sp))), c['bike'])
            plot(int(round(cx - r_ * math.cos(sp))),
                 int(round(wy - r_ * math.sin(sp))), c['bike'])

    def frame_and_bars():
        bb = bx - 8                    # bottom bracket
        for i in range(6):             # down tube: head tube -> bb
            plot(bx - 2 - i, wy - 6 + i, c['bike'])
        for i in range(6):             # seat tube: bb -> saddle
            plot(bb - i // 2, wy - i, c['bike'])
        for i in range(6):             # top tube
            plot(bb - 3 + i, wy - 6, c['bike'])
        for i in range(5):             # chainstay: bb -> rear hub
            plot(bb - 1 - i, wy - 1 + i // 4, c['bike'])
        plot(bx - 1, wy - 7, c['bike'])          # head tube / stem
        plot(bx - 1, wy - 8, c['bike'])
        plot(bx, wy - 8, c['bike'])              # bars

    if not paused:
        wheel(bx)
        wheel(rx)
        frame_and_bars()
        bb = bx - 8
        pedal = (t // 3) % 2
        # legs: hip at saddle, cranks opposed
        hipx, hipy = bb - 3, wy - 7
        if pedal:
            plot(hipx + 1, hipy + 2, c['shorts'])
            plot(hipx + 2, hipy + 4, c['skin'])
            plot(bb, wy - 1, c['skin'])          # foot down
            plot(hipx + 1, hipy + 3, c['shorts'])
        else:
            plot(hipx + 2, hipy + 2, c['shorts'])
            plot(hipx + 3, hipy + 3, c['skin'])
            plot(bb, wy - 3, c['skin'])          # foot up
        # torso leaning to the bars
        for i in range(6):
            plot(hipx + i, hipy - 1 - i // 2, c['jersey'])
            plot(hipx + i, hipy - i // 2, c['jersey'])
        # arms to the bars
        plot(bx - 3, wy - 7, c['skin'])
        plot(bx - 2, wy - 7, c['skin'])
        # head: brown face, black hair swept back
        hx2, hy2 = bx - 4, wy - 11
        plot(hx2, hy2 + 1, c['skin'])
        plot(hx2 + 1, hy2 + 1, c['skin'])
        plot(hx2 - 1, hy2, c['hair'])
        plot(hx2, hy2, c['hair'])
        plot(hx2 + 1, hy2, c['hair'])
        plot(hx2 - 1, hy2 + 1, c['hair'])
        # headlight at night
        if d > 0.8:
            plot(bx + 1, wy - 6, (255, 240, 170))
            for i in range(1, 7):
                x = bx + 1 + i
                if 0 <= x < PW:
                    yy = wy - 6 + i // 3
                    px[x, yy] = lerp(px[x, yy], (255, 240, 170),
                                     max(0.05, 0.28 - i * 0.04))
        return

    # paused: bike parked; rider stands apart, breathing
    wheel(bx)
    wheel(rx)
    frame_and_bars()
    breathe = (tt // 12) % 2 if 6 <= tt < PAUSE_FRAMES - 8 else 0
    hx = bx - 22
    base = ROAD_TOP - 1                # feet on the deck
    # head: black hair over a brown face
    plot(hx, base - 11 - breathe, c['hair'])
    plot(hx + 1, base - 11 - breathe, c['hair'])
    plot(hx, base - 10 - breathe, c['skin'])
    plot(hx + 1, base - 10 - breathe, c['skin'])
    # torso
    for yy in range(base - 8, base - 4):
        plot(hx, yy, c['jersey'])
        plot(hx + 1, yy, c['jersey'])
    plot(hx - 1, base - 7 + breathe, c['jersey'])   # arms
    plot(hx + 2, base - 7 + breathe, c['jersey'])
    plot(hx - 1, base - 6 + breathe, c['skin'])
    plot(hx + 2, base - 6 + breathe, c['skin'])
    # shorts + legs
    for yy in range(base - 4, base - 2):
        plot(hx, yy, c['shorts'])
        plot(hx + 1, yy, c['shorts'])
    for yy in range(base - 2, base + 1):
        plot(hx, yy, c['skin'])
        plot(hx + 1, yy, c['skin'])
    if (t // 7) % 3 == 0:                         # jersey flutter in the wind
        plot(hx + 2, base - 8, c['jersey'])
    if 26 <= tt < 40:                             # the falling star
        i = tt - 26
        sx, sy = 27 + i * 4, 5 + i
        plot(sx, sy, (255, 255, 255))
        plot(sx - 2, sy - 1, (170, 175, 195))
        plot(sx - 5, sy - 1, (110, 115, 140))


# ------------------------------------------------------------ output

def upscale(img):
    return img.resize((PW * SCALE, PH * SCALE), Image.NEAREST)


def label(big):
    dr = ImageDraw.Draw(big)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
    except OSError:
        font = ImageFont.load_default()
    dr.text((big.width - 96, big.height - 20), 'sleipnir029',
            font=font, fill=(110, 116, 130))
    return big


def build_palette():
    """One fixed palette for every frame.

    Per-frame adaptive palettes drop small color regions — the ~10-px red
    jersey lost its slot and flickered to whatever color was nearest.
    Sample frames across the whole day cycle, and pin the rider + accent
    colors with explicit swatch blocks so they always own a palette entry.
    """
    reps = [label(upscale(make_frame(int(TOTAL_FRAMES * k / 12))))
            for k in range(12)]
    w, h = reps[0].size
    sw_cols = []
    for dd in (0.0, 0.3, 0.6, 1.0):
        c = rider_pal(dd)
        sw_cols += [c['jersey'], c['skin'], c['hair'], c['bike'],
                    c['shorts']]
    sw_cols += [(255, 240, 170), (255, 70, 56), FIREFLY, MOON_C,
                SUN_C, SUN_LOW, (236, 242, 250), (255, 255, 255)]
    src = Image.new('RGB', (w, h * 12 + 40))
    for k, r in enumerate(reps):
        src.paste(r, (0, k * h))
    dr = ImageDraw.Draw(src)
    for i, c in enumerate(sw_cols):
        dr.rectangle([(i * 24) % (w - 24), h * 12,
                      (i * 24) % (w - 24) + 23, h * 12 + 39], fill=c)
    return src.quantize(colors=255, dither=Image.NONE)


def build_gif():
    pal_img = build_palette()
    frames = []
    for t in range(TOTAL_FRAMES):
        big = label(upscale(make_frame(t)))
        frames.append(big.quantize(palette=pal_img, dither=Image.NONE))
    gif = ASSETS / 'pixel_journey.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:],
                   duration=int(1000 / FPS), loop=0, optimize=True)
    webp = ASSETS / 'pixel_journey.webp'
    frames[0].save(webp, save_all=True, append_images=frames[1:],
                   duration=int(1000 / FPS), loop=0)
    frames[len(frames) // 2].convert('RGB').save(ASSETS / 'pixel_journey_poster.png')
    return gif


if __name__ == '__main__':
    import sys
    if '--still' in sys.argv:
        for target in [int(a) for a in sys.argv[2:]] or [0]:
            t = min(range(TOTAL_FRAMES), key=lambda i: abs(OFFSETS[i] - target))
            p = ASSETS / f'pixel_s{target}.png'
            label(upscale(make_frame(t))).save(p)
            print('rendered', p)
    else:
        print('built', build_gif(), TOTAL_FRAMES, 'frames')
