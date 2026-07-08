"""One day on the road — a slow ASCII journey with a pause at its heart.

The route: morning fields -> a sunlit lakeshore -> pine forest -> open
hills at sunset -> the suspension bridge at night (stop, breathe, a star
falls) -> dawn fields, wrapping seamlessly into the morning again.

Layers (drawn back-to-front, transparent blits, nothing masks anything):
  celestial (sun/moon/stars by darkness) -> far mountains (0.25x) ->
  hills (0.5x) -> foreground strip (1x) -> rider.

Lighting is a function of world position s, so the loop closes on itself.
Strip lengths tile exactly: fg L=360, hills 180, mountains 90.

  python3 journey_scene.py --still 10 120 180 236 330   stills at position s
  python3 journey_scene.py                              full animation
"""
import random
from render import render_gif, write_txt_frames, get_font, ASSETS
from PIL import Image, ImageDraw

W, H = 100, 30
FPS = 10                   # speed comes from frame rate, not step size:
L = 360                    # the world always moves exactly 1 col/frame
                           # when cruising, so motion never judders

ROAD_ROW = 17
RIDE_ROW = ROAD_ROW - 1
RIDER_X = 44               # rider's fixed screen column

# ------------------------------------------------------------- palettes
# (day, night) pairs; lerped by darkness

P_LINE = ((225, 214, 188), (210, 218, 226))   # road, bridge, fences
P_FIELD = ((196, 172, 104), (86, 98, 118))    # grass, wheat tufts
P_TREE = ((120, 168, 96), (74, 88, 106))
P_HILL = ((150, 152, 118), (88, 96, 112))
P_FAR = ((122, 124, 130), (62, 70, 84))
P_CLOUD = ((205, 200, 185), (110, 118, 132))
P_WATER = ((118, 168, 198), (70, 100, 130))
P_WATER_DEEP = ((88, 128, 158), (52, 78, 104))
SUN = (255, 198, 76)
MOON = (255, 228, 170)
STAR_C = (170, 178, 190)
GLINT = (235, 220, 185)
SPARKLE = (255, 236, 170)
RIDER_C = (242, 245, 248)
LABEL = (100, 110, 120)


def lerp(pair, d):
    (r1, g1, b1), (r2, g2, b2) = pair
    return (int(r1 + (r2 - r1) * d), int(g1 + (g2 - g1) * d),
            int(b1 + (b2 - b1) * d))


def darkness(x):
    """0 = day, 1 = night, by world position (loops at L)."""
    x = x % L
    if x < 195:
        return 0.0
    if x < 245:
        return (x - 195) / 50
    if x < 330:
        return 1.0
    if x < 358:
        return 1.0 - (x - 330) / 28
    return 0.0


# ------------------------------------------------------------- world strip

FG = {c: [] for c in range(L)}


def fg_put(wc, r, ch, role):
    FG[wc % L].append((r, ch, role))


def fg_sprite(wx, top, lines, role):
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            if ch != ' ':
                fg_put(wx + c, top + r, ch, role)


TREE = ["  &&&  ", " &&&&& ", "&&&&&&&", "  | |  "]
PINE = ["  /\\  ", " /  \\ ", " /\\/\\ ", "/    \\", "  ||  "]
TUFTS = ',."\'`'

RNG = random.Random(29)

LAKE_L, LAKE_R = 95, 150          # reeds at edges, water between
BRIDGE_L, BRIDGE_R = 245, 315     # deck zone; river below it
TOWER_A, TOWER_B = 255, 305
TOWER_TOP = 6
WATER_TOP_ROW = ROAD_ROW + 2


def water_cell(wc, r):
    """Is (world col, row) water? The lake is a bowl; the river runs deep."""
    wc = wc % L
    if r < WATER_TOP_ROW:
        return False
    if BRIDGE_L + 2 <= wc <= BRIDGE_R - 2:
        return True
    if r > WATER_TOP_ROW + 6:         # the lake has a floor
        return False
    inset = (r - WATER_TOP_ROW) * 3   # ... and narrows toward it
    return LAKE_L + 4 + inset <= wc <= LAKE_R - 4 - inset

# road (the deck is just the road crossing the river)
for wc in range(L):
    on_bridge = BRIDGE_L <= wc <= BRIDGE_R
    fg_put(wc, ROAD_ROW, '_' if wc % 2 == 0 else ('=' if on_bridge else '_'),
           'line')

