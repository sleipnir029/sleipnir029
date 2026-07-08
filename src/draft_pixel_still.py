"""Mockup: the bridge pause as 16-bit pixel art (dusk gradient, silhouettes)."""
import math, random
from PIL import Image

PW, PH = 185, 85
SCALE = 4
rng = random.Random(7)

# dusk-into-night gradient, top -> horizon
SKY = [(11, 13, 34), (19, 21, 56), (28, 30, 78), (42, 33, 88),
       (58, 42, 99), (88, 48, 107), (124, 58, 107), (163, 74, 98),
       (201, 95, 82), (232, 122, 74)]
HORIZON = 40
MOUNT_FAR = (13, 15, 40)
MOUNT_NEAR = (8, 9, 26)
BRIDGE = (235, 226, 200)
BRIDGE_DIM = (150, 140, 130)
MOON = (255, 238, 200)
WATER_TOP = (36, 26, 60)
WATER_BOT = (8, 8, 20)

img = Image.new('RGB', (PW, PH))
px = img.load()

def lerp(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))

# --- sky: banded gradient with checker dithering at each seam
for y in range(HORIZON + 1):
    f = y / HORIZON * (len(SKY) - 1)
    i, frac = int(f), f - int(f)
    for x in range(PW):
        j = min(i + 1, len(SKY) - 1)
        if frac < 0.35:
            c = SKY[i]
        elif frac > 0.65:
            c = SKY[j]
        else:
            c = SKY[j] if (x + y) % 2 else SKY[i]
        px[x, y] = c

# --- stars (upper sky only)
for _ in range(40):
    x, y = rng.randrange(PW), rng.randrange(22)
    if abs(x - 148) > 14 or abs(y - 11) > 10:
        px[x, y] = (200, 205, 225) if rng.random() < 0.7 else (255, 255, 255)

# --- moon: crescent with soft halo
MX, MY, MR = 148, 11, 7
for y in range(PH):
    for x in range(PW):
        d = math.hypot(x - MX, y - MY)
        d2 = math.hypot(x - (MX + 3), y - (MY - 1))
        if d < MR and d2 > MR - 1:
            px[x, y] = MOON
        elif d < MR + 4 and y <= HORIZON and d >= MR:
            if (x + y) % 2:
                px[x, y] = lerp(px[x, y], MOON, 0.12)

# --- mountains: two silhouette depths
def ridge(seed, base, amp):
    """Triangular peaks, not city blocks."""
    r = random.Random(seed)
    peaks = []
    x = -10
    while x < PW + 10:
        peaks.append((x, base - r.randint(amp // 2, amp)))
        x += r.randint(14, 26)
    ys = []
    for x in range(PW):
        y = base
        for pxx, pyy in peaks:
            slope_y = pyy + abs(x - pxx) * 2 // 3
            y = min(y, slope_y)
        ys.append(min(y, base))
    return ys

far = ridge(3, 34, 12)
near = ridge(9, 39, 8)
for x in range(PW):
    for y in range(far[x], HORIZON + 1):
        px[x, y] = MOUNT_FAR
    for y in range(near[x], HORIZON + 1):
        px[x, y] = MOUNT_NEAR

# --- water: vertical gradient + reflections
for y in range(HORIZON + 1, PH):
    f = (y - HORIZON) / (PH - HORIZON)
    row = lerp(WATER_TOP, WATER_BOT, f)
    for x in range(PW):
        px[x, y] = row
# sky-glow streaks on the water surface
for y in range(HORIZON + 1, HORIZON + 10):
    for x in range(PW):
        if rng.random() < 0.10 * (1 - (y - HORIZON) / 10):
            px[x, y] = lerp(px[x, y], SKY[-1], 0.5)

DECK = 37
TA, TB = 46, 140
TOWER_TOP = 10

# --- cables
def plot(x, y, c):
    if 0 <= x < PW and 0 <= y < PH:
        px[x, y] = c

mid, half = (TA + TB) / 2, (TB - TA) / 2
for x in range(TA, TB + 1):
    y = TOWER_TOP + (DECK - 6 - TOWER_TOP) * (1 - ((x - mid) / half) ** 2)
    plot(x, int(y), BRIDGE)
    if x % 8 == 4:
        for sy in range(int(y) + 1, DECK):
            plot(x, sy, BRIDGE_DIM)
for anchor, tower in ((2, TA), (PW - 3, TB)):
    n = abs(tower - anchor)
    for i in range(n):
        x = anchor + i if anchor < tower else anchor - i
        y = DECK - 1 - (DECK - 1 - TOWER_TOP) * (i / n) ** 2
        plot(x, int(y), BRIDGE)
        if i % 9 == 5:
            for sy in range(int(y) + 1, DECK):
                plot(x, sy, BRIDGE_DIM)

# --- towers + deck
for tx in (TA, TB):
    for y in range(TOWER_TOP - 2, DECK + 6):
        for dx in (-1, 0, 1):
            plot(tx + dx, y, BRIDGE if dx <= 0 else BRIDGE_DIM)
for x in range(PW):
    plot(x, DECK, BRIDGE)
    plot(x, DECK + 1, (60, 50, 70))
    if x % 4 == 0:
        plot(x, DECK - 1, BRIDGE_DIM)          # railing posts

# --- reflections in the water: towers, moon column
for tx in (TA, TB):
    for y in range(DECK + 6, PH):
        if (y + tx) % 3 != 0:
            wob = 1 if (y // 3) % 2 else -1
            for dx in (-1, 0, 1):
                plot(tx + dx + wob, y, lerp(px[min(max(tx + dx, 0), PW - 1), y], MOUNT_NEAR, 0.8))
for y in range(HORIZON + 2, PH):
    if y % 2:
        wob = int(math.sin(y * 0.8) * 2)
        plot(MX + wob, y, lerp(px[MX, y], MOON, 0.55))
        if y % 4 == 1:
            plot(MX + wob + 1, y, lerp(px[MX, y], MOON, 0.3))

# --- the rider: standing silhouette beside the bike, mid-span
SPRITE = [           # person left, bike right; # = solid silhouette
    "..##.........",
    "..##.........",
    "...#....#....",
    "..###...##...",
    "..#.#..#..#..",
    "..#.#..#####.",
    "..#.#.##.#.##",
    ".##.#.##.#.##",
]
sx, sy = 84, DECK - len(SPRITE)
DARK = (4, 4, 12)
for r, line in enumerate(SPRITE):
    for c, ch in enumerate(line):
        if ch == '#':
            plot(sx + c, sy + r, DARK)

out = img.resize((PW * SCALE, PH * SCALE), Image.NEAREST)
out.save('mock_pixel.png')
print('saved mock_pixel.png', out.size)
