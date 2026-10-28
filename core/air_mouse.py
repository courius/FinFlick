"""Air Mouse Controller: maps 3D fingertip tracking to macOS system cursor.

Translates normalized [0..1] camera coordinates to smooth macOS screen positions
with tremor rejection and speed-adaptive exponential smoothing.
"""

import logging
import math
from typing import Optional, Tuple

logger = logging.getLogger("FinFlick.AirMouse")

try:
    import Quartz
    from pynput.mouse import Controller as MouseController
    _HAS_MOUSE = True
except Exception:
    _HAS_MOUSE = False


class AirMouseController:
    """Translates normalized hand coordinates into smooth macOS cursor movements."""

    def __init__(
        self,
        smoothing: float = 0.35,
        min_cutoff: float = 0.002,
        active_x_bounds: Tuple[float, float] = (0.15, 0.85),
        active_y_bounds: Tuple[float, float] = (0.15, 0.80),
        mouse_controller: Optional[object] = None,
    ):
        self.smoothing = smoothing
        self.min_cutoff = min_cutoff
        self.x_min, self.x_max = active_x_bounds
        self.y_min, self.y_max = active_y_bounds

        if mouse_controller is not None:
            self._mouse = mouse_controller
        elif _HAS_MOUSE:
            try:
                self._mouse = MouseController()
            except Exception:
                self._mouse = None
        else:
            self._mouse = None

        self._curr_x: Optional[float] = None
        self._curr_y: Optional[float] = None
        self._screen_width: float = 1440.0
        self._screen_height: float = 900.0
        self._refresh_screen_bounds()

    def _refresh_screen_bounds(self) -> None:
        try:
            main_id = Quartz.CGMainDisplayID()
            bounds = Quartz.CGDisplayBounds(main_id)
            self._screen_width = float(bounds.size.width)
            self._screen_height = float(bounds.size.height)
        except Exception:
            pass

    def reset(self) -> None:
        """Reset interpolation history when tracking is lost or laser deactivated."""
        self._curr_x = None
        self._curr_y = None

    def deactivate(self, park_cursor: bool = True) -> None:
        """Deactivates air mouse and parks cursor at bottom corner so arrow does not overlay slides."""
        self.reset()
        if park_cursor and self._mouse is not None:
            try:
                self._mouse.position = (self._screen_width - 10.0, self._screen_height - 10.0)
            except Exception:
                pass

    def update(self, norm_x: float, norm_y: float) -> Optional[Tuple[float, float]]:
        """Map normalized [0..1] camera coordinates to screen pixels and move system cursor.

        Returns (screen_x, screen_y) if updated, or None if mouse control unavailable.
        """
        if self._mouse is None:
            return None

        # Re-scale active presenter region to full screen [0..1]
        x_span = max(self.x_max - self.x_min, 1e-4)
        y_span = max(self.y_max - self.y_min, 1e-4)

        rel_x = max(0.0, min(1.0, (norm_x - self.x_min) / x_span))
        rel_y = max(0.0, min(1.0, (norm_y - self.y_min) / y_span))

        target_x = rel_x * self._screen_width
        target_y = rel_y * self._screen_height

        if self._curr_x is None or self._curr_y is None:
            self._curr_x = target_x
            self._curr_y = target_y
        else:
            # Deadzone / tiny tremor rejection
            dx = target_x - self._curr_x
            dy = target_y - self._curr_y
            dist = math.hypot(dx, dy)
            if dist < self.min_cutoff * self._screen_width:
                return (self._curr_x, self._curr_y)

            # Responsive Exponential Moving Average:
            # Faster movements increase alpha slightly to reduce lag; slower movements smooth jitter.
            alpha = max(self.smoothing, min(0.75, dist / (0.15 * self._screen_width)))
            self._curr_x += alpha * dx
            self._curr_y += alpha * dy

        try:
            self._mouse.position = (self._curr_x, self._curr_y)
            return (self._curr_x, self._curr_y)
        except Exception as e:
            logger.debug(f"Could not set mouse position: {e}")
            return None
