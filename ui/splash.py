"""Clean, unhurried opening camera-iris swirl animation overlay."""

from __future__ import annotations

import math
import time
import tkinter as tk
from typing import Callable, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageTk

import ui.theme as theme
from ui.logo import FishStatueRenderer
from utils.sound_feedback import SoundFeedback


def _hex_blend(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two #RRGGBB hex colors."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


class SplashOverlay(tk.Canvas):
    """Clean, concise opening screen where the vector fish-camera logo swirls open to reveal the center."""

    ENTRY_DURATION = 0.50   # Calm entrance pause in coiled state
    SWIRL_DURATION = 1.95   # Deliberate, unhurried camera-iris swirl opening the center
    HOLD_DURATION = 1.15    # Poised brand hold once the logo & lens center are revealed
    REVEAL_DURATION = 0.75  # Smooth aperture expansion into the workspace
    TOTAL_DURATION = ENTRY_DURATION + SWIRL_DURATION + HOLD_DURATION + REVEAL_DURATION
    FRAME_INTERVAL_MS = 16  # ~60 FPS

    BG_HEX = "#0a192f"
    BG_RGB = (10, 25, 47)

    def __init__(
        self,
        parent: tk.Misc,
        renderer: FishStatueRenderer,
        frame_provider: Optional[Callable[[], Optional[np.ndarray]]] = None,
        sound: Optional[SoundFeedback] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            parent,
            bg=self.BG_HEX,
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        self.renderer = renderer
        self.frame_provider = frame_provider
        self.sound = sound
        self.on_complete = on_complete
        self._start_time = time.perf_counter()
        self._photo: Optional[ImageTk.PhotoImage] = None
        self._after_id: Optional[str] = None
        self._finished = False
        self._backdrop_cache: Optional[ tuple[int, int, Image.Image] ] = None

        self.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0)
        tk.Misc.tkraise(self)

        # Play modern synthesized camera-iris swirl + harmonic bloom soundscape
        if self.sound is not None:
            self.sound.play_intro()

        # Click anywhere to skip cleanly
        self.bind("<Button-1>", lambda _e: self.finish(skipped=True))
        self.bind("<Configure>", lambda _e: self._draw_frame())

        self._tick()

    def _get_clean_backdrop(self, sz: int) -> Image.Image:
        """Create a clean, minimal square canvas with a soft radial ambient glow behind the vector logo."""
        if self._backdrop_cache is not None and self._backdrop_cache[0] == sz:
            return self._backdrop_cache[2].copy()

        lin = np.linspace(-1.0, 1.0, sz, dtype=np.float32)
        x, y = np.meshgrid(lin, lin)
        r = np.hypot(x, y)
        glow = np.exp(-((r / 0.72) ** 2))

        arr = np.empty((sz, sz, 4), dtype=np.uint8)
        arr[:, :, 0] = np.clip(self.BG_RGB[0] + 14.0 * glow, 0, 255).astype(np.uint8)
        arr[:, :, 1] = np.clip(self.BG_RGB[1] + 34.0 * glow, 0, 255).astype(np.uint8)
        arr[:, :, 2] = np.clip(self.BG_RGB[2] + 64.0 * glow, 0, 255).astype(np.uint8)
        arr[:, :, 3] = 255
        img = Image.fromarray(arr, mode="RGBA")
        self._backdrop_cache = (sz, sz, img)
        return img.copy()

    def _tick(self) -> None:
        if self._finished:
            return
        elapsed = time.perf_counter() - self._start_time
        if elapsed >= self.TOTAL_DURATION:
            self.finish(skipped=False)
            return

        self._draw_frame(elapsed)
        self._after_id = self.after(self.FRAME_INTERVAL_MS, self._tick)

    def _draw_frame(self, elapsed: Optional[float] = None) -> None:
        if self._finished:
            return
        if elapsed is None:
            elapsed = time.perf_counter() - self._start_time

        w = max(640, self.winfo_width())
        h = max(480, self.winfo_height())
        cx = w * 0.5
        cy = h * 0.43

        t1 = self.ENTRY_DURATION
        t2 = t1 + self.SWIRL_DURATION
        t3 = t2 + self.HOLD_DURATION

        if elapsed <= t1:
            entry_p = elapsed / max(1e-4, t1)
            swirl_p = 0.0
            hold_p = 0.0
            reveal_p = 0.0
        elif elapsed <= t2:
            entry_p = 1.0
            swirl_p = (elapsed - t1) / max(1e-4, self.SWIRL_DURATION)
            hold_p = 0.0
            reveal_p = 0.0
        elif elapsed <= t3:
            entry_p = 1.0
            swirl_p = 1.0
            hold_p = (elapsed - t2) / max(1e-4, self.HOLD_DURATION)
            reveal_p = 0.0
        else:
            entry_p = 1.0
            swirl_p = 1.0
            hold_p = 1.0
            reveal_p = min(1.0, (elapsed - t3) / max(1e-4, self.REVEAL_DURATION))

        self.delete("all")

        # 1. Render the vector Fish-Camera Logo frame
        frame_rgba = self.renderer.render_frame(
            progress=swirl_p,
            include_lens=(reveal_p < 0.08),
            hole_expand=reveal_p,
        )

        # Smooth fade-in during the initial 0.5s entrance and smooth fade-out at the end of reveal
        master_alpha = (1.0 - (1.0 - entry_p) ** 2.5) * (1.0 - (reveal_p ** 2.2) * 0.85)
        if master_alpha < 0.995:
            arr = np.asarray(frame_rgba).copy()
            arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * master_alpha).astype(np.uint8)
            frame_rgba = Image.fromarray(arr, mode="RGBA")

        bg_img = self._get_clean_backdrop(frame_rgba.size[0])
        bg_img.alpha_composite(frame_rgba)

        # Subtle single optical ring glint inside the center hole as it locks open
        if swirl_p > 0.72 and reveal_p < 0.15:
            glint_phase = min(1.0, (swirl_p - 0.72) / 0.28 + hold_p * 0.35)
            glint_a = int(170 * math.sin(min(1.0, glint_phase) * math.pi) * (1.0 - reveal_p * 6.0))
            if glint_a > 8:
                draw = ImageDraw.Draw(bg_img)
                mid = frame_rgba.size[0] * 0.5
                r_px = frame_rgba.size[0] * 0.072
                draw.ellipse(
                    (mid - r_px, mid - r_px, mid + r_px, mid + r_px),
                    outline=(125, 211, 252, glint_a),
                    width=2,
                )

        self._photo = ImageTk.PhotoImage(bg_img.convert("RGB"))
        self.create_image(cx, cy, image=self._photo, anchor="center")

        # 2. Clean, concise typography lockup below the logo
        # Begins fading in gracefully once the camera iris is well underway (swirl_p > 0.48)
        text_in = max(0.0, min(1.0, (swirl_p - 0.48) / 0.48 + hold_p * 0.25))
        text_in_smooth = text_in * text_in * (3.0 - 2.0 * text_in)
        text_vis = text_in_smooth * (1.0 - reveal_p ** 1.4)

        if text_vis > 0.02:
            y_lift = (1.0 - text_in_smooth) * 10.0
            title_col = _hex_blend(self.BG_HEX, "#ffffff", text_vis)
            sub_col = _hex_blend(self.BG_HEX, "#7dd3fc", text_vis * 0.85)
            line_col = _hex_blend(self.BG_HEX, "#38bdf8", text_vis * 0.45)

            title_y = cy + (frame_rgba.size[1] * 0.5) + 34 + y_lift
            self.create_text(
                cx,
                title_y,
                text="FinFlick",
                fill=title_col,
                font=("Helvetica Neue", 26, "bold"),
            )

            # Minimal 32px accent divider line
            half_w = 18.0 * text_in_smooth
            if half_w > 2.0:
                self.create_line(
                    cx - half_w,
                    title_y + 22,
                    cx + half_w,
                    title_y + 22,
                    fill=line_col,
                    width=1,
                )

            self.create_text(
                cx,
                title_y + 38,
                text="Flick to Advance",
                fill=sub_col,
                font=(theme.FONT_FAMILY, 10, "bold"),
            )

    def finish(self, skipped: bool = False) -> None:
        if self._finished:
            return
        self._finished = True
        if skipped and self.sound is not None:
            self.sound.stop_intro()
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self.destroy()
        if self.on_complete is not None:
            self.on_complete()
