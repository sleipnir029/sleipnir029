"""Build the profile animation (assets/current.*) from the chosen scene.

Current style: 16-bit pixel art (src/pixel_journey.py).
Drafts kept for history / future restyling:
  - src/journey_scene.py   pure ASCII journey (previous production cut)
  - src/ride_scene.py      static ASCII night-bridge scene
  - src/draft_ansi_still.py / draft_pixel_still.py   style mockups
  - src/variant_*.py       first-round concepts
"""
import shutil
from pixel_journey import build_gif, ASSETS

if __name__ == '__main__':
    gif = build_gif()
    shutil.copy(gif, ASSETS / 'current.gif')
    shutil.copy(ASSETS / 'pixel_journey.webp', ASSETS / 'current.webp')
    shutil.copy(ASSETS / 'pixel_journey_poster.png', ASSETS / 'current_poster.png')
    print('built assets/current.gif (+webp, poster)')
