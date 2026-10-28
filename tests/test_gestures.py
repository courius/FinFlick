"""Behavioural tests for GestureEngine, played back frame-by-frame at 30 fps."""

import unittest

from core.config import AppConfig
from core.gesture_engine import GestureEngine, Pose, measure_hand
from tests.helpers import FIST, PALM, PEACE, POINT, INDEX_UP, THUMBS_UP, THUMBS_DOWN, W_SIGN, Player, make_hand

LEFT, RIGHT = (440.0, 500.0), (840.0, 500.0)   # 400 px apart = 5 palms at palm_px=80


class TestPoseClassification(unittest.TestCase):
    def setUp(self):
        self.engine = GestureEngine(AppConfig())

    def classify(self, hand):
        return self.engine._classify(measure_hand(hand))

    def test_poses(self):
        self.assertEqual(self.classify(make_hand(POINT)), Pose.POINT)
        self.assertEqual(self.classify(make_hand(INDEX_UP, index_up=True)), Pose.INDEX_UP)
        self.assertEqual(self.classify(make_hand(THUMBS_UP, thumb_up=True)), Pose.THUMBS_UP)
        self.assertEqual(self.classify(make_hand(THUMBS_DOWN, thumb_down=True)), Pose.THUMBS_DOWN)
        self.assertEqual(self.classify(make_hand(PEACE)), Pose.PEACE)
        self.assertEqual(self.classify(make_hand(FIST)), Pose.FIST)
        self.assertEqual(self.classify(make_hand(PALM, thumb_out=True)), Pose.PALM)
        self.assertEqual(self.classify(make_hand({"middle": True, "ring": True, "pinky": True}, ok_sign=True)), Pose.OK)
        self.assertEqual(self.classify(make_hand(W_SIGN)), Pose.W_SIGN)
        self.assertEqual(self.classify(make_hand(POINT, thumb_out=True)), Pose.L_SIGN)

    def test_classification_is_scale_invariant(self):
        for palm_px in (20.0, 50.0, 120.0):
            self.assertEqual(self.classify(make_hand(POINT, palm_px=palm_px)), Pose.POINT, palm_px)


class TestSwipes(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig()
        self.p = Player(GestureEngine(self.config))

    def flick(self, start, end, seconds=0.2, **kw):
        self.p.move(seconds, start, end, fingers=POINT, **kw)

    def test_flick_right_is_next(self):
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT)
        self.assertEqual(self.p.events, ["NEXT_SLIDE"])

    def test_flick_left_is_previous(self):
        self.p.hold(0.3, fingers=POINT, center=RIGHT)
        self.flick(RIGHT, LEFT)
        self.assertEqual(self.p.events, ["PREV_SLIDE"])

    def test_works_when_standing_far_away(self):
        # Same physical flick with a hand 3x smaller in the image
        left, right = (600.0, 400.0), (725.0, 400.0)  # 5 palms at palm_px=25
        self.p.hold(0.3, fingers=POINT, center=left, palm_px=25)
        self.p.move(0.2, left, right, fingers=POINT, palm_px=25)
        self.assertEqual(self.p.events, ["NEXT_SLIDE"])

    def test_slow_drift_is_ignored(self):
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT, seconds=2.5)
        self.assertEqual(self.p.events, [])

    def test_vertical_flick_is_ignored(self):
        top, bottom = (640.0, 250.0), (640.0, 650.0)
        self.p.hold(0.3, fingers=POINT, center=top)
        self.flick(top, bottom)
        self.assertEqual(self.p.events, [])

    def test_open_hand_wave_is_ignored(self):
        # Lecturers talk with their hands: a fast open-hand wave must not change slides
        self.p.hold(0.3, fingers=PALM, thumb_out=True, center=LEFT)
        self.p.move(0.2, LEFT, RIGHT, fingers=PALM, thumb_out=True)
        self.p.move(0.2, RIGHT, LEFT, fingers=PALM, thumb_out=True)
        self.assertEqual(self.p.events, [])

    def test_return_stroke_does_not_undo_swipe(self):
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT)
        self.p.hold(0.3, fingers=POINT, center=RIGHT)
        self.flick(RIGHT, LEFT)  # natural return of the hand
        self.assertEqual(self.p.events, ["NEXT_SLIDE"])

    def test_deliberate_reverse_after_block_works(self):
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT)
        self.p.hold(self.config.reverse_block_sec + 0.3, fingers=POINT, center=RIGHT)
        self.flick(RIGHT, LEFT)
        self.assertEqual(self.p.events, ["NEXT_SLIDE", "PREV_SLIDE"])

    def test_two_nexts_in_a_row(self):
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT)
        self.p.hold(0.3, fingers=POINT, center=RIGHT)
        self.flick(RIGHT, LEFT, seconds=2.0)   # slow reset of the hand
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT)
        self.assertEqual(self.p.events, ["NEXT_SLIDE", "NEXT_SLIDE"])

    def test_tracking_dropout_mid_flick_is_tolerated(self):
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT, drop_frames=(2, 3))  # motion blur loses the hand for 2 frames
        self.assertEqual(self.p.events, ["NEXT_SLIDE"])

    def test_no_swipe_while_pose_is_still_forming(self):
        self.p.gap(0.5)
        self.flick(LEFT, RIGHT)  # hand appears already moving
        self.assertEqual(self.p.events, [])

    def test_unmirrored_camera_keeps_user_direction(self):
        self.config.mirror_camera = False
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.flick(LEFT, RIGHT)  # image-right is the user's left without mirroring
        self.assertEqual(self.p.events, ["PREV_SLIDE"])

    def test_phone_style_inversion(self):
        self.config.invert_swipe_direction = True
        self.p.hold(0.3, fingers=POINT, center=RIGHT)
        self.flick(RIGHT, LEFT)
        self.assertEqual(self.p.events, ["NEXT_SLIDE"])


