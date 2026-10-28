"""Presentation Controller: turns gesture actions into keystrokes for the frontmost app."""

import os
import time
import logging
import threading
from typing import Callable, Optional

from pynput.keyboard import Key, Controller as KeyboardController

from core.config import AppConfig
from core.app_profiles import (
    GENERIC,
    FrontmostApp,
    KeyCombo,
    KeyProfile,
    detect_frontmost_app,
    profile_for_bundle,
    get_last_external_app,
    activate_app,
)
from utils.sound_feedback import SoundFeedback
from utils.apple_script_bridge import dispatch_powerpoint, dispatch_keynote

logger = logging.getLogger("FinFlick.Controller")

# Actions gated by the navigation cooldown. Hold gestures (fist / palm / peace / first_slide / last_slide)
# are already debounced by their hold time and fire once per hold, so they bypass it.
NAV_ACTIONS = {"NEXT_SLIDE", "PREV_SLIDE", "PLAY_PAUSE"}
ZOOM_ACTIONS = {"ZOOM_IN", "ZOOM_OUT"}

ACTION_LABELS = {
    "NEXT_SLIDE": "Next Slide",
    "PREV_SLIDE": "Previous Slide",
    "PLAY_PAUSE": "Play / Pause",
    "BLACKOUT": "Blank Screen",
    "START_PRESENTATION": "Start Presenting",
    "FIRST_SLIDE": "First Slide",
    "LAST_SLIDE": "Last Slide",
    "ZOOM_IN": "Zoom In (+)",
    "ZOOM_OUT": "Zoom Out (-)",
    "LASER_POINTER": "Laser Pointer",
    "WHITE_SCREEN": "White Screen",
}

ACTION_SOUNDS = {
    "NEXT_SLIDE": "next",
    "PREV_SLIDE": "prev",
    "PLAY_PAUSE": "action",
    "BLACKOUT": "sleep",
    "START_PRESENTATION": "wake",
    "FIRST_SLIDE": "wake",
    "LAST_SLIDE": "action",
    "ZOOM_IN": "next",
    "ZOOM_OUT": "prev",
    "LASER_POINTER": "action",
    "WHITE_SCREEN": "wake",
}

_SPECIAL_KEYS = {
    "right": Key.right,
    "left": Key.left,
    "up": Key.up,
    "down": Key.down,
    "space": Key.space,
    "return": Key.enter,
    "enter": Key.enter,
    "esc": Key.esc,
    "page_down": Key.page_down,
    "page_up": Key.page_up,
    "home": Key.home,
    "end": Key.end,
    "cmd": Key.cmd,
    "alt": Key.alt,
    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "f5": Key.f5,
}


