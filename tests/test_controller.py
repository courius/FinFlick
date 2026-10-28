"""Tests for PresentationController: profiles, key combos, cooldown, pause, and config persistence."""

import os
import tempfile
import unittest

from core.app_profiles import FrontmostApp
from core.config import AppConfig
from core.controller import PresentationController
from utils.sound_feedback import SoundFeedback


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def make_controller(bundle_id=None, ppt_handled=False, keynote_handled=False, **cfg):
    clock = FakeClock()
    app = FrontmostApp(name="TestApp", bundle_id=bundle_id, pid=1) if bundle_id else None
    c = PresentationController(
        AppConfig(sound_feedback=False, **cfg),
        sound_feedback=SoundFeedback(enabled=False),
        app_detector=lambda: app,
        clock=clock,
        powerpoint_dispatcher=lambda action: ppt_handled,
        keynote_dispatcher=lambda action: keynote_handled,
    )
    sent = []
    c._send_combo = lambda combo: sent.append(combo)
    return c, sent, clock


class TestProfiles(unittest.TestCase):
    def test_google_slides_uses_k_for_video(self):
        c, sent, _ = make_controller("com.google.Chrome")
        c.trigger_action("PLAY_PAUSE")
        self.assertEqual(sent, [("k",)])

    def test_powerpoint_media_and_start(self):
        c, sent, _ = make_controller("com.microsoft.Powerpoint")
        c.trigger_action("PLAY_PAUSE")
        c.trigger_action("START_PRESENTATION")
        self.assertEqual(sent, [("alt", "p"), ("cmd", "return")])

    def test_keynote_start(self):
        c, sent, _ = make_controller("com.apple.iWork.Keynote")
        c.trigger_action("START_PRESENTATION")
        self.assertEqual(sent, [("alt", "cmd", "p")])

    def test_adobe_acrobat_start(self):
        c, sent, _ = make_controller("com.adobe.Reader")
        c.trigger_action("START_PRESENTATION")
        self.assertEqual(sent, [("cmd", "l")])

    def test_canva_and_pitch(self):
        c_canva, sent_canva, _ = make_controller("com.canva.CanvaDesktop")
        c_canva.trigger_action("START_PRESENTATION")
        self.assertEqual(sent_canva, [("alt", "cmd", "p")])

        c_pitch, sent_pitch, _ = make_controller("com.pitch.desktop")
        c_pitch.trigger_action("START_PRESENTATION")
        self.assertEqual(sent_pitch, [("cmd", "return")])

    def test_expanded_browser_bundles(self):
        for bundle in ("company.thebrowser.Browser", "com.kagi.kagisafari", "com.duckduckgo.macos.browser"):
            c, sent, _ = make_controller(bundle)
            c.trigger_action("PLAY_PAUSE")
            self.assertEqual(sent, [("k",)], bundle)

    def test_laser_pointer_and_white_screen(self):
        c_gs, sent_gs, _ = make_controller("com.google.Chrome")
        c_gs.trigger_action("LASER_POINTER")
        c_gs.trigger_action("WHITE_SCREEN")
        self.assertEqual(sent_gs, [("l",), ("w",)])

        c_ppt, sent_ppt, _ = make_controller("com.microsoft.Powerpoint")
        c_ppt.trigger_action("LASER_POINTER")
        c_ppt.trigger_action("WHITE_SCREEN")
        self.assertEqual(sent_ppt, [("cmd", "l"), ("w",)])

    def test_unsupported_action_sends_nothing(self):
        c, sent, _ = make_controller(None)  # generic profile has no "start presenting"
        self.assertFalse(c.trigger_action("START_PRESENTATION"))
        self.assertEqual(sent, [])

    def test_arrows_everywhere(self):
        for bundle in (None, "com.apple.Safari", "com.microsoft.Powerpoint", "com.apple.iWork.Keynote", "com.apple.Preview", "com.adobe.Reader", "com.canva.CanvaDesktop"):
            c, sent, _ = make_controller(bundle)
            c.trigger_action("NEXT_SLIDE")
            self.assertEqual(sent, [("right",)], bundle)

    def test_no_double_skip_when_handled_by_applescript(self):
        # When PowerPoint AppleScript handles the slide change, virtual keys are NOT sent
        c, sent, _ = make_controller("com.microsoft.Powerpoint", ppt_handled=True)
        self.assertTrue(c.trigger_action("NEXT_SLIDE"))
        self.assertEqual(sent, [], "Should NOT send virtual keys when AppleScript already handled it!")

        # Same for Keynote
        c_k, sent_k, _ = make_controller("com.apple.iWork.Keynote", keynote_handled=True)
        self.assertTrue(c_k.trigger_action("NEXT_SLIDE"))
        self.assertEqual(sent_k, [], "Should NOT send virtual keys when Keynote AppleScript handled it!")

    def test_first_and_last_slide_keys(self):
        c, sent, _ = make_controller("com.google.Chrome")
        c.trigger_action("FIRST_SLIDE")
        c.trigger_action("LAST_SLIDE")
        self.assertEqual(sent, [("home",), ("end",)])
        self.assertEqual(c.first_last_slides_count, 2)

    def test_zoom_in_and_out_keys(self):
        c, sent, _ = make_controller("com.google.Chrome")
        c.trigger_action("ZOOM_IN")
        c.trigger_action("ZOOM_OUT", bypass_cooldown=True)
        self.assertEqual(sent, [("cmd", "="), ("cmd", "-")])
        self.assertEqual(c.zoom_count, 2)

    def test_powerpoint_first_last_slide_handled_by_applescript(self):
        c, sent, _ = make_controller("com.microsoft.Powerpoint", ppt_handled=True)
        self.assertTrue(c.trigger_action("FIRST_SLIDE"))
        self.assertTrue(c.trigger_action("LAST_SLIDE"))
        self.assertEqual(sent, [])