class TestHoldGestures(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig()
        self.p = Player(GestureEngine(self.config))

    def test_fist_fires_once_after_hold(self):
        self.p.hold(0.5, fingers=FIST)
        self.assertEqual(self.p.events, [])
        self.p.hold(1.5, fingers=FIST)
        self.assertEqual(self.p.events, ["BLACKOUT"])

    def test_palm_hold_toggles_pause(self):
        self.p.hold(1.7, fingers=PALM, thumb_out=True)
        self.assertEqual(self.p.events, ["TOGGLE_PAUSE"])

    def test_peace_hold_starts_presentation(self):
        self.p.hold(1.0, fingers=PEACE)
        self.assertEqual(self.p.events, ["START_PRESENTATION"])

    def test_ok_sign_fires_once_per_pinch(self):
        ok = dict(fingers={"middle": True, "ring": True, "pinky": True}, ok_sign=True)
        self.p.hold(1.0, **ok)
        self.assertEqual(self.p.events, ["PLAY_PAUSE"])
        self.p.hold(0.3, fingers=PALM, thumb_out=True)   # release
        self.p.hold(0.5, **ok)
        self.assertEqual(self.p.events, ["PLAY_PAUSE", "PLAY_PAUSE"])

    def test_index_up_fires_first_slide_after_hold(self):
        self.p.hold(0.6, fingers=INDEX_UP, index_up=True)
        self.assertEqual(self.p.events, [])
        self.p.hold(0.5, fingers=INDEX_UP, index_up=True)
        self.assertEqual(self.p.events, ["FIRST_SLIDE"])

    def test_thumbs_up_fires_last_slide_after_hold(self):
        self.p.hold(0.6, fingers=THUMBS_UP, thumb_up=True)
        self.assertEqual(self.p.events, [])
        self.p.hold(0.5, fingers=THUMBS_UP, thumb_up=True)
        self.assertEqual(self.p.events, ["LAST_SLIDE"])

    def test_thumbs_down_fires_zoom_out_after_hold(self):
        self.p.hold(0.2, fingers=THUMBS_DOWN, thumb_down=True)
        self.assertEqual(self.p.events, [])
        self.p.hold(0.3, fingers=THUMBS_DOWN, thumb_down=True)
        self.assertEqual(self.p.events, ["ZOOM_OUT"])

    def test_thumbs_down_repeats_while_held(self):
        """Holding thumbs down auto-repeats zoom out every zoom_cooldown_sec."""
        self.p.hold(0.45, fingers=THUMBS_DOWN, thumb_down=True)
        self.assertEqual(self.p.events, ["ZOOM_OUT"])
        # Hold another 0.35s
        self.p.hold(0.35, fingers=THUMBS_DOWN, thumb_down=True)
        self.assertEqual(self.p.events, ["ZOOM_OUT", "ZOOM_OUT"])

    def test_moving_index_finger_does_not_fire_first_slide(self):
        """Moving index finger (swiping or repositioning) must reset the hold timer."""
        left, right = (440.0, 500.0), (840.0, 500.0)
        self.p.move(1.2, left, right, fingers=INDEX_UP, index_up=True)
        self.assertNotIn("FIRST_SLIDE", self.p.events)

    def test_white_screen_fires_after_hold(self):
        self.p.hold(0.5, fingers=W_SIGN)
        self.assertEqual(self.p.events, [])
        self.p.hold(0.5, fingers=W_SIGN)
        self.assertEqual(self.p.events, ["WHITE_SCREEN"])

    def test_laser_pointer_fires_after_hold(self):
        l_hand = dict(fingers=POINT, thumb_out=True)
        self.p.hold(0.5, **l_hand)
        self.assertEqual(self.p.events, [])
        self.p.hold(0.5, **l_hand)
        self.assertEqual(self.p.events, ["LASER_POINTER"])

    def test_laser_mode_blocks_other_gestures_and_allows_exit(self):
        # In laser mode, other gestures are suppressed so laser aiming is never interrupted
        self.p.engine.laser_mode = True

        # OK sign hold must NOT trigger PLAY_PAUSE and laser mode stays active
        ok = dict(fingers={"middle": True, "ring": True, "pinky": True}, ok_sign=True)
        self.p.hold(1.2, **ok)
        self.assertEqual(self.p.events, [])
        self.assertTrue(self.p.engine.laser_mode)

        # Fist must NOT exit laser mode (laser pointer stays active!)
        self.p.hold(0.3, fingers=FIST)
        self.assertEqual(self.p.events, [])
        self.assertTrue(self.p.engine.laser_mode)

        # Flicking must NOT exit laser mode (laser pointer stays active!)
        left, right = (440.0, 500.0), (840.0, 500.0)
        self.p.hold(0.2, fingers=POINT, center=left)
        self.p.move(0.2, left, right, fingers=POINT)
        self.assertEqual(self.p.events, [])
        self.assertTrue(self.p.engine.laser_mode)

        # ONLY holding L-shape exits laser mode
        self.p.engine._last_swipe_time = float("-inf")
        self.p.events.clear()
        l_hand = dict(fingers=POINT, thumb_out=True)
        self.p.hold(1.0, **l_hand)
        self.assertEqual(self.p.events, ["LASER_POINTER"])
        self.assertFalse(self.p.engine.laser_mode)

    def test_brief_dropout_does_not_reset_hold(self):
        self.p.hold(0.6, fingers=FIST)
        self.p.gap(0.1)
        self.p.hold(0.5, fingers=FIST)
        self.assertEqual(self.p.events, ["BLACKOUT"])

    def test_long_dropout_resets_hold(self):
        self.p.hold(0.6, fingers=FIST)
        self.p.gap(1.0)
        self.p.hold(0.6, fingers=FIST)
        self.assertEqual(self.p.events, [])

    def test_downward_or_lowered_fist_does_not_trigger_blackout(self):
        """A closed hand hanging downward or resting near the bottom of the frame must NEVER trigger BLACKOUT."""
        # 1. Hand low at the bottom edge of the camera frame (center y=690 -> middle_mcp y=610 > 0.82 * 720)
        self.p.hold(1.5, fingers=FIST, center=(640.0, 690.0))
        self.assertEqual(self.p.events, [])

        # 2. Hand inverted / hanging downward (wrist above knuckles: mcp_dy > 0)
        for _ in range(int(1.5 * 30)):
            h = make_hand(FIST, center=(640.0, 400.0))
            wy = h.landmarks[0].y
            for lm in h.landmarks:
                lm.y = wy - (lm.y - wy)  # flip hand upside-down (pointing downward)
            self.p.frame(h)
        self.assertEqual(self.p.events, [])

    def test_moving_fist_does_not_trigger_blackout(self):
        """Moving a closed fist across the screen (e.g. transitioning between gestures) must not trigger BLACKOUT."""
        self.p.move(1.3, (400.0, 480.0), (800.0, 480.0), fingers=FIST)
        self.assertNotIn("BLACKOUT", self.p.events)


class TestPinchZoom(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(zoom_cooldown_sec=0.30, zoom_min_delta=0.22, zoom_window_sec=0.45, thumbs_down_hold_sec=0.40)
        self.p = Player(GestureEngine(self.config))

    def pinch_expand(self, duration: float = 0.20, center=(640.0, 500.0)):
        """Dynamic inside-out pinch: starts close (0.25) and expands open (0.75)."""
        steps = int(round(duration * 30.0))
        for i in range(steps + 1):
            ratio = 0.25 + (0.75 - 0.25) * (i / steps)
            self.p.frame(make_hand({"index": True}, pinch_ratio=ratio, center=center))

    def pinch_close(self, duration: float = 0.20, center=(640.0, 500.0)):
        """Dynamic outside-in pinch: starts open (0.75) and closes (0.25)."""
        steps = int(round(duration * 30.0))
        for i in range(steps + 1):
            ratio = 0.75 - (0.75 - 0.25) * (i / steps)
            self.p.frame(make_hand({"index": True}, pinch_ratio=ratio, center=center))

    def bloom_expand(self, closed_sec: float = 0.15, open_sec: float = 0.10, **kw):
        """Fist-to-Palm Bloom: briefly gather fingers into a fist and burst open into a palm."""
        self.p.hold(closed_sec, fingers=FIST, **kw)
        self.p.hold(open_sec, fingers=PALM, thumb_out=True, **kw)

    def test_pinch_expand_triggers_zoom_in(self):
        self.pinch_expand(0.20)
        self.assertEqual(self.p.events, ["ZOOM_IN"])

    def test_fist_to_palm_bloom_triggers_zoom_in(self):
        self.bloom_expand()
        self.assertEqual(self.p.events, ["ZOOM_IN"])

    def test_fast_single_frame_bloom_with_palm_expansion_and_wrist_shift(self):
        """Real-world MediaPipe: opening a fist fast in 1 frame expands palm size by ~25%
        and shifts wrist landmark slightly. Must reliably trigger ZOOM_IN.
        """
        # Closed fist at (850, 500) with palm_px=75 (and thumb on top like a natural vertical fist)
        self.p.frame(make_hand(FIST, thumb_up=True, center=(850.0, 500.0), palm_px=75.0))
        # Next frame (33ms later): hand snaps open into a palm, palm_px grows to 95 (+27%), wrist shifts by 20px
        self.p.frame(make_hand(PALM, thumb_out=True, center=(870.0, 515.0), palm_px=95.0))
        self.assertEqual(self.p.events, ["ZOOM_IN"])

    def test_fist_to_palm_bloom_with_three_fingers_detected(self):
        """At an angle or during a fast snap, pinky may lag by 1 frame (3 fingers extended). Still triggers ZOOM_IN."""
        self.p.hold(0.10, fingers=FIST)
        self.p.frame(make_hand({"index": True, "middle": True, "ring": True, "pinky": False}, thumb_out=True))
        self.assertEqual(self.p.events, ["ZOOM_IN"])

    def test_fist_to_palm_bloom_works_far_away(self):
        """Bloom zoom works reliably when standing 2-3 meters from the camera (palm_px=25)."""
        self.bloom_expand(palm_px=25.0)
        self.assertEqual(self.p.events, ["ZOOM_IN"])

    def test_rapid_multi_bloom_zoom(self):
        """User can rapidly repeat Fist -> Palm blooms (even closing fist during cooldown) without triggering blackout or pause."""
        self.bloom_expand()
        self.assertEqual(self.p.events, ["ZOOM_IN"])
        # User immediately closes fist during the 0.30s cooldown, then opens right after 0.30s
        self.p.hold(0.25, fingers=FIST)
        self.p.hold(0.10, fingers=PALM, thumb_out=True)
        self.assertEqual(self.p.events, ["ZOOM_IN", "ZOOM_IN"])

    def test_releasing_fist_after_blackout_does_not_zoom(self):
        """Holding a fist for >1.0s (triggering BLACKOUT) and then opening the hand must NOT trigger ZOOM_IN."""
        self.p.hold(1.2, fingers=FIST)
        self.assertEqual(self.p.events, ["BLACKOUT"])
        self.p.hold(0.2, fingers=PALM, thumb_out=True)
        self.assertEqual(self.p.events, ["BLACKOUT"])

    def test_pinch_expand_after_pointing_triggers_zoom_in(self):
        """Pinch-open works even if the user was previously in Pose.POINT (armed=True)."""
        self.p.hold(0.30, fingers=POINT)
        self.assertTrue(self.p.engine.armed)
        self.pinch_expand(0.20)
        self.assertEqual(self.p.events, ["ZOOM_IN"])

    def test_angled_pinch_expand_triggers_zoom_in(self):
        """When hand is angled 60 degrees to camera (x compressed by 0.5x), foreshortening compensation still detects zoom."""
        steps = 6
        for i in range(steps + 1):
            ratio = 0.25 + (0.75 - 0.25) * (i / steps)
            hand = make_hand({"index": True}, pinch_ratio=ratio)
            # Compress all horizontal coordinates by 0.5x to simulate 60-degree hand yaw (cos(60°) = 0.5)
            cx = 640.0 / 1280.0
            for lm in hand.landmarks:
                lm.x = cx + (lm.x - cx) * 0.5
            self.p.frame(hand)
        self.assertEqual(self.p.events, ["ZOOM_IN"])

    def test_pinch_close_does_not_trigger_zoom_out(self):
        """Closing fingers after an expand or from open must NOT trigger zoom out."""
        self.pinch_close(0.20)
        self.assertEqual(self.p.events, [])

    def test_slide_never_triggers_zoom(self):
        """Sliding/flicking left or right must ONLY trigger slide navigation, never zoom."""
        left, right = (440.0, 500.0), (840.0, 500.0)
        self.p.hold(0.3, fingers=POINT, center=left)
        self.p.move(0.2, left, right, fingers=POINT)
        self.assertEqual(self.p.events, ["NEXT_SLIDE"])

        # And sliding back left (after reverse_block_sec)
        self.p.hold(self.config.reverse_block_sec + 0.3, fingers=POINT, center=right)
        self.p.move(0.2, right, left, fingers=POINT)
        self.assertEqual(self.p.events, ["NEXT_SLIDE", "PREV_SLIDE"])

    def test_pointing_or_swiping_then_opening_hand_never_zooms(self):
        """Pointing to pass a slide and then relaxing/opening the hand into a palm must NEVER trigger ZOOM_IN."""
        # 1. Pointing and then opening hand into palm without swiping
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.p.hold(0.2, fingers=PALM, thumb_out=True, center=LEFT)
        self.assertEqual(self.p.events, [])

        # 2. Swiping to pass a slide and immediately opening hand into palm
        self.p.hold(0.3, fingers=POINT, center=LEFT)
        self.p.move(0.2, LEFT, RIGHT, fingers=POINT)
        self.p.hold(0.3, fingers=PALM, thumb_out=True, center=RIGHT)
        self.assertEqual(self.p.events, ["NEXT_SLIDE"])

    def test_rapid_multi_zoom(self):
        """User quickly zooms in, then zooms out with thumbs down."""
        self.pinch_expand(0.15)
        self.assertEqual(self.p.events, ["ZOOM_IN"])

        # Advance past short zoom cooldown (0.30s)
        self.p.gap(0.32)
        self.pinch_expand(0.15)
        self.assertEqual(self.p.events, ["ZOOM_IN", "ZOOM_IN"])

        # Now zoom out with thumbs down
        self.p.gap(0.32)
        self.p.hold(0.45, fingers=THUMBS_DOWN, thumb_down=True)
        self.assertEqual(self.p.events, ["ZOOM_IN", "ZOOM_IN", "ZOOM_OUT"])

    def test_slow_spread_ignored(self):
        """Opening fingers very slowly over 1.5 seconds is not a zoom gesture."""
        steps = int(round(1.5 * 30.0))
        for i in range(steps + 1):
            ratio = 0.25 + (0.75 - 0.25) * (i / steps)
            self.p.frame(make_hand({"index": True}, pinch_ratio=ratio))
        self.assertEqual(self.p.events, [])

    def test_slow_close_ignored(self):
        """Closing fingers very slowly over 1.5 seconds is not a zoom gesture."""
        steps = int(round(1.5 * 30.0))
        for i in range(steps + 1):
            ratio = 0.75 - (0.75 - 0.25) * (i / steps)
            self.p.frame(make_hand({"index": True}, pinch_ratio=ratio))
        self.assertEqual(self.p.events, [])

    def test_peace_sign_held_steady_starts_presentation(self):
        """Holding 2 fingers steady starts presentation, does not zoom."""
        self.p.hold(1.0, fingers=PEACE, center=(640.0, 500.0))
        self.assertEqual(self.p.events, ["START_PRESENTATION"])

    def test_pinch_hold_does_not_trigger_blackout(self):
        """Holding fingers pinched together must NEVER trigger blackout (fist)."""
        self.p.hold(1.5, fingers={"thumb": True, "index": False, "middle": False, "ring": False, "pinky": False}, pinch_ratio=0.25)
        self.assertEqual(self.p.events, [])


if __name__ == "__main__":
    unittest.main()
