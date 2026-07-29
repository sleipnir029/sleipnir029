# ASCII Profile Draft

Retro animated header for the GitHub profile README: **one day on the
road** — 16-bit pixel art (~42 s loop, 5.1 MB, 420 frames @ 10 fps,
246x113 canvas at x3 nearest-neighbor; canvas was enlarged from 185x85
because the rider didn't read in daylight at the smaller size). Route: morning fields (rabbit
bolts as you near) -> lake with sun glints -> pine forest -> golden hour
-> the suspension bridge at night (stop, breathe, a star falls, an owl
watches from the tower, fireflies drift) -> dawn mist -> morning again.

## Build

```bash
python3 src/build_animation.py     # renders assets/current.gif (+webp, poster)
python3 src/check_scene.py         # invariant checks -- run after any scene edit
python3 src/build_badges.py        # regenerates assets/badge-*.svg
```

`check_scene.py` exists because every rule below was prose, and prose does not
fail a build. Each assert in it guards something that actually broke once.

## Layout

- `src/pixel_journey.py` — the production scene (pixel art).
  `--still <s> ...` renders stills at world positions.
- Drafts kept for history / future restyling:
  `src/journey_scene.py` (ASCII journey, previous production cut),
  `src/ride_scene.py` (static ASCII night bridge),
  `src/draft_ansi_still.py`, `src/draft_pixel_still.py` (style mockups),
  `src/variant_*.py` (first-round concepts), `src/render.py` (ASCII
  renderer used by the drafts)

## Craft notes (learned the hard way)

