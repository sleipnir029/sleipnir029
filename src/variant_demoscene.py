"""Variant 4: demoscene resolve — green ASCII rain settles into 'sleipnir029'."""
import random
from render import render_gif, write_txt_frames

GREEN = (80, 255, 120)
DIM = (30, 120, 55)
W, H = 64, 15
FPS = 8
RESOLVE, HOLD, DISSOLVE = 16, 18, 10
RAIN_CHARS = '01.:+*|/\\<>~'

FONT = {  # 5-row mini block font, only the glyphs we need
    's': ['###', '#  ', '###', '  #', '###'],
    'l': ['#  ', '#  ', '#  ', '#  ', '###'],
    'e': ['###', '#  ', '## ', '#  ', '###'],
    'i': ['#', '#', '#', '#', '#'],
    'p': ['###', '# #', '###', '#  ', '#  '],
    'n': ['###', '# #', '# #', '# #', '# #'],
    'r': ['## ', '# #', '## ', '# #', '# #'],
    '0': ['###', '# #', '# #', '# #', '###'],
    '2': ['###', '  #', '###', '#  ', '###'],
    '9': ['###', '# #', '###', '  #', '###'],
}

NAME = 'sleipnir029'


def name_cells():
    rows = 5
    cols = []
    text_rows = ['' for _ in range(rows)]
    for chn in NAME:
        g = FONT[chn]
        for r in range(rows):
            text_rows[r] += g[r] + ' '
    width = len(text_rows[0])
    top = (H - rows) // 2
    left = (W - width) // 2
    cells = {}
    for r in range(rows):
        for c, chh in enumerate(text_rows[r]):
            if chh == '#':
                cells[(top + r, left + c)] = True
    return cells


def build():
    rng = random.Random(29)
    mask = name_cells()
    lock = {cell: rng.randint(3, RESOLVE - 1) for cell in mask}
    unlock = {cell: rng.randint(1, DISSOLVE - 2) for cell in mask}
    total = RESOLVE + HOLD + DISSOLVE
    frames = []
    for t in range(total):
        grid = [[(' ', None)] * W for _ in range(H)]
        if t < RESOLVE:
            rain_p = 0.28 * (1 - t / RESOLVE)
            for r in range(H):
                for c in range(W):
                    if (r, c) in mask:
                        if t >= lock[(r, c)]:
                            grid[r][c] = ('█', GREEN)
                        elif rng.random() < 0.5:
                            grid[r][c] = (rng.choice(RAIN_CHARS), DIM)
                    elif rng.random() < rain_p:
                        grid[r][c] = (rng.choice(RAIN_CHARS), DIM)
        elif t < RESOLVE + HOLD:
            for (r, c) in mask:
                grid[r][c] = ('█', GREEN)
            # occasional soft shimmer pixel off to the side
            for _ in range(3):
                r, c = rng.randrange(H), rng.randrange(W)
                if (r, c) not in mask:
                    grid[r][c] = ('.', DIM)
        else:
            td = t - RESOLVE - HOLD
            rain_p = 0.22 * (td / DISSOLVE)
            for (r, c) in mask:
                if td < unlock[(r, c)]:
                    grid[r][c] = ('█', GREEN)
                elif rng.random() < 0.4:
                    grid[r][c] = (rng.choice(RAIN_CHARS), DIM)
            for r in range(H):
                for c in range(W):
                    if (r, c) not in mask and rng.random() < rain_p:
                        grid[r][c] = (rng.choice(RAIN_CHARS), DIM)
        frames.append([row[:] for row in grid])
    return frames


if __name__ == '__main__':
    frames = build()
    write_txt_frames(frames, 'demoscene')
    paths = render_gif(frames, 'variant_demoscene', fg=GREEN, fps=FPS,
                       scale=18, width_chars=W, height_lines=H)
    print('built', *paths, sep='\n  ')
