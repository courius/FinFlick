"""Self-contained HTML5 / CSS3 / SVG / WebAudio frontend bundle for the native WKWebView metallic-blue UI."""

from __future__ import annotations

import json
from typing import Dict


def get_hand_filter_svgs() -> Dict[str, str]:
    """Return 3 custom light-blue metallic SVG hand vectors for the 3 square Hand-Filter buttons ('left', 'any', 'right')."""
    defs = """
    <defs>
      <linearGradient id="hfGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#E0F2FE" stop-opacity="0.98"/>
        <stop offset="55%" stop-color="#7DD3FC" stop-opacity="0.90"/>
        <stop offset="100%" stop-color="#2563EB" stop-opacity="0.85"/>
      </linearGradient>
      <linearGradient id="hfBackGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#BAE6FD" stop-opacity="0.72"/>
        <stop offset="100%" stop-color="#1D4ED8" stop-opacity="0.62"/>
      </linearGradient>
      <filter id="hfGlow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="1.8" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    """

    # Base open right-hand path (thumb on left, 4 fingers up)
    right_hand_path = (
        "M23 32 V15.5 C23 13.8 24.3 12.5 25.8 12.5 C27.3 12.5 28.5 13.8 28.5 15.5 V29 "
        "H30.2 V13 C30.2 11.3 31.5 10 33 10 C34.5 10 35.8 11.3 35.8 13 V29 "
        "H37.5 V15.8 C37.5 14.1 38.8 12.8 40.3 12.8 C41.8 12.8 43 14.1 43 15.8 V31 "
        "H44.6 V21.5 C44.6 19.9 45.8 18.6 47.2 18.6 C48.6 18.6 49.8 19.9 49.8 21.5 V42.5 "
        "C49.8 50.8 43.6 56.5 35 56.5 H28 "
        "C21.8 56.5 17.6 52.8 15.6 47.2 L12.4 38 "
        "C11.7 36 12.8 34 14.7 33.5 C16.5 33 18.4 34.1 19.2 36 L21.3 41 V32 H23 Z"
    )

    return {
        # 1. Left Hand Tilted to the Left (mirrored horizontally & rotated -15 deg)
        "left": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <g transform="rotate(-15 32 35) translate(64 0) scale(-1 1)">
            <path d="{right_hand_path}" fill="url(#hfGrad)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#hfGlow)"/>
            <circle cx="33.5" cy="43" r="3.5" fill="#00F5D4" fill-opacity="0.85"/>
          </g>
        </svg>""",

        # 2. Both Hands Overlapping (left hand tilted left behind + right hand tilted right in front)
        "any": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <g transform="translate(-6 1) rotate(-14 32 36) translate(64 0) scale(-0.84 0.84)">
            <path d="{right_hand_path}" fill="url(#hfBackGrad)" stroke="#BAE6FD" stroke-width="1.5" stroke-linejoin="round"/>
          </g>
          <g transform="translate(11 2) rotate(14 32 36) scale(0.84 0.84)">
            <path d="{right_hand_path}" fill="url(#hfGrad)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#hfGlow)"/>
          </g>
          <circle cx="32" cy="41" r="4.2" fill="#00F5D4" fill-opacity="0.9" stroke="#FFFFFF" stroke-width="1.2"/>
        </svg>""",

        # 3. Right Hand Tilted to the Right (rotated +15 deg)
        "right": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <g transform="rotate(15 32 35)">
            <path d="{right_hand_path}" fill="url(#hfGrad)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#hfGlow)"/>
            <circle cx="33.5" cy="43" r="3.5" fill="#00F5D4" fill-opacity="0.85"/>
          </g>
        </svg>""",
    }


def get_gesture_svgs() -> Dict[str, str]:
    """Return 10 custom light-blue metallic SVG hand-gesture vector illustrations (viewBox 0 0 64 64)."""
    defs = """
    <defs>
      <linearGradient id="handFill" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#E0F2FE" stop-opacity="0.96"/>
        <stop offset="50%" stop-color="#7DD3FC" stop-opacity="0.88"/>
        <stop offset="100%" stop-color="#2563EB" stop-opacity="0.82"/>
      </linearGradient>
      <linearGradient id="handAccent" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#38BDF8"/>
        <stop offset="100%" stop-color="#00F5D4"/>
      </linearGradient>
      <filter id="softGlow" x="-25%" y="-25%" width="150%" height="150%">
        <feGaussianBlur stdDeviation="2.2" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    """

    return {
        # 1. Pointing index hand + glowing motion arc & chevron to the RIGHT
        "NEXT_SLIDE": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M16 14 C28 7, 42 7, 54 15" stroke="url(#handAccent)" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="3 3"/>
          <path d="M47 10 L54 15 L47 20" stroke="#00F5D4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M52 10 L59 15 L52 20" stroke="#7DD3FC" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="28" cy="14" r="5.5" fill="#00F5D4" fill-opacity="0.28"/>
          <path d="M24.5 34 V14.5 C24.5 12.3 26.1 10.8 28 10.8 C29.9 10.8 31.5 12.3 31.5 14.5 V31.5
                   H33.5 C35.2 31.5 36.5 32.8 36.5 34.5 V35.5
                   H38.5 C40.2 35.5 41.5 36.8 41.5 38.5 V39.5
                   H43 C44.7 39.5 46 40.8 46 42.5 V46.5
                   C46 53.2 40.8 58 34 58 H25.5
                   C20.5 58 17 54.6 15.6 50.2 L13.2 42.5
                   C12.5 40.3 13.8 38.2 15.9 37.8 C17.8 37.4 19.6 38.5 20.4 40.4 L22 44 V34 H24.5 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <circle cx="28" cy="14" r="2.6" fill="#FFFFFF"/>
        </svg>""",

        # 2. Pointing index hand + glowing motion arc & chevron to the LEFT
        "PREV_SLIDE": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M48 14 C36 7, 22 7, 10 15" stroke="url(#handAccent)" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="3 3"/>
          <path d="M17 10 L10 15 L17 20" stroke="#00F5D4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M12 10 L5 15 L12 20" stroke="#7DD3FC" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="34" cy="14" r="5.5" fill="#00F5D4" fill-opacity="0.28"/>
          <path d="M30.5 34 V14.5 C30.5 12.3 32.1 10.8 34 10.8 C35.9 10.8 37.5 12.3 37.5 14.5 V31.5
                   H39.5 C41.2 31.5 42.5 32.8 42.5 34.5 V35.5
                   H44.5 C46.2 35.5 47.5 38.5 V39.5
                   H49 C50.7 39.5 52 40.8 52 42.5 V46.5
                   C52 53.2 46.8 58 40 58 H31.5
                   C26.5 58 23 54.6 21.6 50.2 L19.2 42.5
                   C18.5 40.3 19.8 38.2 21.9 37.8 C23.8 37.4 25.6 38.5 26.4 40.4 L28 44 V34 H30.5 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <circle cx="34" cy="14" r="2.6" fill="#FFFFFF"/>
        </svg>""",

        # 3. Expanding Open Palm Bloom (Zoom In +)
        "ZOOM_IN": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M11 19 V11 H19" stroke="#00F5D4" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M53 19 V11 H45" stroke="#00F5D4" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M11 45 V53 H19" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M53 45 V53 H45" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M23 33 V16 C23 14.3 24.3 13 25.8 13 C27.3 13 28.5 14.3 28.5 16 V30
                   H30 V13.5 C30 11.8 31.3 10.5 32.8 10.5 C34.3 10.5 35.5 11.8 35.5 13.5 V30
                   H37 V16.5 C37 14.8 38.3 13.5 39.8 13.5 C41.3 13.5 42.5 14.8 42.5 16.5 V32
                   H44 V22 C44 20.5 45.2 19.2 46.6 19.2 C48 19.2 49.2 20.5 49.2 22 V43
                   C49.2 51.5 43 57.5 34.5 57.5 H27.5
                   C21.5 57.5 17.5 53.8 15.5 48.2 L12.2 38.8
                   C11.5 36.8 12.6 34.8 14.5 34.3 C16.3 33.8 18.2 34.9 19 36.8 L21.2 42 V33 H23 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.5" stroke-linejoin="round" filter="url(#softGlow)"/>
          <path d="M33 40 V48 M29 44 H37" stroke="#081C38" stroke-width="2.6" stroke-linecap="round"/>
        </svg>""",

        # 4. Thumbs Down Hand (Zoom Out -)
        "ZOOM_OUT": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M15 44 L15 55 M10.5 50.5 L15 55.5 L19.5 50.5" stroke="#00F5D4" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M24 14 H42 C46.5 14 50 17.5 50 22 V35
                   C50 37.5 48 39.5 45.5 39.5 H29
                   V51.5 C29 54.3 26.8 56.5 24 56.5 C21.2 56.5 19 54.3 19 51.5 V34
                   C19 29.5 20.5 26 22 22 V16 C22 14.9 22.9 14 24 14 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <path d="M37 20 H49 M37 26.5 H49 M37 33 H48" stroke="#0B2246" stroke-width="2.0" stroke-linecap="round"/>
          <path d="M26 26 H33" stroke="#081C38" stroke-width="2.6" stroke-linecap="round"/>
        </svg>""",

        # 5. OK Pinch Hand (Play / Pause Media)
        "PLAY_PAUSE": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <circle cx="24" cy="34" r="9.5" stroke="#00F5D4" stroke-width="2.2" stroke-dasharray="3 2.5"/>
          <path d="M33 31 V14 C33 12.2 34.4 10.8 36.2 10.8 C38 10.8 39.4 12.2 39.4 14 V30
                   H41 V16 C41 14.2 42.4 12.8 44.2 12.8 C46 12.8 47.4 14.2 47.4 16 V32
                   H49 V21.5 C49 19.8 50.3 18.5 52 18.5 C53.7 18.5 55 19.8 55 21.5 V43
                   C55 51.5 48.5 57.5 39.5 57.5 H28.5
                   C21 57.5 15.5 52.5 14.5 45.5
                   C13.8 40.5 16.5 36.5 21 36.5 C24 36.5 26 38.5 28 40.5
                   C29.8 38.5 31 35 33 31 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <circle cx="24" cy="34" r="5.5" fill="#091D3E" stroke="#E0F2FE" stroke-width="2.2"/>
          <polygon points="22.5,31.5 27,34 22.5,36.5" fill="#00F5D4"/>
        </svg>""",

        # 6. Raised Closed Fist (Blank Screen / Blackout)
        "BLACKOUT": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M14 26 C16 14, 48 14, 50 26" stroke="url(#handAccent)" stroke-width="2.2" stroke-linecap="round"/>
          <rect x="17" y="21" width="30" height="34" rx="10" fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" filter="url(#softGlow)"/>
          <path d="M24.5 21 V32 M32 21 V32 M39.5 21 V32" stroke="#0B2246" stroke-width="2.1" stroke-linecap="round"/>
          <path d="M17 34 H38 C40.5 34 42.5 36 42.5 38.5 C42.5 41 40.5 43 38 43 H22"
                fill="#7DD3FC" stroke="#0B2246" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",

        # 7. Vertical Index Up Hold (First Slide)
        "FIRST_SLIDE": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M21 9 H43" stroke="#00F5D4" stroke-width="2.8" stroke-linecap="round"/>
          <circle cx="32" cy="16" r="4.8" fill="#00F5D4" fill-opacity="0.32"/>
          <path d="M28.5 34 V16 C28.5 13.8 30.1 12.2 32 12.2 C33.9 12.2 35.5 13.8 35.5 16 V32
                   H42 C45.8 32 48.5 34.8 48.5 38.5 V46.5
                   C48.5 53 43.2 58 36.5 58 H27.5
                   C21.2 58 16.5 53.2 16.5 46.8 V39.5
                   C16.5 35.5 19.5 32.5 23.5 32.5 H28.5 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <circle cx="32" cy="16" r="2.3" fill="#FFFFFF"/>
        </svg>""",

        # 8. Thumbs Up Hand (Last Slide)
        "LAST_SLIDE": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M19 14 L24 9 L29 14" stroke="#00F5D4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M29 29.5 V17.5 C29 14.7 26.8 12.5 24 12.5 C21.2 12.5 19 14.7 19 17.5 V34
                   C19 38.5 20.5 42 22 46 V52 C22 53.7 23.3 55 25 55 H42
                   C46.5 55 50 51.5 50 47 V34
                   C50 31.5 48 29.5 45.5 29.5 H29 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <path d="M37 36 H49 M37 42.5 H49 M37 49 H48" stroke="#0B2246" stroke-width="2.0" stroke-linecap="round"/>
        </svg>""",

        # 9. Peace / V-Sign Hand (Start Presentation)
        "START_PRESENTATION": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <circle cx="23" cy="13" r="4.5" fill="#00F5D4" fill-opacity="0.32"/>
          <circle cx="40" cy="13" r="4.5" fill="#00F5D4" fill-opacity="0.32"/>
          <path d="M26.5 33 L20 14.5 C19.2 12.4 20.3 10.2 22.3 9.6 C24.3 9 26.3 10.2 27.1 12.3 L32 27.5
                   L36.9 12.3 C37.7 10.2 39.7 9 41.7 9.6 C43.7 10.2 44.8 12.4 44 14.5 L37.5 33
                   H43.5 C46.8 33 49.5 35.7 49.5 39 V46.5
                   C49.5 53 44.2 58 37.5 58 H26.5
                   C20.2 58 15.5 53.2 15.5 46.8 V40
                   C15.5 36.2 18.5 33 22.5 33 H26.5 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <circle cx="23.2" cy="13.2" r="2.2" fill="#FFFFFF"/>
          <circle cx="40.8" cy="13.2" r="2.2" fill="#FFFFFF"/>
        </svg>""",

        # 10. Open 5-Finger Hand (Pause / Resume Sensor)
        "TOGGLE_PAUSE": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <path d="M22.5 33 V15.5 C22.5 13.8 23.8 12.5 25.4 12.5 C27 12.5 28.2 13.8 28.2 15.5 V29.5
                   H29.8 V12.5 C29.8 10.8 31.1 9.5 32.7 9.5 C34.3 9.5 35.5 10.8 35.5 12.5 V29.5
                   H37.1 V15.5 C37.1 13.8 38.4 12.5 40 12.5 C41.6 12.5 42.8 13.8 42.8 15.5 V31.5
                   H44.4 V21.5 C44.4 19.9 45.6 18.6 47.1 18.6 C48.6 18.6 49.8 19.9 49.8 21.5 V43
                   C49.8 51.5 43.5 57.5 34.8 57.5 H27.5
                   C21.2 57.5 17 53.6 15 48 L11.6 38.5
                   C10.9 36.5 12 34.4 14 33.9 C15.8 33.4 17.8 34.5 18.6 36.5 L20.8 41.8 V33 H22.5 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <circle cx="33.5" cy="43.5" r="6.2" fill="#081C38" stroke="#00F5D4" stroke-width="2.0"/>
          <line x1="31.5" y1="41" x2="31.5" y2="46" stroke="#E0F2FE" stroke-width="2.0" stroke-linecap="round"/>
          <line x1="35.5" y1="41" x2="35.5" y2="46" stroke="#E0F2FE" stroke-width="2.0" stroke-linecap="round"/>
        </svg>""",

        # 11. L-Shape Hand (Laser Pointer 'L')
        "LASER_POINTER": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <line x1="30" y1="12" x2="30" y2="3" stroke="#FF2A6D" stroke-width="2.8" stroke-linecap="round"/>
          <circle cx="30" cy="3" r="3.2" fill="#FF2A6D" filter="url(#softGlow)"/>
          <circle cx="30" cy="3" r="1.4" fill="#FFFFFF"/>
          <path d="M26.5 34 V14 C26.5 12 28.1 10.5 30 10.5 C31.9 10.5 33.5 12 33.5 14 V32
                   H41 C44.5 32 47 34.5 47 38 V46
                   C47 52.5 42 57.5 35.5 57.5 H26.5
                   C21 57.5 17 54 15 48.5 L12 40
                   C11.2 38 12.2 35.8 14.2 35.2 C16 34.8 17.8 35.8 18.6 37.6 L21 42 V34 H26.5 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
          <path d="M13 41 L7 37 C5.5 35.8 5.2 33.4 6.5 31.8 C7.8 30.2 10.2 29.8 11.8 31.2 L17 35.5"
                stroke="#00F5D4" stroke-width="2.5" stroke-linecap="round"/>
        </svg>""",

        # 12. W-Sign Hand (Whiteboard / White Screen 'W')
        "WHITE_SCREEN": f"""<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">{defs}
          <rect x="10" y="7" width="44" height="26" rx="4" fill="#FFFFFF" fill-opacity="0.18" stroke="#FFFFFF" stroke-width="1.8" stroke-dasharray="3 2"/>
          <text x="32" y="24" font-family="sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF" text-anchor="middle">W</text>
          <path d="M22 34 V15 C22 13.5 23.2 12.2 24.7 12.2 C26.2 12.2 27.4 13.5 27.4 15 V30
                   H29 V13.5 C29 12 30.2 10.8 31.7 10.8 C33.2 10.8 34.4 12 34.4 13.5 V30
                   H36 V15.5 C36 14 37.2 12.8 38.7 12.8 C40.2 12.8 41.4 14 41.4 15.5 V32
                   H45 C48 32 50.5 34.5 50.5 37.5 V45
                   C50.5 52 45 57.5 38 57.5 H28
                   C22 57.5 17.5 53.5 15.5 47.8 L13.2 41
                   C12.5 39.2 13.5 37.2 15.3 36.8 C17 36.4 18.8 37.4 19.5 39.2 L21.2 43 V34 H22 Z"
                fill="url(#handFill)" stroke="#E0F2FE" stroke-width="1.6" stroke-linejoin="round" filter="url(#softGlow)"/>
        </svg>""",
    }


def build_html_ui() -> str:
    """Build the complete metallic-blue futuristic HTML5/CSS3/SVG/JS application shell."""
    svgs = get_gesture_svgs()
    hand_svgs = get_hand_filter_svgs()
    svgs_json = json.dumps(svgs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FinFlick — Touchless Presentation Control</title>
<style>
  :root {{
    /* Metallic-Blue Palette Inspired by the FinFlick Fish-Camera Logo */
    --chassis-deep: #050D1C;
    --chassis-mid: #091933;
    --metallic-surface: linear-gradient(
      145deg,
      rgba(56, 122, 218, 0.36) 0%,
      rgba(22, 54, 108, 0.58) 48%,
      rgba(9, 23, 48, 0.76) 100%
    );
    --metallic-card-hover: linear-gradient(
      145deg,
      rgba(74, 148, 246, 0.46) 0%,
      rgba(28, 68, 134, 0.66) 50%,
      rgba(12, 31, 64, 0.82) 100%
    );
    --metallic-pill: linear-gradient(
      135deg,
      rgba(42, 96, 178, 0.48) 0%,
      rgba(16, 40, 82, 0.72) 100%
    );
    --metallic-pill-active: linear-gradient(
      135deg,
      #38BDF8 0%,
      #1D6FE8 55%,
      #154596 100%
    );
    --border-specular: rgba(186, 230, 253, 0.38);
    --border-bright: rgba(125, 211, 252, 0.78);
    --cyan-glow: #38BDF8;
    --mint-power: #00F5D4;
    --amber-warn: #FBBF24;
    --text-primary: #F8FAFC;
    --text-ice: #BAE6FD;
    --text-muted: #7DD3FC;

    /* Futuristic Geometric Display + Clean Sans Font Stack */
    --font-display: 'Avenir Next', 'SF Pro Display', 'Eurostile', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-sans: 'SF Pro Text', 'Avenir Next', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'SF Mono', 'PT Mono', 'Menlo', monospace;
  }}

  * {{
    box-sizing: border-box;
    user-select: none;
    -webkit-user-select: none;
    margin: 0;
    padding: 0;
  }}

  html, body {{
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    background: radial-gradient(circle at 20% 15%, #0E2750 0%, #061022 65%, #040A16 100%);
    color: var(--text-primary);
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
  }}

  /* Main App Layout: Flush Left Icon Rail + Full-Height Camera Viewport */
  .app-shell {{
    display: flex;
    width: 100vw;
    height: 100vh;
    padding: 8px 10px 10px 0;
    gap: 4px;
  }}

  /* =================================================================
     LEFT METALLIC ICON RAIL (66px)
     ================================================================= */
  .sidebar-rail {{
    width: 66px;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0 12px 0;
    position: relative;
    z-index: 20;
  }}

  .brand-btn {{
    width: 46px;
    height: 46px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    background: linear-gradient(145deg, rgba(56, 126, 224, 0.28), rgba(12, 30, 62, 0.65));
    border: 1px solid rgba(165, 220, 255, 0.35);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.28),
      0 6px 18px rgba(0, 0, 0, 0.45);
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.25s ease, box-shadow 0.25s ease;
  }}
  .brand-btn:hover {{
    transform: scale(1.07);
    border-color: var(--cyan-glow);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.45),
      0 0 18px rgba(56, 189, 248, 0.45);
  }}
  .brand-btn img {{
    width: 34px;
    height: 34px;
    object-fit: contain;
    filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.4));
  }}

  .nav-stack {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    position: relative;
    align-items: center;
    width: 100%;
  }}

  /* Smooth Gliding Active Indicator Pill */
  .sidebar-glider {{
    position: absolute;
    left: 10px;
    width: 46px;
    height: 46px;
    border-radius: 14px;
    background: var(--metallic-pill-active);
    border: 1px solid rgba(224, 242, 254, 0.85);
    box-shadow:
      inset 0 1px 1px rgba(255, 255, 255, 0.48),
      0 0 20px rgba(56, 189, 248, 0.50);
    transition: transform 0.34s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.25s ease;
    pointer-events: none;
    z-index: 1;
  }}
  .sidebar-glider::before {{
    content: '';
    position: absolute;
    left: -8px;
    top: 11px;
    width: 4px;
    height: 22px;
    border-radius: 3px;
    background: var(--mint-power);
    box-shadow: 0 0 10px var(--mint-power);
  }}

  .nav-icon-btn {{
    width: 46px;
    height: 46px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    position: relative;
    z-index: 2;
    color: var(--text-ice);
    background: transparent;
    border: 1px solid transparent;
    transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .nav-icon-btn:hover {{
    color: #FFFFFF;
    background: rgba(42, 98, 184, 0.28);
    border-color: rgba(125, 211, 252, 0.35);
    transform: translateY(-1px);
  }}
  .nav-icon-btn.active {{
    color: #FFFFFF;
  }}
  .nav-icon-btn svg {{
    width: 23px;
    height: 23px;
    stroke-width: 1.9;
    transition: transform 0.22s ease, filter 0.22s ease;
  }}
  .nav-icon-btn.active svg {{
    filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.55));
  }}

  .sidebar-bottom {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 11px;
  }}

  .status-dot-badge {{
    position: absolute;
    top: 8px;
    right: 8px;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--mint-power);
    border: 1.5px solid #061022;
    box-shadow: 0 0 8px var(--mint-power);
  }}
  .status-dot-badge.warn {{
    background: var(--amber-warn);
    box-shadow: 0 0 8px var(--amber-warn);
  }}

  /* Intuitive Luminous Pause / Resume Sensor Orb at Bottom Left */
  .sensor-orb-control {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 14px;
    transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1), background 0.22s ease;
  }}
  .sensor-orb-control:hover {{
    transform: translateY(-2px);
    background: rgba(42, 98, 184, 0.22);
  }}
  .sensor-orb-wrap {{
    width: 42px;
    height: 42px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .sensor-orb-btn {{
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: conic-gradient(from 0deg, #00F5D4, #38BDF8, #2563EB, #7DD3FC, #00F5D4);
    box-shadow:
      inset 0 2px 4px rgba(255, 255, 255, 0.65),
      0 0 18px rgba(56, 189, 248, 0.68);
    animation: orbSpin 5s linear infinite;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
  }}
  .sensor-orb-control:hover .sensor-orb-btn {{
    transform: scale(1.08);
    box-shadow:
      inset 0 2px 5px rgba(255, 255, 255, 0.85),
      0 0 24px rgba(0, 245, 212, 0.88);
  }}
  .sensor-orb-btn.paused {{
    background: conic-gradient(from 0deg, #FBBF24, #F59E0B, #EA580C, #FDE047, #FBBF24);
    box-shadow: 0 0 18px rgba(251, 191, 36, 0.70);
  }}
  /* High-contrast inner core holding the Pause (||) or Play (▶) icon */
  .sensor-orb-core {{
    position: relative;
    z-index: 2;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: rgba(6, 16, 36, 0.82);
    border: 1px solid rgba(224, 242, 254, 0.65);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.6);
  }}
  .sensor-orb-core svg {{
    width: 13px;
    height: 13px;
    filter: drop-shadow(0 0 4px rgba(56, 189, 248, 0.8));
  }}
  .sensor-orb-label {{
    font-family: var(--font-display);
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: var(--text-ice);
    text-align: center;
    line-height: 1;
  }}
  .sensor-orb-label.paused {{
    color: var(--amber-warn);
  }}
  @keyframes orbSpin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
  }}

  /* =================================================================
     FULL-HEIGHT ROUNDED CAMERA VIEWPORT & FLOATING METALLIC-GLASS HUD
     ================================================================= */
  .viewport-container {{
    flex: 1;
    height: 100%;
    border-radius: 22px;
    position: relative;
    overflow: hidden;
    background: linear-gradient(165deg, #163E7A 0%, #2563EB 48%, #38BDF8 100%);
    border: 1px solid rgba(147, 197, 253, 0.35);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.28),
      0 14px 40px rgba(0, 0, 0, 0.55);
  }}

  #camera-feed {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}

  /* Shared Brushed Metallic-Blue Frosted Glass Surface */
  .metallic-glass {{
    background: var(--metallic-surface);
    backdrop-filter: blur(28px) saturate(190%);
    -webkit-backdrop-filter: blur(28px) saturate(190%);
    border: 1px solid var(--border-specular);
    box-shadow:
      inset 0 1px 0 rgba(224, 242, 254, 0.34),
      inset 0 -1px 0 rgba(14, 165, 233, 0.16),
      0 14px 34px rgba(3, 9, 23, 0.55);
  }}

  .hud-logo-dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--cyan-glow);
    box-shadow: 0 0 12px var(--cyan-glow);
    transition: all 0.25s ease;
    flex-shrink: 0;
  }}
  .hud-logo-dot.armed {{
    background: var(--mint-power);
    box-shadow: 0 0 14px var(--mint-power);
  }}
  .hud-logo-dot.paused {{
    background: var(--amber-warn);
    box-shadow: 0 0 12px var(--amber-warn);
  }}

  /* Bottom-Left Floating Live Action & Hold Progress Pill */
  .bottom-hud-pill {{
    position: absolute;
    bottom: 16px;
    left: 18px;
    width: min(560px, calc(100% - 436px));
    min-width: 320px;
    height: 48px;
    padding: 0 20px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    z-index: 10;
    transition: width 0.35s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .bottom-hud-pill.expanded {{
    width: min(680px, calc(100% - 36px));
  }}

  .bottom-status-left {{
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    flex: 1;
  }}

  .bottom-status-text {{
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: #FFFFFF;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .bottom-status-text.armed {{
    color: var(--mint-power);
  }}

  /* Auto-hiding Hold / Cooldown Progress Track (Never overlaps text!) */
  .bottom-progress-wrap {{
    width: 0;
    opacity: 0;
    overflow: hidden;
    transition: width 0.25s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.2s ease;
    flex-shrink: 0;
  }}
  .bottom-progress-wrap.visible {{
    width: 120px;
    opacity: 1;
  }}
  .bottom-progress-track {{
    width: 100%;
    height: 8px;
    border-radius: 99px;
    background: rgba(9, 25, 54, 0.85);
    border: 1px solid rgba(125, 211, 252, 0.45);
    overflow: hidden;
  }}
  .bottom-progress-fill {{
    height: 100%;
    width: 0%;
    border-radius: 99px;
    background: linear-gradient(90deg, #38BDF8, #00F5D4);
    box-shadow: 0 0 10px var(--mint-power);
    transition: width 0.08s linear;
  }}

  /* =================================================================
     CRISP HIGH-DPI RETINA TOP ACTION & PAUSED BANNERS
     (Positioned in clear viewport area: never overlaps behind right dock!)
     ================================================================= */
  .top-hud-action-banner {{
    position: absolute;
    top: 16px;
    left: 18px;
    width: min(560px, calc(100% - 436px));
    height: 48px;
    padding: 0 18px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 11;
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
    transition: opacity 0.22s ease, transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), width 0.35s cubic-bezier(0.22, 1, 0.36, 1);
    pointer-events: none;
    box-shadow:
      inset 0 1px 0 rgba(224, 242, 254, 0.38),
      0 12px 30px rgba(2, 6, 18, 0.55);
  }}
  .top-hud-action-banner.expanded {{
    width: min(680px, calc(100% - 36px));
  }}
  .top-hud-action-banner.visible {{
    opacity: 1;
    transform: translateY(0) scale(1);
  }}
  .top-hud-action-icon {{
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .top-hud-action-icon svg {{
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.7));
  }}
  .top-hud-action-title {{
    font-family: var(--font-display);
    font-size: 14.5px;
    font-weight: 800;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: #FFFFFF;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
    min-width: 0;
  }}
  .top-hud-action-badge {{
    font-family: var(--font-display);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 3px 9px;
    border-radius: 7px;
    background: rgba(0, 245, 212, 0.20);
    border: 1px solid rgba(0, 245, 212, 0.65);
    color: var(--mint-power);
    flex-shrink: 0;
  }}

  /* Top Crisp High-DPI Tracking Paused Banner */
  .top-hud-pause-banner {{
    position: absolute;
    top: 16px;
    left: 18px;
    width: min(560px, calc(100% - 436px));
    height: 48px;
    padding: 0 18px;
    border-radius: 15px;
    display: none;
    align-items: center;
    gap: 12px;
    z-index: 12;
    background: linear-gradient(
      145deg,
      rgba(245, 158, 11, 0.38) 0%,
      rgba(180, 83, 9, 0.58) 50%,
      rgba(120, 53, 15, 0.75) 100%
    );
    backdrop-filter: blur(28px) saturate(190%);
    -webkit-backdrop-filter: blur(28px) saturate(190%);
    border: 1px solid rgba(251, 191, 36, 0.85);
    box-shadow:
      inset 0 1px 0 rgba(254, 243, 199, 0.55),
      0 12px 30px rgba(0, 0, 0, 0.55),
      0 0 20px rgba(245, 158, 11, 0.35);
    pointer-events: none;
    transition: width 0.35s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .top-hud-pause-banner.expanded {{
    width: min(680px, calc(100% - 36px));
  }}
  .top-hud-pause-banner.visible {{
    display: flex;
  }}
  .top-hud-pause-text {{
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: #FEF3C7;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
    min-width: 0;
  }}

  /* Top Crisp High-DPI Laser Pointer Active Banner */
  .top-hud-laser-banner {{
    position: absolute;
    top: 16px;
    left: 18px;
    width: min(560px, calc(100% - 436px));
    height: 48px;
    padding: 0 16px;
    border-radius: 15px;
    display: none;
    align-items: center;
    gap: 12px;
    z-index: 13;
    background: linear-gradient(
      145deg,
      rgba(225, 29, 72, 0.42) 0%,
      rgba(159, 18, 57, 0.62) 50%,
      rgba(88, 28, 55, 0.78) 100%
    );
    backdrop-filter: blur(28px) saturate(190%);
    -webkit-backdrop-filter: blur(28px) saturate(190%);
    border: 1px solid rgba(251, 113, 133, 0.85);
    box-shadow:
      inset 0 1px 0 rgba(255, 228, 230, 0.55),
      0 12px 30px rgba(0, 0, 0, 0.55),
      0 0 24px rgba(225, 29, 72, 0.40);
    pointer-events: auto;
    transition: width 0.35s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .top-hud-laser-banner.expanded {{
    width: min(680px, calc(100% - 36px));
  }}
  .top-hud-laser-banner.visible {{
    display: flex;
  }}
  .laser-dot-pulse {{
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #FF2E5B;
    box-shadow: 0 0 12px #FF2E5B, 0 0 24px #FF2E5B;
    animation: laserPulse 1.2s infinite ease-in-out;
    flex-shrink: 0;
  }}
  @keyframes laserPulse {{
    0%, 100% {{ transform: scale(0.92); opacity: 0.85; }}
    50% {{ transform: scale(1.18); opacity: 1; }}
  }}
  .top-hud-laser-text-col {{
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
  }}
  .top-hud-laser-title {{
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.09em;
    color: #FFF1F2;
    text-transform: uppercase;
  }}
  .top-hud-laser-sub {{
    font-family: var(--font-body);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: rgba(255, 228, 230, 0.85);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .top-hud-laser-btn {{
    font-family: var(--font-display);
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 5px 10px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.45);
    color: #FFFFFF;
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.15s ease, transform 0.15s ease;
  }}
  .top-hud-laser-btn:hover {{
    background: rgba(255, 255, 255, 0.32);
    transform: scale(1.04);
  }}

  /* Lecture Timer & Rehearsal Card */
  .timer-display-card {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 12px 10px;
    border-radius: 14px;
    background: rgba(6, 16, 36, 0.72);
    border: 1px solid rgba(125, 211, 252, 0.32);
    box-shadow: inset 0 1px 0 rgba(224, 242, 254, 0.25);
    margin-bottom: 4px;
  }}
  .timer-display-time {{
    font-family: var(--font-mono);
    font-size: 28px;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: var(--mint-power);
    text-shadow: 0 0 16px rgba(0, 245, 212, 0.45);
    line-height: 1.1;
  }}
  .timer-display-sub {{
    font-family: var(--font-display);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: var(--text-ice);
    opacity: 0.8;
    margin-top: 4px;
  }}

  /* =================================================================
     RIGHT-SIDE SEE-THROUGH METALLIC-GLASS OVERLAY STACK (396px)
     ================================================================= */
  .right-hud-dock {{
    position: absolute;
    top: 16px;
    right: 16px;
    bottom: 16px;
    width: 396px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 12;
    transition: transform 0.38s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.32s ease;
  }}
  .right-hud-dock.hidden {{
    transform: translateX(430px);
    opacity: 0;
    pointer-events: none;
  }}

  .hud-card {{
    border-radius: 20px;
    padding: 14px 18px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
  }}
  .hud-card:hover {{
    border-color: rgba(147, 218, 255, 0.58);
  }}

  /* Subtle top metallic specular sheen line on every card */
  .hud-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 12%;
    right: 12%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(224, 242, 254, 0.75), transparent);
    pointer-events: none;
  }}

  .card-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    padding-bottom: 7px;
    border-bottom: 1px solid rgba(125, 211, 252, 0.20);
  }}

  .card-title {{
    font-family: var(--font-display);
    font-size: 13.5px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-ice);
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .card-title-accent {{
    width: 7px;
    height: 7px;
    border-radius: 2px;
    background: var(--cyan-glow);
    box-shadow: 0 0 8px var(--cyan-glow);
    transform: rotate(45deg);
  }}

  .card-badge {{
    font-family: var(--font-display);
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 3px 9px;
    border-radius: 7px;
    background: rgba(56, 189, 248, 0.16);
    border: 1px solid rgba(125, 211, 252, 0.42);
    color: var(--text-ice);
    cursor: pointer;
    transition: all 0.2s ease;
  }}
  .card-badge:hover {{
    background: rgba(56, 189, 248, 0.34);
    border-color: #FFFFFF;
    color: #FFFFFF;
  }}

  /* Card 1: System Status Checklist + 3 Square Hand-Filter Vector Buttons */
  .status-list {{
    display: flex;
    flex-direction: column;
    gap: 7px;
  }}
  .status-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 11px;
    border-radius: 11px;
    background: rgba(8, 22, 46, 0.42);
    border: 1px solid rgba(125, 211, 252, 0.16);
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .status-row:hover {{
    background: rgba(34, 82, 156, 0.42);
    border-color: rgba(147, 218, 255, 0.55);
    transform: translateX(2px);
  }}
  .status-row-left {{
    display: flex;
    align-items: center;
    gap: 11px;
    min-width: 0;
  }}
  .status-led {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--mint-power);
    box-shadow: 0 0 9px var(--mint-power);
    flex-shrink: 0;
  }}
  .status-led.warn {{
    background: var(--amber-warn);
    box-shadow: 0 0 9px var(--amber-warn);
  }}
  .status-row-label {{
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: #F0F9FF;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .status-row-tag {{
    font-family: var(--font-display);
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--cyan-glow);
    flex-shrink: 0;
  }}

  /* 3 Square Hand-Selection Vector Buttons (Left Tilted, Both Overlapping, Right Tilted) */
  .hand-square-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 2px;
  }}
  .hand-square-btn {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px 6px 7px 6px;
    border-radius: 13px;
    background: linear-gradient(
      160deg,
      rgba(36, 86, 164, 0.34) 0%,
      rgba(12, 32, 68, 0.65) 100%
    );
    border: 1px solid rgba(125, 211, 252, 0.28);
    box-shadow: inset 0 1px 0 rgba(224, 242, 254, 0.22);
    cursor: pointer;
    transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .hand-square-btn:hover {{
    transform: translateY(-2px);
    background: var(--metallic-card-hover);
    border-color: #7DD3FC;
  }}
  .hand-square-btn.active {{
    background: linear-gradient(
      150deg,
      rgba(56, 189, 248, 0.42) 0%,
      rgba(29, 111, 232, 0.68) 60%,
      rgba(21, 69, 150, 0.85) 100%
    );
    border-color: #E0F2FE;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.55),
      0 0 18px rgba(56, 189, 248, 0.42);
  }}
  .hand-sq-vector {{
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 3px;
    transition: transform 0.22s ease;
  }}
  .hand-square-btn:hover .hand-sq-vector {{
    transform: scale(1.08);
  }}
  .hand-sq-vector svg {{
    width: 100%;
    height: 100%;
    overflow: visible;
  }}
  .hand-sq-label {{
    font-family: var(--font-display);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.06em;
    color: #FFFFFF;
    text-align: center;
    line-height: 1.1;
  }}

  /* Card 2: Middle Interactive Tab Deck (4 Smooth Tabs: SETUP, AURA, TUNE, GUIDE) */
  .middle-card {{
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }}

  .tab-bar {{
    position: relative;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    background: rgba(6, 16, 36, 0.68);
    border: 1px solid rgba(125, 211, 252, 0.28);
    border-radius: 12px;
    padding: 3px;
    margin-bottom: 12px;
    flex-shrink: 0;
  }}
  .tab-glider {{
    position: absolute;
    top: 3px;
    bottom: 3px;
    left: 3px;
    width: calc((100% - 6px) / 5);
    border-radius: 9px;
    background: var(--metallic-pill-active);
    border: 1px solid rgba(224, 242, 254, 0.85);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.45),
      0 2px 12px rgba(29, 111, 232, 0.55);
    transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1);
    pointer-events: none;
  }}
  .tab-btn {{
    position: relative;
    z-index: 2;
    padding: 7px 0;
    text-align: center;
    font-family: var(--font-display);
    font-size: 11.5px;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: var(--text-ice);
    cursor: pointer;
    transition: color 0.2s ease;
  }}
  .tab-btn.active, .tab-btn:hover {{
    color: #FFFFFF;
  }}

  .tab-viewport {{
    flex: 1;
    position: relative;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 2px;
  }}
  .tab-viewport::-webkit-scrollbar {{
    width: 4px;
  }}
  .tab-viewport::-webkit-scrollbar-thumb {{
    background: rgba(125, 211, 252, 0.35);
    border-radius: 4px;
  }}

  .tab-pane {{
    display: none;
    flex-direction: column;
    gap: 11px;
    animation: tabSlideFade 0.28s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  }}
  .tab-pane.active {{
    display: flex;
  }}
  @keyframes tabSlideFade {{
    from {{
      opacity: 0;
      transform: translateY(8px);
    }}
    to {{
      opacity: 1;
      transform: translateY(0);
    }}
  }}

  /* Controls inside Tabs: Segmented Pills, Metallic Switches, Sliders */
  .control-group-label {{
    font-family: var(--font-display);
    font-size: 12.5px;
    font-weight: 700;
    letter-spacing: 0.11em;
    color: var(--text-ice);
    text-transform: uppercase;
  }}

  .segmented-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 7px;
  }}

  .metallic-btn {{
    padding: 8px 12px;
    border-radius: 10px;
    background: var(--metallic-pill);
    border: 1px solid rgba(125, 211, 252, 0.32);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
    color: var(--text-ice);
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .metallic-btn:hover {{
    transform: translateY(-1px);
    border-color: var(--border-bright);
    color: #FFFFFF;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.35),
      0 4px 14px rgba(14, 165, 233, 0.28);
  }}
  .metallic-btn.active {{
    background: var(--metallic-pill-active);
    border-color: #E0F2FE;
    color: #FFFFFF;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.48),
      0 0 16px rgba(56, 189, 248, 0.45);
  }}

  /* Metallic Toggle Switch Rows (Larger 14.5px Typography) */
  .switch-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 11px;
    border-radius: 11px;
    background: rgba(8, 22, 46, 0.38);
    border: 1px solid rgba(125, 211, 252, 0.15);
    cursor: pointer;
    transition: all 0.2s ease;
  }}
  .switch-row:hover {{
    background: rgba(28, 72, 138, 0.38);
    border-color: rgba(125, 211, 252, 0.45);
  }}
  .switch-label {{
    font-family: var(--font-display);
    font-size: 14.5px;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: #F0F9FF;
  }}
  .switch-pill {{
    width: 44px;
    height: 24px;
    border-radius: 99px;
    background: rgba(12, 30, 62, 0.9);
    border: 1px solid rgba(125, 211, 252, 0.42);
    position: relative;
    transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
    flex-shrink: 0;
  }}
  .switch-pill.on {{
    background: linear-gradient(90deg, #0EA5E9, #00F5D4);
    border-color: #E0F2FE;
    box-shadow: 0 0 12px rgba(0, 245, 212, 0.45);
  }}
  .switch-knob {{
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #FFFFFF;
    position: absolute;
    top: 2px;
    left: 2px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.35);
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .switch-pill.on .switch-knob {{
    transform: translateX(20px);
  }}

  /* Futuristic Metallic Sliders */
  .slider-block {{
    display: flex;
    flex-direction: column;
    gap: 5px;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(8, 22, 46, 0.35);
    border: 1px solid rgba(125, 211, 252, 0.14);
  }}
  .slider-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .slider-title {{
    font-family: var(--font-display);
    font-size: 13.5px;
    font-weight: 600;
    color: #F0F9FF;
  }}
  .slider-val {{
    font-family: var(--font-mono);
    font-size: 12.5px;
    font-weight: 700;
    color: var(--cyan-glow);
  }}
  input[type=range].futuristic-slider {{
    -webkit-appearance: none;
    width: 100%;
    height: 6px;
    border-radius: 99px;
    background: rgba(14, 38, 78, 0.9);
    border: 1px solid rgba(125, 211, 252, 0.32);
    outline: none;
  }}
  input[type=range].futuristic-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #FFFFFF;
    border: 2.5px solid var(--cyan-glow);
    box-shadow: 0 0 10px var(--cyan-glow);
    cursor: pointer;
    transition: transform 0.15s ease;
  }}
  input[type=range].futuristic-slider::-webkit-slider-thumb:hover {{
    transform: scale(1.2);
  }}

  /* =================================================================
     GESTURE VECTOR CARDS (Medium Light-Blue Hand Vector + Centered Title Below)
     ================================================================= */
  .gesture-vector-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 9px;
  }}
  .gesture-vector-grid.compact {{
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }}

  .gesture-card {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 10px 8px 9px 8px;
    border-radius: 14px;
    background: linear-gradient(
      160deg,
      rgba(44, 102, 188, 0.34) 0%,
      rgba(16, 40, 82, 0.62) 60%,
      rgba(8, 22, 46, 0.78) 100%
    );
    border: 1px solid rgba(147, 218, 255, 0.32);
    box-shadow:
      inset 0 1px 0 rgba(224, 242, 254, 0.28),
      0 4px 14px rgba(0, 0, 0, 0.28);
    cursor: pointer;
    transition: all 0.24s cubic-bezier(0.22, 1, 0.36, 1);
    position: relative;
    overflow: hidden;
  }}
  .gesture-card:hover {{
    transform: translateY(-2px) scale(1.02);
    background: var(--metallic-card-hover);
    border-color: #7DD3FC;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.48),
      0 8px 22px rgba(14, 165, 233, 0.35);
  }}
  .gesture-card.live {{
    background: linear-gradient(160deg, rgba(0, 245, 212, 0.30) 0%, rgba(14, 165, 233, 0.52) 100%);
    border-color: var(--mint-power);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.65),
      0 0 22px rgba(0, 245, 212, 0.50);
  }}

  .gesture-vector-wrap {{
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 5px;
    transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .gesture-vector-grid.compact .gesture-vector-wrap {{
    width: 44px;
    height: 44px;
    margin-bottom: 4px;
  }}
  .gesture-card:hover .gesture-vector-wrap {{
    transform: scale(1.09);
  }}
  .gesture-vector-wrap svg {{
    width: 100%;
    height: 100%;
    overflow: visible;
  }}

  .gesture-card-title {{
    font-family: var(--font-display);
    font-size: 13.5px;
    font-weight: 800;
    letter-spacing: 0.06em;
    color: #FFFFFF;
    line-height: 1.15;
    text-align: center;
  }}
  .gesture-vector-grid.compact .gesture-card-title {{
    font-size: 12.5px;
  }}

  .gesture-card-sub {{
    font-family: var(--font-sans);
    font-size: 11px;
    font-weight: 500;
    color: var(--text-ice);
    opacity: 0.85;
    margin-top: 2px;
    text-align: center;
  }}

  /* =================================================================
     CAMERA-IRIS INTRO OVERLAY (Metallic-Blue FinFlick Logo Reveal)
     ================================================================= */
  .intro-overlay {{
    position: fixed;
    inset: 0;
    z-index: 100;
    background: radial-gradient(circle at center, #0F2B59 0%, #050E20 72%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 22px;
    cursor: pointer;
    transition: opacity 0.65s cubic-bezier(0.22, 1, 0.36, 1), transform 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  }}
  .intro-overlay.finished {{
    opacity: 0;
    transform: scale(1.08);
    pointer-events: none;
  }}
  .intro-logo-wrap {{
    width: 220px;
    height: 220px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: irisUncurl 2.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  .intro-logo-wrap img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 0 36px rgba(56, 189, 248, 0.65));
  }}
  .intro-ring {{
    position: absolute;
    inset: -16px;
    border-radius: 50%;
    border: 1.5px dashed rgba(125, 211, 252, 0.45);
    animation: spinSlow 8s linear infinite;
  }}
  @keyframes irisUncurl {{
    0% {{
      opacity: 0;
      transform: scale(0.55) rotate(-140deg);
    }}
    65% {{
      opacity: 1;
      transform: scale(1.04) rotate(6deg);
    }}
    100% {{
      opacity: 1;
      transform: scale(1.0) rotate(0deg);
    }}
  }}
  @keyframes spinSlow {{
    to {{ transform: rotate(360deg); }}
  }}
  .intro-title {{
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 800;
    letter-spacing: 0.22em;
    background: linear-gradient(90deg, #FFFFFF, #7DD3FC, #00F5D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .intro-sub {{
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.16em;
    color: var(--text-ice);
    opacity: 0.8;
  }}
</style>
</head>
<body>

<!-- Metallic-Blue Camera-Iris Intro Overlay -->
<div id="intro-overlay" class="intro-overlay" onclick="skipIntro()">
  <div class="intro-logo-wrap">
    <div class="intro-ring"></div>
    <img src="finflick://app/logo.svg" alt="FinFlick Logo"/>
  </div>
  <div class="intro-title">FINFLICK</div>
  <div class="intro-sub">Flick to Advance</div>
</div>

<div class="app-shell">
  <!-- 1. FLUSH LEFT METALLIC ICON RAIL -->
  <aside class="sidebar-rail">
    <div class="brand-btn" onclick="replayIntro()" onmouseenter="hoverHint('REPLAY METALLIC IRIS INTRO')" onmouseleave="clearHint()">
      <img src="finflick://app/logo.svg" alt="FinFlick"/>
    </div>

    <div class="nav-stack" id="sidebar-nav">
      <div class="sidebar-glider" id="sidebar-glider"></div>

      <div class="nav-icon-btn active" onclick="selectTab(0)" onmouseenter="hoverHint('01 // SENSOR & CAMERA SETUP')" onmouseleave="clearHint()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="6" width="18" height="12" rx="4"/>
          <circle cx="9" cy="12" r="1.5" fill="currentColor"/>
          <circle cx="15" cy="12" r="1.5" fill="currentColor"/>
        </svg>
      </div>

      <div class="nav-icon-btn" onclick="selectTab(1)" onmouseenter="hoverHint('02 // HAND POWER AURA & AUDIO')" onmouseleave="clearHint()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
      </div>

      <div class="nav-icon-btn" onclick="selectTab(2)" onmouseenter="hoverHint('03 // PRECISION SENSITIVITY TUNING')" onmouseleave="clearHint()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
          <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
          <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
          <line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>
        </svg>
      </div>

      <div class="nav-icon-btn" onclick="selectTab(3)" onmouseenter="hoverHint('04 // VECTOR GESTURE LIBRARY')" onmouseleave="clearHint()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/>
          <rect x="14" y="14" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/>
        </svg>
      </div>

      <div class="nav-icon-btn" onclick="selectTab(4)" onmouseenter="hoverHint('05 // LECTURE TIMER & REHEARSAL')" onmouseleave="clearHint()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
      </div>
    </div>

    <div class="sidebar-bottom">
      <div class="nav-icon-btn" id="btn-toggle-dock" onclick="toggleRightDock()" onmouseenter="hoverHint('SHOW / HIDE FLOATING HUD DECK')" onmouseleave="clearHint()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="3"/>
          <line x1="15" y1="3" x2="15" y2="21"/>
        </svg>
      </div>

      <div class="nav-icon-btn" onclick="sendAction('open_permissions')" onmouseenter="hoverHint('MACOS ACCESSIBILITY PERMISSIONS')" onmouseleave="clearHint()">
        <span class="status-dot-badge" id="perm-dot"></span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
      </div>

      <!-- Intuitive Luminous Pause / Resume Sensor Button -->
      <div class="sensor-orb-control" onclick="sendAction('toggle_pause')" onmouseenter="hoverHint('CLICK TO PAUSE / RESUME HAND TRACKING')" onmouseleave="clearHint()">
        <div class="sensor-orb-wrap">
          <div class="sensor-orb-btn" id="sensor-orb"></div>
          <div class="sensor-orb-core" id="sensor-orb-core">
            <!-- Pause (||) icon shown when active; switches to Play (▶) when paused -->
            <svg id="orb-icon-pause" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="5" width="4" height="14" rx="1.5"/>
              <rect x="14" y="5" width="4" height="14" rx="1.5"/>
            </svg>
            <svg id="orb-icon-play" viewBox="0 0 24 24" fill="currentColor" style="display:none;">
              <polygon points="7,5 19,12 7,19"/>
            </svg>
          </div>
        </div>
        <span class="sensor-orb-label" id="sensor-orb-label">PAUSE</span>
      </div>
    </div>
  </aside>

  <!-- 2. FULL-HEIGHT ROUNDED CAMERA VIEWPORT + FLOATING SEE-THROUGH HUD -->
  <main class="viewport-container">
    <img id="camera-feed" src="finflick://app/frame.jpg" alt="Live Camera Stream"/>

    <!-- High-DPI Crisp Top Action Notification Banner (Positioned away from right menu dock) -->
    <div class="top-hud-action-banner metallic-glass" id="top-hud-action-banner">
      <div class="top-hud-action-icon" id="top-action-icon"></div>
      <div class="top-hud-action-title" id="top-action-title">NEXT SLIDE</div>
      <div class="top-hud-action-badge" id="top-action-badge">TRIGGERED</div>
    </div>

    <!-- High-DPI Crisp Top Tracking Paused Banner -->
    <div class="top-hud-pause-banner" id="top-hud-pause-banner">
      <div class="sensor-orb-core" style="width:24px;height:24px;border-color:#FDE047;">
        <svg viewBox="0 0 24 24" fill="#FDE047" style="width:12px;height:12px;">
          <rect x="6" y="5" width="4" height="14" rx="1.5"/>
          <rect x="14" y="5" width="4" height="14" rx="1.5"/>
        </svg>
      </div>
      <div class="top-hud-pause-text">TRACKING PAUSED  ·  Hold Palm 1.5s to Resume</div>
    </div>

    <!-- High-DPI Crisp Top Laser Pointer Active Banner -->
    <div class="top-hud-laser-banner" id="top-hud-laser-banner">
      <div class="laser-dot-pulse"></div>
      <div class="top-hud-laser-text-col">
        <div class="top-hud-laser-title">LASER POINTER ACTIVE</div>
        <div class="top-hud-laser-sub">Aim with index finger · Other gestures paused · Hold L (0.8s) to exit</div>
      </div>
      <button class="top-hud-laser-btn" onclick="sendAction('toggle_laser')">✕ EXIT</button>
    </div>

    <!-- Bottom-Left Floating Action & Progress Pill -->
    <div class="bottom-hud-pill metallic-glass" id="bottom-hud-pill">
      <div class="bottom-status-left">
        <div class="hud-logo-dot" id="bottom-dot"></div>
        <div class="bottom-status-text" id="bottom-status-text">SHOW YOUR HAND TO BEGIN</div>
      </div>
      <div class="bottom-progress-wrap" id="bottom-progress-wrap">
        <div class="bottom-progress-track">
          <div class="bottom-progress-fill" id="bottom-progress-fill"></div>
        </div>
      </div>
    </div>

    <!-- 3. RIGHT-SIDE FLOATING SEE-THROUGH METALLIC-GLASS OVERLAY -->
    <section class="right-hud-dock" id="right-hud-dock">
      <!-- CARD 1: SYSTEM STATUS + 3 SQUARE HAND-SELECTION VECTOR BUTTONS -->
      <div class="hud-card metallic-glass">
        <div class="card-header">
          <div class="card-title"><span class="card-title-accent"></span>SYSTEM STATUS</div>
          <div class="card-badge" id="btn-focus-target" onclick="sendAction('focus_slides')">FOCUS SLIDES</div>
        </div>
        <div class="status-list">
          <div class="status-row" onclick="sendAction('focus_slides')" onmouseenter="hoverHint('CLICK TO BRING PRESENTATION WINDOW TO FRONT')" onmouseleave="clearHint()">
            <div class="status-row-left">
              <span class="status-led" id="led-target"></span>
              <span class="status-row-label" id="lbl-target">Target: Detecting…</span>
            </div>
            <span class="status-row-tag">LINKED</span>
          </div>
          <div class="status-row" onclick="sendAction('open_permissions')" onmouseenter="hoverHint('OPEN MACOS ACCESSIBILITY SETTINGS')" onmouseleave="clearHint()">
            <div class="status-row-left">
              <span class="status-led" id="led-perm"></span>
              <span class="status-row-label" id="lbl-perm">Accessibility: Granted</span>
            </div>
            <span class="status-row-tag" id="tag-perm">READY</span>
          </div>

          <!-- 3 Individual Square Hand-Filter Vector Buttons (Left Tilted, Both Overlapping, Right Tilted) -->
          <div class="hand-square-grid">
            <div class="hand-square-btn" id="hand-sq-left" onclick="setConfig('track_hand', 'left')"
                 onmouseenter="hoverHint('TRACK LEFT HAND ONLY')" onmouseleave="clearHint()">
              <div class="hand-sq-vector">{hand_svgs['left']}</div>
              <div class="hand-sq-label">Left Hand</div>
            </div>
            <div class="hand-square-btn active" id="hand-sq-any" onclick="setConfig('track_hand', 'any')"
                 onmouseenter="hoverHint('TRACK BOTH HANDS (AUTO-LOCK)')" onmouseleave="clearHint()">
              <div class="hand-sq-vector">{hand_svgs['any']}</div>
              <div class="hand-sq-label">Both Hands</div>
            </div>
            <div class="hand-square-btn" id="hand-sq-right" onclick="setConfig('track_hand', 'right')"
                 onmouseenter="hoverHint('TRACK RIGHT HAND ONLY')" onmouseleave="clearHint()">
              <div class="hand-sq-vector">{hand_svgs['right']}</div>
              <div class="hand-sq-label">Right Hand</div>
            </div>
          </div>
        </div>
      </div>

      <!-- CARD 2: INTERACTIVE CONTROL DECK (5 SMOOTH TABS: SETUP, AURA, TUNE, GUIDE, TIMER) -->
      <div class="hud-card metallic-glass middle-card">
        <div class="tab-bar">
          <div class="tab-glider" id="tab-glider"></div>
          <div class="tab-btn active" onclick="selectTab(0)">SETUP</div>
          <div class="tab-btn" onclick="selectTab(1)">AURA</div>
          <div class="tab-btn" onclick="selectTab(2)">TUNE</div>
          <div class="tab-btn" onclick="selectTab(3)">GUIDE</div>
          <div class="tab-btn" onclick="selectTab(4)">TIMER</div>
        </div>

        <div class="tab-viewport">
          <!-- TAB 0: SETUP -->
          <div class="tab-pane active" id="tab-pane-0">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
              <span class="control-group-label" style="font-size:12px;">Camera Source</span>
              <div class="metallic-btn" id="btn-cam" onclick="sendAction('cycle_camera')"
                   style="font-size:11.5px; padding:6px 10px; max-width:215px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                CAM 00 [SWITCH]
              </div>
            </div>

            <div class="switch-row" onclick="toggleConfig('invert_swipe_direction')">
              <span class="switch-label">Invert Swipe (Flick Left = Next)</span>
              <div class="switch-pill" id="sw-invert_swipe_direction"><div class="switch-knob"></div></div>
            </div>
            <div class="switch-row" onclick="toggleConfig('mirror_camera')">
              <span class="switch-label">Mirror Selfie Camera</span>
              <div class="switch-pill" id="sw-mirror_camera"><div class="switch-knob"></div></div>
            </div>
            <div class="switch-row" onclick="toggleConfig('auto_focus_target')">
              <span class="switch-label">Auto-Focus Slides Window</span>
              <div class="switch-pill" id="sw-auto_focus_target"><div class="switch-knob"></div></div>
            </div>
          </div>

          <!-- TAB 1: BIO AURA & AUDIO -->
          <div class="tab-pane" id="tab-pane-1">
            <div class="switch-row" onclick="toggleConfig('draw_skeleton')">
              <span class="switch-label">Futuristic Hand Power Aura</span>
              <div class="switch-pill" id="sw-draw_skeleton"><div class="switch-knob"></div></div>
            </div>
            <div class="switch-row" onclick="toggleConfig('show_motion_trail')">
              <span class="switch-label">Plasma Comet Motion Trail</span>
              <div class="switch-pill" id="sw-show_motion_trail"><div class="switch-knob"></div></div>
            </div>
            <div class="switch-row" onclick="toggleConfig('show_hud_notifications')">
              <span class="switch-label">On-Video HUD Action Pills</span>
              <div class="switch-pill" id="sw-show_hud_notifications"><div class="switch-knob"></div></div>
            </div>
            <div class="switch-row" onclick="toggleConfig('sound_feedback')">
              <span class="switch-label">Sci-Fi Metallic Audio Cues</span>
              <div class="switch-pill" id="sw-sound_feedback"><div class="switch-knob"></div></div>
            </div>
          </div>

          <!-- TAB 2: SENSITIVITY TUNING -->
          <div class="tab-pane" id="tab-pane-2">
            <div class="segmented-row">
              <div class="metallic-btn" id="preset-GENTLE" onclick="applyPreset('GENTLE', 1.3, 3.5, 0.9)">GENTLE</div>
              <div class="metallic-btn active" id="preset-BALANCED" onclick="applyPreset('BALANCED', 0.9, 2.4, 0.65)">BALANCED</div>
              <div class="metallic-btn" id="preset-FAST" onclick="applyPreset('FAST', 0.7, 1.8, 0.5)">FAST</div>
            </div>

            <div class="slider-block">
              <div class="slider-header">
                <span class="slider-title">Swipe Distance</span>
                <span class="slider-val" id="val-swipe_min_distance_palms">0.90 Palms</span>
              </div>
              <input type="range" class="futuristic-slider" id="sl-swipe_min_distance_palms" min="0.5" max="2.5" step="0.05"
                     oninput="onSliderInput('swipe_min_distance_palms', this.value, ' Palms')"/>
            </div>

            <div class="slider-block">
              <div class="slider-header">
                <span class="slider-title">Swipe Speed</span>
                <span class="slider-val" id="val-swipe_min_speed_palms">2.40 Palms/s</span>
              </div>
              <input type="range" class="futuristic-slider" id="sl-swipe_min_speed_palms" min="1.0" max="6.0" step="0.1"
                     oninput="onSliderInput('swipe_min_speed_palms', this.value, ' Palms/s')"/>
            </div>

            <div class="slider-block">
              <div class="slider-header">
                <span class="slider-title">Slide Cooldown</span>
                <span class="slider-val" id="val-cooldown_seconds">0.65 sec</span>
              </div>
              <input type="range" class="futuristic-slider" id="sl-cooldown_seconds" min="0.3" max="2.0" step="0.05"
                     oninput="onSliderInput('cooldown_seconds', this.value, ' sec')"/>
            </div>
          </div>

          <!-- TAB 3: FULL GESTURE VECTOR MATRIX (All 12 Vector Cards) -->
          <div class="tab-pane" id="tab-pane-3">
            <div class="gesture-vector-grid" id="full-gesture-grid"></div>
          </div>

          <!-- TAB 4: LECTURE TIMER & REHEARSAL -->
          <div class="tab-pane" id="tab-pane-4">
            <div class="timer-display-card">
              <div class="timer-display-time" id="lecture-timer-display">00:00:00</div>
              <div class="timer-display-sub" id="lecture-timer-label">STOPWATCH // READY</div>
            </div>
            <div class="segmented-row">
              <div class="metallic-btn" id="btn-timer-toggle" onclick="toggleLectureTimer()">START</div>
              <div class="metallic-btn" onclick="resetLectureTimer()">RESET</div>
              <div class="metallic-btn" onclick="cycleTimerPreset()">MODE</div>
            </div>

            <div class="control-group-label" style="margin-top:6px;">SESSION METRICS</div>
            <div class="status-list">
              <div class="status-row">
                <span class="status-row-label">Slides Advanced</span>
                <span class="status-row-tag" id="stat-fwd">0</span>
              </div>
              <div class="status-row">
                <span class="status-row-label">Slides Reversed</span>
                <span class="status-row-tag" id="stat-back">0</span>
              </div>
              <div class="status-row">
                <span class="status-row-label">Media / Actions</span>
                <span class="status-row-tag" id="stat-media">0</span>
              </div>
              <div class="status-row">
                <span class="status-row-label">Zoom Commands</span>
                <span class="status-row-tag" id="stat-zoom">0</span>
              </div>
            </div>

            <div class="control-group-label" style="margin-top:8px;">PRESENTER QUICK TOOLS</div>
            <div class="segmented-row">
              <div class="metallic-btn" id="btn-quick-laser" onclick="sendAction('toggle_laser')">🔴 LASER POINTER</div>
              <div class="metallic-btn" onclick="sendAction('countdown_test', {{action:'WHITE_SCREEN'}})">⚪ WHITEBOARD</div>
            </div>
          </div>
        </div>
      </div>

      <!-- CARD 3: QUICK GESTURE VECTOR DECK (Medium Light-Blue Hand Vectors + Centered Title Below) -->
      <div class="hud-card metallic-glass">
        <div class="card-header">
          <div class="card-title"><span class="card-title-accent"></span>QUICK GESTURES</div>
          <div class="card-badge" onclick="selectTab(3)">ALL 12 GESTURES →</div>
        </div>
        <div class="gesture-vector-grid compact" id="quick-gesture-grid"></div>
      </div>
    </section>
  </main>
</div>

<script>
  const GESTURE_SVGS = {svgs_json};

  const GESTURE_CATALOG = [
    {{ act: "NEXT_SLIDE", title: "Next Slide", sub: "Flick Index Right", subInv: "Flick Index Left", poses: ["POINT"] }},
    {{ act: "PREV_SLIDE", title: "Prev Slide", sub: "Flick Index Left", subInv: "Flick Index Right", poses: ["POINT"] }},
    {{ act: "LASER_POINTER", title: "Laser Pointer", sub: "Hold L-Shape (0.8s)", poses: ["L_SIGN"] }},
    {{ act: "WHITE_SCREEN", title: "Whiteboard", sub: "Hold W-Sign (0.8s)", poses: ["W_SIGN"] }},
    {{ act: "ZOOM_IN", title: "Zoom In", sub: "Fist to Open Palm", poses: [] }},
    {{ act: "ZOOM_OUT", title: "Zoom Out", sub: "Thumb Down (0.4s)", poses: ["THUMBS_DOWN"] }},
    {{ act: "PLAY_PAUSE", title: "Play / Pause", sub: "OK Sign (👌)", poses: ["OK"] }},
    {{ act: "BLACKOUT", title: "Blank Screen", sub: "Hold Fist (1.0s)", poses: ["FIST"] }},
    {{ act: "FIRST_SLIDE", title: "First Slide", sub: "Index Up (1.0s)", poses: ["INDEX_UP"] }},
    {{ act: "LAST_SLIDE", title: "Last Slide", sub: "Thumb Up (1.0s)", poses: ["THUMBS_UP"] }},
    {{ act: "START_PRESENTATION", title: "Start Slides", sub: "Peace Sign (0.8s)", poses: ["PEACE"] }},
    {{ act: "TOGGLE_PAUSE", title: "Pause Sensor", sub: "Open Palm (1.5s)", poses: ["PALM"] }}
  ];

  let activeTab = 0;
  let showRightDock = true;
  let soundEnabled = true;
  let customHint = null;
  let audioCtx = null;

  /* ===============================================================
     SMOOTH WEBAUDIO UNIFIED HAPTIC CLICK
     =============================================================== */
  function ensureAudio() {{
    if (!audioCtx) {{
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) audioCtx = new AC();
    }}
    if (audioCtx && audioCtx.state === 'suspended') {{
      audioCtx.resume();
    }}
  }}

  function playUiClick() {{
    if (!soundEnabled) return;
    try {{
      ensureAudio();
      if (!audioCtx) return;
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(320, now + 0.032);

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.linearRampToValueAtTime(0.035, now + 0.004);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.032);

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.035);
    }} catch (e) {{}}
  }}

  /* ===============================================================
     BUILD GESTURE VECTOR CARDS (Centered Light-Blue Vector + Title Underneath)
     =============================================================== */
  function renderGestureGrids(invertSwipe = false) {{
    const quickGrid = document.getElementById('quick-gesture-grid');
    const fullGrid = document.getElementById('full-gesture-grid');
    quickGrid.innerHTML = '';
    fullGrid.innerHTML = '';

    GESTURE_CATALOG.forEach((g, idx) => {{
      let svgKey = g.act;
      if (invertSwipe && g.act === 'NEXT_SLIDE') svgKey = 'PREV_SLIDE';
      if (invertSwipe && g.act === 'PREV_SLIDE') svgKey = 'NEXT_SLIDE';
      const svgMarkup = GESTURE_SVGS[svgKey] || GESTURE_SVGS['TOGGLE_PAUSE'];
      const subText = (invertSwipe && g.subInv) ? g.subInv : g.sub;

      const makeCard = (idPrefix) => {{
        const card = document.createElement('div');
        card.className = 'gesture-card';
        card.id = `${{idPrefix}}-${{g.act}}`;
        card.innerHTML = `
          <div class="gesture-vector-wrap">${{svgMarkup}}</div>
          <div class="gesture-card-title">${{g.title}}</div>
          <div class="gesture-card-sub">${{subText}}</div>
        `;
        card.onmouseenter = () => {{
          hoverHint(`${{g.title.toUpperCase()}} — ${{subText.toUpperCase()}} (CLICK FOR 3S LIVE TEST)`);
        }};
        card.onmouseleave = clearHint;
        card.onclick = () => {{
          playUiClick();
          sendAction('countdown_test', {{ action: g.act }});
        }};
        return card;
      }};

      if (idx < 6) {{
        quickGrid.appendChild(makeCard('qcard'));
      }}
      fullGrid.appendChild(makeCard('fcard'));
    }});
  }}

  /* ===============================================================
     SMOOTH NAVIGATION & RPC BRIDGE TO PYTHON
     =============================================================== */
  function sendAction(cmd, payload = {{}}) {{
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.finflick) {{
      window.webkit.messageHandlers.finflick.postMessage({{ cmd, ...payload }});
    }}
  }}

  function selectTab(idx) {{
    activeTab = idx;
    playUiClick();
    if (!showRightDock) {{
      showRightDock = true;
      updateDockVisibility();
    }}

    // Glide left sidebar indicator
    const sbGlider = document.getElementById('sidebar-glider');
    if (sbGlider) sbGlider.style.transform = `translateY(${{idx * 56}}px)`;
    document.querySelectorAll('#sidebar-nav .nav-icon-btn').forEach((btn, i) => {{
      btn.classList.toggle('active', i === idx);
    }});

    // Glide top tab capsule
    const tabGlider = document.getElementById('tab-glider');
    if (tabGlider) tabGlider.style.transform = `translateX(${{idx * 100}}%)`;
    document.querySelectorAll('.tab-btn').forEach((btn, i) => {{
      btn.classList.toggle('active', i === idx);
    }});

    // Activate tab pane (5 tabs: 0..4)
    for (let i = 0; i < 5; i++) {{
      const pane = document.getElementById(`tab-pane-${{i}}`);
      if (pane) pane.classList.toggle('active', i === idx);
    }}
  }}

  function toggleRightDock() {{
    showRightDock = !showRightDock;
    playUiClick();
    updateDockVisibility();
  }}

  function updateDockVisibility() {{
    const dock = document.getElementById('right-hud-dock');
    const bottomPill = document.getElementById('bottom-hud-pill');
    const topActionBanner = document.getElementById('top-hud-action-banner');
    const topPauseBanner = document.getElementById('top-hud-pause-banner');
    const topLaserBanner = document.getElementById('top-hud-laser-banner');
    const sbGlider = document.getElementById('sidebar-glider');
    dock.classList.toggle('hidden', !showRightDock);
    bottomPill.classList.toggle('expanded', !showRightDock);
    if (topActionBanner) topActionBanner.classList.toggle('expanded', !showRightDock);
    if (topPauseBanner) topPauseBanner.classList.toggle('expanded', !showRightDock);
    if (topLaserBanner) topLaserBanner.classList.toggle('expanded', !showRightDock);
    if (sbGlider) sbGlider.style.opacity = showRightDock ? '1' : '0';
  }}

  function setConfig(key, value) {{
    playUiClick();
    sendAction('set_config', {{ key, value }});
  }}

  function toggleConfig(key) {{
    const pill = document.getElementById(`sw-${{key}}`);
    const nextVal = !(pill && pill.classList.contains('on'));
    playUiClick();
    sendAction('set_config', {{ key, value: nextVal }});
  }}

  function applyPreset(name, dist, speed, cd) {{
    playUiClick();
    sendAction('apply_preset', {{ name, dist, speed, cd }});
  }}

  function onSliderInput(key, val, unit) {{
    const num = parseFloat(val);
    const lbl = document.getElementById(`val-${{key}}`);
    if (lbl) lbl.textContent = num.toFixed(2) + unit;
    sendAction('set_config', {{ key, value: num }});
  }}

  function hoverHint(txt) {{
    customHint = txt;
  }}

  function clearHint() {{
    customHint = null;
  }}

  function skipIntro() {{
    const el = document.getElementById('intro-overlay');
    if (el && !el.classList.contains('finished')) {{
      el.classList.add('finished');
      sendAction('stop_intro_sound');
    }}
  }}

  function replayIntro() {{
    const el = document.getElementById('intro-overlay');
    if (el) {{
      el.classList.remove('finished');
      sendAction('play_intro_sound');
      setTimeout(skipIntro, 3800);
    }}
  }}

  /* ===============================================================
     LECTURE STOPWATCH & COUNTDOWN TIMER
     =============================================================== */
  let timerMode = 0; // 0: Stopwatch, 1: 15m, 2: 30m, 3: 45m
  const TIMER_PRESETS = [0, 15 * 60, 30 * 60, 45 * 60];
  const TIMER_LABELS = ['STOPWATCH // READY', 'COUNTDOWN // 15 MIN', 'COUNTDOWN // 30 MIN', 'COUNTDOWN // 45 MIN'];
  let timerSeconds = 0;
  let timerRunning = false;
  let timerInterval = null;

  function formatTime(totalSec) {{
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    return `${{String(h).padStart(2, '0')}}:${{String(m).padStart(2, '0')}}:${{String(s).padStart(2, '0')}}`;
  }}

  function updateTimerDisplay() {{
    const disp = document.getElementById('lecture-timer-display');
    const lbl = document.getElementById('lecture-timer-label');
    if (disp) disp.textContent = formatTime(timerSeconds);
    if (lbl) {{
      if (timerRunning) {{
        lbl.textContent = timerMode === 0 ? 'STOPWATCH // RUNNING' : 'COUNTDOWN // ACTIVE';
      }} else {{
        lbl.textContent = TIMER_LABELS[timerMode];
      }}
    }}
  }}

  function toggleLectureTimer() {{
    playUiClick();
    timerRunning = !timerRunning;
    const btn = document.getElementById('btn-timer-toggle');
    if (btn) btn.textContent = timerRunning ? 'PAUSE' : 'START';

    if (timerRunning) {{
      if (!timerInterval) {{
        timerInterval = setInterval(() => {{
          if (!timerRunning) return;
          if (timerMode === 0) {{
            timerSeconds++;
          }} else {{
            if (timerSeconds > 0) {{
              timerSeconds--;
            }} else {{
              timerRunning = false;
              if (btn) btn.textContent = 'START';
              playUiClick();
            }}
          }}
          updateTimerDisplay();
        }}, 1000);
      }}
    }}
    updateTimerDisplay();
  }}

  function resetLectureTimer() {{
    playUiClick();
    timerRunning = false;
    const btn = document.getElementById('btn-timer-toggle');
    if (btn) btn.textContent = 'START';
    timerSeconds = TIMER_PRESETS[timerMode];
    updateTimerDisplay();
  }}

  function cycleTimerPreset() {{
    playUiClick();
    timerMode = (timerMode + 1) % TIMER_PRESETS.length;
    resetLectureTimer();
  }}

  /* ===============================================================
     60-FPS CAMERA STREAM & STATE TELEMETRY LOOP
     =============================================================== */
  let lastInvertSwipe = null;
  let frameBusy = false;
  const camImg = document.getElementById('camera-feed');

  function refreshCameraFrame() {{
    if (frameBusy) return;
    frameBusy = true;
    const nextImg = new Image();
    nextImg.onload = () => {{
      camImg.src = nextImg.src;
      frameBusy = false;
    }};
    nextImg.onerror = () => {{
      frameBusy = false;
    }};
    nextImg.src = 'finflick://app/frame.jpg?t=' + performance.now();
  }}

  async function pollTelemetry() {{
    try {{
      const res = await fetch('finflick://app/state.json?t=' + performance.now(), {{ cache: 'no-store' }});
      if (!res.ok) return;
      const st = await res.json();
      applyTelemetryState(st);
    }} catch (e) {{}}
  }}

  function applyTelemetryState(st) {{
    soundEnabled = !!st.config.sound_feedback;

    if (lastInvertSwipe !== st.config.invert_swipe_direction) {{
      lastInvertSwipe = st.config.invert_swipe_direction;
      renderGestureGrids(lastInvertSwipe);
    }}

    // High-DPI Crisp Top HUD Action Banner, Pause Banner & Laser Banner
    const topActionBanner = document.getElementById('top-hud-action-banner');
    const topActionIcon = document.getElementById('top-action-icon');
    const topActionTitle = document.getElementById('top-action-title');
    const topPauseBanner = document.getElementById('top-hud-pause-banner');
    const topLaserBanner = document.getElementById('top-hud-laser-banner');

    if (st.paused) {{
      if (topPauseBanner) topPauseBanner.classList.add('visible');
      if (topActionBanner) topActionBanner.classList.remove('visible');
      if (topLaserBanner) topLaserBanner.classList.remove('visible');
    }} else {{
      if (topPauseBanner) topPauseBanner.classList.remove('visible');
      if (topLaserBanner) topLaserBanner.classList.toggle('visible', !!st.laser_active);

      if (st.recent_action && st.recent_action_age < 1.1) {{
        if (topActionBanner && topActionIcon && topActionTitle) {{
          const svgMarkup = GESTURE_SVGS[st.recent_action] || GESTURE_SVGS['NEXT_SLIDE'];
          const item = GESTURE_CATALOG.find(g => g.act === st.recent_action);
          const title = item ? item.title : st.recent_action.replace(/_/g, ' ');
          topActionIcon.innerHTML = svgMarkup;
          topActionTitle.textContent = title;
          topActionBanner.classList.add('visible');
        }}
      }} else {{
        if (topActionBanner) topActionBanner.classList.remove('visible');
      }}
    }}

    const btnLaser = document.getElementById('btn-quick-laser');
    if (btnLaser) {{
      btnLaser.style.borderColor = st.laser_active ? '#FF2E5B' : '';
      btnLaser.style.color = st.laser_active ? '#FFFFFF' : '';
      btnLaser.style.background = st.laser_active ? 'rgba(255, 46, 91, 0.32)' : '';
    }}

    // Bottom Status Dot & Intuitive Pause/Resume Luminous Orb
    const bottomDot = document.getElementById('bottom-dot');
    const orb = document.getElementById('sensor-orb');
    const orbLabel = document.getElementById('sensor-orb-label');
    const iconPause = document.getElementById('orb-icon-pause');
    const iconPlay = document.getElementById('orb-icon-play');

    bottomDot.className = 'hud-logo-dot' + (st.paused ? ' paused' : (st.armed ? ' armed' : ''));
    orb.classList.toggle('paused', !!st.paused);
    if (orbLabel) {{
      orbLabel.textContent = st.paused ? 'RESUME' : 'PAUSE';
      orbLabel.classList.toggle('paused', !!st.paused);
    }}
    if (iconPause && iconPlay) {{
      iconPause.style.display = st.paused ? 'none' : 'block';
      iconPlay.style.display = st.paused ? 'block' : 'none';
    }}

    // Bottom Status Bar & Auto-Hiding Progress Bar (Never overlaps text!)
    const botTxt = document.getElementById('bottom-status-text');
    botTxt.textContent = customHint || st.status_message;
    botTxt.classList.toggle('armed', !!st.armed && !customHint);

    const progWrap = document.getElementById('bottom-progress-wrap');
    const progFill = document.getElementById('bottom-progress-fill');
    if (st.progress_visible) {{
      progWrap.classList.add('visible');
      progFill.style.width = `${{Math.round(st.progress_value * 100)}}%`;
    }} else {{
      progWrap.classList.remove('visible');
    }}

    // Card 1: System Status & 3 Square Hand-Filter Vector Buttons
    document.getElementById('lbl-target').textContent = st.target_text;
    document.getElementById('btn-focus-target').style.display = st.has_ext_focus ? 'block' : 'none';
    if (st.has_ext_focus) {{
      document.getElementById('btn-focus-target').textContent = `FOCUS ${{st.ext_name.slice(0, 8).toUpperCase()}}`;
    }}

    const permOk = !!st.perm_ok;
    document.getElementById('perm-dot').className = 'status-dot-badge' + (permOk ? '' : ' warn');
    document.getElementById('led-perm').className = 'status-led' + (permOk ? '' : ' warn');
    document.getElementById('lbl-perm').textContent = permOk ? 'Accessibility: Granted' : 'Accessibility: Required';
    document.getElementById('tag-perm').textContent = permOk ? 'GRANTED' : 'ENABLE';

    ['left', 'any', 'right'].forEach(h => {{
      const sq = document.getElementById(`hand-sq-${{h}}`);
      if (sq) sq.classList.toggle('active', st.config.track_hand === h);
    }});

    // Card 2: Controls sync
    const camBtn = document.getElementById('btn-cam');
    if (camBtn) {{
      camBtn.textContent = st.camera_name || `CAM 0${{st.config.camera_index}} [SWITCH]`;
    }}

    ['invert_swipe_direction', 'mirror_camera', 'auto_focus_target', 'draw_skeleton', 'show_motion_trail', 'show_hud_notifications', 'sound_feedback'].forEach(k => {{
      const el = document.getElementById(`sw-${{k}}`);
      if (el) el.classList.toggle('on', !!st.config[k]);
    }});

    // Tab 4 (TIMER): Session stats sync
    if (st.stats) {{
      const sf = document.getElementById('stat-fwd');
      const sb = document.getElementById('stat-back');
      const sm = document.getElementById('stat-media');
      const sz = document.getElementById('stat-zoom');
      if (sf) sf.textContent = st.stats.forward;
      if (sb) sb.textContent = st.stats.backward;
      if (sm) sm.textContent = st.stats.media;
      if (sz) sz.textContent = st.stats.zoom;
    }}

    // Sliders (only update if user isn't actively dragging)
    if (document.activeElement.tagName !== 'INPUT') {{
      const setSl = (k, unit) => {{
        const sl = document.getElementById(`sl-${{k}}`);
        const vl = document.getElementById(`val-${{k}}`);
        if (sl && st.config[k] !== undefined) sl.value = st.config[k];
        if (vl && st.config[k] !== undefined) vl.textContent = Number(st.config[k]).toFixed(2) + unit;
      }};
      setSl('swipe_min_distance_palms', ' Palms');
      setSl('swipe_min_speed_palms', ' Palms/s');
      setSl('cooldown_seconds', ' sec');
    }}

    // Presets highlight
    const d = st.config.swipe_min_distance_palms;
    document.getElementById('preset-GENTLE').classList.toggle('active', Math.abs(d - 2.0) < 0.15);
    document.getElementById('preset-BALANCED').classList.toggle('active', Math.abs(d - 1.5) < 0.15);
    document.getElementById('preset-FAST').classList.toggle('active', Math.abs(d - 1.1) < 0.15);

    // Highlight Live Gesture Cards
    GESTURE_CATALOG.forEach(g => {{
      const isLive = (st.recent_action === g.act && st.recent_action_age < 0.9) ||
                     (st.hand_visible && g.poses.includes(st.pose_name));
      const qEl = document.getElementById(`qcard-${{g.act}}`);
      const fEl = document.getElementById(`fcard-${{g.act}}`);
      if (qEl) qEl.classList.toggle('live', isLive);
      if (fEl) fEl.classList.toggle('live', isLive);
    }});
  }}

  // Initialize Gesture Vector Grids & Auto-dismiss Intro after 3.6s
  renderGestureGrids(false);
  setTimeout(skipIntro, 3600);
  setInterval(refreshCameraFrame, 16);
  setInterval(pollTelemetry, 45);
</script>

  // Initialize Gesture Vector Grids & Auto-dismiss Intro after 3.6s
  renderGestureGrids(false);
  setTimeout(skipIntro, 3600);
  setInterval(refreshCameraFrame, 16);
  setInterval(pollTelemetry, 45);
</script>
</body>
</html>
"""
