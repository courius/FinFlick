"""Gesture Recognition Engine.

Pipeline per frame:
  1. Measure the hand in square pixel space; express all distances in palm lengths
     (wrist -> middle knuckle) so behaviour is independent of distance to camera.
  2. Classify a raw pose (POINT, PEACE, FIST, PALM, OK, OTHER).
  3. Debounce the pose (it must persist `pose_confirm_sec`), tolerate short dropouts.
  4. Hold poses (FIST / PALM / PEACE / OK) fire once per hold.
     POINT arms swipe detection after a short dwell; a swipe must be fast, long and
     horizontal. After a swipe the fingertip must settle before re-arming, and the
     opposite direction is blocked for a while (kills the "return stroke").
"""

import math
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Deque, List, Optional, Tuple

from core.config import AppConfig
from core.hand_tracker import HandObservation

WRIST, THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 0, 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
RING_MCP, RING_PIP, RING_TIP = 13, 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20

EXTENSION_RATIO = 1.15  # tip must be this much farther from the wrist than the PIP joint


class Pose(Enum):
    NONE = "No hand"
    OTHER = "Hand visible"
    POINT = "Pointing"
    INDEX_UP = "Index finger up"
    THUMBS_UP = "Thumb up"
    THUMBS_DOWN = "Thumb down"
    PEACE = "Peace sign"
    FIST = "Fist"
    PALM = "Open palm"
    OK = "OK sign"
    L_SIGN = "L-shape pointer"
    W_SIGN = "W-sign whiteboard"


@dataclass
class GestureEvent:
    name: str     # NEXT_SLIDE, PREV_SLIDE, PLAY_PAUSE, BLACKOUT, START_PRESENTATION, TOGGLE_PAUSE, FIRST_SLIDE, LAST_SLIDE, ZOOM_IN, ZOOM_OUT
    details: str = ""


@dataclass
class FingerState:
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool


@dataclass
class HandGeometry:
    pts: List[Tuple[float, float]]   # square-pixel coordinates
    palm: float                      # palm length in pixels
    fingers: FingerState
    pinch_ratio: float               # thumb-tip to index-tip distance / palm
    norm_tip: Tuple[float, float] = (0.0, 0.0)  # normalized (x, y) [0..1]
    zoom_pinch_ratio: float = 0.0    # 3D & foreshortening-compensated pinch ratio
    finger_radius: float = 0.0       # mean 4-fingertip distance from wrist / palm
    raw_tip_dist: float = 0.0        # mean 4-fingertip distance from wrist in pixels
    curl_ratio: float = 0.0          # mean tip-to-wrist / pip-to-wrist ratio (angle & palm-scale invariant)
    is_upright: bool = True          # whether wrist->middle_mcp points upward (not hanging down or sideways)
    norm_mcp_y: float = 0.5          # normalized vertical position of middle knuckle [0=top..1=bottom]


