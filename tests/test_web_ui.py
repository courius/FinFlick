"""Unit tests for the native WKWebView metallic-blue UI bundle, custom SVG gesture vectors, and FinFlickApp bridge."""

import json
import time
import unittest
import xml.etree.ElementTree as ET

import numpy as np

from core.config import AppConfig
from core.controller import PresentationController
from core.pipeline import PipelineSnapshot
from ui.app_window import FinFlickApp
from ui.web_assets import build_html_ui, get_gesture_svgs, get_hand_filter_svgs


class _FakePipeline:
    def __init__(self, snap: PipelineSnapshot):
        self.snap = snap
        self.mirror_called = None
        self.reset_called = False
        self.switched_cam = None

    def snapshot(self) -> PipelineSnapshot:
        return self.snap

    def start(self) -> bool:
        return True

    def stop(self) -> None:
        pass

    def reset_tracking(self) -> None:
        self.reset_called = True

    def set_mirror(self, mirror: bool) -> None:
        self.mirror_called = mirror

    def switch_camera(self, idx: int) -> None:
        self.switched_cam = idx


class TestWebUiAndGestureVectors(unittest.TestCase):
    def test_all_twelve_gesture_svgs_are_valid_xml(self) -> None:
        svgs = get_gesture_svgs()
        expected = {
            "NEXT_SLIDE",
            "PREV_SLIDE",
            "ZOOM_IN",
            "ZOOM_OUT",
            "PLAY_PAUSE",
            "BLACKOUT",
            "FIRST_SLIDE",
            "LAST_SLIDE",
            "START_PRESENTATION",
            "TOGGLE_PAUSE",
            "LASER_POINTER",
            "WHITE_SCREEN",
        }
        self.assertEqual(set(svgs.keys()), expected)
        for key, markup in svgs.items():
            root = ET.fromstring(markup.strip())
            self.assertTrue(root.tag.endswith("svg"), f"{key} root is not <svg>")

    def test_hand_filter_svgs_are_valid_xml(self) -> None:
        hf_svgs = get_hand_filter_svgs()
        self.assertEqual(set(hf_svgs.keys()), {"left", "any", "right"})
        for key, markup in hf_svgs.items():
            root = ET.fromstring(markup.strip())
            self.assertTrue(root.tag.endswith("svg"), f"{key} root is not <svg>")

    def test_html_bundle_contains_vectors_and_refined_layout(self) -> None:
        html = build_html_ui()
        self.assertNotIn("top-hud-pill", html)
        self.assertNotIn(">STATS<", html)
        self.assertIn("Left Hand", html)
        self.assertIn("Both Hands", html)
        self.assertIn("Right Hand", html)
        self.assertIn("orb-icon-pause", html)
        self.assertIn("orb-icon-play", html)
        self.assertIn("QUICK GESTURES", html)
        self.assertIn("gesture-vector-wrap", html)
        self.assertIn("gesture-card-title", html)
        self.assertIn("top-hud-action-banner", html)
        self.assertIn("top-hud-pause-banner", html)
        self.assertIn("top-hud-laser-banner", html)
        self.assertIn("OK Sign (👌)", html)
        self.assertIn("btn-quick-laser", html)
        self.assertIn("lecture-timer-display", html)

    def test_finflick_app_scheme_and_rpc_bridge(self) -> None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 2] = 180
        snap = PipelineSnapshot(
            display_frame=frame,
            label="Armed — flick index left or right",
            armed=True,
            hold_progress=None,
            hand_visible=True,
            processing_fps=60.0,
            camera_fps=60.0,
            camera_error=None,
            pose_name="POINT",
            handedness="Right",
            recent_action="NEXT_SLIDE",
            recent_action_age=0.2,
        )
        cfg = AppConfig()
        ctrl = PresentationController(cfg)
        pipe = _FakePipeline(snap)
        app = FinFlickApp(cfg, pipe, ctrl)

        html_bytes, ctype = app.serve_resource("/index.html")
        self.assertIn("text/html", ctype)
        self.assertGreater(len(html_bytes), 5000)

        t0 = time.perf_counter()
        jpg_bytes, jpg_type = app.serve_resource("/frame.jpg")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.assertEqual(jpg_type, "image/jpeg")
        self.assertEqual(jpg_bytes[:2], b"\xff\xd8")
        self.assertLess(elapsed_ms, 15.0)

        state_bytes, st_type = app.serve_resource("/state.json")
        self.assertIn("application/json", st_type)
        st = json.loads(state_bytes.decode("utf-8"))
        self.assertEqual(st["state_tag"], "ARMED")
        self.assertFalse(st["progress_visible"])

        # Test RPC commands
        app.handle_rpc({"cmd": "set_config", "key": "track_hand", "value": "left"})
        self.assertEqual(app.app_config.track_hand, "left")
        self.assertTrue(pipe.reset_called)

        app.handle_rpc({"cmd": "apply_preset", "name": "FAST", "dist": 1.1, "speed": 3.0, "cd": 0.7})
        self.assertAlmostEqual(app.app_config.swipe_min_distance_palms, 1.1)

        # Test cycle_camera and set_camera RPCs
        app.handle_rpc({"cmd": "set_camera", "index": 1})
        self.assertEqual(app.app_config.camera_index, 1)
        self.assertEqual(pipe.switched_cam, 1)

        # Test toggle_laser RPC
        self.assertFalse(ctrl.is_laser_active)
        app.handle_rpc({"cmd": "toggle_laser"})
        self.assertTrue(ctrl.is_laser_active)
        st_laser = json.loads(app.serve_resource("/state.json")[0].decode("utf-8"))
        self.assertTrue(st_laser["laser_active"])
        app.handle_rpc({"cmd": "toggle_laser"})
        self.assertFalse(ctrl.is_laser_active)


class TestRealPipelineMethods(unittest.TestCase):
    def test_pipeline_implements_camera_and_tracking_helpers(self) -> None:
        from core.pipeline import GesturePipeline
        self.assertTrue(hasattr(GesturePipeline, "switch_camera"))
        self.assertTrue(hasattr(GesturePipeline, "set_mirror"))
        self.assertTrue(hasattr(GesturePipeline, "reset_tracking"))


if __name__ == "__main__":
    unittest.main()
