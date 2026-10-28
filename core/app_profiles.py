"""Per-application key profiles and frontmost-app detection.

Keystrokes always go to whichever app is frontmost, so FinFlick detects that app and
uses the right shortcuts for it. Shortcuts below are the documented macOS ones:
  * Google Slides: K = play/pause video, B = black screen, Cmd+Return = present
  * PowerPoint:    Option+P = play/pause media, B = black screen, Cmd+Return = present from current slide
  * Keynote:       K = pause/resume movie, B = black screen, Option+Cmd+P = play slideshow
  * Preview:       Shift+Cmd+F = slideshow
"""

import logging
import platform
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger("FinFlick.Profiles")

# A key combo is a tuple of key names, e.g. ("cmd", "return") or ("right",)
KeyCombo = Tuple[str, ...]


@dataclass(frozen=True)
class KeyProfile:
    name: str
    next_slide: Optional[KeyCombo] = ("right",)
    prev_slide: Optional[KeyCombo] = ("left",)
    play_pause: Optional[KeyCombo] = None
    blackout: Optional[KeyCombo] = ("b",)
    start_presentation: Optional[KeyCombo] = None
    first_slide: Optional[KeyCombo] = ("home",)
    last_slide: Optional[KeyCombo] = ("end",)
    zoom_in: Optional[KeyCombo] = ("cmd", "=")
    zoom_out: Optional[KeyCombo] = ("cmd", "-")
    laser_pointer: Optional[KeyCombo] = ("l",)
    white_screen: Optional[KeyCombo] = ("w",)


GENERIC = KeyProfile(name="Generic", play_pause=("space",))
GOOGLE_SLIDES = KeyProfile(
    name="Google Slides (browser)",
    play_pause=("k",),
    start_presentation=("cmd", "return"),
    laser_pointer=("l",),
    white_screen=("w",),
)
POWERPOINT = KeyProfile(
    name="PowerPoint",
    play_pause=("alt", "p"),
    start_presentation=("cmd", "return"),
    zoom_in=("=",),
    zoom_out=("-",),
    laser_pointer=("cmd", "l"),
    white_screen=("w",),
)
KEYNOTE = KeyProfile(
    name="Keynote",
    play_pause=("k",),
    start_presentation=("alt", "cmd", "p"),
    laser_pointer=("cmd", "l"),
    white_screen=("w",),
)
PREVIEW = KeyProfile(
    name="Preview (PDF)",
    blackout=None,
    start_presentation=("shift", "cmd", "f"),
    laser_pointer=None,
    white_screen=None,
)
ADOBE_ACROBAT = KeyProfile(
    name="Adobe Acrobat",
    blackout=None,
    start_presentation=("cmd", "l"),
    laser_pointer=None,
    white_screen=None,
)
CANVA = KeyProfile(name="Canva", play_pause=("space",), start_presentation=("alt", "cmd", "p"), laser_pointer=None, white_screen=None)
PITCH = KeyProfile(name="Pitch", play_pause=("space",), start_presentation=("cmd", "return"), laser_pointer=None, white_screen=None)

BROWSER_BUNDLE_IDS = {
    "com.google.Chrome",
    "com.google.Chrome.canary",
    "com.apple.Safari",
    "com.apple.SafariTechnologyPreview",
    "org.mozilla.firefox",
    "com.microsoft.edgemac",
    "com.brave.Browser",
    "company.thebrowser.Browser",  # Arc
    "com.operasoftware.Opera",
    "com.vivaldi.Vivaldi",
    "com.kagi.kagisafari",         # Orion
    "com.duckduckgo.macos.browser",
}

BUNDLE_PROFILES = {
    "com.microsoft.Powerpoint": POWERPOINT,
    "com.apple.iWork.Keynote": KEYNOTE,
    "com.apple.Preview": PREVIEW,
    "com.adobe.Reader": ADOBE_ACROBAT,
    "com.adobe.Acrobat.Pro": ADOBE_ACROBAT,
    "com.canva.CanvaDesktop": CANVA,
    "com.pitch.desktop": PITCH,
}


@dataclass(frozen=True)
class FrontmostApp:
    name: str
    bundle_id: Optional[str]
    pid: Optional[int]


_last_external_app: Optional[FrontmostApp] = None


def get_last_external_app() -> Optional[FrontmostApp]:
    """Returns the most recent frontmost application that was not FinFlick itself."""
    return _last_external_app


def set_last_external_app(app: Optional[FrontmostApp]) -> None:
    """Manually sets or updates the remembered external app (useful for tests or explicit focus)."""
    global _last_external_app
    _last_external_app = app


def activate_app(app: Optional[FrontmostApp]) -> bool:
    """Activates the given app window on macOS so it receives keyboard focus."""
    if not app or not app.pid or platform.system() != "Darwin":
        return False
    try:
        from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
        running_app = NSRunningApplication.runningApplicationWithProcessIdentifier_(app.pid)
        if running_app:
            return bool(running_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps))
    except Exception as e:
        logger.debug(f"Failed to activate app {app.name}: {e}")
    return False


def profile_for_bundle(bundle_id: Optional[str]) -> KeyProfile:
    if not bundle_id:
        return GENERIC
    if bundle_id in BUNDLE_PROFILES:
        return BUNDLE_PROFILES[bundle_id]
    if bundle_id in BROWSER_BUNDLE_IDS:
        # We can't see which tab is open without Screen Recording permission,
        # so assume a browser means Google Slides (also fine for most web decks).
        return GOOGLE_SLIDES
    return GENERIC


def detect_frontmost_app() -> Optional[FrontmostApp]:
    """Returns the app owning the frontmost on-screen window (macOS only).

    Uses NSWorkspace.frontmostApplication for canonical active window tracking,
    with Quartz window list as a fallback.
    """
    global _last_external_app
    if platform.system() != "Darwin":
        return None
    try:
        import os
        from AppKit import NSWorkspace

        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is not None:
            pid = int(app.processIdentifier()) or None
            name = str(app.localizedName() or "Unknown")
            bundle_id = str(app.bundleIdentifier() or "") or None
            front = FrontmostApp(name=name, bundle_id=bundle_id, pid=pid)
            if pid and pid != os.getpid():
                _last_external_app = front
            return front
    except Exception as e:
        logger.debug(f"NSWorkspace frontmost app query failed: {e}")

    try:
        import os
        import Quartz
        from AppKit import NSRunningApplication

        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID,
        )
        for win in windows or []:
            if win.get(Quartz.kCGWindowLayer, 1) != 0:
                continue  # skip menu bar, dock, overlays
            pid = int(win.get(Quartz.kCGWindowOwnerPID, 0)) or None
            name = str(win.get(Quartz.kCGWindowOwnerName, "Unknown"))
            bundle_id = None
            if pid:
                app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
                if app is not None and app.bundleIdentifier():
                    bundle_id = str(app.bundleIdentifier())
            front = FrontmostApp(name=name, bundle_id=bundle_id, pid=pid)
            if pid and pid != os.getpid():
                _last_external_app = front
            return front
    except Exception as e:
        logger.debug(f"Frontmost app detection fallback failed: {e}")
    return None
