# ASCII Profile Draft

Retro animated header for the GitHub profile README: **one day on the
road** — 16-bit pixel art (~42 s loop, 5.6 MB, 420 frames @ 10 fps,
246x113 canvas at x3 nearest-neighbor; canvas was enlarged from 185x85
because the rider didn't read in daylight at the smaller size). Route: morning fields (rabbit
bolts as you near) -> lake with sun glints -> pine forest -> golden hour
-> the suspension bridge at night (stop, breathe, a star falls, an owl
watches from the tower, fireflies drift) -> dawn mist -> morning again.

## Build

```bash
python3 src/build_animation.py
```

Generates `assets/current.gif` / `.webp` / `current_poster.png` and text
frames in `src/frames/current/`.

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
