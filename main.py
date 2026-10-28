#!/usr/bin/env python3
"""FinFlick: touchless, gesture-controlled presentation clicker."""

import argparse
import logging
import os
import signal
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.config import AppConfig
from core.camera import CameraFeed, list_cameras
from core.hand_tracker import HandTracker
from core.gesture_engine import GestureEngine
from core.controller import PresentationController
from core.pipeline import GesturePipeline
from utils.macos_permissions import (
    check_accessibility_permission,
    request_accessibility_permission,
    prevent_app_nap,
)


def setup_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="FinFlick — gesture-controlled presentation clicker")
    p.add_argument("--camera", type=int, help="Camera index (see --list-cameras)")
    p.add_argument("--list-cameras", action="store_true", help="List available cameras and exit")
    p.add_argument("--cooldown", type=float, help="Minimum seconds between slide changes")
    p.add_argument("--no-sound", action="store_true", help="Disable audio feedback")
    p.add_argument("--no-mirror", action="store_true", help="Disable selfie mirroring")
    p.add_argument("--track-hand", choices=["any", "right", "left"], help="Hand tracking preference (any, right, left)")
    p.add_argument("--headless", action="store_true", help="Run without the window (Ctrl+C to stop)")
    p.add_argument("--reset-settings", action="store_true", help="Ignore saved settings")
    p.add_argument("--debug", action="store_true", help="Verbose logging")
    return p.parse_args()


def build_config(args: argparse.Namespace) -> AppConfig:
    config = AppConfig() if args.reset_settings else AppConfig.load()
    if args.camera is not None:
        config.camera_index = args.camera
    if args.cooldown is not None:
        config.cooldown_seconds = args.cooldown
    if args.no_sound:
        config.sound_feedback = False
    if args.no_mirror:
        config.mirror_camera = False
    if args.track_hand is not None:
        config.track_hand = args.track_hand
    return config


def main() -> None:
    args = parse_args()
    setup_logging(args.debug)
    log = logging.getLogger("FinFlick")

    if args.list_cameras:
        cams = list_cameras()
        print("\n".join(cams) if cams else "No cameras found (check camera permission).")
        return

    config = build_config(args)

    if check_accessibility_permission() is False:
        log.warning(
            "Accessibility permission is NOT granted: macOS will silently drop FinFlick keystrokes into browsers and external apps. "
            "Enable your Terminal/IDE in System Settings → Privacy & Security → Accessibility, then restart it."
        )
        request_accessibility_permission()
    prevent_app_nap()

    camera = CameraFeed(
        camera_index=config.camera_index,
        width=config.frame_width,
        height=config.frame_height,
        fps=config.target_fps,
        mirror=config.mirror_camera,
    )
    tracker = HandTracker(
        num_hands=config.max_num_hands,
        min_detection_confidence=config.min_detection_confidence,
        min_presence_confidence=config.min_presence_confidence,
        min_tracking_confidence=config.min_tracking_confidence,
        track_hand=config.track_hand,
        mirror=config.mirror_camera,
    )
    engine = GestureEngine(config)
    controller = PresentationController(config)
    pipeline = GesturePipeline(config, camera, tracker, engine, controller, render=not args.headless)

    if args.headless:
        stop = {"flag": False}
        signal.signal(signal.SIGINT, lambda *_: stop.update(flag=True))
        if not pipeline.start():
            log.error(camera.error)
            pipeline.stop()
            sys.exit(1)
        log.info("FinFlick running headless — Ctrl+C to stop.")
        while not stop["flag"]:
            time.sleep(0.2)
        pipeline.stop()
        config.save()
        return

    from ui.app_window import FinFlickApp  # import Tk only when needed

    app = FinFlickApp(config, pipeline, controller)
    app.mainloop()


if __name__ == "__main__":
    main()
