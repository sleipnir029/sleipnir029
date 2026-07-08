"""Mockup: the bridge pause as ANSI textmode art (shade blocks + color)."""
import math, random, sys
sys.path.insert(0, '/Users/rakibuzzamanrahat/Downloads/ascii_profile_draft/src')
from render import get_font
from PIL import Image, ImageDraw

W, H = 100, 30
rng = random.Random(7)

SKY = [(14, 16, 42), (22, 24, 60), (34, 34, 86), (54, 42, 108),
       (82, 54, 124), (122, 66, 130), (168, 82, 122), (208, 100, 104),
       (238, 126, 88), (252, 152, 84)]
HORIZON = 12
MOUNT = (16, 17, 44)
MOUNT_DK = (10, 11, 30)
BRIDGE = (238, 230, 205)
BRIDGE_DIM = (150, 140, 130)
MOON = (255, 238, 200)
DARK = (5, 5, 14)

grid = [[(' ', None)] for _ in range(H)]
grid = [[(' ', None)] * W for _ in range(H)]

def put(r, c, ch, col):
    if 0 <= r < H and 0 <= c < W:
        grid[r][c] = (ch, col)

def lerp(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))

# --- sky: colored shade-block bands, dithered at seams
for r in range(HORIZON):
    f = r / (HORIZON - 1) * (len(SKY) - 1)
    i, frac = int(f), f - int(f)
    j = min(i + 1, len(SKY) - 1)
    for c in range(W):
        col = SKY[j] if (frac > 0.5) == ((c + r) % 2 == 0) else SKY[i]
        ch = ' ' if r < 4 else ('░' if r < 8 else '▒')
        if r >= 10:
            ch = '▓'
        put(r, c, ch if ch != ' ' else ' ', col)
        if ch == ' ':
            grid[r][c] = (' ', None)

# stars in the dark upper sky
for x, r, ch in [(6,1,'·'),(17,2,'+'),(29,0,'·'),(40,2,'·'),(52,1,'*'),
                 (63,3,'·'),(9,4,'·'),(47,4,'+'),(70,0,'·'),(33,3,'·'),
                 (57,5,'·'),(13,5,'*')]:
    put(r, x, ch, (200, 205, 225))

# --- moon: blocky crescent
MC, MR_ROW = 86, 3
for r in range(H):
    for c in range(W):
        d = math.hypot((c - MC) * 0.55, r - MR_ROW)
        d2 = math.hypot((c - MC - 2.6) * 0.55, r - MR_ROW + 0.4)
        if d < 2.5 and d2 > 2.2:
            put(r, c, '█', MOON)

