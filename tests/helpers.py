"""Shared test helpers: a geometric hand model and frame-sequence playback."""

from typing import Dict, List, Optional, Tuple

from core.hand_tracker import HandObservation, LandmarkPoint

W, H = 1280, 720
FPS = 30.0

# Hand defined in "palm units" relative to the wrist; image y grows downwards.
MCP = {"index": (-0.30, -0.95), "middle": (0.0, -1.0), "ring": (0.25, -0.95), "pinky": (0.50, -0.85)}
EXTENDED = [(0.0, -0.45), (0.0, -0.75), (0.0, -1.00)]   # PIP, DIP, TIP offsets from MCP (pointing straight up)
POINT_HORIZONTAL = [(0.45, -0.15), (0.75, -0.15), (1.00, -0.15)]  # Index pointing horizontally for swiping
CURLED = [(0.0, -0.35), (0.0, -0.10), (0.0, 0.25)]      # fingertip folds back towards the palm
THUMB_OUT = [(-0.35, -0.25), (-0.60, -0.45), (-0.75, -0.65), (-0.85, -0.85)]
THUMB_TUCKED = [(-0.30, -0.25), (-0.40, -0.45), (-0.25, -0.60), (-0.05, -0.65)]
THUMB_UP = [(-0.25, -0.30), (-0.30, -0.60), (-0.30, -0.90), (-0.30, -1.30)]
THUMB_DOWN = [(-0.25, -0.10), (-0.30, 0.20), (-0.30, 0.50), (-0.30, 0.85)]


def make_hand(
    fingers: Dict[str, bool],
    thumb_out: bool = False,
    thumb_up: bool = False,
    thumb_down: bool = False,
    index_up: bool = False,
    ok_sign: bool = False,
    pinch_ratio: Optional[float] = None,
    center: Tuple[float, float] = (640.0, 500.0),
    palm_px: float = 80.0,
) -> HandObservation:
    """Builds a 21-landmark hand. `palm_px` ~80 = sitting at laptop, ~25 = standing 2 m away."""
    pts: List[Tuple[float, float]] = [(0.0, 0.0)]
    if ok_sign:
        # Index curls forward and its tip meets the thumb tip
        thumb = [(-0.35, -0.25), (-0.60, -0.45), (-0.65, -0.85), (-0.62, -1.20)]
    elif thumb_up:
        thumb = THUMB_UP
    elif thumb_down:
        thumb = THUMB_DOWN
    else:
        thumb = THUMB_OUT if thumb_out else THUMB_TUCKED
    pts.extend(thumb)
    for name in ("index", "middle", "ring", "pinky"):
        mx, my = MCP[name]
        pts.append((mx, my))
        if name == "index" and ok_sign:
            pts.extend([(-0.40, -1.40), (-0.55, -1.40), (-0.60, -1.25)])
            continue
        if name == "index" and fingers.get("index", False) and not index_up and not (fingers.get("middle") or fingers.get("ring") or fingers.get("pinky")):
            offsets = POINT_HORIZONTAL
        else:
            offsets = EXTENDED if fingers.get(name, False) else CURLED
        pts.extend((mx + ox, my + oy) for ox, oy in offsets)

    if pinch_ratio is not None:
        # Landmark 4 is THUMB_TIP, Landmark 8 is INDEX_TIP
        idx_tip = pts[8]
        pts[4] = (idx_tip[0] - pinch_ratio, idx_tip[1])

    cx, cy = center
    lms = [LandmarkPoint(x=(cx + ux * palm_px) / W, y=(cy + uy * palm_px) / H, z=0.0) for ux, uy in pts]
    return HandObservation(landmarks=lms, width=W, height=H)


POINT = {"index": True}
INDEX_UP = {"index": True}
THUMBS_UP: Dict[str, bool] = {}
THUMBS_DOWN: Dict[str, bool] = {}
PEACE = {"index": True, "middle": True}
W_SIGN = {"index": True, "middle": True, "ring": True}
PALM = {"index": True, "middle": True, "ring": True, "pinky": True}
FIST: Dict[str, bool] = {}


class Player:
    """Feeds frames to an engine at a fixed frame rate and records emitted events."""

    def __init__(self, engine, start: float = 100.0):
        self.engine = engine
        self.t = start
        self.events: List[str] = []

    def frame(self, hand: Optional[HandObservation]) -> Optional[str]:
        ev = self.engine.evaluate(hand, now=self.t)
        self.t += 1.0 / FPS
        if ev:
            self.events.append(ev.name)
            return ev.name
        return None

    def hold(self, seconds: float, **hand_kwargs) -> None:
        for _ in range(int(round(seconds * FPS))):
            self.frame(make_hand(**hand_kwargs))

    def gap(self, seconds: float) -> None:
        for _ in range(int(round(seconds * FPS))):
            self.frame(None)

    def move(self, seconds: float, start: Tuple[float, float], end: Tuple[float, float],
             drop_frames: Tuple[int, ...] = (), **hand_kwargs) -> None:
        n = max(1, int(round(seconds * FPS)))
        for i in range(1, n + 1):
            if i in drop_frames:
                self.frame(None)
                continue
            a = i / n
            c = (start[0] + (end[0] - start[0]) * a, start[1] + (end[1] - start[1]) * a)
            self.frame(make_hand(center=c, **hand_kwargs))
