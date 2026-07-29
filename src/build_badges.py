"""Regenerate the README link badges into assets/badge-*.svg.

Self-hosted on purpose: exact control of the palette, and these four never break
if a badge service goes down. Note the README also carries a komarev view counter,
which IS a third-party request -- counting needs a server and GitHub has none, so
that one cannot be self-hosted. These four can, so they are.

Style: near-black chip in Quench Core `bg`, label in `ink`, and the site's own
logo carrying the only saturated colour in the row. GitHub strips `style=` and
CSS from README SVG, so everything here is an inline `fill=` attribute and no
<style> block. `textLength` pins each label to an exact pixel width, so a font
fallback in GitHub's renderer cannot overflow the chip.

The website mark is the rzaman.site favicon's R, redrawn as a 2x pixel grid
rather than embedded as a nested base64 image (camo can strip nested <image>).

Brand glyphs are simple-icons paths (CC0), 24x24 viewBox scaled to 12x12.

    python3 src/build_badges.py
"""
import html
import pathlib

ASSETS = pathlib.Path(__file__).resolve().parents[1] / 'assets'

BG, INK = '#14131a', '#e8e6e3'
FONT = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'
CH, FS, H = 6.6, 11, 20

# The favicon's R, traced off /Users/.../faviconV2.png at its native 6x7. Drawn
# at 2x so it carries the same visual weight as the 12x12 brand glyphs.
R_GLYPH = [
    '#####.',
    '######',
    '##..##',
    '######',
    '#####.',
    '##.###',
    '##..##',
]
R_TEAL = '#55d5b8'   # sampled from the favicon

ICONS = {
    'itch': 'M3.13 1.338C2.08 1.96.02 4.328 0 4.95v1.03c0 1.303 1.22 2.45 2.325 2.45 1.33 0 2.436-1.102 2.436-2.41 0 1.308 1.07 2.41 2.4 2.41 1.328 0 2.362-1.102 2.362-2.41 0 1.308 1.137 2.41 2.466 2.41h.024c1.33 0 2.466-1.102 2.466-2.41 0 1.308 1.034 2.41 2.363 2.41 1.33 0 2.4-1.102 2.4-2.41 0 1.308 1.106 2.41 2.435 2.41C22.78 8.43 24 7.282 24 5.98V4.95c-.02-.62-2.082-2.99-3.13-3.612-3.253-.114-5.508-.134-8.87-.133-3.362 0-7.945.053-8.87.133zm6.376 6.477a2.74 2.74 0 0 1-.468.602c-.5.49-1.19.795-1.947.795a2.786 2.786 0 0 1-1.95-.795c-.182-.178-.32-.37-.446-.59-.127.222-.303.412-.486.59a2.788 2.788 0 0 1-1.95.795c-.092 0-.187-.025-.264-.052-.107 1.113-.152 2.176-.168 2.95v.005l-.006 1.167c.02 2.334-.23 7.564 1.03 8.85 1.952.454 5.545.662 9.15.663 3.605 0 7.198-.21 9.15-.664 1.26-1.284 1.01-6.514 1.03-8.848l-.006-1.167v-.004c-.016-.775-.06-1.838-.168-2.95-.077.026-.172.052-.263.052a2.788 2.788 0 0 1-1.95-.795c-.184-.178-.36-.368-.486-.59-.127.22-.265.412-.447.59a2.786 2.786 0 0 1-1.95.794c-.76 0-1.446-.303-1.948-.793a2.74 2.74 0 0 1-.468-.602 2.738 2.738 0 0 1-.463.602 2.787 2.787 0 0 1-1.95.794h-.16a2.787 2.787 0 0 1-1.95-.793 2.738 2.738 0 0 1-.464-.602zm-2.004 2.59v.002c.795.002 1.5 0 2.373.953.687-.072 1.406-.108 2.125-.107.72 0 1.438.035 2.125.107.873-.953 1.578-.95 2.372-.953.376 0 1.876 0 2.92 2.934l1.123 4.028c.832 2.995-.266 3.068-1.636 3.07-2.03-.075-3.156-1.55-3.156-3.025-1.124.184-2.436.276-3.748.277-1.312 0-2.624-.093-3.748-.277 0 1.475-1.125 2.95-3.156 3.026-1.37-.004-2.468-.077-1.636-3.072l1.122-4.027c1.045-2.934 2.545-2.934 2.92-2.934zM12 12.714c-.002.002-2.14 1.964-2.523 2.662l1.4-.056v1.22c0 .056.56.033 1.123.007.562.026 1.124.05 1.124-.008v-1.22l1.4.055C14.138 14.677 12 12.713 12 12.713z',
    'bsky': 'M5.202 2.857C7.954 4.922 10.913 9.11 12 11.358c1.087-2.247 4.046-6.436 6.798-8.501C20.783 1.366 24 .213 24 3.883c0 .732-.42 6.156-.667 7.037-.856 3.061-3.978 3.842-6.755 3.37 4.854.826 6.089 3.562 3.422 6.299-5.065 5.196-7.28-1.304-7.847-2.97-.104-.305-.152-.448-.153-.327 0-.121-.05.022-.153.327-.568 1.666-2.782 8.166-7.847 2.97-2.667-2.737-1.432-5.473 3.422-6.3-2.777.473-5.899-.308-6.755-3.369C.42 10.04 0 4.615 0 3.883c0-3.67 3.217-2.517 5.202-1.026',
    'lc': 'M13.483 0a1.374 1.374 0 0 0-.961.438L7.116 6.226l-3.854 4.126a5.266 5.266 0 0 0-1.209 2.104 5.35 5.35 0 0 0-.125.513 5.527 5.527 0 0 0 .062 2.362 5.83 5.83 0 0 0 .349 1.017 5.938 5.938 0 0 0 1.271 1.818l4.277 4.193.039.038c2.248 2.165 5.852 2.133 8.063-.074l2.396-2.392c.54-.54.54-1.414.003-1.955a1.378 1.378 0 0 0-1.951-.003l-2.396 2.392a3.021 3.021 0 0 1-4.205.038l-.02-.019-4.276-4.193c-.652-.64-.972-1.469-.948-2.263a2.68 2.68 0 0 1 .066-.523 2.545 2.545 0 0 1 .619-1.164L9.13 8.114c1.058-1.134 3.204-1.27 4.43-.278l3.501 2.831c.593.48 1.461.387 1.94-.207a1.384 1.384 0 0 0-.207-1.943l-3.5-2.831c-.8-.647-1.766-1.045-2.774-1.202l2.015-2.158A1.384 1.384 0 0 0 13.483 0zm-2.866 12.815a1.38 1.38 0 0 0-1.38 1.382 1.38 1.38 0 0 0 1.38 1.382H20.79a1.38 1.38 0 0 0 1.38-1.382 1.38 1.38 0 0 0-1.38-1.382z',
}


