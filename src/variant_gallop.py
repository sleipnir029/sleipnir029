"""Variant 1: Sleipnir gallop — eight-legged block-silhouette horse under stars."""
from render import render_gif, write_txt_frames, get_font, ASSETS
from PIL import Image, ImageDraw

FG = (235, 235, 235)
W, H = 78, 17
FPS = 8
N_CYCLES = 4

# Body silhouette, facing left. Legs are drawn procedurally below it.
# Rows 0..8; leg rows are 9..12; ground row 13.
BODY = [
    "  # #                                    ",
    "  ###                                    ",
    "#####                                    ",
    "  #####                                  ",
    "   ######                        ##      ",
    "    ##########################  ####     ",
    "    ############################ ##      ",
    "     ##########################%##       ",
    "      ########################           ",
]

# 8 legs: 4 front (attach col, near chest) + 4 hind. Each pose gives every
# leg a horizontal drift per row (in chars); legs are 4 rows long.
FRONT_ATTACH = [7, 9, 11, 13]
HIND_ATTACH = [23, 25, 27, 29]

POSES = [
    # (front drifts, hind drifts) — one drift value per leg, applied per row
    ([-0.9, -0.6, -0.4, -0.1], [0.9, 0.6, 0.4, 0.1]),   # extended (flight)
    ([-0.3, -0.1, 0.1, 0.3],   [0.3, 0.1, -0.1, -0.3]), # passing vertical
    ([0.5, 0.3, 0.1, -0.1],    [-0.5, -0.3, -0.1, 0.1]),# gathered (tucked)
    ([-0.1, 0.1, 0.3, 0.5],    [0.1, -0.1, -0.3, -0.5]),# passing (other phase)
]

LEG_ROWS = 4
STARS = [(3, 2), (14, 1), (26, 3), (38, 1), (49, 2), (60, 1), (71, 3),
         (8, 4), (33, 0), (55, 4), (66, 2), (20, 5), (44, 5), (74, 0)]
GROUND_ROW = 14
HORSE_COL = 20


def draw_legs(grid, top_row, pose_i, bob):
    front, hind = POSES[pose_i]
    for attaches, drifts in ((FRONT_ATTACH, front), (HIND_ATTACH, hind)):
        for attach, drift in zip(attaches, drifts):
            x = float(attach)
            # legs always end just above the ground row, whatever the bob
            rows = GROUND_ROW - top_row
            for r in range(rows):
                row = top_row + r
                col = HORSE_COL + int(round(x))
                if 0 <= row < H and 0 <= col < W:
                    grid[row][col] = '#'
                x += drift * (LEG_ROWS / rows)


def make_frame(t):
    grid = [[' '] * W for _ in range(H)]

    for i, (x, y) in enumerate(STARS):
        phase = (t + i * 3) % 8
        ch = '*' if phase < 2 else ('.' if phase < 6 else '+')
        if phase == 7:
            ch = ' '
        grid[y][x] = ch

    pose = t % 4
    bob = 1 if pose in (1, 3) else 0   # body drops when legs pass under
    body_top = GROUND_ROW - LEG_ROWS - len(BODY) + bob
    for r, line in enumerate(BODY):
        row = body_top + r
        if 0 <= row < H:
            for c, ch in enumerate(line):
                col = HORSE_COL + c
                if ch != ' ' and 0 <= col < W:
                    grid[row][col] = ch
    draw_legs(grid, body_top + len(BODY), pose, bob)

    shift = (t * 3) % W
    ground = ['_'] * W
    for gx in (5, 19, 31, 47, 58, 70):
        ground[(gx + shift) % W] = ','
    grid[GROUND_ROW] = ground

    label = 'sleipnir029'
    for i, c in enumerate(label):
        grid[H - 1][W - len(label) - 2 + i] = c

    return [''.join(r).replace('#', '█').replace('%', '▓') for r in grid]


def build():
    return [make_frame(t) for t in range(N_CYCLES * 4)]


def contact_sheet():
    frames = [make_frame(t) for t in range(4)]
    font = get_font(14)
    bbox = font.getbbox('M')
    cw, chh = bbox[2] - bbox[0], bbox[3] - bbox[1] + 4
    img = Image.new('RGB', (W * cw + 20, (H * chh + 10) * 4 + 20), (0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 10
    for f in frames:
        for line in f:
            d.text((10, y), line, font=font, fill=FG)
            y += chh
        y += 10
    p = ASSETS / 'gallop_sheet.png'
    img.save(p)
    print('sheet:', p)


if __name__ == '__main__':
    import sys
    if '--sheet' in sys.argv:
        contact_sheet()
    else:
        frames = build()
        write_txt_frames(frames, 'gallop')
        paths = render_gif(frames, 'variant_gallop', fg=FG, fps=FPS, scale=16,
                           width_chars=W, height_lines=H)
        print('built', *paths, sep='\n  ')
