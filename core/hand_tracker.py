"""MediaPipe Hand Landmarker wrapper (Tasks API, VIDEO mode with temporal tracking)."""

import os
import math
import time
import urllib.request
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions

logger = logging.getLogger("FinFlick.HandTracker")

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "hand_landmarker.task")

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),            # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),            # index
    (9, 10), (10, 11), (11, 12),               # middle
    (13, 14), (14, 15), (15, 16),              # ring
    (0, 17), (17, 18), (18, 19), (19, 20),     # pinky
    (5, 9), (9, 13), (13, 17),                 # knuckles
]


@dataclass
class LandmarkPoint:
    x: float  # normalized [0, 1] across image width
    y: float  # normalized [0, 1] across image height
    z: float  # relative depth (not used for geometry: different scale than x/y)


@dataclass
class HandObservation:
    landmarks: List[LandmarkPoint]
    width: int    # image size, needed to convert normalized coords to square pixels
    height: int
    handedness: str = "Unknown"

    def px(self, i: int) -> "tuple[float, float]":
        lm = self.landmarks[i]
        return lm.x * self.width, lm.y * self.height


class HandTracker:
    """Detects hands per frame and tracks a single consistent hand at a time.
    When multiple hands are present, locks onto one and disables the other hand.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        num_hands: int = 2,
        min_detection_confidence: float = 0.6,
        min_presence_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
        hand_switch_grace_sec: float = 0.40,
        track_hand: str = "any",
        mirror: bool = True,
    ):
        self.model_path = model_path or MODEL_PATH
        self._ensure_model_exists()
        self._last_ts_ms = -1
        self.hand_switch_grace_sec = hand_switch_grace_sec
        self.track_hand = track_hand.lower()
        self.mirror = mirror

        # Single-hand tracking lock state
        self._tracked_wrist: Optional[tuple[float, float]] = None
        self._tracked_handedness: Optional[str] = None
        self._tracked_last_seen: float = float("-inf")
        self.detected_hands_count: int = 0

        # Always detect up to 2 hands in MediaPipe so we can filter and stick to one hand
        actual_num_hands = max(2, num_hands)

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=actual_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        logger.info(f"MediaPipe HandLandmarker ready (VIDEO mode, track_hand={self.track_hand}).")

    def _ensure_model_exists(self) -> None:
        if os.path.exists(self.model_path) and os.path.getsize(self.model_path) > 1_000_000:
            return
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        tmp_path = self.model_path + ".download"
        logger.info(f"Downloading hand landmark model to {self.model_path}...")
        urllib.request.urlretrieve(MODEL_URL, tmp_path)
        os.replace(tmp_path, self.model_path)  # never leave a half-downloaded model behind

    def set_track_hand(self, hand: str) -> None:
        """Sets hand filter preference ('any', 'right', 'left') and clears lock."""
        val = hand.lower()
        if val in ("any", "right", "left"):
            if self.track_hand != val:
                self.track_hand = val
                self.reset_tracking()

    def reset_tracking(self) -> None:
        """Clears the locked hand so a new hand can be chosen immediately."""
        self._tracked_wrist = None
        self._tracked_handedness = None
        self._tracked_last_seen = float("-inf")
        self.detected_hands_count = 0

    def process(self, frame_bgr: np.ndarray, timestamp_sec: float) -> Optional[HandObservation]:
        """Runs detection/tracking. Timestamps must increase; we enforce it defensively."""
        h, w = frame_bgr.shape[:2]
        ts_ms = int(timestamp_sec * 1000)
        if ts_ms <= self._last_ts_ms:
            ts_ms = self._last_ts_ms + 1
        self._last_ts_ms = ts_ms

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        try:
            result = self.landmarker.detect_for_video(mp_image, ts_ms)
        except Exception as e:
            logger.debug(f"Hand detection error: {e}")
            return None

        if not result.hand_landmarks:
            self.detected_hands_count = 0
            if (timestamp_sec - self._tracked_last_seen) > self.hand_switch_grace_sec:
                self._tracked_wrist = None
                self._tracked_handedness = None
            return None

        candidates: List[HandObservation] = []
        for i, lms in enumerate(result.hand_landmarks):
            landmarks = [LandmarkPoint(lm.x, lm.y, lm.z) for lm in lms]
            raw_handedness = "Unknown"
            if result.handedness and i < len(result.handedness) and result.handedness[i]:
                raw_handedness = result.handedness[i][0].category_name or "Unknown"

            # In selfie/mirrored mode, cv2.flip(image, 1) was applied before inference,
            # which inverts visual handedness. We swap it so HandObservation.handedness
            # always corresponds to the user's physical hand.
            if self.mirror:
                if raw_handedness == "Left":
                    physical_handedness = "Right"
                elif raw_handedness == "Right":
                    physical_handedness = "Left"
                else:
                    physical_handedness = raw_handedness
            else:
                physical_handedness = raw_handedness

            candidates.append(HandObservation(landmarks=landmarks, width=w, height=h, handedness=physical_handedness))

        self.detected_hands_count = len(candidates)
        return self._select_tracked_hand(candidates, timestamp_sec)

    def _select_tracked_hand(
        self, candidates: List[HandObservation], timestamp_sec: float
    ) -> Optional[HandObservation]:
        """Ensures FinFlick only tracks ONE hand at a time.
        If track_hand is 'right' or 'left', only that designated hand is tracked and the
        other hand is completely ignored.
        If a hand is already being tracked, other hands are disabled.
        If tracking is lost for hand_switch_grace_sec, the lock is released.
        """
        # If user designated a specific hand, filter out candidates of the opposite hand
        if self.track_hand in ("right", "left"):
            target = self.track_hand.capitalize()  # "Right" or "Left"
            candidates = [c for c in candidates if c.handedness == target or c.handedness == "Unknown"]
            if self._tracked_handedness and self._tracked_handedness != target:
                self._tracked_wrist = None
                self._tracked_handedness = None
        if not candidates:
            if (timestamp_sec - self._tracked_last_seen) > self.hand_switch_grace_sec:
                self._tracked_wrist = None
                self._tracked_handedness = None
            return None

        # Case 1: We are actively tracking a locked hand
        if self._tracked_wrist is not None and (timestamp_sec - self._tracked_last_seen) <= self.hand_switch_grace_sec:
            best_cand: Optional[HandObservation] = None
            best_score = float("inf")

            for cand in candidates:
                wx, wy = cand.landmarks[0].x, cand.landmarks[0].y
                dist = math.hypot(wx - self._tracked_wrist[0], wy - self._tracked_wrist[1])

                # Handedness match bonus/penalty
                score = dist
                if self._tracked_handedness and cand.handedness != "Unknown":
                    if cand.handedness == self._tracked_handedness:
                        score *= 0.7  # prioritize same hand
                    else:
                        score = dist * 1.6 + 0.15  # strong penalty for opposite hand

                if score < best_score:
                    best_score = score
                    best_cand = cand

            # If the candidate matches our tracked hand (within 0.50 normalized screen width)
            if best_cand is not None and best_score < 0.50:
                self._tracked_wrist = (best_cand.landmarks[0].x, best_cand.landmarks[0].y)
                if best_cand.handedness != "Unknown":
                    self._tracked_handedness = best_cand.handedness
                self._tracked_last_seen = timestamp_sec
                return best_cand

            # If tracked hand is temporarily occluded/lost, do NOT jump to the other hand!
            # Wait until hand_switch_grace_sec expires.
            return None

        # Case 2: No hand is locked, or previous lock timed out. Pick the dominant hand.
        if len(candidates) == 1:
            chosen = candidates[0]
        else:
            # When multiple hands appear simultaneously, pick the most prominent hand
            # (larger palm, closer to center, higher in frame)
            def _prominence(c: HandObservation) -> float:
                palm_sz = math.hypot(c.landmarks[9].x - c.landmarks[0].x, c.landmarks[9].y - c.landmarks[0].y)
                center_dist = abs(c.landmarks[0].x - 0.5)
                return palm_sz * 2.0 - c.landmarks[0].y * 0.5 - center_dist * 0.2

            chosen = max(candidates, key=_prominence)

        self._tracked_wrist = (chosen.landmarks[0].x, chosen.landmarks[0].y)
        if chosen.handedness != "Unknown":
            self._tracked_handedness = chosen.handedness
        self._tracked_last_seen = timestamp_sec
        return chosen

    def close(self) -> None:
        try:
            self.landmarker.close()
        except Exception:
            pass


def _smooth_chain(points: List[Tuple[float, float]], subdivisions: int = 2) -> List[Tuple[int, int]]:
    """Subdivide a polyline using Chaikin's corner-cutting algorithm to create organic energy curves."""
    pts = [(float(p[0]), float(p[1])) for p in points]
    for _ in range(subdivisions):
        if len(pts) < 2:
            break
        new_pts: List[Tuple[float, float]] = [pts[0]]
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            new_pts.append(q)
            new_pts.append(r)
        new_pts.append(pts[-1])
        pts = new_pts
    return [(int(round(x)), int(round(y))) for x, y in pts]


