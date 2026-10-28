"""Color palette, Inky-Mono style technical typography loader, and interpolation utilities for FinFlick UI."""

import os
from typing import Dict, Tuple
from PIL import ImageFont

# ---------------- Inky Mono + Cerulean Sky-Glass Aesthetic ----------------
BG_DARK = "#0c1d36"          # Deep nautical cerulean base
BG_SHELL = "#102544"         # Outer shell fill
BG_SHELL_BORDER = "#3b72be"  # Luminous sky-blue rim

SIDEBAR_BG = "#0a192f"       # Crisp technical left icon rail (flush with full-height viewport)
SIDEBAR_HOVER = "#17345e"    # Hovered icon badge in left rail
SIDEBAR_ACTIVE = "#0ea5e9"   # Active gliding pill in left rail

CARD_BG = "#16335e"          # Cerulean card surface
CARD_ELEVATED = "#1d4278"    # Elevated cerulean surface
CARD_HOVER = "#255294"       # Hovered card surface
CARD_ACTIVE = "#2b5fab"      # Active card surface
CARD_INNER = "#10274a"       # Inset pill track surface

CARD_BORDER = "#38bdf8"          # Resting sky-blue border
CARD_BORDER_HOVER = "#7dd3fc"    # Hovered bright sky-cyan border
CARD_BORDER_ACTIVE = "#e0f2fe"   # Active ice-sky border

# ---------------- Interactive Pills & Capsules ----------------
PILL_BG = "#163562"
PILL_HOVER = "#234f8f"
PILL_ACTIVE = "#0ea5e9"
PILL_GLOW = "#7dd3fc"

# ---------------- Inky Mono Accent Pops ----------------
INKY_MINT = "#00e676"        # Signature Inky Mono electric mint/emerald ('*' emblem & [ARMED])
INKY_SKY = "#38bdf8"         # Primary electric sky-blue
INKY_ICE = "#bae6fd"         # High-contrast ice-blue metadata
INKY_CORAL = "#fb7185"       # Bracketed secondary tag / warning accent
INKY_AMBER = "#fbbf24"       # Cooldown / numeric bracket accent

ACCENT_BLUE = "#38bdf8"
ACCENT_CYAN = "#7dd3fc"
ACCENT_ICE = "#e0f2fe"
ACCENT_BRIGHT_CYAN = "#38bdf8"
ACCENT_GREEN = "#00e676"
ACCENT_EMERALD = "#00e676"
ACCENT_ORANGE = "#fbbf24"
ACCENT_RED = "#fb7185"
ACCENT_PURPLE = "#c084fc"

# ---------------- Typography ----------------
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#dbeafe"
TEXT_MUTED = "#7dd3fc"

FONT_FAMILY = "PT Mono"

_FONT_PATHS_REGULAR = [
    ("/System/Library/Fonts/Supplemental/PTMono.ttc", 0),
    ("/System/Library/Fonts/SFNSMono.ttf", 0),
    ("/System/Library/Fonts/Menlo.ttc", 0),
    ("/System/Library/Fonts/Monaco.ttf", 0),
]

_FONT_PATHS_BOLD = [
    ("/System/Library/Fonts/Supplemental/PTMono.ttc", 1),
    ("/System/Library/Fonts/Menlo.ttc", 1),
    ("/System/Library/Fonts/SFNSMono.ttf", 0),
]

_FONT_CACHE: Dict[Tuple[int, bool], ImageFont.FreeTypeFont] = {}


def get_mono_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load and cache the technical monospaced TrueType font (PT Mono / SF Mono) for pixel-perfect HUD rendering."""
    key = (int(size), bool(bold))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    candidates = _FONT_PATHS_BOLD if bold else _FONT_PATHS_REGULAR
    for path, idx in candidates:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, int(size), index=idx)
                _FONT_CACHE[key] = f
                return f
            except Exception:
                continue
    fallback = ImageFont.load_default()
    _FONT_CACHE[key] = fallback  # type: ignore[assignment]
    return fallback  # type: ignore[return-value]


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert '#RRGGBB' to (R, G, B) integers in [0, 255]."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (22, 51, 94)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hex_blend(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two '#RRGGBB' colors for fluid hover/state animations."""
    t_clamped = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t_clamped)
    g = int(g1 + (g2 - g1) * t_clamped)
    b = int(b1 + (b2 - b1) * t_clamped)
    return f"#{r:02x}{g:02x}{b:02x}"


def rgba_blend(
    c1: Tuple[int, int, int, int], c2: Tuple[int, int, int, int], t: float
) -> Tuple[int, int, int, int]:
    """Linearly interpolate between two (R, G, B, A) tuples."""
    tc = max(0.0, min(1.0, float(t)))
    return (
        int(c1[0] + (c2[0] - c1[0]) * tc),
        int(c1[1] + (c2[1] - c1[1]) * tc),
        int(c1[2] + (c2[2] - c1[2]) * tc),
        int(c1[3] + (c2[3] - c1[3]) * tc),
    )
