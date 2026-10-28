"""macOS helpers: Accessibility permission checks and App Nap prevention."""

import logging
import platform
import subprocess
from typing import Optional

logger = logging.getLogger("FinFlick.macOS")

_activity_token = None  # must stay referenced for the activity to remain active


def is_macos() -> bool:
    return platform.system() == "Darwin"


def check_accessibility_permission() -> Optional[bool]:
    """True/False on macOS, None if it cannot be determined.

    Without this permission, synthetic key presses are silently dropped by macOS.
    The permission is granted to the *host* app (Terminal, iTerm, VS Code...), and
    macOS usually requires that app to be restarted after granting it.
    """
    if not is_macos():
        return True
    try:
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except Exception as e:
        logger.debug(f"Could not query Accessibility permission: {e}")
        return None


def request_accessibility_permission() -> bool:
    """Triggers the macOS system dialog to authorize Accessibility for the host app."""
    if not is_macos():
        return True
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
        return bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}))
    except Exception as e:
        logger.debug(f"Could not request Accessibility permission: {e}")
        return False


def open_accessibility_settings() -> None:
    if is_macos():
        subprocess.run(
            ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
            check=False,
        )


def open_camera_settings() -> None:
    if is_macos():
        subprocess.run(
            ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera"],
            check=False,
        )


def prevent_app_nap(reason: str = "FinFlick is tracking presentation gestures") -> bool:
    """Stops macOS from throttling FinFlick while it sits behind a fullscreen presentation."""
    global _activity_token
    if not is_macos() or _activity_token is not None:
        return _activity_token is not None
    try:
        from Foundation import (
            NSProcessInfo,
            NSActivityUserInitiated,
            NSActivityLatencyCritical,
        )
        _activity_token = NSProcessInfo.processInfo().beginActivityWithOptions_reason_(
            NSActivityUserInitiated | NSActivityLatencyCritical, reason
        )
        logger.info("App Nap disabled for this session.")
        return True
    except Exception as e:
        logger.warning(f"Could not disable App Nap: {e}")
        return False
