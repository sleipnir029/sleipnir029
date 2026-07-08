"""Variant 3 (winner): side-scrolling life world — a calm evening ride past
the scenes of a life: the arcade, the university, home, the library.

Three parallax layers scroll behind a cyclist pedaling in place. Every layer's
strip length divides evenly into N_FRAMES * speed, so the loop is seamless.
"""
from render import render_gif, write_txt_frames

W, H = 90, 20
FPS = 6
N_FRAMES = 192        # fg speed 1 char/frame over a 192-char world strip

# retro dusk palette
STAR = (150, 160, 180)
SUN = (255, 190, 70)
CLOUD = (170, 180, 200)
BIRD = (200, 205, 215)
MOUNTAIN = (75, 85, 120)
TREE = (90, 200, 110)
TRUNK = (150, 110, 75)
BUILD = (205, 175, 135)
ROOF = (225, 120, 90)
ARCADE = (140, 160, 255)
ARCADE_GLOW = (255, 230, 120)
HEART = (255, 100, 120)
HEART_DIM = (200, 70, 95)
BOOKS = [(230, 120, 100), (120, 200, 140), (130, 160, 240), (240, 200, 110)]
ROAD = (130, 130, 140)
GRASS = (80, 150, 90)
RIDER = (240, 240, 240)
LABEL = (120, 130, 140)

GROUND_ROW = 15
RIDER_COL = 10


def blit(grid, top, left, lines, color):
    for r, line in enumerate(lines):
        row = top + r
        if not 0 <= row < H:
            continue
        for c, ch in enumerate(line):
            col = left + c
            if ch != ' ' and 0 <= col < W:
                grid[row][col] = (ch, color)


def put(grid, r, c, ch, color):
    if 0 <= r < H and 0 <= c < W:
        grid[r][c] = (ch, color)


TREE_S = ["▟█▙", " █ "]
TREE_BIG = [" ▄█▄ ", "▟███▙", "  █  "]
HOUSE_ROOF = ["  ▄▄▄▄  ", " ▟████▙ "]
HOUSE_BODY = [" ██▐▌██ ", " ██▐▌██ "]
ARCADE_S = [" ▄▄▄ ", "▐▓▓▓▌", "▐···▌", "▐▄▄▄▌"]
UNI = ["  ▄▄▄▄▄▄ ", " ▐██████▌", "  ▌▌▌▌▌▌ "]
LIB = [" ▄▄▄▄▄▄ ", " █    █ ", " █▄▄▄▄█ "]
CLOUD_S = ["░░░░"]
SUN_S = ["▄██▄", "████", "▀██▀"]

# foreground strip (speed 1, length 192)
FG_LEN = 192
LANDMARKS = [
    (14, 'tree'), (38, 'arcade'), (60, 'tree_big'), (84, 'uni'),
    (116, 'house'), (140, 'tree'), (164, 'library'),
]
GRASS_XS = [3, 9, 22, 29, 45, 51, 68, 74, 92, 99, 108, 125, 133,
            148, 155, 172, 180, 187]

# mountains (speed 1/2, strip 96) and clouds/birds (speed 1/4, strip 48)
MT_LEN = 96
MOUNTS = [(8, 3), (24, 4), (46, 3), (64, 5), (84, 3)]
CL_LEN = 48
CLOUDS = [(6, 2), (30, 4)]
BIRDS = [(18, 3), (40, 5)]

STARS = [(5, 0), (20, 1), (36, 0), (52, 1), (63, 0), (12, 1), (70, 1)]

PEDAL = [
    ["   _o  ", " _ \\<,_", "( )/( )"],
    ["   _o  ", " _ \\<._", "( )/( )"],
]
SPOKES = ['*', '×', '+']


