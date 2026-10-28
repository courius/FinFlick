"""Threaded webcam capture that always serves the newest frame (no buffer lag)."""

import time
import threading
import logging
from dataclasses import dataclass
import platform
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger("FinFlick.Camera")


@dataclass
class Frame:
    image: np.ndarray   # BGR, already mirrored if mirroring is on
    frame_id: int       # strictly increasing
    timestamp: float    # time.monotonic() at capture


class CameraFeed:
    """Grabs frames on a background thread; consumers wait for the next new frame."""

    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720, fps: int = 30, mirror: bool = True):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = fps
        self.mirror = mirror

        self.cap: Optional[cv2.VideoCapture] = None
        self.running: bool = False
        self.error: Optional[str] = None
        self.thread: Optional[threading.Thread] = None

        self._latest: Optional[Frame] = None
        self._next_id: int = 1
        self._cond = threading.Condition()

        self.fps: float = 0.0
        self._fps_count: int = 0
        self._fps_start: float = time.monotonic()

    def start(self) -> bool:
        if self.running:
            return True

        logger.info(f"Opening camera index {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.error = (
                f"Could not open camera {self.camera_index}. On macOS, allow camera access for your "
                "Terminal/IDE in System Settings → Privacy & Security → Camera, or try --camera 1."
            )
            logger.error(self.error)
            self.cap.release()
            self.cap = None
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Camera opened at {actual_w}x{actual_h}")

        self.error = None
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, name="CameraCapture", daemon=True)
        self.thread.start()
        return True

    def stop(self) -> None:
        self.running = False
        with self._cond:
            self._cond.notify_all()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("Camera stopped.")

    def switch_camera(self, new_index: int) -> bool:
        """Dynamically switches to a different camera device without recreating the pipeline."""
        if new_index == self.camera_index and self.running:
            return True
        logger.info(f"Switching camera to index {new_index}...")
        was_running = self.running
        self.stop()
        self.camera_index = new_index
        if was_running:
            return self.start()
        return True

    def wait_for_frame(self, after_id: int, timeout: float = 0.5) -> Optional[Frame]:
        """Blocks until a frame newer than `after_id` is available (or timeout)."""
        with self._cond:
            if self._latest is None or self._latest.frame_id <= after_id:
                self._cond.wait(timeout=timeout)
            if self._latest is not None and self._latest.frame_id > after_id:
                return self._latest
            return None

    def _capture_loop(self) -> None:
        consecutive_failures = 0
        while self.running and self.cap is not None:
            ok, image = self.cap.read()
            if not ok or image is None:
                consecutive_failures += 1
                if consecutive_failures > 60:
                    self.error = "Camera stopped delivering frames (unplugged or in use by another app?)."
                    logger.error(self.error)
                    consecutive_failures = 0
                time.sleep(0.01)
                continue
            consecutive_failures = 0

            if self.mirror:
                image = cv2.flip(image, 1)

            now = time.monotonic()
            self._fps_count += 1
            if now - self._fps_start >= 1.0:
                self.fps = self._fps_count / (now - self._fps_start)
                self._fps_count = 0
                self._fps_start = now

            with self._cond:
                self._latest = Frame(image=image, frame_id=self._next_id, timestamp=now)
                self._next_id += 1
                self._cond.notify_all()


class _SilenceStderr:
    """Temporarily silences C-level stderr to avoid OpenCV probe spam."""
    def __enter__(self):
        try:
            import os
            self.devnull = os.open(os.devnull, os.O_WRONLY)
            self.saved_stderr = os.dup(2)
            os.dup2(self.devnull, 2)
            self.active = True
        except Exception:
            self.active = False
        return self

    def __exit__(self, *args):
        if getattr(self, "active", False):
            import os
            try:
                os.dup2(self.saved_stderr, 2)
                os.close(self.saved_stderr)
                os.close(self.devnull)
            except Exception:
                pass


