"""Night ride over the river — fixed ASCII panorama with a narrative loop.

A jgs-inspired suspension bridge spans the scene. The cyclist crosses,
stops mid-bridge, dismounts, breathes, and rides on. Only the rider, the
water, the moon glint and a few stars move; the scene itself is still.

  python3 ride_scene.py --elements   render each element for review
  python3 ride_scene.py --still      composed static scene
  python3 ride_scene.py              full animation
"""
import math
import random
from render import render_gif, write_txt_frames, get_font, ASSETS
from PIL import Image, ImageDraw

W, H = 100, 30
FPS = 8

INK = (215, 222, 228)      # line art
DIM = (120, 130, 142)      # suspenders, underside
FAR = (62, 70, 84)         # background mountains, barely-there
WATER = (110, 150, 185)
WATER_DIM = (70, 100, 130)
MOON = (255, 228, 170)
GLINT = (235, 220, 185)
STAR = (170, 178, 190)
RIDER = (240, 244, 248)
LABEL = (100, 110, 120)

DECK_ROW = 17              # the bridge deck line
RIDE_ROW = DECK_ROW - 1    # wheels roll one row above the deck line
TOWER_L, TOWER_R = 24, 74
TOWER_TOP = 6
WATER_TOP, WATER_BOT = 20, 28

# ---------------------------------------------------------------- elements

MOON_S = [                 # after jgs
    "   _.._ ",
    "  .' .-'`",
    " /  /    ",
    " |  |    ",
    " \\  '.___",
    "  '._  _ ",
    "     ``  ",
]

MOUNTAINS = [              # jgs vocabulary: /\ ridges, ^ faces, `-. curves
    "                 _                                          _                                       ",
    "         .   . _/ \\_    .     /\\       *        .        _/ \\   .     _       .    *              ",
    "    *       _/      \\__/\\   _/  \\_        _/\\_      ._ _/    \\_     _/ \\_   /\\        .          ",
    "          _/    ^     \\  \\_/  ^   \\   ._/     \\_  _/  \\/   ^    \\  _/ ^   \\_/  \\_   _/\\_         ",
    "       _/   ^     .'\\  \\/   ^   ^  \\_/    ^      \\/  ^   _  ^     \\/    ^        \\_/     \\_       ",
    "     _/  ^     _/    \\_    ^    _      ^     ^    _   ^ / \\    ^      ^     _  ^    ^      \\_     ",
    "   _/       ^ /        \\_    _/ \\_  ^     _   ^  / \\_  /   \\_      _  ^   _/ \\_   ^     ^    \\_   ",
    " _/    ^     /    ^       \\_/     \\    ^ / \\    /    \\/       \\  _/ \\__ _/     \\_      ^        \\_ ",
]

RIDE_POSES = [             # facing right; legs and spokes cycle
    ["    __o ", "  _ \\<,_", " (*)/(*)"],
    ["    __o ", "  _ \\<'_", " (\\)/(\\)"],
    ["    __o ", "  _ \\<,_", " (|)/(|)"],
    ["    __o ", "  _ \\<'_", " (/)/(/)"],
]
BIKE_ALONE = ["   __   ", " _ \\ ,_ ", " (*)/(*)"]
STAND = [" o ", "/|\\", "/ \\"]          # standing, facing the water
STAND_BREATHE = [" o ", "(|)", "/ \\"]   # shoulders lifted mid-breath

STARS = [(4, 1), (15, 3), (30, 0), (41, 2), (55, 1), (64, 3),
         (10, 5), (49, 4), (70, 0), (96, 4), (36, 5), (22, 2)]
TWINKLERS = {1, 4, 7, 10}   # indices of STARS that pulse


def put(grid, r, c, ch, color):
    if 0 <= r < H and 0 <= c < W:
        grid[r][c] = (ch, color)


def blit(grid, top, left, lines, color):
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            if ch != ' ':
                put(grid, top + r, left + c, ch, color)


def cable_run(grid, xs_ys, color):
    """Draw a cable as a continuous run: rows step -> \\ or /, flat -> _."""
    pts = [(x, int(round(y))) for x, y in xs_ys]
    for i, (x, ry) in enumerate(pts):
        nxt = pts[i + 1][1] if i + 1 < len(pts) else ry
        ch = '\\' if nxt > ry else ('/' if nxt < ry else '_')
        put(grid, ry, x, ch, color)