class TestCooldownAndPause(unittest.TestCase):
    def test_cooldown_blocks_then_allows(self):
        c, sent, clock = make_controller(cooldown_seconds=1.0)
        self.assertTrue(c.trigger_action("NEXT_SLIDE"))
        clock.t += 0.5
        self.assertFalse(c.trigger_action("NEXT_SLIDE"))
        clock.t += 0.6
        self.assertTrue(c.trigger_action("NEXT_SLIDE"))
        self.assertEqual(c.slides_forward_count, 2)

    def test_zoom_uses_shorter_refresh_cooldown(self):
        # Zoom cooldown (0.30s) allows zooming at +0.35s while nav cooldown (1.0s) blocks next slide
        c, sent, clock = make_controller(cooldown_seconds=1.0, zoom_cooldown_sec=0.30)
        self.assertTrue(c.trigger_action("NEXT_SLIDE"))
        self.assertTrue(c.trigger_action("ZOOM_IN"))

        # At +0.35s: nav action is blocked (needs 1.0s), but zoom is allowed!
        clock.t += 0.35
        self.assertFalse(c.trigger_action("NEXT_SLIDE"))
        self.assertTrue(c.trigger_action("ZOOM_IN"))
        self.assertEqual(c.zoom_count, 2)

    def test_hold_gestures_bypass_nav_cooldown(self):
        c, sent, clock = make_controller(cooldown_seconds=1.0)
        c.trigger_action("NEXT_SLIDE")
        clock.t += 0.2
        self.assertTrue(c.trigger_action("BLACKOUT"))
        self.assertTrue(c.trigger_action("FIRST_SLIDE"))
        self.assertTrue(c.trigger_action("LAST_SLIDE"))

    def test_pause_blocks_actions_and_resume_is_immediate(self):
        c, sent, clock = make_controller(cooldown_seconds=1.0)
        c.trigger_action("TOGGLE_PAUSE")
        self.assertFalse(c.trigger_action("NEXT_SLIDE"))
        c.trigger_action("TOGGLE_PAUSE")
        self.assertTrue(c.trigger_action("NEXT_SLIDE"))
        self.assertEqual(sent, [("right",)])

    def test_callback_receives_labels(self):
        c, _, _ = make_controller("com.apple.iWork.Keynote")
        labels = []
        c.set_action_callback(labels.append)
        c.trigger_action("NEXT_SLIDE")
        self.assertTrue(labels and "Next Slide" in labels[0] and "TestApp" in labels[0])

    def test_laser_pointer_toggle_and_pause_deactivation(self):
        c, sent, _ = make_controller("com.google.Chrome")
        self.assertFalse(c.is_laser_active)

        # First trigger activates laser
        self.assertTrue(c.trigger_action("LASER_POINTER"))
        self.assertTrue(c.is_laser_active)
        self.assertIn("Laser Pointer Active", c.last_action_name)
        self.assertEqual(sent, [("l",)])

        # Second trigger deactivates laser
        self.assertTrue(c.trigger_action("LASER_POINTER"))
        self.assertFalse(c.is_laser_active)
        self.assertIn("Laser Pointer Deactivated", c.last_action_name)
        self.assertEqual(sent, [("l",), ("l",)])

        # Activating again then pausing tracking turns laser off
        c.trigger_action("LASER_POINTER")
        self.assertTrue(c.is_laser_active)
        c.set_paused(True)
        self.assertFalse(c.is_laser_active)

        # Test LASER_POINTER_AND_NAV: deactivates laser AND immediately advances slide
        c.set_paused(False)
        c.trigger_action("LASER_POINTER")
        self.assertTrue(c.is_laser_active)
        self.assertTrue(c.trigger_action("LASER_POINTER_AND_NAV", details="NEXT_SLIDE"))
        self.assertFalse(c.is_laser_active)
        self.assertEqual(sent[-2:], [("l",), ("right",)])

    def test_auto_refocus_external_app(self):
        from core.app_profiles import set_last_external_app
        ext_app = FrontmostApp(name="Keynote", bundle_id="com.apple.iWork.Keynote", pid=99999)
        set_last_external_app(ext_app)

        finflick_app = FrontmostApp(name="FinFlick", bundle_id="com.finflick", pid=os.getpid())
        clock = FakeClock()
        c = PresentationController(
            AppConfig(sound_feedback=False, auto_focus_target=True),
            sound_feedback=SoundFeedback(enabled=False),
            app_detector=lambda: finflick_app,
            clock=clock,
        )
        sent = []
        c._send_combo = lambda combo: sent.append(combo)
        # When FinFlick is frontmost, it automatically resolves to the external target and sends right arrow
        self.assertTrue(c.trigger_action("NEXT_SLIDE"))
        self.assertEqual(sent, [("right",)])


class TestConfigPersistence(unittest.TestCase):
    def test_roundtrip_and_bad_values(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "config.json")
            cfg = AppConfig(cooldown_seconds=2.2, invert_swipe_direction=True)
            cfg.save(path)
            loaded = AppConfig.load(path)
            self.assertEqual(loaded.cooldown_seconds, 2.2)
            self.assertTrue(loaded.invert_swipe_direction)

            with open(path, "w") as fh:
                fh.write('{"cooldown_seconds": "oops", "unknown_key": 1, "mirror_camera": false}')
            loaded = AppConfig.load(path)
            self.assertEqual(loaded.cooldown_seconds, AppConfig().cooldown_seconds)
            self.assertFalse(loaded.mirror_camera)

    def test_corrupt_file_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "config.json")
            with open(path, "w") as fh:
                fh.write("{not json")
            self.assertEqual(AppConfig.load(path), AppConfig())


if __name__ == "__main__":
    unittest.main()