def _query_macos_cameras() -> List[Dict[str, Any]]:
    """Query macOS AVFoundation for real camera device names and types."""
    if platform.system() != "Darwin":
        return []
    devices: List[Dict[str, Any]] = []
    try:
        import objc
        objc.loadBundle(
            "AVFoundation",
            bundle_path="/System/Library/Frameworks/AVFoundation.framework",
            module_globals=globals(),
        )
        AVCaptureDevice = objc.lookUpClass("AVCaptureDevice")
        AVCaptureDeviceDiscoverySession = objc.lookUpClass("AVCaptureDeviceDiscoverySession")
        types = [
            "AVCaptureDeviceTypeBuiltInWideAngleCamera",
            "AVCaptureDeviceTypeContinuityCamera",
            "AVCaptureDeviceTypeExternal",
            "AVCaptureDeviceTypeDeskViewCamera",
        ]
        session = AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
            types, "vide", 0
        )
        av_devices = list(session.devices() or [])
        if not av_devices and hasattr(AVCaptureDevice, "devicesWithMediaType_"):
            av_devices = list(AVCaptureDevice.devicesWithMediaType_("vide") or [])

        for idx, dev in enumerate(av_devices):
            name = str(dev.localizedName() or f"Camera {idx}")
            dtype = str(getattr(dev, "deviceType", lambda: "")() or "")
            is_cont = (
                ("continuity" in dtype.lower())
                or ("iphone" in name.lower())
                or ("ipad" in name.lower())
                or bool(getattr(dev, "isContinuityCamera", lambda: False)())
            )
            is_builtin = (
                ("builtin" in dtype.lower())
                or ("facetime" in name.lower())
                or ("built-in" in name.lower())
                or ("macbook" in name.lower())
            )
            devices.append({
                "index": idx,
                "name": name,
                "is_continuity": is_cont,
                "is_builtin": is_builtin,
            })
    except Exception as e:
        logger.debug(f"AVFoundation camera query error: {e}")
    return devices


def get_camera_devices(max_index: int = 5) -> List[Dict[str, Any]]:
    """Returns detected camera devices with friendly names, continuity flags, and resolutions."""
    try:
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
    except Exception:
        pass

    mac_cams = {d["index"]: d for d in _query_macos_cameras()}
    found: List[Dict[str, Any]] = []

    with _SilenceStderr():
        for idx in range(max_index):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()

                meta = mac_cams.get(idx, {})
                name = meta.get("name")
                if not name:
                    if idx == 0 and platform.system() == "Darwin":
                        name = "FaceTime HD Camera (Built-in)"
                    else:
                        name = f"Camera {idx:02d}"

                found.append({
                    "index": idx,
                    "name": name,
                    "width": w,
                    "height": h,
                    "is_continuity": meta.get("is_continuity", "iphone" in name.lower()),
                    "is_builtin": meta.get("is_builtin", "facetime" in name.lower() or "built-in" in name.lower()),
                })
            else:
                cap.release()

    return found


def find_default_camera_index() -> int:
    """Finds the best camera index for presentations, prioritizing built-in laptop cameras over Continuity Cameras."""
    devices = get_camera_devices()
    if not devices:
        return 0
    # 1. Prefer built-in laptop camera
    for d in devices:
        if d.get("is_builtin") and not d.get("is_continuity"):
            return d["index"]
    # 2. Prefer any external USB webcam (not continuity)
    for d in devices:
        if not d.get("is_continuity"):
            return d["index"]
    # 3. Fallback
    return devices[0]["index"]


def list_cameras(max_index: int = 5) -> List[str]:
    """Probes camera indices (useful when an iPhone Continuity Camera or USB webcam is attached)."""
    devices = get_camera_devices(max_index=max_index)
    if devices:
        return [f"[{d['index']}] {d['name']} ({d['width']}x{d['height']})" for d in devices]

    try:
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
    except Exception:
        pass

    found = []
    with _SilenceStderr():
        for idx in range(max_index):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                found.append(f"[{idx}] {w}x{h}")
            cap.release()
    return found
