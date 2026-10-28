"""Tests for HandTracker single-hand locking and disabling secondary hands."""

import unittest
import numpy as np
from core.hand_tracker import HandTracker, HandObservation, LandmarkPoint, draw_skeleton


def make_obs(wrist_x: float, wrist_y: float, handedness: str = "Right", palm_size: float = 0.15) -> HandObservation:
    """Creates a synthetic 21-landmark HandObservation positioned at wrist (wrist_x, wrist_y)."""
    lms = []
    # Landmark 0: wrist
    lms.append(LandmarkPoint(wrist_x, wrist_y, 0.0))
    # Landmarks 1..8: thumb & index
    for i in range(1, 9):
        lms.append(LandmarkPoint(wrist_x, wrist_y - (i * 0.015), 0.0))
    # Landmark 9: middle_mcp (determines palm size)
    lms.append(LandmarkPoint(wrist_x, wrist_y - palm_size, 0.0))
    # Landmarks 10..20: remaining fingers
    for i in range(10, 21):
        lms.append(LandmarkPoint(wrist_x + 0.05, wrist_y - (i * 0.01), 0.0))
    return HandObservation(landmarks=lms, width=1280, height=720, handedness=handedness)


class TestHandTrackerSingleHandLock(unittest.TestCase):
    def setUp(self):
        self.tracker = HandTracker()

    def test_single_hand_locks(self):
        hand1 = make_obs(0.6, 0.5, handedness="Right")
        chosen = self.tracker._select_tracked_hand([hand1], timestamp_sec=1.0)
        self.assertIsNotNone(chosen)
        self.assertAlmostEqual(chosen.landmarks[0].x, 0.6)
        self.assertEqual(chosen.handedness, "Right")

    def test_second_hand_is_disabled_while_first_hand_is_tracked(self):
        # 1. Lock onto Right hand
        right_hand = make_obs(0.7, 0.5, handedness="Right")
        chosen = self.tracker._select_tracked_hand([right_hand], timestamp_sec=1.0)
        self.assertEqual(chosen.handedness, "Right")

        # 2. Both Right hand and Left hand are visible on next frame
        right_hand_t2 = make_obs(0.71, 0.51, handedness="Right")
        left_hand = make_obs(0.2, 0.5, handedness="Left")

        # Pass both hands in list (Left first, then Right)
        chosen = self.tracker._select_tracked_hand([left_hand, right_hand_t2], timestamp_sec=1.033)

        # MUST track Right hand and disable Left hand
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.handedness, "Right")
        self.assertAlmostEqual(chosen.landmarks[0].x, 0.71)

    def test_tracker_follows_moving_hand_and_ignores_secondary_hand(self):
        # Track hand across 10 frames while second hand sits in frame
        for i in range(10):
            t = 1.0 + (i * 0.033)
            # Active hand moving rightwards (e.g. flicking)
            active_hand = make_obs(0.5 + (i * 0.02), 0.5, handedness="Right")
            # Inactive second hand stationary on left side
            inactive_hand = make_obs(0.2, 0.5, handedness="Left")

            chosen = self.tracker._select_tracked_hand([inactive_hand, active_hand], timestamp_sec=t)
            self.assertEqual(chosen.handedness, "Right")
            self.assertAlmostEqual(chosen.landmarks[0].x, 0.5 + (i * 0.02))

    def test_dropout_grace_does_not_jump_to_other_hand(self):
        # 1. Lock onto Right hand
        right_hand = make_obs(0.7, 0.5, handedness="Right")
        self.tracker._select_tracked_hand([right_hand], timestamp_sec=1.0)

        # 2. Right hand drops out for 0.15s (blur during fast flick), while Left hand is visible
        left_hand = make_obs(0.2, 0.5, handedness="Left")
        chosen = self.tracker._select_tracked_hand([left_hand], timestamp_sec=1.15)

        # Within 0.40s grace period, it must NOT jump to Left hand
        self.assertIsNone(chosen)

        # 3. Right hand reappears at +0.25s
        right_hand_back = make_obs(0.75, 0.5, handedness="Right")
        chosen = self.tracker._select_tracked_hand([left_hand, right_hand_back], timestamp_sec=1.25)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.handedness, "Right")

    def test_switch_hand_after_grace_period_expires(self):
        # 1. Lock onto Right hand
        right_hand = make_obs(0.7, 0.5, handedness="Right")
        self.tracker._select_tracked_hand([right_hand], timestamp_sec=1.0)

        # 2. Right hand is gone for 0.6s (> 0.40s grace period)
        left_hand = make_obs(0.2, 0.5, handedness="Left")
        chosen = self.tracker._select_tracked_hand([left_hand], timestamp_sec=1.60)

        # Lock expired, so it smoothly switches to Left hand
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.handedness, "Left")
        self.assertAlmostEqual(chosen.landmarks[0].x, 0.2)

    def test_reset_tracking_clears_lock_immediately(self):
        right_hand = make_obs(0.7, 0.5, handedness="Right")
        self.tracker._select_tracked_hand([right_hand], timestamp_sec=1.0)

        # Explicit reset (e.g. on unpause)
        self.tracker.reset_tracking()

        left_hand = make_obs(0.2, 0.5, handedness="Left")
        chosen = self.tracker._select_tracked_hand([left_hand], timestamp_sec=1.05)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.handedness, "Left")

    def test_right_hand_only_ignores_left_hand(self):
        self.tracker.set_track_hand("right")
        left_hand = make_obs(0.2, 0.5, handedness="Left")
        # When only left hand is present, nothing is tracked
        chosen = self.tracker._select_tracked_hand([left_hand], timestamp_sec=1.0)
        self.assertIsNone(chosen)

        # When right hand enters alongside left hand, only right hand is tracked
        right_hand = make_obs(0.7, 0.5, handedness="Right")
        chosen = self.tracker._select_tracked_hand([left_hand, right_hand], timestamp_sec=1.033)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.handedness, "Right")
        self.assertAlmostEqual(chosen.landmarks[0].x, 0.7)

    def test_left_hand_only_ignores_right_hand(self):
        self.tracker.set_track_hand("left")
        right_hand = make_obs(0.7, 0.5, handedness="Right")
        # When only right hand is present, nothing is tracked
        chosen = self.tracker._select_tracked_hand([right_hand], timestamp_sec=1.0)
        self.assertIsNone(chosen)

        # When left hand enters alongside right hand, only left hand is tracked
        left_hand = make_obs(0.2, 0.5, handedness="Left")
        chosen = self.tracker._select_tracked_hand([right_hand, left_hand], timestamp_sec=1.033)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.handedness, "Left")
        self.assertAlmostEqual(chosen.landmarks[0].x, 0.2)

    def test_switch_setting_immediately_drops_disallowed_hand(self):
        # 1. Tracking right hand
        self.tracker.set_track_hand("right")
        right_hand = make_obs(0.7, 0.5, handedness="Right")
        self.tracker._select_tracked_hand([right_hand], timestamp_sec=1.0)

        # 2. User switches setting to left hand in settings
        self.tracker.set_track_hand("left")

        # Right hand is now immediately ignored even though it was previously locked
        chosen = self.tracker._select_tracked_hand([right_hand], timestamp_sec=1.033)
        self.assertIsNone(chosen)

        # Left hand is tracked immediately
        left_hand = make_obs(0.2, 0.5, handedness="Left")
        chosen = self.tracker._select_tracked_hand([left_hand], timestamp_sec=1.066)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.handedness, "Left")

    def test_draw_skeleton_renders_blue_cyan_power_aura_without_yellow(self):
        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        hand = make_obs(0.5, 0.6, handedness="Right")
        # Extend index fingertip upward to trigger primary fingertip orb
        hand.landmarks[5] = LandmarkPoint(0.50, 0.48, 0.0)
        hand.landmarks[6] = LandmarkPoint(0.50, 0.40, 0.0)
        hand.landmarks[7] = LandmarkPoint(0.50, 0.33, 0.0)
        hand.landmarks[8] = LandmarkPoint(0.50, 0.25, 0.0)

        draw_skeleton(frame, hand, armed=True, phase=1.25)

        # Ensure glowing pixels were rendered and Blue channel dominates Red channel (no yellow lines/circles)
        total_blue = int(frame[:, :, 0].sum())
        total_green = int(frame[:, :, 1].sum())
        total_red = int(frame[:, :, 2].sum())
        self.assertGreater(total_blue, 5000)
        self.assertGreater(total_blue, total_green)
        self.assertGreater(total_green, total_red)


if __name__ == "__main__":
    unittest.main()
