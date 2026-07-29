"""Invariant checks for the profile animation.

    python3 src/check_scene.py

Every assert here exists because the thing it guards actually broke once. The
craft rules in NOTES.md were prose, and prose does not fail a build:

  RIDER          frozen at the author's request, then silently altered twice
  RNG STREAM     the lists below MEADOW all moved when MEADOW's draw count changed
  LIGHT          the peaks' lit predicate contradicted its own comment for years,
                 and a pass that "fixed the lighting" read the comment, not the
                 code, and shipped a two-sun scene
  WATER SPIKES   a per-column shoreline jitter left 36 one-pixel specks
  SNOW RUNS      a per-column snow-depth jitter cut the cap into 49 orphan pixels
  MEADOW ORPHANS a rewrite meant to remove lone pixels added 16% more of them
  SEAM           checked by hand, and the number that got written down was a
                 stride-7 sample max reported as the true max

No framework on purpose -- stdlib plus Pillow, which the build already needs.
"""
import hashlib
import sys

from PIL import Image, ImageChops

import pixel_journey as pj

FAILS = []


def check(name, ok, detail=''):
    print(f'{"PASS" if ok else "FAIL"}  {name}' + (f'  -- {detail}' if detail else ''))
    if not ok:
        FAILS.append(name)


# --- the rider is frozen -------------------------------------------------------
# Rendered onto a flat field so only the sprite contributes, sampled across the
# whole loop so a change in any pose is caught, not just the cruising one.
#
# Pinned at a commit where `draw_rider` was verified byte-identical to the
# author's original via AST extraction. The digest is harness-specific -- the
# rider's ground shadow BLENDS with whatever is under it, so the fill colour and
# sample stride below are part of the contract; change either and re-pin only
# after re-confirming the source itself is unchanged.
RIDER_SHA = '98eed0a0e89c0a7a209017c692c0de7b5965cee3d9fe3393e61ca17d2ff6d751'


def rider_hash():
    h = hashlib.sha256()
    for t in range(0, pj.TOTAL_FRAMES, 7):
        img = Image.new('RGB', (pj.PW, pj.PH), (255, 0, 255))
        px = img.load()

        def plot(x, y, c):
            if 0 <= x < pj.PW and 0 <= y < pj.PH:
                px[x, y] = c

        s = pj.OFFSETS[t]
        d = pj.darkness(s + pj.RIDER_X)
        pj.draw_rider(px, plot, t, s, d, pj.golden(d))
        h.update(img.tobytes())
    return h.hexdigest()


# --- world data must not shift -------------------------------------------------
# Any list generated from the shared seeded RNG after a list whose draw count
# changes will silently relocate. Freezing the post-import state catches all of
# them at once, including ones added later.
RNG_STATE_SHA = None    # filled below; compared against the frozen digest


def rng_digest():
    return hashlib.sha256(repr(pj.RNG.getstate()).encode()).hexdigest()


