"""Configuration settings for FinFlick, with JSON persistence."""

import json
import logging
import os
from dataclasses import dataclass, asdict, fields
from typing import Any, Dict

logger = logging.getLogger("FinFlick.Config")

CONFIG_DIR = os.path.expanduser("~/Library/Application Support/FinFlick")
LEGACY_CONFIG_PATH = os.path.expanduser("~/Library/Application Support/SlidePass/config.json")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


@dataclass
class AppConfig:
    # ---------------- Camera ----------------
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    target_fps: int = 30
    mirror_camera: bool = True  # Selfie view: moving your hand to YOUR right moves it right on screen

    # ---------------- MediaPipe & Hand Tracking ----------------
    max_num_hands: int = 2
    track_hand: str = "any"  # "any", "right", or "left" (physical hand)
    min_detection_confidence: float = 0.6
    min_presence_confidence: float = 0.6
    min_tracking_confidence: float = 0.5

    # ---------------- Gestures ----------------
    # All distances are measured in "palm lengths" (wrist -> middle-finger knuckle),
    # so thresholds behave the same whether you sit at the laptop or stand 2 m away.
    swipe_min_distance_palms: float = 1.10  # Natural flick distance (~110-130 px)
    swipe_min_speed_palms: float = 3.0      # Responsive speed threshold
    swipe_window_sec: float = 0.40          # Detection time window
    swipe_horizontal_ratio: float = 1.25    # Allows natural curved wrist arcs

    # Fast arm dwell: responsive immediate flicks upon hand raise
    arm_dwell_sec: float = 0.10
    # Rapid re-arming between slide passes
    rearm_settle_sec: float = 0.18
    settle_speed_palms: float = 1.5
    # Swipes in the OPPOSITE direction blocked briefly to reject return stroke
    reverse_block_sec: float = 1.20
    # Swipe left = next (phone style) instead of swipe right = next
    invert_swipe_direction: bool = False

    # A raw pose change must persist this long to be accepted (filters 1-frame flicker)
    pose_confirm_sec: float = 0.08
    # Tolerate brief hand-tracking dropouts (motion blur during a fast flick)
    dropout_grace_sec: float = 0.20

    # OK-sign pinch: thumb-tip to index-tip distance (palm lengths), with hysteresis
    pinch_enter_palms: float = 0.35
    pinch_release_palms: float = 0.55
    pinch_hold_sec: float = 0.15

    # Hold-to-trigger gestures
    fist_hold_sec: float = 1.0         # Blank screen (deliberate 1.0s hold)
    palm_hold_sec: float = 1.5         # Pause / resume tracking
    peace_hold_sec: float = 0.8        # Start presenting
    first_slide_hold_sec: float = 1.0  # Index finger up -> first slide (1.0s deliberate hold)
    last_slide_hold_sec: float = 1.0   # Thumb up -> last slide (1.0s deliberate hold)
    thumbs_down_hold_sec: float = 0.40 # Thumb down -> zoom out (-15%)
    laser_hold_sec: float = 0.80       # L-shape -> toggle laser pointer
    whiteboard_hold_sec: float = 0.80  # W-sign (3 fingers) -> toggle whiteboard screen

    # Dynamic pinch-zoom & bloom-zoom
    zoom_cooldown_sec: float = 0.30    # Fast refresh for rapid multi-zoom
    zoom_min_delta: float = 0.22       # Minimum pinch distance change (palm lengths)
    zoom_window_sec: float = 0.45      # Max seconds to complete pinch or bloom zoom movement

    # Minimum gap between slide navigation actions (swipe)
    cooldown_seconds: float = 0.70

    # ---------------- Application Control ----------------
    auto_focus_target: bool = True       # Refocus presentation window if FinFlick was focused

    # ---------------- Feedback & HUD ----------------
    sound_feedback: bool = True
    draw_skeleton: bool = True
    show_motion_trail: bool = True       # Draw laser trajectory trail behind pointing finger
    show_hud_notifications: bool = True  # Draw animated on-video badge when gestures trigger

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Builds a config, ignoring unknown keys and keys with the wrong type."""
        defaults = cls()
        kwargs = {}
        for f in fields(cls):
            if f.name in data:
                value = data[f.name]
                default_value = getattr(defaults, f.name)
                if isinstance(default_value, bool):
                    if isinstance(value, bool):
                        kwargs[f.name] = value
                elif isinstance(default_value, (int, float)) and isinstance(value, (int, float)) and not isinstance(value, bool):
                    kwargs[f.name] = type(default_value)(value)
                elif isinstance(default_value, str) and isinstance(value, str):
                    kwargs[f.name] = value
        return cls(**kwargs)

    # ---------------- Persistence ----------------
    @classmethod
    def load(cls, path: str = CONFIG_PATH) -> "AppConfig":
        target_path = path
        if path == CONFIG_PATH and not os.path.exists(path) and os.path.exists(LEGACY_CONFIG_PATH):
            target_path = LEGACY_CONFIG_PATH
        try:
            with open(target_path, "r", encoding="utf-8") as fh:
                return cls.from_dict(json.load(fh))
        except FileNotFoundError:
            return cls()
        except Exception as e:
            logger.warning(f"Could not read settings from {target_path} ({e}); using defaults.")
            return cls()

    def save(self, path: str = CONFIG_PATH) -> None:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(self.to_dict(), fh, indent=2)
            os.replace(tmp_path, path)
        except Exception as e:
            logger.warning(f"Could not save settings to {path}: {e}")