- Scene-first: design elements separately, compose a still, then animate.
- Line-art vocabulary from jgs/classic archives (asciiart.eu): ridges
  `_/ \_` with `^`, water rows mixing `~ ^ - _` with density fading by
  depth, cables as continuous runs (`\`, `/`, `_` by row step).
- Parallax without masking: layers are sparse dicts blitted back-to-front
  with transparent spaces — never clear a box around an actor.
- Lighting = f(world position), not time: the loop seam closes itself.
  Strip lengths: fg 360 (1x), hills/clouds 180 (0.5x), mountains 90
  (0.25x) — each divides total scroll distance so all layers tile.
  Anything time-driven that's visible at the wrap (clouds!) must live on
  a tiling strip too, or it jumps at the loop seam.
- ASCII depth is luminance, not detail: background faint, structure bright.
- Motion on a char grid: always exactly 1 col/frame when moving; get
  speed from FPS, never from step size (fractional steps round unevenly
  and read as dropped frames). Ease by dwell — hold a column 2-4 frames.
- Fill the canvas: a density-gradient meadow below the road keeps the
  scene a landscape instead of a thin horizontal band. Water bodies get
  shaped floors and sloped banks, never rectangles.
- Size budget: quality wins; ~5 MB is fine (GitHub camo allows 10 MB).
- The rider is a colored sprite (helmet/jersey/skin/bike palettes that
  shift moonlit at night) — a silhouette vanishes against day greens.
- NO visible breath/exhaust on the standing rider — puffs read as
  smoking. Breathing = shoulder rise only; ambient life comes from wind
  (drifting flecks, swaying reeds, jersey flutter).
- GIFs must use ONE global palette (sampled frames + pinned swatches for
  rider/accent colors). Per-frame adaptive palettes drop small color
  regions — the red jersey flickered to random colors.
- Review the ACTUAL rendered frames (extract every ~30th) before calling
  a pass done — stills at hand-picked positions miss composition bugs
  (a cloud once parked exactly on a tower top through the whole pause).
- Pixel art: sky gradients banded with checker dither; silhouettes carry
  depth; every row of the canvas must be painted (watch gaps between
  layer bands); golden-hour = warm push on all layer palettes.

## Craft notes — round two (bug fixes and the scenery pass)

- **A written craft rule decays at the branch you weren't looking at.**
  `water_cell` had two water bodies. The lake got sloped banks via a per-row
  `inset`; the river under the bridge just `return True`d, so it was a
  hard-walled rectangle to the canvas floor — the exact thing the rule above
  forbids. Fix was four lines. The lesson is the duplication: the bank *pixels*
  re-derived the same geometry in a second place, which is how they drifted.
  The bank pass now asks water_cell "is this land next to water?" and cannot
  disagree with it.
- **At ~10 px a figure has no room for a value ramp, and trying is a regression.**
  The rider is ~10x11 px of human. Two attempts to "draw it properly" failed:
  a 1px selout rim was just an outline, not art; and a full redraw with
  hue-shifted ramps, one committed light and 34 px instead of 23 read *worse*
  than the flat original and was thrown away. Why it failed is measurable — the
  highlight `#ff9c72` has luminance 180 and the road is 173, and the mid step
  135 sits between sky 145 and ground 129, so most of the jersey landed inside
  the background's own value band. The flat `#d64036` works because it is a
  large solid block of high chroma, and saturation separates where value cannot.
  Spreading it over four values shrank the one saturated note into four paler
  pieces. Ramps need room; spend the art budget on elements 20-60 px across.
- **Read the code, not the comment — especially your own.** The sun sits at
  x=187 of 246, so light comes from the upper RIGHT. Every element was lit from
  the upper LEFT: peaks, leafy crowns, pines. The world was self-consistent and
  merely disagreed with its own sun. But `far_ridge` returns a screen y, so
  `far_ridge(wx+1) < top_y` is the flank that RISES to the right and therefore
  faces left — under a comment that said "right-descending = lit edge". Trusting
  that comment produced a diagnosis of "two different suns", a fix applied only
  to the plants, and an actual two-sun scene where there had been one. Measure the
  predicate: sweep the strip and count lit columns per flank direction.
- **A five-step ramp on a ten-pixel form is banding, not shading.** Shading the
  whole tree crown from one origin gave five parallel equal-width diagonal
  stripes across all three lobes — the textbook pseudo-gradient — and the lobes
  bought silhouette variety with zero volume. Shading each lobe from ITS OWN
  centre makes each mass round. Same lesson as the rider: ramps need room, and
  the unit that gets the ramp has to be the unit that has the room.
- **Jitter the shape, never the thickness.** A per-column +/-1 on snow DEPTH cut
  the cap into a comb: snow runs went 52 -> 99, mean length 4.73 -> 2.11, with 49
  single-pixel runs, and the mountain band's frame-to-frame delta rose 47% so the
  ridge sparkled. A per-column jitter on the shoreline INSET did the same in
  plan: 18 land nubs stranded in the river and 18 water nubs in the land, each
  painted bank-colour and world-keyed so they never moved. Both were reverted.
  If an edge only moves a pixel every other row, a per-column wobble is
  guaranteed to produce orphans; bake the mask and de-speckle it, or jitter over
  a run of several columns so the result is a shape.
- **Contrast survives quantization; small deltas do not.** A fourth cloud step
  11/7/2 RGB from its neighbour collapsed to the same palette entry in daylight,
  so it existed in the source and not in the GIF. And the cloud's darkest step
  sat ~17 luminance above the sky at the cloud's own altitude, which is invisible
  — white pixels dropped 46 -> 18 and the cloud lost its figure-ground read.
  Check ramps against the QUANTIZED output and against the background they
  actually sit on, not against the palette table.
- **A rim light that lightens every edge is pillow shading.** The hill "lit
  crest" varied only the AMOUNT per column, so a pale hairline traced the entire
  silhouette including slopes facing away from the sun. Its target was also
  hard-coded with no d/g, so at night the hills were rim-lit in daylight-coloured
  light at the same value as the bridge railings. Reverted. A rim must be absent
  where the form turns away, and must take the scene's own light.
- **Quantize against the ACTUAL range, or the ramp collapses.** The pine rows
  used a fixed shading span, so narrow rows mapped onto a single ramp step and
  the darkest foliage tone was never used at all — the trees came out uniformly
  pale. Scaling the span to each row's real light range (`w * LIGHT[0]`) restored
  the full ramp. Worth printing which indices a shader actually reaches.
- **Scattered single pixels aren't texture, but tufts alone aren't either.**
  The meadow was 4600 independent pixels — stipple. Replacing it with clustered
  tufts fixed the structure and introduced a new problem: flat bare ground
  between the clumps, which let the flowers pop as isolated dots. Grass needs
  two layers — a weak tonal grain (+/-12%) everywhere, plus deliberate clumps
  on top. And it can't be dither: the meadow scrolls, and a bayer field crawls.
- **A visible repeat can be the cheaper flaw.** The far ridge is six peaks with
  one shared slope and one cap depth, so it reads as a stamp repeated across the
  strip. Fixing that by giving every peak its own slope and height flattened them
  all: the range lost its hierarchy, no summit anchored the background, and the
  snowcaps lost shape with it. Reverted. Before trading a flaw away, check what
  the trade costs -- a monotonous ridge that reads as depth beats a varied one
  that reads as noise.
- **Verify the wrap numerically -- over ALL pairs, not a sample.** Compare the
  419->0 pixel delta against the adjacent-frame deltas. Measured on the current
  build: seam 13.77%, mean step 16.53%, max step 94.91%. A stride-7 sample of
  those pairs gives a max of 79.79%, and quoting that as "the max" is how a
  sampled statistic ends up recorded as a population one. `src/check_scene.py`
  runs this now, so it stops being a hand-run measurement.
- **Coalesce before you judge a frame.** These GIFs are delta-optimised, so
  indexing a single frame yields transparency residue that looks exactly like
  an art bug. Extract with a full-sequence coalesce. This cost one false alarm.
- **Pillow drops duplicate consecutive frames** and folds their delay into the
  previous frame, so a held beat shows up as fewer frames at longer durations.
  Timing survives; the frame count you asked for is not the frame count you get.
  Check total duration, not `%n`.
