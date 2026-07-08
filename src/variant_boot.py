"""Variant 2: CRT boot sequence — green phosphor terminal typing out the profile."""
import math
from render import render_gif, write_txt_frames

GREEN = (80, 255, 120)
W, H = 62, 13
TYPE_SPEED = 3          # chars per frame
HOLD_FRAMES = 28        # loop tail with blinking cursor
FPS = 9

SCRIPT = [
    "sleipnir029 :: profile v2.9",
    "",
    "> boot",
    "  loading games ............... ok",
    "  loading ai/automation ....... ok",
    "  cycling daemon .............. always running",
    "  family.core ................. ♥ mounted",
    "  peace.service ............... active",
    "",
    "> ",
]

TOTAL_CHARS = sum(len(l) for l in SCRIPT)


def frame_at(chars_shown: int, cursor_on: bool):
    lines, remaining = [], chars_shown
    cursor_row = cursor_col = None
    for line in SCRIPT:
        if remaining >= len(line):
            lines.append(line)
            remaining -= len(line)
            if remaining == 0:
                cursor_row, cursor_col = len(lines) - 1, len(line)
        else:
            lines.append(line[:remaining])
            cursor_row, cursor_col = len(lines) - 1, remaining
            remaining = 0
            break
    if cursor_on and cursor_row is not None:
        lines[cursor_row] = lines[cursor_row][:cursor_col] + '█'
    # top/left margin inside the char grid
    return [''] + ['  ' + l for l in lines]


def build():
    frames = []
    n_type = math.ceil(TOTAL_CHARS / TYPE_SPEED)
    for t in range(n_type):
        shown = min(TOTAL_CHARS, (t + 1) * TYPE_SPEED)
        flicker = 1.0 - 0.06 * ((t * 7) % 3 == 0)  # subtle CRT shimmer
        fg = tuple(int(c * flicker) for c in GREEN)
        frames.append((frame_at(shown, cursor_on=True), fg))
    for t in range(HOLD_FRAMES):
        cursor_on = (t // 4) % 2 == 0
        frames.append((frame_at(TOTAL_CHARS, cursor_on), GREEN))
    return frames


if __name__ == '__main__':
    frames = build()
    write_txt_frames(frames, 'boot')
    paths = render_gif(frames, 'variant_boot', fg=GREEN, fps=FPS, scale=20,
                       width_chars=W, height_lines=H)
    print('built', *paths, sep='\n  ')