def draw_landmark(grid, kind, left, t):
    top_of = {'tree': 2, 'tree_big': 3, 'arcade': 4, 'uni': 3,
              'house': 3, 'library': 3}
    top = GROUND_ROW - top_of[kind]
    if kind == 'tree':
        blit(grid, top, left, TREE_S, TREE)
        put(grid, GROUND_ROW - 1, left + 1, '█', TRUNK)
    elif kind == 'tree_big':
        blit(grid, top, left, TREE_BIG, TREE)
        put(grid, GROUND_ROW - 1, left + 2, '█', TRUNK)
    elif kind == 'arcade':
        blit(grid, top, left, ARCADE_S, ARCADE)
        # tiny game playing on the screen
        px = (t // 3) % 3
        put(grid, top + 2, left + 1 + px, '·', ARCADE_GLOW)
        put(grid, top + 2, left + 3 - px, ':', ARCADE_GLOW)
    elif kind == 'uni':
        blit(grid, top, left, UNI, BUILD)
    elif kind == 'house':
        blit(grid, top - 1, left, HOUSE_ROOF, ROOF)
        blit(grid, top + 1, left, HOUSE_BODY, BUILD)
        beat = (t // 4) % 2
        put(grid, top - 2, left + 4, '♥', HEART if beat else HEART_DIM)
    elif kind == 'library':
        blit(grid, top, left, LIB, BUILD)
        for i in range(4):  # book spines in the window
            put(grid, top + 1, left + 2 + i, '▌', BOOKS[i])


def make_frame(t):
    grid = [[(' ', None)] * W for _ in range(H)]

    for i, (x, r) in enumerate(STARS):
        if (t // 6 + i) % 7:            # slow twinkle, mostly on
            put(grid, r, x, '.', STAR)

    cl_off = (t * 0.25) % CL_LEN
    for x, row in CLOUDS:
        sx = int(x - cl_off) % CL_LEN
        for rep in range(-1, W // CL_LEN + 2):
            blit(grid, row, sx + rep * CL_LEN, CLOUD_S, CLOUD)
    wing = 'v' if (t // 4) % 2 else 'w'
    for x, row in BIRDS:
        sx = int(x - cl_off) % CL_LEN
        for rep in range(-1, W // CL_LEN + 2):
            put(grid, row, sx + rep * CL_LEN, wing, BIRD)
            put(grid, row, sx + rep * CL_LEN + 3, wing, BIRD)

    blit(grid, 1, W - 12, SUN_S, SUN)   # after clouds: sun stays in front

    mt_off = (t * 0.5) % MT_LEN
    for x, h in MOUNTS:
        for rep in range(-1, W // MT_LEN + 2):
            base = int(x - mt_off) + rep * MT_LEN
            for i in range(h):
                row = GROUND_ROW - 1 - i
                half = h - i
                for c in range(base - half, base + half + 1):
                    if 0 <= c < W and 0 <= row < H and grid[row][c][0] == ' ':
                        grid[row][c] = ('▒', MOUNTAIN)

    fg_off = t % FG_LEN
    for x, kind in LANDMARKS:
        sx = (x - fg_off) % FG_LEN
        left = sx - FG_LEN // 2
        for rep in (0, 1):
            draw_landmark(grid, kind, left + rep * FG_LEN, t)

    grid[GROUND_ROW] = [('─', ROAD)] * W
    for gx in GRASS_XS:
        c = (gx - fg_off) % FG_LEN - FG_LEN // 2
        for rep in (0, 1):
            put(grid, GROUND_ROW + 1, c + rep * FG_LEN, ',', GRASS)
    for c in range(W):                   # lane dashes drift with the road
        if (c + fg_off) % 8 == 0:
            put(grid, GROUND_ROW + 1, c, '.', ROAD)

    # rider: clear a quiet box so the background never swallows them
    for r in range(GROUND_ROW - 4, GROUND_ROW):
        for c in range(RIDER_COL - 1, RIDER_COL + 8):
            if 0 <= r < H and 0 <= c < W:
                grid[r][c] = (' ', None)
    rider = PEDAL[(t // 2) % 2]
    blit(grid, GROUND_ROW - 3, RIDER_COL, rider, RIDER)
    spoke = SPOKES[(t // 2) % 3]
    put(grid, GROUND_ROW - 1, RIDER_COL + 1, spoke, RIDER)
    put(grid, GROUND_ROW - 1, RIDER_COL + 5, spoke, RIDER)

    label = 'sleipnir029'
    for i, ch in enumerate(label):
        grid[H - 1][W - len(label) - 2 + i] = (ch, LABEL)

    return grid


def build():
    return [make_frame(t) for t in range(N_FRAMES)]


if __name__ == '__main__':
    frames = build()
    write_txt_frames(frames, 'world')
    paths = render_gif(frames, 'variant_world', fg=RIDER, fps=FPS, scale=14,
                       width_chars=W, height_lines=H)
    print('built', *paths, sep='\n  ')