# --- mountains: shade-block silhouette
peaks = [(-5, 5), (14, 3), (30, 5), (46, 4), (62, 5), (78, 3), (95, 5), (108, 4)]
def ridge_row(c):
    y = HORIZON
    for pxx, h in peaks:
        y = min(y, HORIZON - h + abs(c - pxx) // 3)
    return max(y, 8)
for c in range(W):
    top = ridge_row(c)
    for r in range(top, HORIZON + 1):
        put(r, c, '▓' if r == top else '█', MOUNT if r <= top + 1 else MOUNT_DK)

DECK = 17
TA, TB = 26, 76
TOWER_TOP = 5

# --- cables
mid, half = (TA + TB) / 2, (TB - TA) / 2
pts = []
for x in range(TA + 1, TB):
    y = TOWER_TOP + ((DECK - 3) - TOWER_TOP) * (1 - ((x - mid) / half) ** 2)
    pts.append((x, y))
ipts = [(x, int(round(y))) for x, y in pts]
for k, (x, ry) in enumerate(ipts):
    nxt = ipts[k + 1][1] if k + 1 < len(ipts) else ry
    put(ry, x, '\\' if nxt > ry else ('/' if nxt < ry else '_'), BRIDGE)
    if x % 7 == 3:
        for sr in range(ry + 1, DECK):
            put(sr, x, ':', BRIDGE_DIM)
for anchor, tower in ((1, TA), (W - 2, TB)):
    n = abs(tower - anchor)
    step = 1 if anchor < tower else -1
    spts = []
    for i in range(1, n):
        x = anchor + i * step
        y = TOWER_TOP + (DECK - 1 - TOWER_TOP) * (1 - i / n) ** 2
        spts.append((x, int(round(y))))
    if step < 0:
        spts.reverse()
    for k, (x, ry) in enumerate(spts):
        nxt = spts[k + 1][1] if k + 1 < len(spts) else ry
        put(ry, x, '\\' if nxt > ry else ('/' if nxt < ry else '_'), BRIDGE)

# --- towers + deck
for tx in (TA, TB):
    for r in range(TOWER_TOP - 1, DECK):
        put(r, tx - 1, '▐', BRIDGE)
        put(r, tx, ' ', None)
        put(r, tx + 1, '▌', BRIDGE_DIM)
    put(TOWER_TOP - 2, tx - 1, '▄', BRIDGE)
    put(TOWER_TOP - 2, tx, '▄', BRIDGE)
    put(TOWER_TOP - 2, tx + 1, '▄', BRIDGE)
for c in range(W):
    put(DECK, c, '▄', BRIDGE)
    put(DECK + 1, c, '▀', (70, 60, 80))
    if c % 4 == 0:
        put(DECK - 1, c, '¦', BRIDGE_DIM)

# --- water: gradient shade rows with reflections
for r in range(DECK + 2, H):
    f = (r - DECK - 2) / (H - DECK - 2)
    base = lerp((72, 48, 96), (10, 10, 24), f)
    for c in range(W):
        roll = rng.random()
        if roll < 0.55 * (1 - f) + 0.15:
            ch = '▒' if roll < 0.2 else '░'
            put(r, c, ch, base)
# warm horizon streaks on the surface
for r in range(DECK + 2, DECK + 4):
    for c in range(W):
        if rng.random() < 0.18:
            put(r, c, '▒', lerp((72, 48, 96), SKY[-1], 0.7))
# tower reflections
for tx in (TA, TB):
    for r in range(DECK + 2, H):
        if (r + tx) % 3:
            wob = 1 if (r // 2) % 2 else -1
            put(r, tx + wob, '█', MOUNT_DK)
# moon reflection column
for r in range(DECK + 2, H):
    if r % 2 == 0:
        wob = int(math.sin(r * 0.9) * 1.5)
        put(r, MC + wob, '▒', lerp((72, 48, 96), MOON, 0.6))

# --- rider: dark silhouette, standing beside the bike mid-span
put(DECK - 3, 48, '█', DARK)                 # head+torso
put(DECK - 2, 48, '█', DARK)
put(DECK - 2, 47, '▐', DARK)
put(DECK - 2, 52, '▄', DARK)                 # handlebar
put(DECK - 1, 48, '▙', DARK)                 # legs
put(DECK - 1, 51, '▟', DARK)                 # bike frame
put(DECK - 1, 52, '█', DARK)
put(DECK - 1, 53, '▛', DARK)

label = 'sleipnir029'
for i, ch in enumerate(label):
    put(H - 1, W - len(label) - 2 + i, ch, (110, 100, 120))

# --- render
font = get_font(12)
bbox = font.getbbox('M')
cw, chh = bbox[2] - bbox[0], bbox[3] - bbox[1] + 1
img = Image.new('RGB', (W * cw + 24, H * chh + 24), (6, 6, 14))
dr = ImageDraw.Draw(img)
for r in range(H):
    for c in range(W):
        ch, col = grid[r][c]
        if ch != ' ' and col:
            dr.text((12 + c * cw, 12 + r * chh), ch, font=font, fill=col)
img.save('mock_ansi.png')
print('saved mock_ansi.png', img.size)