# the meadow: a foreground band below the road, dense near, sparse deep —
# the jgs density-gradient trick, so the canvas reads as land, not a strip
def near_water(wc):
    return any(a - 3 <= wc <= b + 3 for a, b in
               [(LAKE_L, LAKE_R), (BRIDGE_L, BRIDGE_R)])

MEADOW = [  # (row offset below road, density, charset)
    (1, 0.30, ',."\'`'), (2, 0.20, ',.\'`'), (3, 0.12, ',.'),
    (4, 0.07, '.,'), (5, 0.05, '.'), (6, 0.03, '.'), (7, 0.02, '.'),
    (8, 0.015, '.'), (9, 0.01, '.'),
]
for wc in range(L):
    if near_water(wc):
        continue
    for dr, dens, chars in MEADOW:
        if RNG.random() < dens:
            role = 'field' if dr <= 2 else 'field_deep'
            fg_put(wc, ROAD_ROW + dr, RNG.choice(chars), role)
    if RNG.random() < 0.04:            # a taller grass clump
        for j, ch in enumerate('\\|/'):
            fg_put(wc + j - 1, ROAD_ROW + 1, ch, 'field')
    if RNG.random() < 0.035:           # a wildflower
        fg_put(wc, ROAD_ROW + 1 + RNG.randint(0, 1), '*', 'flower')
    if RNG.random() < 0.20 and wc % 3 == 0:
        fg_put(wc, ROAD_ROW - 1, '"', 'field')

# fences along the morning and dawn fields
for lo, hi in ((8, 62), (326, 354)):
    for wx in range(lo, hi, 7):
        fg_put(wx, ROAD_ROW - 1, '|', 'line')
        fg_put(wx, ROAD_ROW - 2, '|', 'line')
        for c in range(wx + 1, min(wx + 7, hi)):
            fg_put(c, ROAD_ROW - 2, '-', 'line')

# trees: leafy in the fields, pines in the forest stretch
for wx in (26, 70, 210, 232, 340):
    fg_sprite(wx, ROAD_ROW - len(TREE), TREE, 'tree')
for wx in (158, 168, 175, 186, 196, 203):
    fg_sprite(wx, ROAD_ROW - len(PINE), PINE, 'tree')

# reeds at every water's edge
for wx in (LAKE_L, LAKE_L + 2, LAKE_R - 2, LAKE_R,
           BRIDGE_L - 4, BRIDGE_L - 2, BRIDGE_R + 2, BRIDGE_R + 4):
    fg_put(wx, ROAD_ROW + 1, '\\' if wx % 2 else '/', 'tree')
    fg_put(wx, ROAD_ROW, ';', 'tree')

# the lake's sloping banks trace the bowl down to its floor
for r in range(WATER_TOP_ROW, WATER_TOP_ROW + 7):
    inset = (r - WATER_TOP_ROW) * 3
    fg_put(LAKE_L + 4 + inset - 1, r, '\\', 'field')
    fg_put(LAKE_R - 4 - inset + 1, r, '/', 'field')

# --- the suspension bridge, stamped into the strip ---
def cable_run_strip(pts, role):
    ipts = [(x, int(round(y))) for x, y in pts]
    for i, (x, ry) in enumerate(ipts):
        nxt = ipts[i + 1][1] if i + 1 < len(ipts) else ry
        ch = '\\' if nxt > ry else ('/' if nxt < ry else '_')
        fg_put(x, ry, ch, role)


half = (TOWER_B - TOWER_A) / 2
mid = (TOWER_A + TOWER_B) / 2
sag = (ROAD_ROW - 5) - TOWER_TOP
xs = list(range(TOWER_A + 1, TOWER_B))
main = [(x, TOWER_TOP + sag * (1 - ((x - mid) / half) ** 2)) for x in xs]
cable_run_strip(main, 'line')
for x, y in main:
    if x % 7 == 3:
        for sr in range(int(round(y)) + 1, ROAD_ROW):
            fg_put(x, sr, ':', 'line')

