import os
import unittest

import numpy as np

from ui.logo import FishStatueRenderer, ICON_PATH, LOGO_PATH, SVG_PATH, ensure_logo_assets
from ui.splash import SplashOverlay
from utils.sound_feedback import ensure_sound_assets


class TestLogoAndAnimation(unittest.TestCase):
    def test_ensure_logo_assets_creates_files(self) -> None:
        logo, icon = ensure_logo_assets()
        self.assertTrue(os.path.exists(LOGO_PATH))
        self.assertTrue(os.path.exists(ICON_PATH))
        self.assertTrue(os.path.exists(SVG_PATH))
        self.assertEqual(logo.size, (512, 512))
        self.assertEqual(icon.size, (128, 128))
        self.assertEqual(logo.mode, "RGBA")

    def test_swirl_animation_frames_reveal_center(self) -> None:
        renderer = FishStatueRenderer(size=160)

        # At progress=0.0 (closed camera iris), the center pixel is covered by the swirling dark-blue iris blades
        closed_frame = np.asarray(renderer.render_frame(progress=0.0, include_lens=False))
        mid = 160 // 2
        self.assertGreater(closed_frame[mid, mid, 3], 240)

        # At progress=1.0 (fully open statue logo without lens), the central hole is open/transparent
        open_frame = np.asarray(renderer.render_frame(progress=1.0, include_lens=False))
        self.assertEqual(open_frame[mid, mid, 3], 0)

        # During hole_expand=1.0, the central aperture expands outward to reveal the app behind it
        expanded_frame = np.asarray(renderer.render_frame(progress=1.0, include_lens=False, hole_expand=1.0))
        self.assertEqual(expanded_frame[mid, mid, 3], 0)

    def test_splash_timing_and_sound_assets(self) -> None:
        self.assertGreaterEqual(SplashOverlay.TOTAL_DURATION, 4.0)
        paths = ensure_sound_assets()
        for key in ("intro", "next", "prev", "action", "wake", "sleep"):
            self.assertIn(key, paths)
            self.assertTrue(os.path.exists(paths[key]))
            self.assertGreater(os.path.getsize(paths[key]), 1000)


if __name__ == "__main__":
    unittest.main()