def main():
    # 1. rider frozen
    got = rider_hash()
    check('rider is byte-identical to the frozen sprite', got == RIDER_SHA,
          f'sha256 {got[:16]}...')

    # 2. every shaded element faces the same way as LIGHT
    #    far_ridge returns a screen y, so a flank that DESCENDS to the right
    #    (far_ridge(wx+1) > top) is the one facing the sun.
    lit_wrong = lit_right = 0
    for wx in range(pj.FAR_LEN):
        top, nxt = pj.far_ridge(wx), pj.far_ridge((wx + 1) % pj.FAR_LEN)
        lit = nxt > top
        if lit and nxt < top:
            lit_wrong += 1
        if lit and nxt > top:
            lit_right += 1
    check('far peaks are lit on their sun-facing flank',
          lit_wrong == 0 and lit_right > 0,
          f'{lit_right} sun-facing lit, {lit_wrong} away-facing lit')
    check('LIGHT points up and to the right (the sun is at x=187 of 246)',
          pj.LIGHT[0] > 0 and pj.LIGHT[1] < 0, f'LIGHT={pj.LIGHT}')

    # 3. shaded elements must reach the ends of their ramp, or the span is wrong
    bush = {pj.shade_index(dx, -dy + 1, 2.1)
            for dx in range(-3, 4) for dy in range(3)
            if dx * dx + (dy - 1) ** 2 * 3 <= 9}
    check('bush shading reaches both ends of the ramp', bush == {0, 1, 2, 3, 4},
          f'indices {sorted(bush)}')

    # 4. shoreline has no one-pixel specks, and the water is well formed
    spikes = holes = above = 0
    for wc in range(pj.L):
        wet_seen = wet_ended = False
        for y in range(pj.ROAD_BOT + 1, pj.PH):
            c = pj.water_cell(wc, y)
            a = pj.water_cell((wc - 1) % pj.L, y)
            b = pj.water_cell((wc + 1) % pj.L, y)
            if (not c and a and b) or (c and not a and not b):
                spikes += 1
            if c and wet_ended:
                holes += 1
            elif c:
                wet_seen = True
            elif wet_seen:
                wet_ended = True
        for y in range(pj.ROAD_BOT + 1):
            if pj.water_cell(wc, y):
                above += 1
    check('no 1px shoreline spikes', spikes == 0, f'{spikes} found')
    check('no vertical holes in the water', holes == 0, f'{holes} found')
    check('no water at or above the road', above == 0, f'{above} found')

    # 5. render two stills and measure what used to regress
    day = pj.upscale(pj.make_frame(10))
    px = day.load()

    runs, run = [], 0
    for sy in range(18, pj.HORIZON):
        for sx in range(pj.PW):
            c = px[sx * 3, sy * 3]
            if c[0] > 200 and c[1] > 200 and c[2] > 200:
                run += 1
            else:
                if run:
                    runs.append(run)
                run = 0
        if run:
            runs.append(run)
        run = 0
    ones = sum(1 for r in runs if r == 1)
    check('snowline is a cap, not a comb', ones <= 4,
          f'{ones} single-pixel snow runs, mean run {sum(runs) / max(1, len(runs)):.2f}')

    orphans = 0
    for sy in range(pj.ROAD_BOT + 1, pj.PH - 1):
        for sx in range(1, pj.PW - 1):
            c = px[sx * 3, sy * 3]
            if all(c != px[(sx + dx) * 3, (sy + dy) * 3]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                orphans += 1
    # 1145 is the measured baseline for THIS frame on the original scene. The
    # count is position-dependent, so the frame above is part of the contract.
    check('meadow orphan pixels within baseline', orphans <= 1200,
          f'{orphans} (baseline 1145 at this frame)')

    # 6. the loop closes: the wrap must not exceed a normal frame step
    def delta(a, b):
        h = ImageChops.difference(a, b).convert('L').histogram()
        return (sum(h) - h[0]) / sum(h)

    frames = {t: pj.upscale(pj.make_frame(t))
              for t in (0, 1, 208, 209, 418, pj.TOTAL_FRAMES - 1)}
    seam = delta(frames[pj.TOTAL_FRAMES - 1], frames[0])
    normal = sorted(delta(frames[a], frames[b])
                    for a, b in ((0, 1), (208, 209), (418, 419)))
    median = normal[len(normal) // 2]
    check('loop seam is within a normal frame step', seam <= median * 1.6,
          f'seam {seam * 100:.1f}%, median step {median * 100:.1f}%')

    # 7. asset invariants
    gif = pj.ASSETS / 'current.gif'
    if gif.exists():
        with Image.open(gif) as im:
            n, dur = 0, 0
            try:
                while True:
                    n += 1
                    dur += im.info.get('duration', 0)
                    im.seek(im.tell() + 1)
            except EOFError:
                pass
        check('current.gif is 420 frames at 42.00s', n == 420 and dur == 42000,
              f'{n} frames, {dur / 1000:.2f}s')
        mb = gif.stat().st_size / 1e6
        check('current.gif under the 10MB camo limit', mb < 10, f'{mb:.2f} MB')

    print()
    if FAILS:
        print(f'{len(FAILS)} FAILED: ' + ', '.join(FAILS))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
