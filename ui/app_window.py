"""FinFlick Native Metallic-Blue Desktop UI Host (macOS AppKit + GPU-Accelerated WKWebView).

Serves the custom HTML5 / CSS3 / SVG / WebAudio metallic-blue interface and 60-FPS camera +
hand-aura stream directly from Python memory via an in-process `finflick://` WKURLSchemeHandler
and zero-latency WKScriptMessageHandler bridge.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from core.app_profiles import activate_app, get_last_external_app
from core.camera import get_camera_devices, find_default_camera_index, list_cameras
from core.config import AppConfig
from core.controller import PresentationController
from core.pipeline import GesturePipeline
from ui.logo import LOGO_PATH, SVG_PATH, ensure_logo_assets
from ui.web_assets import build_html_ui, get_gesture_svgs
from utils.macos_permissions import (
    check_accessibility_permission,
    open_accessibility_settings,
    request_accessibility_permission,
)

logger = logging.getLogger("FinFlick.App")

TARGET_POLL_SEC = 1.0
PERMISSION_POLL_SEC = 3.0


class FinFlickApp:
    """Native macOS WKWebView application host with metallic-blue UI, custom SVG gesture vectors, and 60-FPS camera bridge."""

    def __init__(self, config: AppConfig, pipeline: GesturePipeline, controller: PresentationController):
        self.app_config = config
        self.pipeline = pipeline
        self.controller = controller

        self._events: "queue.Queue[str]" = queue.Queue()
        self.controller.set_action_callback(self._events.put)

        self._banner_text: str = ""
        self._banner_until: float = 0.0
        self._next_target_poll: float = 0.0
        self._next_perm_poll: float = 0.0
        self._countdown_timer: Optional[threading.Timer] = None

        self._target_app_text: str = "Target: Detecting…"
        self._has_ext_focus: bool = False
        self._ext_name: str = ""
        self._perm_ok: bool = True
        self._camera_devices: List[Dict[str, Any]] = []
        self._available_cameras: List[int] = [self.app_config.camera_index]
        self._discover_cameras(initial=True)

        # Prebuild static web bundle & logo SVG bytes
        ensure_logo_assets()
        self._html_bytes: bytes = build_html_ui().encode("utf-8")
        if os.path.exists(SVG_PATH):
            with open(SVG_PATH, "rb") as f:
                self._logo_svg_bytes: bytes = f.read()
        else:
            self._logo_svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'></svg>"

        self._sky_jpeg_cache: Optional[bytes] = None
        self._closed: bool = False

    def _discover_cameras(self, initial: bool = False) -> None:
        try:
            devs = get_camera_devices(max_index=4)
            self._camera_devices = devs
            indices = [d["index"] for d in devs] if devs else []
            if not indices:
                cams = list_cameras(max_index=4)
                indices = [int(c.split("]")[0].replace("[", "").strip()) for c in cams if "]" in c]

            if not indices:
                indices = [0]

            # On initial launch: if current camera is index 0 and it's a Continuity Camera,
            # switch to the built-in laptop camera automatically!
            if initial and devs:
                default_idx = find_default_camera_index()
                cur_dev = next((d for d in devs if d["index"] == self.app_config.camera_index), None)
                if cur_dev and cur_dev.get("is_continuity") and default_idx != self.app_config.camera_index:
                    logger.info(f"Prioritizing built-in camera index {default_idx} over Continuity Camera.")
                    self.app_config.camera_index = default_idx
                    self.pipeline.switch_camera(default_idx)

            if self.app_config.camera_index not in indices:
                indices.insert(0, self.app_config.camera_index)
            self._available_cameras = indices
        except Exception as e:
            logger.debug(f"Camera discovery error: {e}")
            self._available_cameras = [self.app_config.camera_index]

    def get_current_camera_name(self) -> str:
        cur = self.app_config.camera_index
        for d in getattr(self, "_camera_devices", []):
            if d.get("index") == cur:
                return str(d.get("name", f"Camera 0{cur}"))
        return f"Camera 0{cur}"

    # ================================================================== In-Memory Resource Server (finflick://)
    def serve_resource(self, path: str) -> Tuple[bytes, str]:
        """Return (payload_bytes, content_type) for a finflick://app/* request."""
        clean_path = (path or "/index.html").split("?")[0]
        if clean_path in ("", "/", "/index.html"):
            return self._html_bytes, "text/html; charset=utf-8"
        if clean_path == "/logo.svg":
            return self._logo_svg_bytes, "image/svg+xml"
        if clean_path == "/frame.jpg":
            return self.get_frame_jpeg(), "image/jpeg"
        if clean_path == "/state.json":
            return self.get_state_json(), "application/json; charset=utf-8"
        return b"Not Found", "text/plain; charset=utf-8"

    def get_frame_jpeg(self) -> bytes:
        """Encode the latest RGB camera frame (with futuristic hand aura) or metallic sky backdrop as JPEG."""
        snap = self.pipeline.snapshot()
        if snap.display_frame is not None:
            bgr = cv2.cvtColor(snap.display_frame, cv2.COLOR_RGB2BGR)
            ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
            if ok:
                return buf.tobytes()

        if self._sky_jpeg_cache is None:
            w, h = 960, 600
            y = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
            x = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
            # Metallic sapphire-to-cerulean atmospheric backdrop
            b = 78.0 + 135.0 * (y ** 0.85) + 22.0 * np.cos(x * 3.14)
            g = 34.0 + 95.0 * (y ** 0.95) + 16.0 * np.sin(x * 2.5)
            r = 12.0 + 48.0 * (y ** 1.10)
            bgr = np.empty((h, w, 3), dtype=np.uint8)
            bgr[:, :, 0] = np.clip(b, 0, 255).astype(np.uint8)
            bgr[:, :, 1] = np.clip(g, 0, 255).astype(np.uint8)
            bgr[:, :, 2] = np.clip(r, 0, 255).astype(np.uint8)
            ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            self._sky_jpeg_cache = buf.tobytes() if ok else b""
        return self._sky_jpeg_cache

    def get_state_json(self) -> bytes:
        """Build the real-time telemetry & configuration state JSON payload."""
        now = time.monotonic()

        while True:
            try:
                evt = self._events.get_nowait()
                self._show_banner(evt, 1.6)
            except queue.Empty:
                break

        if now >= self._next_target_poll:
            self._update_target()
            self._next_target_poll = now + TARGET_POLL_SEC

        if now >= self._next_perm_poll:
            self._update_permission()
            self._next_perm_poll = now + PERMISSION_POLL_SEC

        snap = self.pipeline.snapshot()
        ctrl = self.controller

        # Compute state badge tag
        if ctrl.is_tracking_paused:
            state_tag = "PAUSED"
        elif snap.hold_progress is not None:
            state_tag = "CHARGING"
        elif ctrl.in_cooldown:
            state_tag = "COOLDOWN"
        elif snap.armed:
            state_tag = "ARMED"
        elif snap.hand_visible:
            state_tag = f"{snap.handedness.upper()} LOCK" if snap.handedness in ("Right", "Left") else "HAND LOCKED"
        else:
            state_tag = "STANDBY"

        # Compute bottom status message
        if now < self._banner_until:
            status_message = f"ACTION // {self._banner_text.upper()}"
        elif snap.camera_error:
            status_message = f"CAMERA // {snap.camera_error.upper()}"
        else:
            status_message = snap.label.upper()

        # Auto-hiding progress bar (only visible during active hold or cooldown)
        if not ctrl.is_tracking_paused and snap.hold_progress is not None:
            progress_visible = True
            progress_value = float(max(0.0, min(1.0, snap.hold_progress)))
        elif not ctrl.is_tracking_paused and ctrl.in_cooldown:
            progress_visible = True
            progress_value = float(
                max(0.0, min(1.0, 1.0 - ctrl.remaining_cooldown / max(0.01, self.app_config.cooldown_seconds)))
            )
        else:
            progress_visible = False
            progress_value = 0.0

        payload = {
            "fps": float(snap.processing_fps or snap.camera_fps or 60.0),
            "armed": bool(snap.armed),
            "paused": bool(ctrl.is_tracking_paused),
            "laser_active": bool(ctrl.is_laser_active),
            "in_cooldown": bool(ctrl.in_cooldown),
            "hand_visible": bool(snap.hand_visible),
            "pose_name": snap.pose_name,
            "handedness": snap.handedness,
            "recent_action": snap.recent_action,
            "recent_action_age": float(snap.recent_action_age),
            "state_tag": state_tag,
            "status_message": status_message,
            "progress_visible": progress_visible,
            "progress_value": progress_value,
            "target_text": self._target_app_text,
            "has_ext_focus": self._has_ext_focus,
            "ext_name": self._ext_name,
            "perm_ok": bool(self._perm_ok),
            "camera_name": self.get_current_camera_name(),
            "camera_devices": self._camera_devices,
            "stats": {
                "forward": int(ctrl.slides_forward_count),
                "backward": int(ctrl.slides_backward_count),
                "zoom": int(ctrl.zoom_count),
                "media": int(ctrl.media_toggles_count + ctrl.first_last_slides_count),
            },
            "config": {
                "camera_index": int(self.app_config.camera_index),
                "track_hand": self.app_config.track_hand,
                "invert_swipe_direction": bool(self.app_config.invert_swipe_direction),
                "mirror_camera": bool(self.app_config.mirror_camera),
                "auto_focus_target": bool(self.app_config.auto_focus_target),
                "draw_skeleton": bool(self.app_config.draw_skeleton),
                "show_motion_trail": bool(self.app_config.show_motion_trail),
                "show_hud_notifications": bool(self.app_config.show_hud_notifications),
                "sound_feedback": bool(self.app_config.sound_feedback),
                "swipe_min_distance_palms": float(self.app_config.swipe_min_distance_palms),
                "swipe_min_speed_palms": float(self.app_config.swipe_min_speed_palms),
                "cooldown_seconds": float(self.app_config.cooldown_seconds),
            },
        }
        return json.dumps(payload).encode("utf-8")

    # ================================================================== RPC Command Handler (JS -> Python)
    def handle_rpc(self, msg: Dict[str, Any]) -> None:
        """Process an interactive command sent from the WKWebView frontend."""
        cmd = msg.get("cmd", "")
        if cmd == "set_config":
            key = str(msg.get("key", ""))
            val = msg.get("value")
            if hasattr(self.app_config, key):
                setattr(self.app_config, key, val)
                if key == "mirror_camera":
                    self.pipeline.set_mirror(bool(val))
                elif key == "track_hand":
                    self.pipeline.reset_tracking()
                    self._show_banner(f"Hand Filter: {str(val).upper()}", 1.3)
                elif key == "sound_feedback":
                    self.controller.sound.enabled = bool(val)
                self.app_config.save()

        elif cmd == "apply_preset":
            name = str(msg.get("name", "BALANCED"))
            self.app_config.swipe_min_distance_palms = float(msg.get("dist", 1.5))
            self.app_config.swipe_min_speed_palms = float(msg.get("speed", 4.0))
            self.app_config.cooldown_seconds = float(msg.get("cd", 1.0))
            self.app_config.save()
            self._show_banner(f"Preset Applied: {name}", 1.4)

        elif cmd == "cycle_camera":
            self._discover_cameras()
            cur = self.app_config.camera_index
            if cur in self._available_cameras and len(self._available_cameras) > 1:
                nxt = self._available_cameras[(self._available_cameras.index(cur) + 1) % len(self._available_cameras)]
            elif self._available_cameras:
                nxt = self._available_cameras[0]
            else:
                nxt = 0
            self.app_config.camera_index = nxt
            self.pipeline.switch_camera(nxt)
            self.app_config.save()
            cam_name = self.get_current_camera_name()
            self._show_banner(f"Camera: {cam_name}", 1.6)

        elif cmd == "set_camera":
            self._discover_cameras()
            nxt = int(msg.get("index", 0))
            self.app_config.camera_index = nxt
            self.pipeline.switch_camera(nxt)
            self.app_config.save()
            cam_name = self.get_current_camera_name()
            self._show_banner(f"Camera: {cam_name}", 1.6)

        elif cmd == "cycle_hand":
            order = ["any", "right", "left"]
            cur = self.app_config.track_hand if self.app_config.track_hand in order else "any"
            nxt = order[(order.index(cur) + 1) % len(order)]
            self.app_config.track_hand = nxt
            self.pipeline.reset_tracking()
            self.app_config.save()
            self._show_banner(f"Hand Filter: {nxt.upper()}", 1.4)

        elif cmd == "focus_slides":
            ext = get_last_external_app()
            if ext and ext.pid != os.getpid():
                activate_app(ext.pid)
                self._show_banner(f"Focused {ext.name}", 1.3)
            else:
                self._show_banner("Click your presentation window once to link it", 2.0)

        elif cmd == "open_permissions":
            request_accessibility_permission()
            open_accessibility_settings()
            self._show_banner("Enable Accessibility in macOS System Settings", 2.2)

        elif cmd == "toggle_pause":
            paused = not self.controller.is_tracking_paused
            self.controller.set_paused(paused)
            self.pipeline.reset_tracking()

        elif cmd == "toggle_laser":
            self.controller.trigger_action("LASER_POINTER")

        elif cmd == "countdown_test":
            action = str(msg.get("action", "NEXT_SLIDE"))
            self._start_countdown_test(action)

        elif cmd == "play_intro_sound":
            self.controller.sound.play_intro()

        elif cmd == "stop_intro_sound":
            self.controller.sound.stop_intro()

    def _start_countdown_test(self, action: str, remaining: int = 3) -> None:
        if self._countdown_timer is not None:
            self._countdown_timer.cancel()
            self._countdown_timer = None

        if remaining > 0:
            self._show_banner(f"Testing {action} in {remaining}s — switch to slides", 1.1)
            self._countdown_timer = threading.Timer(
                1.0, lambda: self._start_countdown_test(action, remaining - 1)
            )
            self._countdown_timer.daemon = True
            self._countdown_timer.start()
            return

        if action == "TOGGLE_PAUSE":
            self.controller.set_paused(not self.controller.is_tracking_paused)
            self.pipeline.reset_tracking()
        else:
            self.controller.trigger_action(action, bypass_cooldown=True)

    def _show_banner(self, text: str, duration: float = 1.5) -> None:
        self._banner_text = text
        self._banner_until = time.monotonic() + duration

    def _update_target(self) -> None:
        app, profile = self.controller.current_target()
        if app is None:
            self._has_ext_focus = False
            self._target_app_text = f"Target: {profile.name}"
        elif app.pid == os.getpid():
            ext = get_last_external_app()
            if ext and ext.pid != os.getpid():
                self._has_ext_focus = True
                self._ext_name = ext.name
                self._target_app_text = f"Target: {ext.name} (Auto-Focus)"
            else:
                self._has_ext_focus = False
                self._target_app_text = "Target: Click your slides window once"
        else:
            self._has_ext_focus = False
            self._target_app_text = f"Target: {app.name}"

    def _update_permission(self) -> None:
        granted = check_accessibility_permission()
        self._perm_ok = bool(granted) if granted is not None else False

    # ================================================================== Native macOS AppKit + WKWebView Lifecycle
    def mainloop(self) -> None:
        """Launch the native macOS AppKit NSWindow + GPU-accelerated WKWebView event loop."""
        self.pipeline.start()
        self.controller.sound.play_intro()

        import AppKit
        import Foundation
        import objc

        objc.loadBundle(
            "WebKit",
            bundle_path="/System/Library/Frameworks/WebKit.framework",
            module_globals=globals(),
        )

        app_host = self

        class _FinFlickWebBridge(Foundation.NSObject):
            def userContentController_didReceiveScriptMessage_(self, _controller, message):
                try:
                    body = message.body()
                    if isinstance(body, str):
                        data = json.loads(body)
                    else:
                        data = dict(body)
                    app_host.handle_rpc(data)
                except Exception as e:
                    logger.debug(f"RPC bridge error: {e}")

            def webView_startURLSchemeTask_(self, _webview, task):
                try:
                    url = task.request().URL()
                    path = url.path() if url is not None else "/index.html"
                    payload, ctype = app_host.serve_resource(path)
                    resp = Foundation.NSHTTPURLResponse.alloc().initWithURL_statusCode_HTTPVersion_headerFields_(
                        url,
                        200,
                        "HTTP/1.1",
                        {
                            "Content-Type": ctype,
                            "Cache-Control": "no-store, no-cache, must-revalidate",
                            "Access-Control-Allow-Origin": "*",
                        },
                    )
                    task.didReceiveResponse_(resp)
                    ns_data = Foundation.NSData.dataWithBytes_length_(payload, len(payload))
                    task.didReceiveData_(ns_data)
                    task.didFinish()
                except Exception as e:
                    logger.debug(f"Scheme task error: {e}")

            def webView_stopURLSchemeTask_(self, _webview, _task):
                pass

            def applicationDidFinishLaunching_(self, _notification):
                if getattr(app_host, "_window_ref", None) is not None:
                    app_host._window_ref.makeKeyAndOrderFront_(None)
                    app_host._window_ref.orderFrontRegardless()
                AppKit.NSApp.activateIgnoringOtherApps_(True)

            def applicationShouldTerminateAfterLastWindowClosed_(self, _app):
                return True

            def windowWillClose_(self, _notification):
                app_host.on_close()
                AppKit.NSApp.terminate_(None)

        ns_app = AppKit.NSApplication.sharedApplication()
        ns_app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

        # Apply sleek dark metallic window chrome
        dark_appearance = AppKit.NSAppearance.appearanceNamed_(AppKit.NSAppearanceNameDarkAqua)
        if dark_appearance is not None:
            ns_app.setAppearance_(dark_appearance)

        # Set dock icon from FinFlick metallic-blue logo
        ensure_logo_assets()
        if os.path.exists(LOGO_PATH):
            ns_img = AppKit.NSImage.alloc().initWithContentsOfFile_(LOGO_PATH)
            if ns_img is not None:
                ns_app.setApplicationIconImage_(ns_img)

        bridge = _FinFlickWebBridge.alloc().init()
        self._bridge_ref = bridge
        ns_app.setDelegate_(bridge)

        wk_cfg = WKWebViewConfiguration.alloc().init()  # noqa: F821
        wk_cfg.userContentController().addScriptMessageHandler_name_(bridge, "finflick")
        wk_cfg.setURLSchemeHandler_forURLScheme_(bridge, "finflick")

        rect = Foundation.NSMakeRect(120.0, 90.0, 1240.0, 780.0)
        style_mask = (
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable
            | AppKit.NSWindowStyleMaskMiniaturizable
            | AppKit.NSWindowStyleMaskResizable
        )
        window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            style_mask,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        window.setTitle_("FinFlick — Touchless Presentation Control")
        window.setMinSize_(Foundation.NSMakeSize(1020.0, 660.0))
        window.setBackgroundColor_(
            AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.02, 0.05, 0.11, 1.0)
        )
        window.setDelegate_(bridge)
        self._window_ref = window

        webview = WKWebView.alloc().initWithFrame_configuration_(rect, wk_cfg)  # noqa: F821
        webview.setValue_forKey_(False, "drawsBackground")
        window.setContentView_(webview)
        self._webview_ref = webview

        req_url = Foundation.NSURL.URLWithString_("finflick://app/index.html")
        req = Foundation.NSURLRequest.requestWithURL_(req_url)
        webview.loadRequest_(req)

        window.center()
        window.makeKeyAndOrderFront_(None)
        window.orderFrontRegardless()
        ns_app.activateIgnoringOtherApps_(True)

        from PyObjCTools import AppHelper

        AppHelper.runEventLoop(installInterrupt=True)

    def on_close(self) -> None:
        if self._closed:
            return
        self._closed = True
        logger.info("Closing FinFlick…")
        if self._countdown_timer is not None:
            self._countdown_timer.cancel()
        self.controller.sound.stop_intro()
        self.app_config.save()
        self.pipeline.stop()


# Backward-compatible alias
SlidePassApp = FinFlickApp