def _draw_futuristic_orb(
    aura: np.ndarray,
    core: np.ndarray,
    center: Tuple[int, int],
    scale: float,
    phase: float,
    intensity: float = 1.0,
    is_primary: bool = True,
    armed: bool = False,
) -> None:
    """Render a futuristic glowing energy orb with counter-rotating orbital arcs around a fingertip."""
    cx, cy = center
    s = max(0.75, scale)

    # 1. Volumetric plasma corona on the bloom/aura buffer (BGR colors: pure sapphire/cyan, zero yellow)
    outer_r = max(4, int(round((17 if is_primary else 11) * s * (1.15 if armed else 1.0))))
    mid_r = max(3, int(round((9 if is_primary else 6) * s * (1.1 if armed else 1.0))))

    b_outer = int(255 * intensity)
    g_outer = int((145 if armed else 110) * intensity)
    r_outer = int((35 if armed else 15) * intensity)
    cv2.circle(aura, (cx, cy), outer_r, (b_outer, g_outer, r_outer), -1, cv2.LINE_AA)

    b_mid = int(255 * intensity)
    g_mid = int((225 if armed else 195) * intensity)
    r_mid = int((95 if armed else 55) * intensity)
    cv2.circle(aura, (cx, cy), mid_r, (b_mid, g_mid, r_mid), -1, cv2.LINE_AA)

    # 2. Concentrated white-hot ice-cyan core on the sharp core buffer
    core_r = max(2, int(round((4.0 if is_primary else 2.5) * s)))
    ring_r = max(3, int(round((6.5 if is_primary else 4.5) * s)))
    cv2.circle(core, (cx, cy), ring_r, (int(255 * intensity), int(215 * intensity), int(85 * intensity)), max(1, int(round(1.5 * s))), cv2.LINE_AA)
    cv2.circle(core, (cx, cy), core_r, (int(255 * intensity), int(248 * intensity), int(225 * intensity)), -1, cv2.LINE_AA)

    if not is_primary:
        # Subtle energy crescent for secondary extended fingertips
        arc_r = max(5, int(round(8.5 * s)))
        ang = (phase * 120.0) % 360.0
        cv2.ellipse(
            core,
            (cx, cy),
            (arc_r, arc_r),
            ang,
            0,
            110,
            (int(240 * intensity), int(185 * intensity), int(65 * intensity)),
            max(1, int(round(1.2 * s))),
            cv2.LINE_AA,
        )
        return

    # 3. Counter-rotating sci-fi orbital energy arcs for the primary fingertip
    orb1_r = max(7, int(round((11.5 if not armed else 13.0) * s)))
    orb2_r = max(10, int(round((16.0 if not armed else 18.0) * s)))
    thick = max(1, int(round(1.6 * s)))

    ang1 = (phase * 155.0) % 360.0
    ang2 = (-phase * 210.0) % 360.0

    arc_col1 = (255, 235, 135) if armed else (255, 210, 80)
    arc_col2 = (255, 185, 65) if armed else (235, 145, 35)

    # Inner dual orbital arcs
    for offset in (0.0, 180.0):
        cv2.ellipse(core, (cx, cy), (orb1_r, orb1_r), ang1 + offset, 12, 82, arc_col1, thick, cv2.LINE_AA)
        cv2.ellipse(aura, (cx, cy), (orb1_r, orb1_r), ang1 + offset, 12, 82, (255, 160, 30), thick + 1, cv2.LINE_AA)

    # Outer tri-segmented energy field
    for offset in (0.0, 120.0, 240.0):
        cv2.ellipse(core, (cx, cy), (orb2_r, orb2_r), ang2 + offset, 0, 48, arc_col2, max(1, thick - 1), cv2.LINE_AA)

    # 4. Armed state: expanding harmonic pulse wave & telekinetic flick chevrons
    if armed:
        pulse_t = (phase * 1.85) % 1.0
        pulse_r = int(round((11.0 + 16.0 * pulse_t) * s))
        pulse_fade = (1.0 - pulse_t) ** 1.5
        p_col = (int(255 * pulse_fade), int(220 * pulse_fade), int(95 * pulse_fade))
        if pulse_fade > 0.08:
            cv2.circle(core, (cx, cy), pulse_r, p_col, max(1, int(round(1.3 * s))), cv2.LINE_AA)
            cv2.circle(aura, (cx, cy), pulse_r, p_col, max(1, int(round(2.2 * s))), cv2.LINE_AA)

        # Subtle horizontal directional brackets (<  o  >) indicating ready-to-flick power
        b_dist = int(round((22.0 + 2.5 * math.sin(phase * 7.0)) * s))
        b_h = int(round(5.5 * s))
        b_w = int(round(4.0 * s))
        chev_col = (255, 230, 120)
        # Left chevron '<'
        l_pts = np.array([[cx - b_dist + b_w, cy - b_h], [cx - b_dist, cy], [cx - b_dist + b_w, cy + b_h]], dtype=np.int32)
        # Right chevron '>'
        r_pts = np.array([[cx + b_dist - b_w, cy - b_h], [cx + b_dist, cy], [cx + b_dist - b_w, cy + b_h]], dtype=np.int32)
        cv2.polylines(core, [l_pts, r_pts], False, chev_col, thick, cv2.LINE_AA)
        cv2.polylines(aura, [l_pts, r_pts], False, (255, 160, 35), thick + 2, cv2.LINE_AA)


