"""Clean, digitally-drawn vector renderer and camera-iris animator for the FinFlick Fish-Camera Logo."""

from __future__ import annotations

import math
import os
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
SVG_PATH = os.path.join(ASSETS_DIR, "logo.svg")


def _smoothstep(edge0: float, edge1: float, x: np.ndarray | float) -> np.ndarray | float:
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _point_to_segment_dist(
    px: np.ndarray, py: np.ndarray, x1: float, y1: float, x2: float, y2: float
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (distance, parameter_t_in_0_1) from grid (px, py) to segment (x1,y1)->(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy + 1e-12
    t = np.clip(((px - x1) * dx + (py - y1) * dy) / l2, 0.0, 1.0)
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    dist = np.hypot(px - proj_x, py - proj_y)
    return dist, t


def _drop_shadow(mask: np.ndarray, shift_px: Tuple[int, int], blur_sigma: float, opacity: float) -> np.ndarray:
    """Create a soft vector drop-shadow alpha map from a [0, 1] shape mask."""
    h, w = mask.shape
    M = np.float32([[1, 0, shift_px[0]], [0, 1, shift_px[1]]])
    shifted = cv2.warpAffine(mask, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
    ksize = max(3, int(blur_sigma * 3.0) | 1)
    blurred = cv2.GaussianBlur(shifted, (ksize, ksize), blur_sigma)
    return np.clip(blurred * opacity, 0.0, 1.0)


def _lerp_color(
    c1: Tuple[float, float, float], c2: Tuple[float, float, float], t: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    t_c = np.clip(t, 0.0, 1.0)
    return (
        c1[0] + (c2[0] - c1[0]) * t_c,
        c1[1] + (c2[1] - c1[1]) * t_c,
        c1[2] + (c2[2] - c1[2]) * t_c,
    )


class FishStatueRenderer:
    """Renders the clean vector FinFlick fish-camera logo and its swirling camera-iris animation."""

    def __init__(self, size: int = 360):
        self.size = size
        self._layers: Optional[Dict[str, np.ndarray]] = None

        sub = int(self.size * 0.60)
        if sub % 2 == 1:
            sub += 1
        self._iris_sub = sub
        lin_sub = np.linspace(-0.54, 0.54, sub, dtype=np.float32)
        self._iris_x, self._iris_y = np.meshgrid(lin_sub, lin_sub)
        self._iris_r = np.hypot(self._iris_x, self._iris_y)
        self._iris_theta = np.arctan2(self._iris_y, self._iris_x)

        lin_full = np.linspace(-1.06, 1.06, self.size, dtype=np.float32)
        fx, fy = np.meshgrid(lin_full, lin_full)
        self._full_r = np.hypot(fx, fy)

        self._build_layers()

    def _build_layers(self) -> None:
        # 2x supersampling for razor-sharp vector anti-aliasing
        ss = 2
        N = self.size * ss
        lin = np.linspace(-1.06, 1.06, N, dtype=np.float32)
        x, y = np.meshgrid(lin, lin)
        r = np.hypot(x, y)
        theta = np.arctan2(y, x)
        theta_deg = np.degrees(theta)
        theta_left_deg = np.where(theta_deg > 60.0, theta_deg - 360.0, theta_deg)

        aa = 2.0 / N

        # Core geometric radii (bold, clean proportions for far-away legibility)
        r_outer = 0.985
        r_torus = 0.455
        r_funnel = 0.248
        r_hole = 0.155

        u_r = np.clip((r - r_torus) / (r_outer - r_torus + 1e-6), 0.0, 1.0)

        # ------------------------------------------------------------------
        # 1. Clean Vector Curves & Boundaries
        # ------------------------------------------------------------------
        # Top-left S-curve where the Dorsal Wave nose curls into the Fish Head
        dorsal_left_deg = -96.0 - 14.0 * u_r - 24.0 * np.sin(np.pi * (u_r ** 0.82))

        # 4 Wavy Fluted Camera Blades on the right/lower-right (~2:15 to ~5:25)
        crease0_deg = -13.0 + 24.0 * (u_r ** 0.82)   # Bottom of Dorsal Wave / Top of Flute 1
        crease1_deg = 7.0 + 21.0 * (u_r ** 0.85)     # Flute 1 / Flute 2
        crease2_deg = 26.0 + 18.0 * (u_r ** 0.88)    # Flute 2 / Flute 3
        crease3_deg = 45.0 + 14.0 * (u_r ** 0.90)    # Flute 3 / Flute 4
        crease4_deg = 65.0 + 7.5 * (u_r ** 0.92)     # Bottom of Flute 4 / Right edge of 6:00 stem

        # Bottom-left diagonal seam (~7:40)
        cut_nx, cut_ny = -0.545, -0.838
        cut_val = (x - (-0.30)) * cut_nx + (y - 0.31) * cut_ny

        # ------------------------------------------------------------------
        # 2. Layer: BOTTOM-LEFT VENTRAL FIN SECTOR (6:00 to 7:40)
        # ------------------------------------------------------------------
        r_ventral = 0.938
        v_outer_a = _smoothstep(r_ventral + aa, r_ventral - aa, r)
        v_inner_a = _smoothstep(0.34 - aa, 0.34 + aa, r)
        v_right_a = _smoothstep(aa, -aa, x - 0.03) * _smoothstep(-aa, aa, y)
        v_left_a = _smoothstep(aa, -aa, cut_val - 0.03)
        v_mask = v_outer_a * v_inner_a * v_right_a * v_left_a

        v_grad_t = np.clip((x + 0.75) * 0.8 + (y - 0.35) * 0.9, 0.0, 1.0)
        vr, vg, vb = _lerp_color((24.0, 62.0, 116.0), (9.0, 24.0, 48.0), v_grad_t)

        # Clean vector inner rim highlight along the outer arc
        v_rim = np.exp(-(((r - (r_ventral - 0.010)) / 0.008) ** 2)) * _smoothstep(0.02, 0.08, -cut_val)
        vr += 45.0 * v_rim
        vg += 86.0 * v_rim
        vb += 140.0 * v_rim

        # Soft overlap shadow cast by the 7:40 head edge and 6:00 stem
        v_shadow = _smoothstep(0.0, 0.06, -cut_val) * _smoothstep(0.0, 0.05, -x) * _smoothstep(r_torus, r_torus + 0.06, r)
        vr *= 0.46 + 0.54 * v_shadow
        vg *= 0.46 + 0.54 * v_shadow
        vb *= 0.46 + 0.54 * v_shadow

        layer_ventral = np.stack(
            [np.clip(vr, 0, 255), np.clip(vg, 0, 255), np.clip(vb, 0, 255), v_mask * 255.0],
            axis=-1,
        ).astype(np.uint8)

        # ------------------------------------------------------------------
        # 3. Layers: 4 WAVY SCALLOPED CAMERA-FIN BLADES (Right / Lower-Right)
        # ------------------------------------------------------------------
        flute_boundaries = [crease0_deg, crease1_deg, crease2_deg, crease3_deg, crease4_deg]
        flute_layers: List[np.ndarray] = []

        for idx in range(4):
            c_start = flute_boundaries[idx]
            c_end = flute_boundaries[idx + 1]
            span = np.maximum(c_end - c_start, 1e-4)
            u_flute = (theta_deg - c_start) / span
            u_clamped = np.clip(u_flute, 0.0, 1.0)

            scallop_r = 0.958 + 0.032 * np.sin(np.pi * u_clamped)
            f_outer_a = _smoothstep(scallop_r + aa, scallop_r - aa, r)
            f_inner_a = _smoothstep(0.34 - aa, 0.34 + aa, r)
            # Extend top edge of Flute 1 by 4 deg underneath Dorsal Wave so there is NEVER a hairline seam!
            start_pad = 4.0 if idx == 0 else 0.0
            f_side1_a = _smoothstep(-aa * 45.0, aa * 45.0, theta_deg - (c_start - start_pad))
            f_side2_a = _smoothstep(-aa * 45.0, aa * 45.0, (c_end + 4.5) - theta_deg)
            f_mask = f_outer_a * f_inner_a * f_side1_a * f_side2_a

            blade_curve = np.sin(np.pi * (u_clamped ** 0.75))
            radial_bright = 0.72 + 0.28 * u_r
            shade_t = np.clip(blade_curve * radial_bright, 0.0, 1.0)

            depth_factor = 1.0 - 0.06 * idx
            fr, fg, fb = _lerp_color(
                (8.0, 21.0, 44.0),
                (46.0 * depth_factor, 110.0 * depth_factor, 190.0 * depth_factor),
                shade_t,
            )

            lead_line = np.exp(-(((u_flute - 0.14) / 0.065) ** 2)) * _smoothstep(r_torus + 0.02, r_torus + 0.12, r)
            outer_bevel = np.exp(-(((r - (scallop_r - 0.010)) / 0.009) ** 2)) * np.sin(np.pi * u_clamped)
            hl = np.clip(lead_line * 0.65 + outer_bevel * 0.75, 0.0, 1.0)
            fr += 62.0 * hl
            fg += 118.0 * hl
            fb += 185.0 * hl

            crease_shadow = _smoothstep(0.0, 0.14, u_flute) * _smoothstep(r_torus, r_torus + 0.05, r)
            fr *= 0.35 + 0.65 * crease_shadow
            fg *= 0.35 + 0.65 * crease_shadow
            fb *= 0.35 + 0.65 * crease_shadow

            flute_layers.append(
                np.stack(
                    [np.clip(fr, 0, 255), np.clip(fg, 0, 255), np.clip(fb, 0, 255), f_mask * 255.0],
                    axis=-1,
                ).astype(np.uint8)
            )

        # ------------------------------------------------------------------
        # 4. Layer: SWEEPING DORSAL WAVE (Top & Upper-Right)
        #    Clean vector ocean-wave facets curving around the dorsal arc!
        # ------------------------------------------------------------------
        dorsal_outer_a = _smoothstep(r_outer + aa, r_outer - aa, r)
        dorsal_inner_a = _smoothstep(0.34 - aa, 0.34 + aa, r)
        # Extend 3.5 deg underneath the Fish Head along the S-curve so the overlap is 100% seamless
        dorsal_left_a = _smoothstep(-aa * 45.0, aa * 45.0, theta_left_deg - (dorsal_left_deg - 3.5))
        dorsal_right_a = _smoothstep(-aa * 45.0, aa * 45.0, crease0_deg - theta_deg)
        dorsal_mask = dorsal_outer_a * dorsal_inner_a * dorsal_left_a * dorsal_right_a

        # Smooth diagonal vector gradient
        d_grad_t = np.clip((x + 0.35) * 0.58 + (y + 0.85) * 0.52, 0.0, 1.0)
        dr, dg, db = _lerp_color((36.0, 90.0, 162.0), (10.0, 26.0, 54.0), d_grad_t)

        # Clean, curved vector wave facets that follow the spiral flow of the dorsal wave
        d_ang_u = np.clip((theta_left_deg - (-118.0)) / 130.0, 0.0, 1.0)
        spiral_r1 = 0.28 + 0.42 * (d_ang_u ** 0.85) + 0.04 * np.sin(np.pi * d_ang_u * 2.0)
        spiral_r2 = 0.52 + 0.36 * (d_ang_u ** 0.90) - 0.03 * np.cos(np.pi * d_ang_u * 1.5)

        facet1 = _smoothstep(spiral_r1 + 0.015, spiral_r1 - 0.015, u_r)
        facet2 = _smoothstep(spiral_r2 + 0.015, spiral_r2 - 0.015, u_r)
        crest_line1 = np.exp(-(((u_r - spiral_r1) / 0.018) ** 2))
        crest_line2 = np.exp(-(((u_r - spiral_r2) / 0.016) ** 2)) * 0.75

        wave_accent = np.clip(0.22 * facet1 + 0.18 * facet2 + 0.42 * crest_line1 + 0.32 * crest_line2, 0.0, 1.0)
        dr, dg, db = _lerp_color((dr, dg, db), (78.0, 152.0, 238.0), wave_accent)

        # Crisp vector rim highlight along outer top arc and lower crease
        left_edge_dist = (dorsal_left_deg - theta_left_deg) * (r * 0.0175)
        outer_arc_stroke = _smoothstep(0.012, 0.003, np.abs(r - (r_outer - 0.008))) * _smoothstep(0.2, -0.8, y)
        bottom_crease_stroke = (
            _smoothstep(0.014, 0.003, np.abs(theta_deg - crease0_deg) * (r * 0.0175))
            * _smoothstep(r_torus + 0.02, r_torus + 0.08, r)
        )
        d_stroke = np.clip(outer_arc_stroke * 0.65 + bottom_crease_stroke * 0.55, 0.0, 1.0)
        dr = np.clip(dr + 68.0 * d_stroke, 0, 255)
        dg = np.clip(dg + 125.0 * d_stroke, 0, 255)
        db = np.clip(db + 195.0 * d_stroke, 0, 255)

        layer_dorsal = np.stack(
            [np.clip(dr, 0, 255), np.clip(dg, 0, 255), np.clip(db, 0, 255), dorsal_mask * 255.0],
            axis=-1,
        ).astype(np.uint8)

        # ------------------------------------------------------------------
        # 5. Layer: SCULPTED FISH HEAD + CENTRAL TORUS RING + 6:00 STEM (Clean Vector Cobalt Surface)
        # ------------------------------------------------------------------
        torus_part = _smoothstep(r_torus + aa, r_torus - aa, r)
        head_part = (
            _smoothstep(r_outer + aa, r_outer - aa, r)
            * _smoothstep(-aa, aa, cut_val)
            * _smoothstep(aa * 45.0, -aa * 45.0, theta_left_deg - dorsal_left_deg)
            * _smoothstep(0.05, -0.05, x)
        )
        stem_part = (
            _smoothstep(0.978 + aa, 0.978 - aa, r)
            * _smoothstep(-aa, aa, x)
            * _smoothstep(-aa, aa, y - 0.25)
            * _smoothstep(crease4_deg - aa * 45.0, crease4_deg + aa * 45.0, theta_deg)
        )

        body_outer = np.clip(np.maximum(torus_part, np.maximum(head_part, stem_part)), 0.0, 1.0)
        hole_clear = _smoothstep(r_hole - aa, r_hole + aa, r)
        body_mask = body_outer * hole_clear

        # Smooth, noise-free vector gradient across the Fish Head & Torus Ring
        body_grad_t = np.clip((x + 0.75) * 0.52 + (y + 0.65) * 0.48, 0.0, 1.0)
        sr, sg, sb = _lerp_color((66.0, 138.0, 224.0), (24.0, 58.0, 114.0), body_grad_t)

        # Clean 3D vector torus ring bevel:
        # Recessed inner funnel ring (r in [r_hole, r_funnel]) shaded with an inverted gradient for depth
        in_funnel = _smoothstep(r_funnel + aa * 2.0, r_funnel - aa * 2.0, r)
        funnel_grad_t = np.clip((-x + 0.25) * 1.4 + (-y + 0.25) * 1.4, 0.0, 1.0)
        fn_r, fn_g, fn_b = _lerp_color((50.0, 112.0, 194.0), (14.0, 34.0, 70.0), funnel_grad_t)
        sr = sr * (1.0 - in_funnel) + fn_r * in_funnel
        sg = sg * (1.0 - in_funnel) + fn_g * in_funnel
        sb = sb * (1.0 - in_funnel) + fn_b * in_funnel

        # Crisp vector ridge ring at r = r_funnel
        ridge_ring = _smoothstep(0.010, 0.002, np.abs(r - r_funnel))
        sr += 50.0 * ridge_ring
        sg += 92.0 * ridge_ring
        sb += 145.0 * ridge_ring

        # Crisp top-left rim highlight along the outer left head edge and torus outer edge
        outer_head_rim = (
            _smoothstep(0.012, 0.002, np.abs(r - (r_outer - 0.007)))
            * _smoothstep(0.0, -0.3, x)
            * _smoothstep(0.5, -0.7, y)
        )
        torus_outer_rim = (
            _smoothstep(0.011, 0.002, np.abs(r - (r_torus - 0.006)))
            * _smoothstep(-0.25, 0.35, x)
            * _smoothstep(0.40, -0.40, y)
        )
        # Subtle bevel highlight along the S-curve lip of the head (fading cleanly before outer rim)
        s_head_rim = (
            _smoothstep(0.012, 0.002, np.abs(left_edge_dist - 0.006))
            * _smoothstep(r_torus + 0.01, r_torus + 0.05, r)
            * _smoothstep(r_outer - 0.01, r_outer - 0.06, r)
        )
        rim_hl = np.clip(outer_head_rim * 0.8 + torus_outer_rim * 0.65 + s_head_rim * 0.55, 0.0, 1.0)
        sr += 65.0 * rim_hl
        sg += 112.0 * rim_hl
        sb += 165.0 * rim_hl

        # ------------------------------------------------------------------
        # 5b. Clean Vector Gill / Aperture Slot (~9:45-10:10)
        # ------------------------------------------------------------------
        g_curve_y = y + 0.020 * np.sin(np.pi * np.clip((-x - 0.48) / 0.47, 0.0, 1.0))
        g_dist, g_t = _point_to_segment_dist(x, g_curve_y, -0.96, -0.36, -0.48, -0.14)
        g_half_width = 0.024 + 0.038 * (1.0 - g_t) + 0.042 * (np.clip(1.0 - g_t / 0.25, 0.0, 1.0) ** 2)
        groove_sdf = g_half_width - g_dist
        groove_mask = _smoothstep(-aa, aa, groove_sdf) * _smoothstep(r_outer + aa, r_outer - aa, r)

        g_dx, g_dy = -0.48 - (-0.96), -0.14 - (-0.36)
        g_len = math.hypot(g_dx, g_dy)
        g_perp = ((x - (-0.96)) * (-g_dy) + (y - (-0.36)) * g_dx) / g_len
        g_grad = _smoothstep(-0.025, 0.030, g_perp)
        gr_r, gr_g, gr_b = _lerp_color((6.0, 15.0, 32.0), (18.0, 48.0, 92.0), g_grad)

        g_bevel = _smoothstep(0.010, 0.002, np.abs(groove_sdf)) * _smoothstep(0.0, 0.015, g_perp)
        sr = sr * (1.0 - groove_mask) + gr_r * groove_mask + 65.0 * g_bevel
        sg = sg * (1.0 - groove_mask) + gr_g * groove_mask + 120.0 * g_bevel
        sb = sb * (1.0 - groove_mask) + gr_b * groove_mask + 185.0 * g_bevel

        # ------------------------------------------------------------------
        # 5c. Bold, Clean Vector Fish Eye at (-0.69, +0.02)
        # ------------------------------------------------------------------
        eye_cx, eye_cy = -0.69, 0.02
        eye_r = 0.060
        socket_r = 0.102
        eye_dx, eye_dy = x - eye_cx, y - eye_cy
        eye_dist = np.hypot(eye_dx, eye_dy)

        in_socket = _smoothstep(socket_r + aa, socket_r - aa, eye_dist) * _smoothstep(eye_r - aa, eye_r + aa, eye_dist)
        socket_bevel = np.clip((eye_dx + eye_dy) / (socket_r * 1.4), -1.0, 1.0)
        sr += in_socket * socket_bevel * 16.0
        sg += in_socket * socket_bevel * 30.0
        sb += in_socket * socket_bevel * 48.0

        eye_shadow = np.exp(-(((np.hypot(eye_dx - 0.008, eye_dy - 0.010) - eye_r) / 0.018) ** 2)) * 0.42
        sr *= 1.0 - eye_shadow * _smoothstep(eye_r, eye_r + 0.01, eye_dist)
        sg *= 1.0 - eye_shadow * _smoothstep(eye_r, eye_r + 0.01, eye_dist)
        sb *= 1.0 - eye_shadow * _smoothstep(eye_r, eye_r + 0.01, eye_dist)

        eye_mask = _smoothstep(eye_r + aa, eye_r - aa, eye_dist)
        eye_grad_t = np.clip((eye_dx + eye_dy) / (eye_r * 1.6) + 0.5, 0.0, 1.0)
        er, eg, eb = _lerp_color((10.0, 28.0, 58.0), (5.0, 13.0, 28.0), 1.0 - eye_grad_t)

        iris_crescent = (
            _smoothstep(0.010, 0.002, np.abs(eye_dist - eye_r * 0.72))
            * _smoothstep(-0.01, 0.03, eye_dx + eye_dy)
        )
        er += 45.0 * iris_crescent
        eg += 110.0 * iris_crescent
        eb += 195.0 * iris_crescent

        glint_dist = np.hypot(eye_dx + eye_r * 0.34, eye_dy + eye_r * 0.34)
        glint_mask = _smoothstep(eye_r * 0.24 + aa, eye_r * 0.24 - aa, glint_dist)
        er = er * (1.0 - glint_mask) + 215.0 * glint_mask
        eg = eg * (1.0 - glint_mask) + 238.0 * glint_mask
        eb = eb * (1.0 - glint_mask) + 255.0 * glint_mask

        sr = sr * (1.0 - eye_mask) + er * eye_mask
        sg = sg * (1.0 - eye_mask) + eg * eye_mask
        sb = sb * (1.0 - eye_mask) + eb * eye_mask

        # ------------------------------------------------------------------
        # 5d. Drop Shadow Cast by the Central Torus & Head Onto the Surrounding Blades
        # ------------------------------------------------------------------
        blades_union = np.clip(
            dorsal_mask
            + v_mask
            + sum(fl[:, :, 3].astype(np.float32) / 255.0 for fl in flute_layers),
            0.0,
            1.0,
        )
        torus_drop = (
            _drop_shadow(body_outer, shift_px=(int(2.5 * ss), int(3.5 * ss)), blur_sigma=6.0 * ss, opacity=0.52)
            * _smoothstep(r_hole - aa, r_hole + aa, r)
            * blades_union
        )

        layer_stipple = np.stack(
            [np.clip(sr, 0, 255), np.clip(sg, 0, 255), np.clip(sb, 0, 255), body_mask * 255.0],
            axis=-1,
        ).astype(np.uint8)

        layer_torus_shadow = np.zeros((N, N, 4), dtype=np.uint8)
        layer_torus_shadow[:, :, 3] = np.clip(torus_drop * (1.0 - body_mask) * 255.0, 0, 255).astype(np.uint8)

        # ------------------------------------------------------------------
        # 6. Layer: CENTER CAMERA LENS APERTURE (Clean Vector Camera Lens)
        # ------------------------------------------------------------------
        lens_mask = _smoothstep(r_hole + aa, r_hole - aa, r)
        lens_norm = np.clip(r / r_hole, 0.0, 1.0)

        lr, lg, lb = _lerp_color((10.0, 28.0, 58.0), (4.0, 10.0, 22.0), lens_norm ** 1.4)

        ap_ring = _smoothstep(0.011, 0.002, np.abs(r - r_hole * 0.76))
        lr += 48.0 * ap_ring
        lg += 118.0 * ap_ring
        lb += 215.0 * ap_ring

        bezel_ring = _smoothstep(0.012, 0.002, np.abs(r - r_hole * 0.94))
        lr += 24.0 * bezel_ring
        lg += 54.0 * bezel_ring
        lb += 96.0 * bezel_ring

        flare_arc = (
            _smoothstep(0.014, 0.003, np.abs(r - r_hole * 0.50))
            * _smoothstep(-0.2, -0.9, (x + y) / (r + 1e-6))
        )
        flare_dot = _smoothstep(0.020, 0.008, np.hypot(x - r_hole * 0.28, y - r_hole * 0.28)) * 0.65
        flare_total = np.clip(flare_arc * 0.75 + flare_dot, 0.0, 1.0)
        lr += 95.0 * flare_total
        lg += 168.0 * flare_total
        lb += 245.0 * flare_total

        layer_lens = np.stack(
            [np.clip(lr, 0, 255), np.clip(lg, 0, 255), np.clip(lb, 0, 255), lens_mask * 255.0],
            axis=-1,
        ).astype(np.uint8)

        # ------------------------------------------------------------------
        # 7. Layer: BACKING DISC
        # ------------------------------------------------------------------
        disc_mask = _smoothstep(0.935 + aa, 0.935 - aa, r) * hole_clear
        layer_backing = np.zeros((N, N, 4), dtype=np.uint8)
        layer_backing[:, :, 0] = 8
        layer_backing[:, :, 1] = 20
        layer_backing[:, :, 2] = 42
        layer_backing[:, :, 3] = np.clip(disc_mask * 255.0, 0, 255).astype(np.uint8)

        def downsample(img: np.ndarray) -> np.ndarray:
            return cv2.resize(img, (self.size, self.size), interpolation=cv2.INTER_AREA)

        self._layers = {
            "lens": downsample(layer_lens),
            "backing": downsample(layer_backing),
            "ventral": downsample(layer_ventral),
            "flute_0": downsample(flute_layers[0]),
            "flute_1": downsample(flute_layers[1]),
            "flute_2": downsample(flute_layers[2]),
            "flute_3": downsample(flute_layers[3]),
            "dorsal": downsample(layer_dorsal),
            "torus_shadow": downsample(layer_torus_shadow),
            "stipple": downsample(layer_stipple),
        }

    @staticmethod
    def _accum_over(acc_rgb: np.ndarray, acc_a: np.ndarray, src: np.ndarray, alpha_mult: float = 1.0) -> None:
        sa = src[:, :, 3:4].astype(np.float32) * (alpha_mult / 255.0)
        inv_sa = 1.0 - sa
        acc_rgb *= inv_sa
        acc_rgb += src[:, :, :3].astype(np.float32) * sa
        acc_a *= inv_sa[:, :, 0]
        acc_a += sa[:, :, 0]

    @staticmethod
    def _transform_layer(
        layer: np.ndarray,
        angle_deg: float = 0.0,
        scale: float = 1.0,
        pivot_norm: Tuple[float, float] = (0.0, 0.0),
        shift_norm: Tuple[float, float] = (0.0, 0.0),
    ) -> np.ndarray:
        if (
            abs(angle_deg) < 1e-3
            and abs(scale - 1.0) < 1e-3
            and abs(shift_norm[0]) < 1e-4
            and abs(shift_norm[1]) < 1e-4
        ):
            return layer
        h, w = layer.shape[:2]
        px = (pivot_norm[0] / 1.06 * 0.5 + 0.5) * w
        py = (pivot_norm[1] / 1.06 * 0.5 + 0.5) * h
        M = cv2.getRotationMatrix2D((px, py), -angle_deg, scale)
        M[0, 2] += (shift_norm[0] / 1.06 * 0.5) * w
        M[1, 2] += (shift_norm[1] / 1.06 * 0.5) * h
        return cv2.warpAffine(
            layer,
            M,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )

    def _render_inner_iris(self, openness: float, swirl_deg: float, scale: float = 1.0) -> np.ndarray:
        """Render clean vector camera-shutter blades that uncurl from the central torus to reveal the lens hole."""
        sub = self._iris_sub
        inv_s = 1.0 / max(scale, 0.5)
        r = self._iris_r * inv_s
        theta = self._iris_theta

        aa = 2.0 / sub
        outer_r = 0.248 * (1.0 - 0.375 * (openness ** 0.95))
        clip_a = _smoothstep(outer_r + aa, outer_r - aa, r)

        aperture_r = (openness ** 1.35) * 0.155
        raw_hole_mask = _smoothstep(aperture_r - aa * 1.5, aperture_r + aa * 1.5, r)
        closed_seal = float(_smoothstep(0.0, 0.03, openness))
        hole_open_mask = 1.0 - closed_seal * (1.0 - raw_hole_mask)

        num_blades = 6
        rot_rad = math.radians(swirl_deg * 1.35)
        twist_strength = 2.8 * (1.0 - 0.35 * openness)
        spiral_phase = (theta - rot_rad + twist_strength * (r - aperture_r)) * (num_blades / (2.0 * math.pi))
        blade_u = spiral_phase - np.floor(spiral_phase)

        blade_grad = 0.25 + 0.75 * (blade_u ** 0.75)
        seam_shadow = _smoothstep(0.0, 0.12, blade_u) * _smoothstep(1.0, 0.90, blade_u)
        edge_stroke = _smoothstep(0.08, 0.015, np.abs(blade_u - 0.10))
        inner_rim_stroke = _smoothstep(0.014, 0.003, np.abs(r - aperture_r)) * closed_seal

        shade = blade_grad * (0.35 + 0.65 * seam_shadow)
        br = 9.0 + 30.0 * shade + 54.0 * edge_stroke + 65.0 * inner_rim_stroke
        bg = 24.0 + 68.0 * shade + 108.0 * edge_stroke + 128.0 * inner_rim_stroke
        bb = 50.0 + 124.0 * shade + 178.0 * edge_stroke + 205.0 * inner_rim_stroke

        retract_fade = float(_smoothstep(1.0, 0.86, openness))
        final_a = clip_a * hole_open_mask * retract_fade

        sub_rgba = np.empty((sub, sub, 4), dtype=np.uint8)
        sub_rgba[:, :, 0] = np.clip(br, 0, 255).astype(np.uint8)
        sub_rgba[:, :, 1] = np.clip(bg, 0, 255).astype(np.uint8)
        sub_rgba[:, :, 2] = np.clip(bb, 0, 255).astype(np.uint8)
        sub_rgba[:, :, 3] = np.clip(final_a * 255.0, 0, 255).astype(np.uint8)
        return sub_rgba

    def render_frame(
        self,
        progress: float = 1.0,
        include_lens: bool = True,
        hole_expand: float = 0.0,
    ) -> Image.Image:
        """Render the vector Fish-Camera Logo at animation progress in [0.0 (closed swirl), 1.0 (open logo)]."""
        assert self._layers is not None
        p = float(np.clip(progress, 0.0, 1.0))
        # Smooth quintic-like ease-in-out / ease-out for unhurried, graceful motion
        if p < 0.35:
            ease = 0.5 * ((p / 0.35) ** 2.2) * 0.45
        else:
            t_rem = (p - 0.35) / 0.65
            ease = 0.225 + 0.775 * (1.0 - (1.0 - t_rem) ** 3.0)

        expand_e = float(np.clip(hole_expand, 0.0, 1.0)) ** 1.8
        global_swirl = (1.0 - ease) * (-165.0) + expand_e * 45.0
        overall_scale = (0.90 + 0.10 * ease) * (1.0 + 0.25 * expand_e)
        curl = 1.0 - ease

        acc_rgb = np.zeros((self.size, self.size, 3), dtype=np.float32)
        acc_a = np.zeros((self.size, self.size), dtype=np.float32)

        # 1. Center Lens Core
        if include_lens and p > 0.10 and expand_e < 0.85:
            lens_alpha = float(_smoothstep(0.10, 0.65, ease)) * (1.0 - expand_e / 0.85)
            lens_layer = self._transform_layer(self._layers["lens"], scale=overall_scale)
            self._accum_over(acc_rgb, acc_a, lens_layer, alpha_mult=lens_alpha)

        # 2. Backing disc
        if curl > 0.005:
            backing = self._transform_layer(self._layers["backing"], angle_deg=global_swirl, scale=overall_scale)
            self._accum_over(acc_rgb, acc_a, backing)

        # 3. Ventral sector
        ventral = self._transform_layer(
            self._layers["ventral"],
            angle_deg=global_swirl - 22.0 * curl,
            scale=overall_scale,
        )
        self._accum_over(acc_rgb, acc_a, ventral)

        # 4. The 4 Wavy Scalloped Flutes fan out sequentially
        for idx in range(3, -1, -1):
            flute_p = float(np.clip((ease - idx * 0.05) / (1.0 - idx * 0.05), 0.0, 1.0))
            flute_curl = (1.0 - flute_p) ** 2.4
            flute_layer = self._transform_layer(
                self._layers[f"flute_{idx}"],
                angle_deg=global_swirl - (15.0 + idx * 11.0) * flute_curl,
                scale=overall_scale,
            )
            self._accum_over(acc_rgb, acc_a, flute_layer)

        # 5. Sweeping Dorsal Wave
        dorsal = self._transform_layer(
            self._layers["dorsal"],
            angle_deg=global_swirl - 28.0 * curl,
            scale=overall_scale,
        )
        self._accum_over(acc_rgb, acc_a, dorsal)

        # 6. Drop shadow cast by the central torus & head onto the surrounding blades
        t_shad = self._transform_layer(
            self._layers["torus_shadow"],
            angle_deg=global_swirl,
            scale=overall_scale,
        )
        self._accum_over(acc_rgb, acc_a, t_shad)

        # 7. Sculpted Fish Head + Central Torus Collar + Eye + Groove
        stipple = self._transform_layer(
            self._layers["stipple"],
            angle_deg=global_swirl,
            scale=overall_scale,
        )
        self._accum_over(acc_rgb, acc_a, stipple)

        # 8. Inner Swirling Camera Iris Blades
        iris_openness = float(_smoothstep(0.06, 0.90, ease))
        if iris_openness < 0.995:
            sub_rgba = self._render_inner_iris(
                openness=iris_openness, swirl_deg=global_swirl, scale=overall_scale
            )
            c0 = (self.size - self._iris_sub) // 2
            c1 = c0 + self._iris_sub
            self._accum_over(acc_rgb[c0:c1, c0:c1], acc_a[c0:c1, c0:c1], sub_rgba)

        if expand_e > 0.001:
            expand_r = (0.155 + 0.92 * expand_e) * overall_scale
            aa_exp = 0.018
            hole_punch = _smoothstep(expand_r - aa_exp, expand_r + aa_exp, self._full_r)
            rim_glow = np.exp(-(((self._full_r - expand_r) / 0.022) ** 2)) * (1.0 - expand_e * 0.5)
            acc_rgb[:, :, 0] += 45.0 * rim_glow * acc_a
            acc_rgb[:, :, 1] += 115.0 * rim_glow * acc_a
            acc_rgb[:, :, 2] += 210.0 * rim_glow * acc_a
            acc_rgb *= hole_punch[:, :, None]
            acc_a *= hole_punch

        safe_a = np.where(acc_a > 1e-5, acc_a, 1.0)
        out = np.empty((self.size, self.size, 4), dtype=np.uint8)
        out[:, :, :3] = np.clip(acc_rgb / safe_a[:, :, None], 0, 255).astype(np.uint8)
        out[:, :, 3] = np.clip(acc_a * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(out, mode="RGBA")


def _write_svg_logo(path: str) -> None:
    """Write a standalone scalable vector SVG representation of the FinFlick Fish-Camera Logo."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-106 -106 212 212" width="512" height="512">
  <defs>
    <linearGradient id="bodyGrad" x1="15%" y1="15%" x2="85%" y2="85%">
      <stop offset="0%" stop-color="#428ADE"/>
      <stop offset="55%" stop-color="#255CA8"/>
      <stop offset="100%" stop-color="#15386E"/>
    </linearGradient>
    <linearGradient id="dorsalGrad" x1="25%" y1="10%" x2="90%" y2="65%">
      <stop offset="0%" stop-color="#245A9E"/>
      <stop offset="55%" stop-color="#113260"/>
      <stop offset="100%" stop-color="#091A36"/>
    </linearGradient>
    <linearGradient id="fluteGrad" x1="0%" y1="0%" x2="80%" y2="100%">
      <stop offset="0%" stop-color="#2D6DC0"/>
      <stop offset="65%" stop-color="#112E59"/>
      <stop offset="100%" stop-color="#07152B"/>
    </linearGradient>
    <linearGradient id="ventralGrad" x1="20%" y1="20%" x2="80%" y2="90%">
      <stop offset="0%" stop-color="#193F75"/>
      <stop offset="100%" stop-color="#091830"/>
    </linearGradient>
    <linearGradient id="funnelGrad" x1="85%" y1="85%" x2="15%" y2="15%">
      <stop offset="0%" stop-color="#3270C2"/>
      <stop offset="100%" stop-color="#0E2246"/>
    </linearGradient>
    <filter id="dropShadow" x="-15%" y="-15%" width="130%" height="130%">
      <feDropShadow dx="2.5" dy="3.5" stdDeviation="4" flood-color="#020710" flood-opacity="0.55"/>
    </filter>
  </defs>
  <!-- Ventral Sector -->
  <path d="M 0,44 L 0,93.8 A 93.8,93.8 0 0,1 -73.9,57.7 L -30,31 Z" fill="url(#ventralGrad)" stroke="#3D78C2" stroke-width="0.8"/>
  <!-- 4 Wavy Camera-Fin Blades -->
  <path d="M 18,41 L 29,93.5 A 98,98 0 0,0 50,84 L 31,32 Z" fill="url(#fluteGrad)" stroke="#488CE0" stroke-width="0.8"/>
  <path d="M 31,32 L 50,84 A 98,98 0 0,0 70,69 L 40,19 Z" fill="url(#fluteGrad)" stroke="#488CE0" stroke-width="0.8"/>
  <path d="M 40,19 L 70,69 A 98,98 0 0,0 86,47 L 45,5 Z" fill="url(#fluteGrad)" stroke="#488CE0" stroke-width="0.8"/>
  <path d="M 45,5 L 86,47 A 98,98 0 0,0 96,19 L 44,-11 Z" fill="url(#fluteGrad)" stroke="#488CE0" stroke-width="0.8"/>
  <!-- Sweeping Dorsal Wave -->
  <path d="M -34,-92.4 A 98.5,98.5 0 0,1 96.5,19 L 44,-11 A 45.5,45.5 0 0,0 -8,-44.8 C -28,-48 -42,-66 -34,-92.4 Z" fill="url(#dorsalGrad)" stroke="#4C92E8" stroke-width="1"/>
  <!-- Sculpted Fish Head, Central Torus & 6-o'clock Stem -->
  <path d="M -34,-92.4 C -42,-66 -28,-48 -8,-44.8 A 45.5,45.5 0 0,1 18,41.8 L 28.5,93.5 A 97.8,97.8 0 0,1 0,97.8 L 0,45.5 A 45.5,45.5 0 0,1 -30,31 L -77.6,60.6 A 98.5,98.5 0 0,1 -92.5,-34 L -48,-14 L -84,-52 A 98.5,98.5 0 0,1 -34,-92.4 Z" fill="url(#bodyGrad)" filter="url(#dropShadow)" stroke="#5CA2F5" stroke-width="1"/>
  <!-- Inner Torus Funnel & Camera Lens Aperture -->
  <circle cx="0" cy="0" r="24.8" fill="url(#funnelGrad)" stroke="#5AA0F2" stroke-width="1.2"/>
  <circle cx="0" cy="0" r="15.5" fill="#061020" stroke="#2D68B8" stroke-width="1.2"/>
  <circle cx="0" cy="0" r="11.8" fill="none" stroke="#3898FF" stroke-width="1.2" opacity="0.85"/>
  <path d="M -6,-5 A 7.8,7.8 0 0,1 5,-6" fill="none" stroke="#85C8FF" stroke-width="1.8" stroke-linecap="round"/>
  <circle cx="4.2" cy="4.2" r="1.6" fill="#68B5FF"/>
  <!-- Fish Eye -->
  <circle cx="-69" cy="2" r="9.8" fill="#1F4E91" opacity="0.55"/>
  <circle cx="-69" cy="2" r="6.0" fill="#07152B" stroke="#2D6BC0" stroke-width="0.9"/>
  <circle cx="-71" cy="0" r="1.5" fill="#D8EEFF"/>
</svg>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def ensure_logo_assets() -> Tuple[Image.Image, Image.Image]:
    """Ensure high-res vector logo.png, icon.png, and logo.svg exist in assets/ and return (logo_img, icon_img)."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.exists(SVG_PATH):
        try:
            _write_svg_logo(SVG_PATH)
        except Exception:
            pass
    if os.path.exists(LOGO_PATH) and os.path.exists(ICON_PATH):
        try:
            return Image.open(LOGO_PATH).convert("RGBA"), Image.open(ICON_PATH).convert("RGBA")
        except Exception:
            pass

    renderer = FishStatueRenderer(size=512)
    logo_img = renderer.render_frame(1.0, include_lens=True)
    icon_img = logo_img.resize((128, 128), Image.LANCZOS)
    logo_img.save(LOGO_PATH)
    icon_img.save(ICON_PATH)
    return logo_img, icon_img