def _d(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def measure_hand(hand: HandObservation) -> HandGeometry:
    pts = [hand.px(i) for i in range(21)]
    wrist = pts[WRIST]
    # Wrist->middle-knuckle survives sideways rotation; knuckle width survives pitch.
    palm = max(_d(wrist, pts[MIDDLE_MCP]), 1.2 * _d(pts[INDEX_MCP], pts[PINKY_MCP]), 1e-6)

    def extended(tip: int, pip: int, mcp: int) -> bool:
        d_tip_wrist = _d(pts[tip], wrist)
        d_pip_wrist = _d(pts[pip], wrist)
        d_tip_mcp = _d(pts[tip], pts[mcp])
        d_pip_mcp = _d(pts[pip], pts[mcp])
        return (d_tip_wrist > EXTENSION_RATIO * d_pip_wrist) or (
            d_tip_mcp > 1.25 * d_pip_mcp and d_tip_mcp > 0.52 * palm
        )

    fingers = FingerState(
        thumb=_d(pts[THUMB_TIP], pts[PINKY_MCP]) > _d(pts[THUMB_IP], pts[PINKY_MCP]),
        index=extended(INDEX_TIP, INDEX_PIP, INDEX_MCP),
        middle=extended(MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP),
        ring=extended(RING_TIP, RING_PIP, RING_MCP),
        pinky=extended(PINKY_TIP, PINKY_PIP, PINKY_MCP),
    )
    pinch_2d = _d(pts[THUMB_TIP], pts[INDEX_TIP])
    pinch_ratio = pinch_2d / palm

    # Compensate for 3D depth and oblique hand rotation (foreshortening) during pinch-zoom
    dz = (hand.landmarks[THUMB_TIP].z - hand.landmarks[INDEX_TIP].z) * hand.width * 0.5
    pinch_3d = math.hypot(pinch_2d, dz)
    knuckle_span = _d(pts[INDEX_MCP], pts[PINKY_MCP]) / palm
    angle_scale = max(0.45, min(1.0, knuckle_span / 0.78))
    zoom_pinch_ratio = pinch_3d / (palm * angle_scale)

    # 360-degree orientation-invariant hand openness across the 4 fingers
    raw_tip_dist = (
        _d(pts[INDEX_TIP], wrist)
        + _d(pts[MIDDLE_TIP], wrist)
        + _d(pts[RING_TIP], wrist)
        + _d(pts[PINKY_TIP], wrist)
    ) / 4.0
    finger_radius = raw_tip_dist / palm

    curl_ratio = (
        _d(pts[INDEX_TIP], wrist) / max(_d(pts[INDEX_PIP], wrist), 1e-6)
        + _d(pts[MIDDLE_TIP], wrist) / max(_d(pts[MIDDLE_PIP], wrist), 1e-6)
        + _d(pts[RING_TIP], wrist) / max(_d(pts[RING_PIP], wrist), 1e-6)
        + _d(pts[PINKY_TIP], wrist) / max(_d(pts[PINKY_PIP], wrist), 1e-6)
    ) / 4.0

    # Upright check: wrist -> middle knuckle must point upward (y decreases upward)
    mcp_dx = pts[MIDDLE_MCP][0] - wrist[0]
    mcp_dy = pts[MIDDLE_MCP][1] - wrist[1]
    is_upright = (mcp_dy < -0.50 * palm) and (abs(mcp_dy) > 1.15 * abs(mcp_dx))
    norm_mcp_y = hand.landmarks[MIDDLE_MCP].y

    norm_tip = (hand.landmarks[INDEX_TIP].x, hand.landmarks[INDEX_TIP].y)
    return HandGeometry(
        pts=pts,
        palm=palm,
        fingers=fingers,
        pinch_ratio=pinch_ratio,
        norm_tip=norm_tip,
        zoom_pinch_ratio=zoom_pinch_ratio,
        finger_radius=finger_radius,
        raw_tip_dist=raw_tip_dist,
        curl_ratio=curl_ratio,
        is_upright=is_upright,
        norm_mcp_y=norm_mcp_y,
    )


HOLD_ACTIONS = {
    Pose.FIST: ("BLACKOUT", "fist_hold_sec"),
    Pose.PALM: ("TOGGLE_PAUSE", "palm_hold_sec"),
    Pose.PEACE: ("START_PRESENTATION", "peace_hold_sec"),
    Pose.OK: ("PLAY_PAUSE", "pinch_hold_sec"),
    Pose.INDEX_UP: ("FIRST_SLIDE", "first_slide_hold_sec"),
    Pose.THUMBS_UP: ("LAST_SLIDE", "last_slide_hold_sec"),
    Pose.THUMBS_DOWN: ("ZOOM_OUT", "thumbs_down_hold_sec"),
    Pose.L_SIGN: ("LASER_POINTER", "laser_hold_sec"),
    Pose.W_SIGN: ("WHITE_SCREEN", "whiteboard_hold_sec"),
}

HOLD_LABELS = {
    Pose.FIST: "Hold fist  ·  Blank screen",
    Pose.PALM: "Hold palm  ·  Pause / resume",
    Pose.PEACE: "Hold peace  ·  Start presenting",
    Pose.OK: "OK sign (👌)  ·  Play / pause",
    Pose.INDEX_UP: "Hold index up  ·  First slide",
    Pose.THUMBS_UP: "Hold thumb up  ·  Last slide",
    Pose.THUMBS_DOWN: "Hold thumb down  ·  Zoom out",
    Pose.L_SIGN: "Hold L-shape  ·  Laser pointer",
    Pose.W_SIGN: "Hold W-sign  ·  White screen",
}


class GestureEngine:
    """Stateful classifier. Call `evaluate()` once per processed frame."""

    def __init__(self, config: AppConfig, clock: Callable[[], float] = time.monotonic):
        self.config = config
        self._clock = clock
        self.laser_mode = False
        self.reset()

    def reset(self) -> None:
        self.laser_mode = False
        self._raw_pose = Pose.NONE
        self._raw_since = 0.0
        self._stable_pose = Pose.NONE
        self._stable_since = 0.0
        self._hold_fired = False
        self._last_seen = float("-inf")

        # (t, x, y, palm) of the index fingertip while armed
        self._traj: Deque[Tuple[float, float, float, float]] = deque(maxlen=90)
        self._norm_traj: Deque[Tuple[float, float, float]] = deque(maxlen=60)  # (t, norm_x, norm_y)
        self._awaiting_settle = False
        self._settle_since: Optional[float] = None
        self._last_swipe_action = 0          # +1 next, -1 prev
        self._last_swipe_time = float("-inf")

        # Dynamic pinch-zoom trajectory: (t, zoom_pinch_ratio, raw_pinch_ratio, wrist_px_x, wrist_px_y, tip_px_x, tip_px_y, palm)
        self._pinch_traj: Deque[Tuple[float, float, float, float, float, float, float, float]] = deque(maxlen=45)
        self._pinch_other_ext_streak: int = 0

        # Dynamic fist-to-palm bloom trajectory:
        # (t, raw_tip_dist, curl_ratio, num_extended, wrist_px_x, wrist_px_y, palm, invalid_closed)
        self._bloom_traj: Deque[Tuple[float, float, float, int, float, float, float, bool]] = deque(maxlen=45)

        # Wrist trajectory for hold-gesture stationarity checks: (t, wrist_px_x, wrist_px_y, palm)
        self._wrist_traj: Deque[Tuple[float, float, float, float]] = deque(maxlen=30)

        self._last_zoom_time = float("-inf")
        self._last_hold_fire_time = float("-inf")
        self._last_point_time = float("-inf")

        # Public state for the UI
        self.pose = Pose.NONE
        self.armed = False
        self.hold_progress: Optional[float] = None
        self.label = "No hand detected"

    @property
    def motion_trail(self) -> List[Tuple[float, float, float]]:
        """Returns list of (norm_x, norm_y, intensity [0.1..1.0]) for drawing a gesture trail."""
        if not self._norm_traj or not self.armed:
            return []
        now = self._clock()
        horizon = max(self.config.swipe_window_sec, 0.25)
        trail = []
        for t, nx, ny in self._norm_traj:
            age = now - t
            if age <= horizon:
                intensity = max(0.1, min(1.0, 1.0 - (age / horizon)))
                trail.append((nx, ny, intensity))
        return trail

    # ------------------------------------------------------------------ public
    def evaluate(self, hand: Optional[HandObservation], now: Optional[float] = None) -> Optional[GestureEvent]:
        now = self._clock() if now is None else now
        self.hold_progress = None

        if hand is None or len(hand.landmarks) < 21:
            if now - self._last_seen > self.config.dropout_grace_sec:
                self._set_stable(Pose.NONE, now)
                self._raw_pose = Pose.NONE
                self.armed = False
                self.label = "Laser Active · Hand not visible" if self.laser_mode else "No hand detected"
            return None  # within grace: keep state, just skip this frame

        self._last_seen = now
        geo = measure_hand(hand)

        # Record wrist trajectory for hold-gesture stationarity checks
        wx, wy = geo.pts[WRIST]
        self._wrist_traj.append((now, wx, wy, geo.palm))
        while self._wrist_traj and now - self._wrist_traj[0][0] > 0.25:
            self._wrist_traj.popleft()

        raw_pose = self._classify(geo)

        # Dedicated Laser Mode: all other presenter actions are paused while aiming.
        # The laser pointer stays active UNTIL the L gesture is held again to exit.
        if self.laser_mode:
            self.armed = False
            self._pinch_traj.clear()
            self._bloom_traj.clear()
            self._traj.clear()
            self._norm_traj.clear()

            self._update_pose(raw_pose, now)
            pose = self._stable_pose
            self.pose = pose

            # L-Sign hold toggles laser mode off
            if pose == Pose.L_SIGN:
                ev = self._handle_hold(Pose.L_SIGN, now)
                if ev is not None:
                    self.laser_mode = False
                    self._set_stable(Pose.NONE, now)
                    return ev
                self.label = "Hold L-shape · Exit Laser Pointer"
                return None

            self.hold_progress = None
            self.label = "🔴 Laser Active · Aim with hand (Hold L-shape to exit)"
            return None

        if raw_pose in (Pose.POINT, Pose.INDEX_UP) and geo.pinch_ratio >= 0.42:
            self._last_point_time = now

        # 1. Evaluate Zoom In: Fist-to-Palm Bloom or Pinch Open
        zoom_in_event = self._detect_zoom_in(geo, now)
        if zoom_in_event is not None:
            self.armed = False
            return zoom_in_event

        # 2. Pose classification & debouncing
        self._update_pose(raw_pose, now)
        pose = self._stable_pose
        self.pose = pose

        # 3. Handle specific poses
        if pose == Pose.INDEX_UP:
            return self._handle_index_up(geo, now)
        if pose == Pose.L_SIGN:
            return self._handle_l_sign(geo, now)
        if pose in HOLD_ACTIONS:
            self.armed = False
            return self._handle_hold(pose, now)
        if pose == Pose.POINT:
            return self._handle_point(geo, now)

        self.armed = False
        self.label = "Hand visible (idle)" if pose == Pose.OTHER else "Detecting…"
        return None

    # ---------------------------------------------------------- classification
    def _classify(self, geo: HandGeometry) -> Pose:
        f = geo.fingers
        pts = geo.pts
        palm = geo.palm

        in_ok = self._raw_pose == Pose.OK or self._stable_pose == Pose.OK
        pinch_thr = self.config.pinch_release_palms if in_ok else self.config.pinch_enter_palms
        other_extended = (1 if f.middle else 0) + (1 if f.ring else 0) + (1 if f.pinky else 0)
        if other_extended >= 2 and geo.pinch_ratio < pinch_thr:
            return Pose.OK
        if f.index and f.middle and f.ring and f.pinky:
            return Pose.PALM

        # W-Sign (Whiteboard): Index, Middle, Ring extended, Pinky curled
        if f.index and f.middle and f.ring and not f.pinky:
            return Pose.W_SIGN

        # Only index extended
        if f.index and not (f.middle or f.ring or f.pinky):
            # If thumb and index are pinched together, that is a pinch start, NOT pointing!
            if geo.pinch_ratio < 0.38:
                return Pose.OTHER
            idx_dx = pts[INDEX_TIP][0] - pts[INDEX_MCP][0]
            idx_dy = pts[INDEX_TIP][1] - pts[INDEX_MCP][1]

            # L-Sign (Laser Pointer): thumb clearly extended perpendicular to index (wide span)
            is_l_shape = (
                f.thumb
                and geo.pinch_ratio > 0.72
                and _d(pts[THUMB_TIP], pts[INDEX_MCP]) > 0.52 * palm
            )
            if is_l_shape:
                return Pose.L_SIGN

            # y increases downwards; idx_dy < 0 means pointing UP.
            # Require steep vertical pointing (>60° from horizontal, dy < -0.50 palm)
            # to distinguish from natural swiping posture.
            if idx_dy < -0.50 * palm and abs(idx_dy) > 1.80 * abs(idx_dx):
                return Pose.INDEX_UP
            return Pose.POINT

        if f.index and f.middle and not (f.ring or f.pinky):
            return Pose.PEACE

        # All 4 fingers curled
        num_extended = (1 if f.index else 0) + (1 if f.middle else 0) + (1 if f.ring else 0) + (1 if f.pinky else 0)
        if num_extended == 0:
            # If thumb and index are touching / pinched, that is a pinch, NOT a fist!
            if geo.pinch_ratio < 0.45 and f.thumb:
                return Pose.OTHER

            # Check for Thumbs Up (thumb extended vertically upward with other fingers curled)
            thumb_dx = pts[THUMB_TIP][0] - pts[THUMB_MCP][0]
            thumb_dy = pts[THUMB_TIP][1] - pts[THUMB_MCP][1]
            is_thumb_up = (
                pts[THUMB_TIP][1] < pts[INDEX_MCP][1]
                and thumb_dy < -0.30 * palm
                and (pts[WRIST][1] - pts[THUMB_TIP][1]) > 0.45 * palm
            )
            if is_thumb_up:
                return Pose.THUMBS_UP

            # Check for Thumbs Down (thumb extended vertically downward with other fingers curled)
            is_thumb_down = (
                pts[THUMB_TIP][1] > pts[WRIST][1]
                and thumb_dy > 0.25 * palm
                and (pts[THUMB_TIP][1] - pts[INDEX_MCP][1]) > 0.40 * palm
                and abs(thumb_dy) > 1.1 * abs(thumb_dx)
            )
            if is_thumb_down:
                return Pose.THUMBS_DOWN

            # Require Fist (Blackout) to be tightly curled, facing UPWARD, and raised in the camera view
            # (prevents resting/hanging hands or mid-gesture transitions from triggering Blackout)
            if geo.is_upright and geo.curl_ratio <= 1.06 and geo.norm_mcp_y <= 0.82:
                return Pose.FIST

        return Pose.OTHER

    def _handle_index_up(self, geo: HandGeometry, now: float) -> Optional[GestureEvent]:
        # If user performs a flick, prioritize the swipe
        swipe_ev = self._handle_point(geo, now)
        if swipe_ev is not None:
            self._stable_since = now
            self._hold_fired = False
            return swipe_ev

        # If hand/fingertip is moving, user is aiming or swiping, not holding steady for First Slide!
        if self._wrist_speed(now) > 0.85 or self._recent_speed(now) > 1.2:
            self._hold_fired = False
            self.armed = True
            return None

        # Otherwise track the deliberate stationary hold for FIRST_SLIDE
        hold_ev = self._handle_hold(Pose.INDEX_UP, now)
        self.armed = True
        return hold_ev

    def _handle_l_sign(self, geo: HandGeometry, now: float) -> Optional[GestureEvent]:
        # If user performs a flick, prioritize the swipe
        swipe_ev = self._handle_point(geo, now)
        if swipe_ev is not None:
            self._stable_since = now
            self._hold_fired = False
            return swipe_ev

        # If hand/fingertip is moving, user is swiping or repositioning
        if self._wrist_speed(now) > 0.85 or self._recent_speed(now) > 1.2:
            self._hold_fired = False
            self.armed = True
            return None

        # Otherwise track deliberate stationary hold for LASER_POINTER
        hold_ev = self._handle_hold(Pose.L_SIGN, now)
        # Keep armed = True so pointing fingertip orb and trail stay visible and ready to flick
        self.armed = True
        return hold_ev

    def _detect_zoom_in(self, geo: HandGeometry, now: float) -> Optional[GestureEvent]:
        """Dynamic Zoom In (+15%):
        1. Fist-to-Palm Bloom (✊➡️🖐️): Rapid radial expansion from closed hand to full palm (360° angle-invariant).
        2. Pinch Open (🤏): Inside-out thumb-index spread (with 3D & oblique foreshortening compensation).
        """
        # Strictly block zoom for 1.2s after a slide swipe or while settling after a swipe
        if (now - self._last_swipe_time < 1.20) or self._awaiting_settle:
            self._pinch_traj.clear()
            self._bloom_traj.clear()
            self._pinch_other_ext_streak = 0
            return None

        # Evaluate Fist-to-Palm Bloom first (always update trajectory so closed frames during cooldown are kept)
        bloom_ev = self._detect_bloom_zoom(geo, now)
        if bloom_ev is not None:
            return bloom_ev

        # Evaluate Pinch-Open Zoom
        return self._detect_pinch_zoom(geo, now)

    def _detect_bloom_zoom(self, geo: HandGeometry, now: float) -> Optional[GestureEvent]:
        """Detects ✊➡️🖐️ Fist-to-Palm Bloom:
        Hand starts in a true closed 0-finger fist (never pointing!) and bursts open
        into an upright open palm within zoom_window_sec while wrist stays stationary.
        """
        cfg = self.config
        f = geo.fingers
        pts = geo.pts
        palm = geo.palm

        num_extended = (1 if f.index else 0) + (1 if f.middle else 0) + (1 if f.ring else 0) + (1 if f.pinky else 0)
        wx, wy = pts[WRIST]

        # Invalidate bloom if a hold gesture recently fired, or if user is armed/pointing for slide swipes
        invalid_closed = (
            self._hold_fired
            or (now - self._last_hold_fire_time < 0.80)
            or self.armed
            or (now - self._last_point_time < 0.45 and num_extended > 0)
        )
        if self._hold_fired or (now - self._last_hold_fire_time < 0.80):
            self._bloom_traj.clear()
            return None

        # A closed sample for Bloom MUST have 0 extended fingers (all 4 fingers curled, never pointing!)
        # and the hand must be upright (not hanging down at the user's side)
        can_be_closed = (
            not invalid_closed
            and num_extended == 0
            and not f.index
            and not f.middle
            and geo.curl_ratio <= 1.08
            and geo.is_upright
            and geo.norm_mcp_y <= 0.85
        )
        self._bloom_traj.append((now, geo.raw_tip_dist, geo.curl_ratio, num_extended, wx, wy, palm, not can_be_closed))
        horizon = max(cfg.zoom_window_sec, 0.55)
        while self._bloom_traj and now - self._bloom_traj[0][0] > horizon:
            self._bloom_traj.popleft()

        # Respect zoom cooldown before firing, while keeping trajectory populated
        if (now - self._last_zoom_time) < cfg.zoom_cooldown_sec:
            return None

        # Open state: upright 4-finger palm, OR 3 fingers extended (including index + middle, not OK-sign pinched)
        is_open_palm = (
            geo.is_upright
            and (
                num_extended == 4
                or (num_extended == 3 and f.index and f.middle and geo.pinch_ratio >= 0.50)
            )
        )
        if len(self._bloom_traj) < 2 or not is_open_palm or geo.curl_ratio < 1.18:
            return None

        # Check if any recent true closed-fist sample in the window transitioned into this open palm
        for t0, raw_tip0, curl0, ext0, wx0, wy0, p0, inv0 in self._bloom_traj:
            if inv0 or ext0 != 0:
                continue

            dt = now - t0
            if dt < 0.015 or dt > horizon:
                continue

            scale = (palm + p0) / 2.0
            radial_expansion = (geo.raw_tip_dist - raw_tip0) / scale
            curl_delta = geo.curl_ratio - curl0
            wrist_disp = math.hypot(wx - wx0, wy - wy0) / scale

            if (
                (num_extended - ext0) >= 3
                and (radial_expansion >= 0.25 or curl_delta >= 0.18)
                and curl_delta >= 0.12
                and wrist_disp <= 0.55
            ):
                self._last_zoom_time = now
                self._bloom_traj.clear()
                self._pinch_traj.clear()
                self._stable_since = now
                self._raw_since = now
                self._hold_fired = False
                self.label = "Fist to Palm Bloom  ·  Zoom In"
                return GestureEvent("ZOOM_IN", f"bloom expand curl {curl0:.2f}->{geo.curl_ratio:.2f}")

        return None

    def _detect_pinch_zoom(self, geo: HandGeometry, now: float) -> Optional[GestureEvent]:
        """Detects 🤏 Pinch Open (inside-out thumb + index spread) with foreshortening compensation."""
        cfg = self.config
        f = geo.fingers
        pts = geo.pts
        palm = geo.palm

        # Dynamic pinch zoom is between thumb and index; tolerate 1 frame of middle-finger flicker at distance
        other_extended = (1 if f.middle else 0) + (1 if f.ring else 0) + (1 if f.pinky else 0)
        if other_extended >= 2:
            self._pinch_other_ext_streak += 1
            if self._pinch_other_ext_streak >= 2:
                self._pinch_traj.clear()
            return None
        self._pinch_other_ext_streak = 0

        wx, wy = pts[WRIST]
        tx, ty = pts[INDEX_TIP]
        curr_pinch = geo.zoom_pinch_ratio
        raw_pinch = geo.pinch_ratio

        # If armed for pointing swipe and fingers are NOT tightly pinched together, do not start a pinch trajectory
        if self.armed and raw_pinch >= 0.36 and not self._pinch_traj:
            return None

        self._pinch_traj.append((now, curr_pinch, raw_pinch, wx, wy, tx, ty, palm))
        horizon = max(cfg.zoom_window_sec, 0.35)
        while self._pinch_traj and now - self._pinch_traj[0][0] > horizon:
            self._pinch_traj.popleft()

        if (now - self._last_zoom_time) < cfg.zoom_cooldown_sec or len(self._pinch_traj) < 2:
            return None

        # Disallow zoom if the hand / wrist or index fingertip swept across the screen (flick / swipe)
        t0, _, _, wx0, wy0, tx0, ty0, p0 = self._pinch_traj[0]
        scale0 = (palm + p0) / 2.0
        wrist_disp = math.hypot(wx - wx0, wy - wy0) / scale0
        tip_disp = math.hypot(tx - tx0, ty - ty0) / scale0
        if wrist_disp > 0.40 or tip_disp > 0.60:
            self._pinch_traj.clear()
            return None

        dt_window = now - t0
        if dt_window > 0.03 and (wrist_disp / dt_window) > 2.0:
            self._pinch_traj.clear()
            return None

        min_sample = min(self._pinch_traj, key=lambda s: s[1])
        scale_min = (palm + min_sample[7]) / 2.0
        tip_disp_from_min = math.hypot(tx - min_sample[5], ty - min_sample[6]) / scale_min

        # ZOOM_IN: inside-out movement starting from a genuine tight pinch (raw_pinch <= 0.36 or zoom_pinch <= 0.42)
        if (
            min_sample[1] <= 0.44
            and min_sample[2] <= 0.38
            and curr_pinch >= 0.58
            and (curr_pinch - min_sample[1]) >= cfg.zoom_min_delta
            and tip_disp_from_min <= 0.55
            and (now - min_sample[0]) <= horizon
            and (now - min_sample[0]) >= 0.015
        ):
            self._last_zoom_time = now
            self._pinch_traj.clear()
            self._bloom_traj.clear()
            self._stable_since = now
            self._raw_since = now
            self._hold_fired = False
            self.label = "Pinch Open  ·  Zoom In"
            return GestureEvent("ZOOM_IN", f"pinch expand {min_sample[1]:.2f}->{curr_pinch:.2f}")

        return None

    def _update_pose(self, raw: Pose, now: float) -> None:
        if raw != self._raw_pose:
            self._raw_pose = raw
            self._raw_since = now
        if raw != self._stable_pose and (now - self._raw_since) >= self.config.pose_confirm_sec:
            self._set_stable(raw, self._raw_since)

    def _set_stable(self, pose: Pose, since: float) -> None:
        if pose == self._stable_pose:
            return
        self._stable_pose = pose
        self._stable_since = since
        if pose == Pose.NONE:
            self._raw_pose = Pose.NONE
            self._raw_since = since
        self.pose = pose
        self._hold_fired = False
        self._traj.clear()
        self._norm_traj.clear()
        # Leaving the pointing pose counts as "re-arming" after a swipe.
        self._awaiting_settle = False
        self._settle_since = None

    # ------------------------------------------------------------------- holds
    def _handle_hold(self, pose: Pose, now: float) -> Optional[GestureEvent]:
        action, attr = HOLD_ACTIONS[pose]
        hold_sec = getattr(self.config, attr)

        # Prevent hold gestures from accumulating while the hand is moving or right after a swipe/zoom
        in_dynamic_cooldown = (now - self._last_swipe_time < 0.70) or (
            pose != Pose.THUMBS_DOWN and (now - self._last_zoom_time < 0.70)
        )
        if in_dynamic_cooldown or self._wrist_speed(now) > 0.85:
            self._stable_since = now
            self.hold_progress = 0.0
            self.label = f"{pose.value}  ·  Hold steady…"
            return None

        held = now - self._stable_since
        self.hold_progress = min(1.0, held / hold_sec) if hold_sec > 0 else 1.0
        self.label = HOLD_LABELS[pose] + ("" if not self._hold_fired else "  [Done]")

        # For ZOOM_OUT via Thumbs Down, support smooth repeat every zoom_cooldown_sec while held
        if pose == Pose.THUMBS_DOWN:
            if held >= hold_sec:
                if not self._hold_fired or (now - self._last_zoom_time) >= self.config.zoom_cooldown_sec:
                    self._hold_fired = True
                    self._last_zoom_time = now
                    self._last_hold_fire_time = now
                    self.label = "Thumb Down  ·  Zoom Out"
                    return GestureEvent(action, f"thumb down zoom out (held {held:.2f}s)")
            return None

        if held >= hold_sec and not self._hold_fired:
            self._hold_fired = True
            self._last_hold_fire_time = now
            self._bloom_traj.clear()
            self._pinch_traj.clear()
            return GestureEvent(action, f"{pose.value} held {held:.2f}s")
        return None

    # ------------------------------------------------------------------ swipes
    def _handle_point(self, geo: HandGeometry, now: float) -> Optional[GestureEvent]:
        cfg = self.config
        tip_x, tip_y = geo.pts[INDEX_TIP]

        if not self._awaiting_settle and (now - self._stable_since) < cfg.arm_dwell_sec:
            self.armed = False
            self._traj.clear()
            self._norm_traj.clear()
            self.label = "Pointing… hold steady"
            return None

        if not self._traj or self._traj[-1][0] != now:
            self._traj.append((now, tip_x, tip_y, geo.palm))
            self._norm_traj.append((now, geo.norm_tip[0], geo.norm_tip[1]))
        else:
            self._traj[-1] = (now, tip_x, tip_y, geo.palm)
            self._norm_traj[-1] = (now, geo.norm_tip[0], geo.norm_tip[1])
        horizon = max(cfg.swipe_window_sec, 0.15)
        while self._traj and now - self._traj[0][0] > horizon:
            self._traj.popleft()
        while self._norm_traj and now - self._norm_traj[0][0] > horizon:
            self._norm_traj.popleft()

        if self._awaiting_settle:
            self.armed = False
            self.label = "Swipe registered — settle hand"
            if self._recent_speed(now, settle_check=True) < cfg.settle_speed_palms:
                if self._settle_since is None:
                    self._settle_since = now
                elif now - self._settle_since >= cfg.rearm_settle_sec:
                    self._awaiting_settle = False
                    self._settle_since = None
                    self._traj.clear()
                    self._norm_traj.clear()
                    self._traj.append((now, tip_x, tip_y, geo.palm))
                    self._norm_traj.append((now, geo.norm_tip[0], geo.norm_tip[1]))
            else:
                self._settle_since = None
            return None

        self.armed = True
        self.label = "Armed  ·  Flick left or right"

        direction = self._detect_swipe(now, tip_x, tip_y, geo.palm)
        if direction == 0:
            return None

        # +1 = towards the user's right
        user_dir = direction if cfg.mirror_camera else -direction
        action_dir = -user_dir if cfg.invert_swipe_direction else user_dir

        self._awaiting_settle = True
        self._settle_since = None
        self._traj.clear()
        self._norm_traj.clear()
        self._pinch_traj.clear()
        self._bloom_traj.clear()

        if action_dir == -self._last_swipe_action and (now - self._last_swipe_time) < cfg.reverse_block_sec:
            self.label = "Return stroke ignored"
            return None

        self._last_swipe_action = action_dir
        self._last_swipe_time = now
        name = "NEXT_SLIDE" if action_dir > 0 else "PREV_SLIDE"
        self.label = "Flick → Next" if action_dir > 0 else "Flick → Previous"
        return GestureEvent(name, f"swipe dir={direction:+d}")

    def _detect_swipe(self, now: float, x: float, y: float, palm: float) -> int:
        cfg = self.config
        for t, x0, y0, p0 in self._traj:
            dt = now - t
            if dt < 0.05:
                break  # points are in time order; the rest are too recent
            if dt > cfg.swipe_window_sec:
                continue
            scale = (palm + p0) / 2.0
            dx = (x - x0) / scale
            dy = (y - y0) / scale
            if (
                abs(dx) >= cfg.swipe_min_distance_palms
                and abs(dx) / dt >= cfg.swipe_min_speed_palms
                and abs(dx) >= cfg.swipe_horizontal_ratio * abs(dy)
            ):
                return 1 if dx > 0 else -1
        return 0

    def _recent_speed(self, now: float, window: float = 0.1, settle_check: bool = False) -> float:
        """Fingertip speed in palm lengths / second over the last `window` seconds."""
        if len(self._traj) < 2:
            return 0.0
        t1, x1, y1, p1 = self._traj[-1]
        ref = None
        for sample in reversed(self._traj):
            ref = sample
            if t1 - sample[0] >= window:
                break
        t0, x0, y0, p0 = ref
        dt = t1 - t0
        if dt < 0.03:
            return float("inf") if settle_check else 0.0
        return math.hypot(x1 - x0, y1 - y0) / ((p0 + p1) / 2.0) / dt

    def _wrist_speed(self, now: float, window: float = 0.12) -> float:
        """Wrist translation speed in palm lengths / second over the last `window` seconds."""
        if len(self._wrist_traj) < 2:
            return 0.0
        t1, x1, y1, p1 = self._wrist_traj[-1]
        ref = None
        for sample in reversed(self._wrist_traj):
            ref = sample
            if t1 - sample[0] >= window:
                break
        t0, x0, y0, p0 = ref
        dt = t1 - t0
        if dt < 0.025:
            return 0.0
        return math.hypot(x1 - x0, y1 - y0) / ((p0 + p1) / 2.0) / dt