def draw_skeleton(
    frame: np.ndarray,
    hand: HandObservation,
    armed: bool = False,
    phase: Optional[float] = None,
) -> None:
    """Renders a futuristic bioluminescent blue/cyan 'hand power' aura and fingertip energy orb.

    Replaces mechanical wireframe lines and yellow circles with volumetric Gaussian bloom,
    organic flowing energy conduits from the palm core, and rotating sci-fi fingertip orbitals.
    """
    h, w = frame.shape[:2]
    scale = max(0.75, w / 640.0)
    t = time.monotonic() if phase is None else phase

    pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand.landmarks]
    if len(pts) < 21:
        return

    # Compute bounded ROI around the hand so Gaussian bloom is ultra-fast (< 0.5 ms)
    pad = int(round(48 * scale))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0 = max(0, min(xs) - pad)
    y0 = max(0, min(ys) - pad)
    x1 = min(w, max(xs) + pad)
    y1 = min(h, max(ys) + pad)
    rw, rh = x1 - x0, y1 - y0
    if rw <= 4 or rh <= 4:
        return

    # Local ROI coordinates
    lpts = [(px - x0, py - y0) for px, py in pts]
    aura = np.zeros((rh, rw, 3), dtype=np.uint8)
    core = np.zeros((rh, rw, 3), dtype=np.uint8)

    wrist = lpts[0]
    middle_mcp = lpts[9]
    palm_len = max(12.0, math.hypot(middle_mcp[0] - wrist[0], middle_mcp[1] - wrist[1]))

    # Anatomical Palm Power Nexus (center of palm hollow)
    palm_cx = int(
        round(
            0.28 * lpts[0][0]
            + 0.20 * lpts[5][0]
            + 0.22 * lpts[9][0]
            + 0.16 * lpts[13][0]
            + 0.14 * lpts[17][0]
        )
    )
    palm_cy = int(
        round(
            0.28 * lpts[0][1]
            + 0.20 * lpts[5][1]
            + 0.22 * lpts[9][1]
            + 0.16 * lpts[13][1]
            + 0.14 * lpts[17][1]
        )
    )
    palm_nexus = (palm_cx, palm_cy)

    # Determine extension/activity level of each finger so active gestures channel bright energy
    # while curled fingers only show a subtle, non-intrusive ethereal wisp
    def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    thumb_ext = _dist(lpts[4], lpts[17]) > 1.08 * _dist(lpts[3], lpts[17]) and _dist(lpts[4], palm_nexus) > 0.68 * palm_len
    idx_ext = _dist(lpts[8], wrist) > 1.12 * _dist(lpts[6], wrist) or (
        _dist(lpts[8], lpts[5]) > 1.25 * _dist(lpts[6], lpts[5]) and _dist(lpts[8], lpts[5]) > 0.52 * palm_len
    )
    mid_ext = _dist(lpts[12], wrist) > 1.12 * _dist(lpts[10], wrist) or (
        _dist(lpts[12], lpts[9]) > 1.25 * _dist(lpts[10], lpts[9]) and _dist(lpts[12], lpts[9]) > 0.52 * palm_len
    )
    ring_ext = _dist(lpts[16], wrist) > 1.12 * _dist(lpts[14], wrist) or (
        _dist(lpts[16], lpts[13]) > 1.25 * _dist(lpts[14], lpts[13]) and _dist(lpts[16], lpts[13]) > 0.52 * palm_len
    )
    pinky_ext = _dist(lpts[20], wrist) > 1.12 * _dist(lpts[18], wrist) or (
        _dist(lpts[20], lpts[17]) > 1.25 * _dist(lpts[18], lpts[17]) and _dist(lpts[20], lpts[17]) > 0.52 * palm_len
    )
    extensions = [thumb_ext, idx_ext, mid_ext, ring_ext, pinky_ext]

    finger_chains = [
        [palm_nexus, lpts[1], lpts[2], lpts[3], lpts[4]],      # Thumb
        [palm_nexus, lpts[5], lpts[6], lpts[7], lpts[8]],      # Index
        [palm_nexus, lpts[9], lpts[10], lpts[11], lpts[12]],   # Middle
        [palm_nexus, lpts[13], lpts[14], lpts[15], lpts[16]],  # Ring
        [palm_nexus, lpts[17], lpts[18], lpts[19], lpts[20]],  # Pinky
    ]

    # 1. Palm Arc-Reactor / Energy Source Vortex
    nexus_pulse = 0.82 + 0.18 * math.sin(t * 4.5)
    nexus_r = max(6, int(round(min(22 * scale, palm_len * 0.26) * nexus_pulse)))
    cv2.circle(aura, palm_nexus, int(nexus_r * 1.45), (185, 85, 12), -1, cv2.LINE_AA)
    cv2.circle(aura, palm_nexus, int(nexus_r * 0.80), (255, 165, 35), -1, cv2.LINE_AA)
    cv2.circle(core, palm_nexus, max(2, int(round(3.0 * scale))), (255, 225, 140), -1, cv2.LINE_AA)

    # Subtle rotating energy crescents around the palm core
    palm_arc_r = max(8, int(round(min(20 * scale, palm_len * 0.25))))
    p_ang = (t * 65.0) % 360.0
    for off in (0.0, 180.0):
        cv2.ellipse(
            core,
            palm_nexus,
            (palm_arc_r, palm_arc_r),
            p_ang + off,
            15,
            85,
            (215, 145, 35),
            max(1, int(round(1.2 * scale))),
            cv2.LINE_AA,
        )

    # 2. Flowing Bioluminescent Energy Streams along each finger
    for f_idx, (chain, is_ext) in enumerate(zip(finger_chains, extensions)):
        smooth_pts = _smooth_chain(chain, subdivisions=2)
        n_segs = len(smooth_pts) - 1
        if n_segs < 1:
            continue

        # Index finger gets maximum power when pointing/armed; curled fingers get a soft ghostly wisp
        if f_idx == 1 and (is_ext or armed):
            base_energy = 1.0 if armed else 0.92
        elif is_ext:
            base_energy = 0.80
        else:
            base_energy = 0.22

        for s_idx in range(n_segs):
            p1 = smooth_pts[s_idx]
            p2 = smooth_pts[s_idx + 1]
            u = s_idx / float(max(1, n_segs))  # 0 at palm -> 1 at fingertip

            # Traveling harmonic wave from palm to fingertip
            wave = 0.72 + 0.28 * math.sin(t * 9.0 - u * 4.2 + f_idx * 0.6)
            e = min(1.0, base_energy * wave)

            # Taper thickness gracefully along the finger
            taper = 1.0 - 0.35 * u
            aura_thick = max(2, int(round((7.5 if is_ext else 3.5) * scale * taper)))
            core_thick = max(1, int(round((2.2 if is_ext else 1.0) * scale * taper)))

            # Deep sapphire-to-cyan plasma on aura buffer (BGR)
            aura_col = (
                int(255 * e),
                int((185 if armed and f_idx == 1 else 135) * e),
                int((45 if armed and f_idx == 1 else 20) * e),
            )
            cv2.line(aura, p1, p2, aura_col, aura_thick, cv2.LINE_AA)

            # Crisp luminous cyan-white energy filament inside active fingers
            if is_ext or (f_idx == 1 and armed):
                core_col = (
                    int(255 * e),
                    int((235 if f_idx == 1 else 205) * e),
                    int((175 if f_idx == 1 else 95) * e),
                )
                cv2.line(core, p1, p2, core_col, core_thick, cv2.LINE_AA)

    # 3. Pinch / Zoom Plasma Tether (when thumb tip and index tip interact)
    thumb_tip, index_tip = lpts[4], lpts[8]
    pinch_dist = _dist(thumb_tip, index_tip)
    if pinch_dist < 0.55 * palm_len:
        tether_strength = max(0.2, min(1.0, 1.0 - (pinch_dist / (0.55 * palm_len)) * 0.6))
        mid_pt = ((thumb_tip[0] + index_tip[0]) // 2, (thumb_tip[1] + index_tip[1]) // 2)
        cv2.line(
            aura,
            thumb_tip,
            index_tip,
            (int(255 * tether_strength), int(200 * tether_strength), int(55 * tether_strength)),
            max(3, int(round(6 * scale))),
            cv2.LINE_AA,
        )
        cv2.line(
            core,
            thumb_tip,
            index_tip,
            (255, 240, 185),
            max(1, int(round(1.8 * scale))),
            cv2.LINE_AA,
        )
        # Glowing nexus spark at the pinch midpoint
        cv2.circle(aura, mid_pt, max(5, int(round(9 * scale))), (255, 210, 75), -1, cv2.LINE_AA)
        cv2.circle(core, mid_pt, max(2, int(round(3 * scale))), (255, 250, 230), -1, cv2.LINE_AA)

    # 4. Futuristic Fingertip Power Orbs
    tip_indices = [4, 8, 12, 16, 20]
    only_thumb_active = thumb_ext and not (idx_ext or mid_ext or ring_ext or pinky_ext)

    for f_idx, tip_lm_idx in enumerate(tip_indices):
        tip_pt = lpts[tip_lm_idx]
        is_ext = extensions[f_idx]
        if tip_lm_idx == 8:
            # Index fingertip: primary orb when pointing/extended/armed, or soft node when curled
            if is_ext or armed:
                _draw_futuristic_orb(
                    aura, core, tip_pt, scale, t, intensity=1.0, is_primary=True, armed=armed
                )
            else:
                _draw_futuristic_orb(
                    aura, core, tip_pt, scale * 0.7, t, intensity=0.45, is_primary=False, armed=False
                )
        elif tip_lm_idx == 4 and only_thumb_active:
            # Thumbs Up / Thumbs Down: thumb tip channels primary orb!
            _draw_futuristic_orb(
                aura, core, tip_pt, scale * 0.9, t, intensity=0.95, is_primary=True, armed=False
            )
        elif is_ext:
            # Other extended fingertips (Peace sign, Open Palm, OK sign)
            _draw_futuristic_orb(
                aura, core, tip_pt, scale * 0.85, t + f_idx * 0.5, intensity=0.80, is_primary=False, armed=False
            )

    # 5. Multi-scale Gaussian Bloom & Additive Light Compositing onto the frame ROI
    sigma_wide = max(2.5, 7.0 * scale)
    sigma_tight = max(1.2, 2.6 * scale)
    bloom_wide = cv2.GaussianBlur(aura, (0, 0), sigmaX=sigma_wide, sigmaY=sigma_wide)
    bloom_tight = cv2.GaussianBlur(aura, (0, 0), sigmaX=sigma_tight, sigmaY=sigma_tight)

    glow_combined = cv2.addWeighted(bloom_wide, 0.95, bloom_tight, 0.75, 0)
    glow_combined = cv2.add(glow_combined, core)

    roi_view = frame[y0:y1, x0:x1]
    cv2.add(roi_view, glow_combined, dst=roi_view)