def draw_bridge(grid):
    half = (TOWER_R - TOWER_L) / 2
    mid = (TOWER_L + TOWER_R) / 2
    sag = (DECK_ROW - 5) - TOWER_TOP

    def main_y(x):  # hangs from tower tops, lowest at mid-span
        return TOWER_TOP + sag * (1 - ((x - mid) / half) ** 2)

    xs = list(range(TOWER_L + 1, TOWER_R))
    cable_run(grid, [(x, main_y(x)) for x in xs], INK)
    for x in xs:
        if x % 7 == 3:
            for sr in range(int(round(main_y(x))) + 1, DECK_ROW):
                put(grid, sr, x, ':', DIM)

    for anchor, tower in ((2, TOWER_L), (W - 3, TOWER_R)):
        n = abs(tower - anchor)
        step = 1 if anchor < tower else -1
        pts = []
        for i in range(1, n):
            x = anchor + i * step
            frac = 1 - i / n            # 0 at tower, 1 at anchor
            y = TOWER_TOP + (DECK_ROW - 1 - TOWER_TOP) * frac ** 2
            pts.append((x, y))
        if step < 0:
            pts.reverse()
        cable_run(grid, pts, INK)
        for x, y in pts:
            if x % 8 == 4:
                for sr in range(int(round(y)) + 1, DECK_ROW):
                    put(grid, sr, x, ':', DIM)

    for tx in (TOWER_L, TOWER_R):
        for r in range(TOWER_TOP, WATER_TOP + 2):
            if r < DECK_ROW:
                put(grid, r, tx - 1, '[', INK)
                put(grid, r, tx, ' ', INK)
                put(grid, r, tx + 1, ']', INK)
            elif r > DECK_ROW:
                put(grid, r, tx - 1, '[', DIM)
                put(grid, r, tx + 1, ']', DIM)
        put(grid, TOWER_TOP - 1, tx - 1, '_', INK)
        put(grid, TOWER_TOP - 1, tx, '_', INK)
        put(grid, TOWER_TOP - 1, tx + 1, '_', INK)

    for c in range(W):
        put(grid, DECK_ROW, c, '_' if c % 2 == 0 else ':', INK)
        put(grid, DECK_ROW + 1, c, '!', DIM)


def draw_static(grid):
    for i, (x, r) in enumerate(STARS):
        if i not in TWINKLERS:
            put(grid, r, x, '*' if i % 3 == 0 else '.', STAR)
    blit(grid, 1, 84, MOON_S, MOON)
    blit(grid, 11, 0, MOUNTAINS, FAR)  # peaks at 11; rows past the deck clip
    draw_bridge(grid)
    label = 'sleipnir029'
    for i, ch in enumerate(label):
        put(grid, H - 1, W - len(label) - 2 + i, ch, LABEL)


# ---------------------------------------------------------------- water

RNG = random.Random(29)
WATER_STRIPS = {}
for r in range(WATER_TOP, WATER_BOT + 1):
    depth = (r - WATER_TOP) / (WATER_BOT - WATER_TOP)
    density = 0.55 * (1 - depth) + 0.12
    strip = []
    for _ in range(240):
        strip.append(RNG.choice('~^-_~-') if RNG.random() < density else ' ')
    WATER_STRIPS[r] = strip


