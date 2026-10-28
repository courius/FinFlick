"""Background processing pipeline: camera -> hand tracking -> gestures -> keystrokes.

Runs on its own thread so inference never blocks the UI (and keeps working while the
FinFlick window is hidden behind a fullscreen presentation). The UI only reads a
thread-safe snapshot.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from core.air_mouse import AirMouseController
from core.camera import CameraFeed
from core.config import AppConfig
from core.controller import PresentationController
from core.gesture_engine import GestureEngine
from core.hand_tracker import HandTracker, draw_skeleton

logger = logging.getLogger("FinFlick.Pipeline")


@dataclass
class PipelineSnapshot:
    display_frame: Optional[np.ndarray]   # RGB, already downscaled for the UI
    label: str
    armed: bool
    hold_progress: Optional[float]
    hand_visible: bool
    processing_fps: float
    camera_fps: float
    camera_error: Optional[str]
    pose_name: str = "NONE"
    handedness: str = "Unknown"
    recent_action: Optional[str] = None
    recent_action_age: float = 999.0
    laser_active: bool = False


class GesturePipeline:
    def __init__(
        self,
        config: AppConfig,
        camera: CameraFeed,
        tracker: HandTracker,
        engine: GestureEngine,
        controller: PresentationController,
        render: bool = True,
        display_width: int = 720,
    ):
        self.config = config
        self.camera = camera
        self.tracker = tracker
        self.engine = engine
        self.controller = controller
        self.render = render
        self.display_width = display_width
        self.air_mouse = AirMouseController()
        self._laser_hand_seen_time: float = float("-inf")

        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._snapshot = PipelineSnapshot(None, "Starting…", False, None, False, 0.0, 0.0, None)

        self._fps = 0.0
        self._fps_count = 0
        self._fps_start = time.monotonic()

        self._last_action_name: Optional[str] = None
        self._last_action_time: float = 0.0

    def start(self) -> bool:
        ok = self.camera.start()
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="GesturePipeline", daemon=True)
        self._thread.start()
        return ok

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.camera.stop()
        self.tracker.close()

    def switch_camera(self, new_index: int) -> bool:
        """Switch camera device dynamically without recreating the pipeline."""
        return self.camera.switch_camera(new_index)

    def set_mirror(self, mirror: bool) -> None:
        """Update mirror setting across camera feed and hand tracker."""
        self.config.mirror_camera = mirror
        self.camera.mirror = mirror
        self.tracker.mirror = mirror

    def reset_tracking(self) -> None:
        """Reset hand lock and tracking history."""
        self.tracker.reset_tracking()
        self.engine.reset()

    def snapshot(self) -> PipelineSnapshot:
        with self._lock:
            return self._snapshot

    def _loop(self) -> None:
        last_id = 0
        while self._running:
            if self.camera.error and not self.camera.running:
                self._publish(None, hand_visible=False)
                time.sleep(0.25)
                continue

            frame = self.camera.wait_for_frame(last_id, timeout=0.5)
            if frame is None:
                continue
            last_id = frame.frame_id

            try:
                hand = self.tracker.process(frame.image, frame.timestamp)
                paused = self.controller.is_tracking_paused
                laser_active = self.controller.is_laser_active
                self.engine.laser_mode = laser_active

                # Real-time air-mouse steering when laser pointer is active
                if laser_active:
                    if hand is not None and len(hand.landmarks) >= 9:
                        self._laser_hand_seen_time = frame.timestamp
                        tip = hand.landmarks[8]
                        self.air_mouse.update(tip.x, tip.y)
                    else:
                        self.air_mouse.reset()
                else:
                    self.air_mouse.reset()

                event = self.engine.evaluate(hand, now=frame.timestamp)
                if event is not None and (not paused or event.name == "TOGGLE_PAUSE"):
                    if event.name == "TOGGLE_PAUSE":
                        self.tracker.reset_tracking()
                    # If exiting laser mode, deactivate air mouse and park cursor
                    if event.name in ("LASER_POINTER", "LASER_POINTER_AND_NAV") and self.controller.is_laser_active:
                        self.air_mouse.deactivate(park_cursor=True)
                    if self.controller.trigger_action(event.name, details=event.details):
                        if not self.controller.is_laser_active:
                            self.air_mouse.deactivate(park_cursor=True)
                        self._last_action_name = event.name
                        self._last_action_time = time.monotonic()
            except Exception:
                logger.exception("Error while processing frame")
                continue

            self._tick_fps()
            display = self._render(frame.image, hand) if self.render else None
            self._publish(display, hand=hand)

    def _render(self, image: np.ndarray, hand) -> np.ndarray:
        h, w = image.shape[:2]
        scale = self.display_width / float(w)
        small = cv2.resize(image, (self.display_width, int(h * scale)), interpolation=cv2.INTER_AREA)
        sh, sw = small.shape[:2]

        # 1. Futuristic Plasma Comet Trail (following index fingertip while armed)
        if self.config.show_motion_trail and self.engine.armed:
            trail = self.engine.motion_trail
            if len(trail) >= 2:
                pts = [(int(nx * sw), int(ny * sh), intensity) for nx, ny, intensity in trail]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                pad = 28
                tx0, ty0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
                tx1, ty1 = min(sw, max(xs) + pad), min(sh, max(ys) + pad)
                if tx1 - tx0 > 4 and ty1 - ty0 > 4:
                    t_aura = np.zeros((ty1 - ty0, tx1 - tx0, 3), dtype=np.uint8)
                    t_core = np.zeros((ty1 - ty0, tx1 - tx0, 3), dtype=np.uint8)
                    for i in range(1, len(pts)):
                        p1 = (pts[i - 1][0] - tx0, pts[i - 1][1] - ty0)
                        p2 = (pts[i][0] - tx0, pts[i][1] - ty0)
                        intensity = pts[i][2]
                        aura_thick = max(2, int(round(10 * intensity * scale)))
                        core_thick = max(1, int(round(2.5 * intensity * scale)))
                        # BGR electric blue-cyan glow + ice-white filament
                        cv2.line(
                            t_aura,
                            p1,
                            p2,
                            (int(255 * intensity), int(165 * intensity), int(35 * intensity)),
                            aura_thick,
                            cv2.LINE_AA,
                        )
                        cv2.line(
                            t_core,
                            p1,
                            p2,
                            (int(255 * intensity), int(238 * intensity), int(175 * intensity)),
                            core_thick,
                            cv2.LINE_AA,
                        )
                    t_bloom = cv2.GaussianBlur(t_aura, (0, 0), sigmaX=4.5)
                    t_glow = cv2.add(t_bloom, t_core)
                    roi = small[ty0:ty1, tx0:tx1]
                    cv2.add(roi, t_glow, dst=roi)

        # 2. Bioluminescent Hand Power Aura & Futuristic Fingertip Orb
        if hand is not None and self.config.draw_skeleton:
            draw_skeleton(small, hand, armed=self.engine.armed)

        # 2b. Glowing Neon Ruby Laser Reticle (when laser pointer is active)
        if self.controller.is_laser_active and hand is not None and len(hand.landmarks) >= 9:
            lms = hand.landmarks
            lx = int(lms[8].x * sw)
            ly = int(lms[8].y * sh)
            pad = 28
            lx0, ly0 = max(0, lx - pad), max(0, ly - pad)
            lx1, ly1 = min(sw, lx + pad), min(sh, ly + pad)
            if lx1 - lx0 > 4 and ly1 - ly0 > 4:
                l_aura = np.zeros((ly1 - ly0, lx1 - lx0, 3), dtype=np.uint8)
                l_core = np.zeros((ly1 - ly0, lx1 - lx0, 3), dtype=np.uint8)
                c_pt = (lx - lx0, ly - ly0)
                # Outer ruby bloom & crosshairs
                cv2.circle(l_aura, c_pt, 20, (30, 20, 255), -1, cv2.LINE_AA)
                cv2.line(l_core, (c_pt[0] - 14, c_pt[1]), (c_pt[0] + 14, c_pt[1]), (210, 210, 255), 2, cv2.LINE_AA)
                cv2.line(l_core, (c_pt[0], c_pt[1] - 14), (c_pt[0], c_pt[1] + 14), (210, 210, 255), 2, cv2.LINE_AA)
                cv2.circle(l_core, c_pt, 7, (60, 40, 255), 2, cv2.LINE_AA)
                cv2.circle(l_core, c_pt, 3, (245, 245, 255), -1, cv2.LINE_AA)
                l_bloom = cv2.GaussianBlur(l_aura, (0, 0), sigmaX=4.5)
                l_glow = cv2.add(l_bloom, l_core)
                roi = small[ly0:ly1, lx0:lx1]
                cv2.add(roi, l_glow, dst=roi)

        # 3. Futuristic Arc-Reactor Hold-Progress Halo around the palm nexus
        if hand is not None and self.engine.hold_progress is not None:
            lms = hand.landmarks
            px = int(
                (0.28 * lms[0].x + 0.20 * lms[5].x + 0.22 * lms[9].x + 0.16 * lms[13].x + 0.14 * lms[17].x) * sw
            )
            py = int(
                (0.28 * lms[0].y + 0.20 * lms[5].y + 0.22 * lms[9].y + 0.16 * lms[13].y + 0.14 * lms[17].y) * sh
            )
            angle = int(360 * self.engine.hold_progress)
            r_halo = 34
            pad = r_halo + 20
            hx0, hy0 = max(0, px - pad), max(0, py - pad)
            hx1, hy1 = min(sw, px + pad), min(sh, py + pad)
            if hx1 - hx0 > 4 and hy1 - hy0 > 4:
                h_aura = np.zeros((hy1 - hy0, hx1 - hx0, 3), dtype=np.uint8)
                h_core = np.zeros((hy1 - hy0, hx1 - hx0, 3), dtype=np.uint8)
                c_pt = (px - hx0, py - hy0)
                cv2.ellipse(h_core, c_pt, (r_halo, r_halo), 0, 0, 360, (90, 50, 15), 2, cv2.LINE_AA)
                cv2.ellipse(h_aura, c_pt, (r_halo, r_halo), -90, 0, angle, (255, 165, 30), 7, cv2.LINE_AA)
                cv2.ellipse(h_core, c_pt, (r_halo, r_halo), -90, 0, angle, (255, 235, 150), 3, cv2.LINE_AA)
                h_bloom = cv2.GaussianBlur(h_aura, (0, 0), sigmaX=4.0)
                h_glow = cv2.add(h_bloom, h_core)
                roi = small[hy0:hy1, hx0:hx1]
                cv2.add(roi, h_glow, dst=roi)

        # 4. Subtle dimming when tracking is paused (crisp text & badges rendered in UI)
        if self.controller.is_tracking_paused:
            overlay = small.copy()
            cv2.rectangle(overlay, (0, 0), (sw, sh), (14, 10, 6), -1)
            small = cv2.addWeighted(overlay, 0.45, small, 0.55, 0)

        return cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    def _tick_fps(self) -> None:
        self._fps_count += 1
        now = time.monotonic()
        if now - self._fps_start >= 1.0:
            self._fps = self._fps_count / (now - self._fps_start)
            self._fps_count = 0
            self._fps_start = now

    def _publish(self, display: Optional[np.ndarray], hand=None, hand_visible: Optional[bool] = None) -> None:
        is_vis = (hand is not None) if hand_visible is None else hand_visible
        handedness = hand.handedness if (hand is not None and hasattr(hand, "handedness")) else "Unknown"
        pose_name = self.engine.pose.name if hasattr(self.engine, "pose") else "NONE"
        age = (time.monotonic() - self._last_action_time) if self._last_action_name else 999.0
        snap = PipelineSnapshot(
            display_frame=display,
            label=self.engine.label,
            armed=self.engine.armed,
            hold_progress=self.engine.hold_progress,
            hand_visible=is_vis,
            processing_fps=self._fps,
            camera_fps=self.camera.fps,
            camera_error=self.camera.error,
            pose_name=pose_name,
            handedness=handedness,
            recent_action=self._last_action_name if age < 1.5 else None,
            recent_action_age=age,
            laser_active=self.controller.is_laser_active,
        )
        with self._lock:
            self._snapshot = snap