def r_mark(x0, y0, scale=2):
    """The favicon R as a grid of rects -- font-free and renderer-independent.

    6x7 source at scale 2 is 12x14, so the mark is one pixel taller than the
    12x12 brand glyphs and sits a pixel higher in the row. Left that way on
    purpose: dropping the bottom source row squares it up to 12x12 but takes the
    R's leg with it and the glyph stops reading as a letter.
    """
    out = []
    for ry, row in enumerate(R_GLYPH):
        for rx, ch in enumerate(row):
            if ch == '#':
                out.append(f'<rect x="{x0 + rx * scale}" y="{y0 + ry * scale}" '
                           f'width="{scale}" height="{scale}" fill="{R_TEAL}"/>')
    return ''.join(out)


def glyph(icon, colour):
    return (f'<g transform="translate(7 4) scale(0.5)">'
            f'<path fill="{colour}" d="{ICONS[icon]}"/></g>')


BADGES = [
    ('website',  'website',  r_mark(7, 3),               'website'),
    ('zeezbit',  'zeezbit',  glyph('itch', '#FA5C5C'),   'zeezbit on itch.io'),
    ('bluesky',  'bluesky',  glyph('bsky', '#0285FF'),   'bluesky'),
    ('leetcode', 'leetcode', glyph('lc',   '#FFA116'),   'leetcode'),
]


def build():
    ASSETS.mkdir(exist_ok=True)
    for name, label, mark, aria in BADGES:
        tw = round(len(label) * CH)
        w = 7 + 12 + 6 + tw + 8
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" '
            f'viewBox="0 0 {w} {H}" role="img" aria-label="{html.escape(aria)}">'
            f'<title>{html.escape(aria)}</title>'
            f'<rect width="{w}" height="{H}" fill="{BG}"/>{mark}'
            f'<text x="25" y="14" fill="{INK}" font-family="{FONT}" font-size="{FS}" '
            f'textLength="{tw}" lengthAdjust="spacingAndGlyphs">{html.escape(label)}</text></svg>'
        )
        # GitHub strips <style> and blocks external fetches in README SVG, and
        # the whole point of self-hosting is that these stay renderable. Cheap to
        # assert, so assert it rather than documenting it.
        assert '<style' not in svg and '<script' not in svg, name
        assert 'data:' not in svg and 'url(' not in svg, name
        assert svg.count('http') == 1, name          # the xmlns only
        p = ASSETS / f'badge-{name}.svg'
        p.write_text(svg)
        print(f'{p.name}  {w}x{H}')


if __name__ == '__main__':
    build()