for anchor, tower in ((BRIDGE_L, TOWER_A), (BRIDGE_R, TOWER_B)):
    n = abs(tower - anchor)
    step = 1 if anchor < tower else -1
    pts = []
    for i in range(1, n):
        x = anchor + i * step
        frac = 1 - i / n
        y = TOWER_TOP + (ROAD_ROW - 1 - TOWER_TOP) * frac ** 2
        pts.append((x, y))
    if step < 0:
        pts.reverse()
    cable_run_strip(pts, 'line')
    for x, y in pts:
        if x % 8 == 4:
            for sr in range(int(round(y)) + 1, ROAD_ROW):
                fg_put(x, sr, ':', 'line')

for tx in (TOWER_A, TOWER_B):
    for r in range(TOWER_TOP, ROAD_ROW):
        fg_put(tx - 1, r, '[', 'line')
        fg_put(tx + 1, r, ']', 'line')
    for r in range(ROAD_ROW + 1, ROAD_ROW + 4):
        fg_put(tx - 1, r, '[', 'line')
        fg_put(tx + 1, r, ']', 'line')
    for c in (tx - 1, tx, tx + 1):
        fg_put(c, TOWER_TOP - 1, '_', 'line')

for wc in range(BRIDGE_L, BRIDGE_R + 1):
    fg_put(wc, ROAD_ROW + 1, '!', 'line')

# ------------------------------------------------------------- hills / far

LH = 180
MOTIF = "__,-~'`~-,__,.-''-.__,--~~--,_.-``-."      # 36 chars, tiles LH
assert LH % len(MOTIF) == 0
HILLS = {i: [(14, MOTIF[i % len(MOTIF)], 'hill')] for i in range(LH)}
for wx in (18, 60, 104, 142, 166):
    for dr, dc in ((13, 0), (13, 1), (12, 0)):
        HILLS[(wx + dc) % LH].append((dr, '&', 'tree'))
WINDMILLS = (40, 122)
for wx in WINDMILLS:
    for rr in (12, 13):
        HILLS[wx % LH].append((rr, '|', 'hill'))

LF = 90
MOUNTAINS = [l.ljust(LF)[:LF] for l in [
    "                    _                                                                     ",
    "                  _/ \\_            /\\                    _/\\_                           ",
    "               _/      \\_       _/   \\_      /\\       _/     \\_       _/\\             ",
    "            _/    ^      \\_   _/  ^    \\  _/   \\_   _/   ^     \\_  _/    \\_          ",
    "         _/    ^       '\\  \\_/    ^  ^  \\/   ^    \\_/   _  ^     \\/  ^      \\_      ",
]]

STARS = [(4, 1), (15, 3), (30, 0), (41, 2), (55, 1), (64, 3), (10, 5),
         (49, 4), (70, 0), (96, 4), (36, 5), (22, 2), (88, 2), (79, 5),
         (7, 7), (26, 6), (45, 7), (60, 6), (92, 7), (18, 0), (52, 2),
         (83, 0)]

CLOUDS = [(20, 2), (95, 4), (150, 1)]
BIRDS = [(62, 3), (144, 5)]           # on the 0.5x/180 layer, day only

WATER_LEN = 240
WATER_STRIPS = {}
for r in range(ROAD_ROW + 2, H - 1):
    depth = (r - ROAD_ROW - 2) / max(1, (H - 2 - ROAD_ROW - 2))
    density = 0.5 * (1 - depth) + 0.1
    WATER_STRIPS[r] = [
        (RNG.choice('~^-_~-') if RNG.random() < density else ' ')
        for _ in range(WATER_LEN)]

# ------------------------------------------------------------- timeline

STOP_S = int(mid) - RIDER_X   # rider's wheels at mid-span
PAUSE_FRAMES = 80


def build_offsets():
    """Per-frame world offset s, in whole columns while moving.

    Easing is done by dwell (holding a column for 2-4 frames), never by
    fractional steps — a char grid can't move sub-column, and uneven
    rounding reads as dropped frames.
    """
    steps = []                          # column advance per frame: 0 or 1
    ease_in = [1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]   # rolling to a stop
    ease_out = [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1]     # pulling away
    n_cruise1 = STOP_S - sum(ease_in)
    steps += [1] * n_cruise1
    steps += ease_in
    pause_start = len(steps)
    steps += [0] * PAUSE_FRAMES
    steps += ease_out
    steps += [1] * (L - STOP_S - sum(ease_out))
    s, out = 0, []
    for v in steps:
        out.append(s)
        s += v
    assert s == L
    return out, pause_start