class PresentationController:
    """Translates high-level gesture actions into OS-level keyboard events.

    Thread-safe: may be called from the processing thread and the UI thread.
    """

    def __init__(
        self,
        config: AppConfig,
        sound_feedback: Optional[SoundFeedback] = None,
        app_detector: Callable[[], Optional[FrontmostApp]] = detect_frontmost_app,
        clock: Callable[[], float] = time.monotonic,
        powerpoint_dispatcher: Optional[Callable[[str], bool]] = dispatch_powerpoint,
        keynote_dispatcher: Optional[Callable[[str], bool]] = dispatch_keynote,
    ):
        self.config = config
        self.sound = sound_feedback or SoundFeedback(enabled=config.sound_feedback)
        self.keyboard = KeyboardController()
        self._detect_app = app_detector
        self._clock = clock
        self._powerpoint_dispatch = powerpoint_dispatcher
        self._keynote_dispatch = keynote_dispatcher
        self._lock = threading.RLock()

        self.last_nav_time: float = float("-inf")
        self.last_zoom_time: float = float("-inf")
        self.last_action_name: str = "Ready"
        self.is_tracking_paused: bool = False
        self.is_laser_active: bool = False

        # Metrics
        self.slides_forward_count: int = 0
        self.slides_backward_count: int = 0
        self.media_toggles_count: int = 0
        self.first_last_slides_count: int = 0
        self.zoom_count: int = 0

        # Called as callback(label: str). NOTE: runs on the caller's thread.
        self.action_callback: Optional[Callable[[str], None]] = None

        self._kbd_listener = None
        self._start_keyboard_listener()

    def _start_keyboard_listener(self) -> None:
        try:
            from pynput import keyboard

            def on_press(key):
                if not self.is_laser_active:
                    return
                is_esc = key == keyboard.Key.esc
                is_l = False
                try:
                    if hasattr(key, "char") and key.char and key.char.lower() == "l":
                        is_l = True
                except Exception:
                    pass

                if is_esc or is_l:
                    logger.info("Physical keyboard exit detected (Esc/L)")
                    self.set_laser_active(False, send_keystroke=False)

            self._kbd_listener = keyboard.Listener(on_press=on_press)
            self._kbd_listener.daemon = True
            self._kbd_listener.start()
        except Exception as e:
            logger.debug(f"Could not start keyboard listener: {e}")
            self._kbd_listener = None

    def set_action_callback(self, callback: Callable[[str], None]) -> None:
        self.action_callback = callback

    # ---------------- Cooldown ----------------
    @property
    def in_cooldown(self) -> bool:
        return self.remaining_cooldown > 0.0

    @property
    def remaining_cooldown(self) -> float:
        return max(0.0, self.config.cooldown_seconds - (self._clock() - self.last_nav_time))

    # ---------------- Profiles ----------------
    def current_target(self) -> "tuple[Optional[FrontmostApp], KeyProfile]":
        app = self._detect_app()
        return app, profile_for_bundle(app.bundle_id if app else None)

    # ---------------- Actions ----------------
    def set_paused(self, paused: bool) -> None:
        with self._lock:
            if self.is_tracking_paused == paused:
                return
            self.is_tracking_paused = paused
            if paused and self.is_laser_active:
                self.is_laser_active = False
            self.last_action_name = "Tracking Paused" if paused else "Tracking Resumed"
            if not paused:
                self.last_nav_time = float("-inf")  # act immediately after resuming
                self.last_zoom_time = float("-inf")
        self.sound.play("sleep" if paused else "wake")
        logger.info(self.last_action_name)
        self._notify(self.last_action_name)

    def set_laser_active(self, active: bool, send_keystroke: bool = True) -> None:
        with self._lock:
            if self.is_laser_active == active:
                return
            self.is_laser_active = active
            app, profile = self.current_target()
            target = app.name if app else profile.name
            if active:
                self.last_action_name = f"Laser Pointer Active (Aim with hand) → {target}"
            else:
                self.last_action_name = f"Laser Pointer Deactivated → {target}"
            if send_keystroke:
                combo = self._combo_for("LASER_POINTER", profile)
                if combo is not None:
                    self._send_combo(combo)
        self.sound.play("wake" if active else "sleep")
        logger.info(self.last_action_name)
        self._notify(self.last_action_name)

    def trigger_action(self, action: str, bypass_cooldown: bool = False, details: str = "") -> bool:
        """Executes an action. Returns True if keys were sent (or pause toggled)."""
        if action == "TOGGLE_PAUSE":
            self.set_paused(not self.is_tracking_paused)
            return True

        if action == "LASER_POINTER_AND_NAV":
            nav_action = details or "NEXT_SLIDE"
            self.set_laser_active(False, send_keystroke=True)
            return self.trigger_action(nav_action, bypass_cooldown=True)

        with self._lock:
            if self.is_tracking_paused:
                return False
            is_nav = action in NAV_ACTIONS
            is_zoom = action in ZOOM_ACTIONS

            if is_nav and not bypass_cooldown and self.in_cooldown:
                return False

            # Shorter zoom refresh: speakers often zoom multiple times in quick succession
            if is_zoom and not bypass_cooldown and (self._clock() - self.last_zoom_time < self.config.zoom_cooldown_sec):
                return False

            app, profile = self.current_target()

            # If FinFlick itself is frontmost and auto_focus_target is enabled,
            # switch focus back to the presentation window so keystrokes land on slides.
            if self.config.auto_focus_target and app and app.pid == os.getpid():
                external_app = get_last_external_app()
                if external_app and external_app.pid != os.getpid():
                    if activate_app(external_app):
                        time.sleep(0.04)  # brief grace period for macOS window focus switch
                        app = external_app
                        profile = profile_for_bundle(external_app.bundle_id)

            # Direct AppleScript bridge for PowerPoint and Keynote (works in edit mode and without accessibility permissions)
            handled_by_script = False
            if profile.name == "PowerPoint" and self._powerpoint_dispatch:
                handled_by_script = bool(self._powerpoint_dispatch(action))
            elif profile.name == "Keynote" and self._keynote_dispatch:
                handled_by_script = bool(self._keynote_dispatch(action))

            combo = self._combo_for(action, profile)
            # Only send simulated keystroke if NOT already handled by native AppleScript!
            # This completely eliminates the double-slide skip bug in PowerPoint/Keynote.
            if not handled_by_script:
                if combo is not None:
                    self._send_combo(combo)
                elif profile.name not in ("PowerPoint", "Keynote"):
                    label = f"{ACTION_LABELS.get(action, action)} — not supported in {profile.name}"
                    logger.info(label)
                    self.last_action_name = label
                    self._notify(label)
                    return False

            if is_zoom:
                self.last_zoom_time = self._clock()
                self.zoom_count += 1
            elif is_nav:
                self.last_nav_time = self._clock()
            elif action in ("FIRST_SLIDE", "LAST_SLIDE"):
                self.first_last_slides_count += 1

            if action == "NEXT_SLIDE":
                self.slides_forward_count += 1
            elif action == "PREV_SLIDE":
                self.slides_backward_count += 1
            elif action == "PLAY_PAUSE":
                self.media_toggles_count += 1

            if action == "LASER_POINTER":
                self.is_laser_active = not self.is_laser_active
                target = app.name if app else profile.name
                if self.is_laser_active:
                    label = f"Laser Pointer Active (Aim with hand) → {target}"
                else:
                    label = f"Laser Pointer Deactivated → {target}"
                self.last_action_name = label
            else:
                target = app.name if app else profile.name
                label = f"{ACTION_LABELS.get(action, action)} → {target}"
                self.last_action_name = label

        sound_name = ("wake" if self.is_laser_active else "sleep") if action == "LASER_POINTER" else ACTION_SOUNDS.get(action, "action")
        self.sound.play(sound_name)
        combo_str = '+'.join(combo) if combo else 'native'
        logger.info(f"Triggered: {label} (keys: {combo_str})")
        self._notify(label)
        return True

    @staticmethod
    def _combo_for(action: str, profile: KeyProfile) -> Optional[KeyCombo]:
        return {
            "NEXT_SLIDE": profile.next_slide,
            "PREV_SLIDE": profile.prev_slide,
            "PLAY_PAUSE": profile.play_pause,
            "BLACKOUT": profile.blackout,
            "START_PRESENTATION": profile.start_presentation,
            "FIRST_SLIDE": profile.first_slide,
            "LAST_SLIDE": profile.last_slide,
            "ZOOM_IN": profile.zoom_in,
            "ZOOM_OUT": profile.zoom_out,
            "LASER_POINTER": profile.laser_pointer,
            "WHITE_SCREEN": profile.white_screen,
        }.get(action)

    def _notify(self, label: str) -> None:
        if self.action_callback:
            try:
                self.action_callback(label)
            except Exception as e:
                logger.debug(f"Action callback failed: {e}")

    def _send_combo(self, combo: KeyCombo) -> None:
        """Presses modifiers, taps the final key, releases modifiers in reverse order."""
        keys = [_SPECIAL_KEYS.get(k.lower(), k) for k in combo]
        modifiers, final = keys[:-1], keys[-1]
        pressed = []
        try:
            for mod in modifiers:
                self.keyboard.press(mod)
                pressed.append(mod)
            self.keyboard.press(final)
            time.sleep(0.03)
            self.keyboard.release(final)
        except Exception as e:
            logger.error(f"Failed to send keys {combo}: {e}")
        finally:
            for mod in reversed(pressed):
                try:
                    self.keyboard.release(mod)
                except Exception:
                    pass
