from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(__file__).resolve().parents[1]
ASSETS = OUT / 'assets'
FRAMES_DIR = OUT / 'src' / 'frames'
ASSETS.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

WIDTH_CHARS = 96
HEIGHT_LINES = 28
SCALE = 18
BG = (0, 0, 0)
FG = (235, 235, 235)
FPS = 10
N_FRAMES = 28

# A calm, cinematic ASCII horse with slight motion controls.
BASE = [
"",
"",
"",
"                           .-.                                                ",
"                          /   \\                                               ",
"                 .--''''-;     ;-.                                             ",
"               .'      _/  ^ ^   _\\_                                          ",
"              /      .' |   .-. (o o)                                          ",
"             ;      /   |  /   \\ \\_/                                          ",
"             |     ;    | |     |  \\\\      __                                  ",
"             ;     |    | |     |   \\\\_.-''  `-.                               ",
"              \\    |    | |     |    /  _  _    \\                              ",
"               `-._;    |_|_____|__ /  / \\/ \\    ;                             ",
"                   /            /  \\  \\      /    |                            ",
"                  /   .----.   /    `-._`-..-'    /                             ",
"            _..--'   /      `-'          `-.__.-'                               ",
"         .-'        /                                                           ",
"       .'        _.'                                                            ",
"      /        .'                                                               ",
"     ;       .'                                                                 ",
"     |      /                         _                                         ",
"     ;     ;                        _/ )                                        ",
"      \\    |                    __/  /                                          ",
"       ;   ;               __.--' /  /                                          ",
"       |   |              /_.-._.'  /                                           ",
"       |   |               / / /   /                                            ",
"       /___;              /_/ /___/                                             ",
"",
]


def ensure_size(lines):
    out = []
    for i in range(HEIGHT_LINES):
        s = lines[i] if i < len(lines) else ""
        out.append(s.ljust(WIDTH_CHARS)[:WIDTH_CHARS])
    return out


def overlay(lines, row, col, text):
    lines = lines[:]
    if 0 <= row < len(lines):
        base = list(lines[row])
        for i, ch in enumerate(text):
            j = col + i
            if 0 <= j < len(base):
                base[j] = ch
        lines[row] = ''.join(base)
    return lines


def make_frame(t):
    breathe = (math.sin((t / N_FRAMES) * 2 * math.pi) + 1) / 2
    blink = t in {10, 11}
    ear_flick = t in {6, 7, 8}
    tail_sway = math.sin((t / N_FRAMES) * 2 * math.pi + math.pi/3)

    lines = BASE[:]

    if blink:
        lines[7] = lines[7].replace('(o o)', '(- -)')

    if ear_flick:
        lines[6] = lines[6].replace('^ ^', '^ ~')

    if breathe > 0.66:
        lines[10] = lines[10].replace('   \\\\_.-', '    \\\\_.-')
        lines[13] = lines[13].replace('/  \\\\  \\\\', '/  \\\\   \\\\')
    elif breathe < 0.33:
        lines[10] = lines[10].replace('   \\\\_.-', '  \\\\_.-')
        lines[13] = lines[13].replace('/  \\\\  \\\\', '/  \\\\ \\\\')

    if tail_sway > 0.35:
        lines[16] = "         .-'        /~                                                          "
        lines[17] = "       .'        _.''                                                           "
    elif tail_sway < -0.35:
        lines[16] = "         .-'        /                                                           "
        lines[17] = "       .'        _.`                                                            "

    lines = ensure_size(lines)
    lines = overlay(lines, 1, 27, 'ASCII MOTION STUDY')
    return lines


def render_txt_frames():
    frames = []
    for t in range(N_FRAMES):
        lines = make_frame(t)
        txt = '\n'.join(lines)
        (FRAMES_DIR / f'{t:03d}.txt').write_text(txt, encoding='utf-8')
        frames.append(lines)
    return frames


def get_font():
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf',
    ]
    for c in candidates:
        p = Path(c)
        if p.exists():
            return ImageFont.truetype(str(p), SCALE)
    return ImageFont.load_default()


def render_gif(frames):
    font = get_font()
    bbox = font.getbbox('M')
    cw = bbox[2] - bbox[0]
    ch = bbox[3] - bbox[1] + 4
    width = WIDTH_CHARS * cw + 40
    height = HEIGHT_LINES * ch + 40
    images = []
    for lines in frames:
        img = Image.new('RGB', (width, height), BG)
        draw = ImageDraw.Draw(img)
        y = 20
        for line in lines:
            draw.text((20, y), line, font=font, fill=FG)
            y += ch
        images.append(img)
    gif_path = ASSETS / 'current.gif'
    webp_path = ASSETS / 'current.webp'
    png_path = ASSETS / 'poster.png'
    images[0].save(gif_path, save_all=True, append_images=images[1:], duration=int(1000/FPS), loop=0, disposal=2)
    images[0].save(webp_path, save_all=True, append_images=images[1:], duration=int(1000/FPS), loop=0, lossless=True)
    images[0].save(png_path)
    return gif_path, webp_path, png_path


if __name__ == '__main__':
    frames = render_txt_frames()
    render_gif(frames)
    print('Built animation assets in', ASSETS)