OFFSETS, PAUSE_START = build_offsets()
TOTAL_FRAMES = len(OFFSETS)
PAUSE_END = PAUSE_START + PAUSE_FRAMES

# ------------------------------------------------------------- drawing

def put(grid, r, c, ch, color):
    if 0 <= r < H and 0 <= c < W:
        grid[r][c] = (ch, color)


def blit(grid, top, left, lines, color):
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            if ch != ' ':
                put(grid, top + r, left + c, ch, color)


ROLE_PAL = {'line': P_LINE, 'field': P_FIELD, 'tree': P_TREE,
            'hill': P_HILL,
            'field_deep': ((132, 118, 76), (56, 66, 82)),
            'flower': ((226, 150, 150), (96, 104, 122))}

MOON_S = ["   _.._ ", "  .' .-'`", " /  /    ", " |  |    ",
          " \\  '.___", "  '._  _ ", "     ``  "]


def draw_celestial(grid, d, t, s):
    for i, (x, r) in enumerate(STARS):
        thr = 0.35 + 0.6 * (i / len(STARS))
        if d > thr:
            ch = '*' if (i + t // 8) % 4 else '+'
            put(grid, r, x, ch if i % 2 else '.', STAR_C)
    for i, (x, r) in enumerate(CLOUDS):
        # clouds live on the 0.5x/180 layer so the loop closes exactly;
        # resting during the pause suits them
        cx = int(x - s * 0.5) % 180 - 40
        col = lerp(P_CLOUD, d)
        for j, ch in enumerate('~~~~'):
            put(grid, r, cx + j, ch, col)
    if d < 0.4:                        # birds ride the morning air
        wing = 'v' if (t // 5) % 2 else 'w'
        for x, r in BIRDS:
            bx = int(x - s * 0.5) % 180 - 40
            put(grid, r, bx, wing, lerp(P_CLOUD, d))
            put(grid, r + ((t // 5) % 2), bx + 3, wing, lerp(P_CLOUD, d))
    if d < 0.85:                       # sun sinks as darkness grows
        sy = 2 + d * 11
        blit(grid, int(sy), 72, ["\\ | /", "- O -", "/ | \\"],
             lerp((SUN, (150, 90, 50)), d))
    if d > 0.55:                       # moon rises once the sun is low
        my = 12 - (d - 0.55) / 0.45 * 10
        blit(grid, int(my), 84, MOON_S, MOON)


def draw_far(grid, s, d):
    off = int(s * 0.25) % LF
    col = lerp(P_FAR, d)
    for r, line in enumerate(MOUNTAINS):
        row = 9 + r
        for c in range(W):
            ch = line[(c + off) % LF]
            if ch != ' ':
                put(grid, row, c, ch, col)


def draw_hills(grid, s, d, t):
    off = int(s * 0.5) % LH
    for c in range(W):
        wc = (c + off) % LH
        for r, ch, role in HILLS.get(wc, ()):
            put(grid, r, c, ch, lerp(ROLE_PAL[role], d))
        if wc in WINDMILLS:            # slow blades above the mast
            blades = ['\\|/', '-o-'][(t // 6) % 2]
            for j, ch in enumerate(blades):
                put(grid, 11, c - 1 + j, ch, lerp(P_HILL, d))


def draw_fg(grid, s, d, t):
    off = int(s) % L
    for c in range(W):
        wc = (c + off) % L
        for r, ch, role in FG[wc]:
            put(grid, r, c, ch, lerp(ROLE_PAL[role], d))
        for r, strip in WATER_STRIPS.items():
            if not water_cell(wc, r):
                continue
            depth = r - WATER_TOP_ROW
            speed = 0.5 if depth < 3 else 0.25
            woff = int(t * speed)
            ch = strip[(wc + woff) % WATER_LEN]
            if ch != ' ':
                pal = P_WATER if depth < 4 else P_WATER_DEEP
                put(grid, r, c, ch, lerp(pal, d))


def draw_glints(grid, s, d, t):
    off = int(s) % L
    if d > 0.8:                        # moon glint on the river
        for r in range(ROAD_ROW + 2, ROAD_ROW + 7):
            if (t // 4 + r) % 3:
                wc = mid + 8 + ((t // 3 + r * 5) % 3) - 1
                c = (int(wc) - off) % L
                if 0 <= c < W:
                    put(grid, r, c, "'" if r % 2 else '.', GLINT)
    if d < 0.35:                       # sun sparkles on the lake
        for k in range(4):
            wc = LAKE_L + 8 + ((t // 3 + k * 13) * 7) % (LAKE_R - LAKE_L - 16)
            r = WATER_TOP_ROW + (k + t // 5) % 3
            c = (wc - off) % L
            if 0 <= c < W and water_cell(wc, r):
                put(grid, r, c, '*' if (t // 3 + k) % 2 else "'", SPARKLE)


RIDE_POSES = [
    ["    __o ", "  _ \\<,_", " (*)/(*)"],
    ["    __o ", "  _ \\<'_", " (\\)/(\\)"],
    ["    __o ", "  _ \\<,_", " (|)/(|)"],
    ["    __o ", "  _ \\<'_", " (/)/(/)"],
]
BIKE_ALONE = ["   __   ", " _ \\ ,_ ", " (*)/(*)"]
STAND = [" o ", "/|\\", "/ \\"]
STAND_BREATHE = [" o ", "(|)", "/ \\"]


def draw_rider(grid, t):
    top = RIDE_ROW - 2
    if t < PAUSE_START or t >= PAUSE_END:
        pose = RIDE_POSES[(t // 3) % 4]
        blit(grid, top, RIDER_X, pose, RIDER_C)
        return
    tt = t - PAUSE_START
    blit(grid, top, RIDER_X, BIKE_ALONE, RIDER_C)
    if tt < 4 or tt > PAUSE_FRAMES - 5:
        blit(grid, top, RIDER_X - 4, STAND, RIDER_C)
        return
    breathing = STAND_BREATHE if (tt // 10) % 2 else STAND
    blit(grid, top, RIDER_X - 4, breathing, RIDER_C)
    puff = tt % 30
    if puff < 9:
        put(grid, top - 1 - puff // 4, RIDER_X - 6 + puff // 5, '°',
            (150, 158, 168))
    if 22 <= tt < 34:                  # a star falls while he watches
        i = tt - 22
        sc, sr = 12 + i * 2, 1 + i // 2
        put(grid, sr, sc, '*', STAR_C)
        put(grid, sr, sc - 1, "'", (150, 158, 168))
        put(grid, sr - (1 if i % 2 else 0), sc - 2, '`', (120, 128, 138))


def make_frame(t):
    s = OFFSETS[t]
    d = darkness(s + RIDER_X)          # lighting follows the rider
    grid = [[(' ', None)] * W for _ in range(H)]
    draw_celestial(grid, d, t, s)
    draw_far(grid, s, d)
    draw_hills(grid, s, d, t)
    draw_fg(grid, s, d, t)
    draw_glints(grid, s, d, t)
    draw_rider(grid, t)
    label = 'sleipnir029'
    for i, ch in enumerate(label):
        put(grid, H - 1, W - len(label) - 2 + i, ch, LABEL)
    return grid


def build():
    return [make_frame(t) for t in range(TOTAL_FRAMES)]


def render_once(grid, name):
    font = get_font(12)
    bbox = font.getbbox('M')
    cw, chh = bbox[2] - bbox[0], bbox[3] - bbox[1] + 1
    img = Image.new('RGB', (W * cw + 24, H * chh + 24), (0, 0, 0))
    dr = ImageDraw.Draw(img)
    for r, row in enumerate(grid):
        for c, (ch, col) in enumerate(row):
            if ch != ' ':
                dr.text((12 + c * cw, 12 + r * chh), ch, font=font,
                        fill=col or (220, 220, 220))
    p = ASSETS / f'{name}.png'
    img.save(p)
    print('rendered', p)


if __name__ == '__main__':
    import sys
    if '--still' in sys.argv:
        for target in [int(a) for a in sys.argv[2:]] or [0]:
            t = min(range(TOTAL_FRAMES), key=lambda i: abs(OFFSETS[i] - target))
            render_once(make_frame(t), f'journey_s{target}')
    else:
        frames = build()
        write_txt_frames(frames, 'journey')
        paths = render_gif(frames, 'journey_scene', fg=RIDER_C, fps=FPS,
                           scale=12, width_chars=W, height_lines=H)
        print('built', TOTAL_FRAMES, 'frames', *paths, sep='\n  ')
