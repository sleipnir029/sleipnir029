"""Shared ASCII-frame -> GIF/WebP/PNG renderer.

A frame is a list of lines. A line is either a plain str (drawn in the
frame's fg color) or a list of (char, rgb) cells for per-char color.
A frame may also be a (lines, fg_override) tuple for per-frame brightness
effects (CRT flicker etc.).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FRAMES_DIR = ROOT / 'src' / 'frames'
ASSETS.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    '/System/Library/Fonts/Menlo.ttc',
    '/System/Library/Fonts/SFNSMono.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf',
]


def get_font(size: int) -> ImageFont.FreeTypeFont:
    for c in FONT_CANDIDATES:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def _line_text(line) -> str:
    return line if isinstance(line, str) else ''.join(ch for ch, _ in line)


def write_txt_frames(frames, name: str) -> None:
    d = FRAMES_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    for t, frame in enumerate(frames):
        lines = frame[0] if isinstance(frame, tuple) else frame
        (d / f'{t:03d}.txt').write_text(
            '\n'.join(_line_text(l) for l in lines), encoding='utf-8')


def render_gif(frames, name: str, fg=(235, 235, 235), bg=(0, 0, 0),
               fps: int = 10, scale: int = 16, pad: int = 20,
               width_chars: int = 96, height_lines: int = 28):
    font = get_font(scale)
    bbox = font.getbbox('M')
    cw = bbox[2] - bbox[0]
    ch = bbox[3] - bbox[1] + 1  # tight leading so block glyphs stack solid
    width = width_chars * cw + 2 * pad
    height = height_lines * ch + 2 * pad
    images = []
    for frame in frames:
        lines, frame_fg = frame if isinstance(frame, tuple) else (frame, fg)
        img = Image.new('RGB', (width, height), bg)
        draw = ImageDraw.Draw(img)
        y = pad
        for line in lines[:height_lines]:
            if isinstance(line, str):
                draw.text((pad, y), line[:width_chars], font=font, fill=frame_fg)
            else:
                for i, (c, col) in enumerate(line[:width_chars]):
                    if c != ' ':
                        draw.text((pad + i * cw, y), c, font=font,
                                  fill=col or frame_fg)
            y += ch
        images.append(img)
    gif = ASSETS / f'{name}.gif'
    webp = ASSETS / f'{name}.webp'
    png = ASSETS / f'{name}_poster.png'
    dur = int(1000 / fps)
    images[0].save(gif, save_all=True, append_images=images[1:],
                   duration=dur, loop=0, disposal=2, optimize=True)
    images[0].save(webp, save_all=True, append_images=images[1:],
                   duration=dur, loop=0, lossless=True)
    images[len(images) // 2].save(png)
    return gif, webp, png