def draw_water(grid, t):
    for r in range(WATER_TOP, WATER_BOT + 1):
        depth = r - WATER_TOP
        speed = 0.5 if depth < 3 else 0.25
        off = int(t * speed) % 240
        strip = WATER_STRIPS[r]
        color = WATER if depth < 4 else WATER_DIM
        for c in range(W):
            ch = strip[(c + off) % 240]
            if ch != ' ':
                put(grid, r, c, ch, color)
    # moon glint: a soft shimmering streak under the moon
    for r in range(WATER_TOP, WATER_TOP + 5):
        if (t // 3 + r) % 3:
            c = 88 + ((t // 2 + r * 5) % 3) - 1
            put(grid, r, c, "'" if r % 2 else '.', GLINT)


def draw_twinkle(grid, t):
    for i in TWINKLERS:
        x, r = STARS[i]
        phase = (t // 4 + i) % 4
        ch = ['.', '*', '+', '*'][phase]
        put(grid, r, x, ch, STAR)


# ---------------------------------------------------------------- narrative

def rider_state(t):
    """Return (kind, x) for frame t. x is the sprite's left column."""
    CENTER = 44
    ENTER_END = 50            # frames riding in (with ease-out)
    DISMOUNT = ENTER_END + 6
    BREATHE_END = DISMOUNT + 48
    MOUNT = BREATHE_END + 6
    EXIT_END = MOUNT + 42
    TOTAL = EXIT_END + 12     # empty beat, then loop

    if t < ENTER_END:
        f = t / ENTER_END
        eased = 1 - (1 - f) ** 2
        x = -10 + (CENTER + 10) * eased
        return 'ride', int(round(x)), t
    if t < DISMOUNT:
        return 'dismount', CENTER, t
    if t < BREATHE_END:
        return 'breathe', CENTER, t - DISMOUNT
    if t < MOUNT:
        return 'mount', CENTER, t
    if t < EXIT_END:
        f = (t - MOUNT) / (EXIT_END - MOUNT)
        x = CENTER + (W + 4 - CENTER) * f ** 1.6
        return 'ride', int(round(x)), t
    return 'gone', 0, t


TOTAL_FRAMES = 50 + 6 + 48 + 6 + 42 + 12


def draw_rider(grid, t):
    kind, x, tt = rider_state(t)
    top = RIDE_ROW - 2
    if kind == 'ride':
        pose = RIDE_POSES[(tt // 2) % 4]
        blit(grid, top, x, pose, RIDER)
    elif kind in ('dismount', 'mount'):
        blit(grid, top, x, BIKE_ALONE, RIDER)
        blit(grid, top, x - 4, STAND, RIDER)
    elif kind == 'breathe':
        blit(grid, top, x, BIKE_ALONE, RIDER)
        breathing = STAND_BREATHE if (tt // 8) % 2 else STAND
        blit(grid, top, x - 4, breathing, RIDER)
        puff = (tt % 24)
        if puff < 8:                       # a slow breath drifting up
            put(grid, top - 1 - puff // 3, x - 2 + puff // 4, '°', DIM)
        if 20 <= tt < 30:                  # a star falls while he watches
            i = tt - 20
            sc, sr = 14 + i * 2, 1 + i // 2
            put(grid, sr, sc, '*', STAR)
            put(grid, sr, sc - 1, "'", DIM)
            put(grid, sr - (1 if i % 2 else 0), sc - 2, '`', DIM)


# ---------------------------------------------------------------- build

def make_frame(t):
    grid = [[(' ', None)] * W for _ in range(H)]
    draw_static(grid)
    draw_twinkle(grid, t)
    draw_water(grid, t)
    draw_rider(grid, t)
    return grid


def build():
    return [make_frame(t) for t in range(TOTAL_FRAMES)]


def render_once(grid, name):
    font = get_font(14)
    bbox = font.getbbox('M')
    cw, chh = bbox[2] - bbox[0], bbox[3] - bbox[1] + 1
    img = Image.new('RGB', (W * cw + 24, H * chh + 24), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for r, row in enumerate(grid):
        for c, (ch, col) in enumerate(row):
            if ch != ' ':
                d.text((12 + c * cw, 12 + r * chh), ch, font=font,
                       fill=col or INK)
    p = ASSETS / f'{name}.png'
    img.save(p)
    print('rendered', p)


def elements_sheet():
    grid = [[(' ', None)] * W for _ in range(H)]
    blit(grid, 0, 2, MOON_S, MOON)
    blit(grid, 0, 20, RIDE_POSES[0], RIDER)
    blit(grid, 0, 32, RIDE_POSES[1], RIDER)
    blit(grid, 0, 44, BIKE_ALONE, RIDER)
    blit(grid, 0, 56, STAND, RIDER)
    blit(grid, 0, 62, STAND_BREATHE, RIDER)
    blit(grid, 9, 0, MOUNTAINS, DIM)
    for r in range(WATER_TOP, WATER_BOT + 1):
        strip = WATER_STRIPS[r]
        color = WATER if r - WATER_TOP < 4 else WATER_DIM
        for c in range(W):
            ch = strip[c % 240]
            if ch != ' ':
                put(grid, r, c, ch, color)
    render_once(grid, 'scene_elements')


if __name__ == '__main__':
    import sys
    if '--elements' in sys.argv:
        elements_sheet()
    elif '--still' in sys.argv:
        render_once(make_frame(70), 'scene_still')
    else:
        frames = build()
        write_txt_frames(frames, 'ride')
        paths = render_gif(frames, 'ride_scene', fg=INK, fps=FPS, scale=12,
                           width_chars=W, height_lines=H)
        print('built', *paths, sep='\n  ')
