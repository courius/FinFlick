"""Low-latency, procedurally synthesized futuristic metallic-glass UI & gesture audio cues."""

from __future__ import annotations

import logging
import math
import os
import platform
import subprocess
import threading
import wave
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("FinFlick.Sound")

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sounds")
SOUND_VERSION_FILE = os.path.join(SOUNDS_DIR, ".sound_version_v3")
SAMPLE_RATE = 44100


def _write_stereo_wav(path: str, left: np.ndarray, right: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """Write normalized float32 [-1, 1] stereo channels to a 16-bit PCM WAV file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    l_int = np.clip(left * 32767.0, -32767, 32767).astype(np.int16)
    r_int = np.clip(right * 32767.0, -32767, 32767).astype(np.int16)
    interleaved = np.empty(l_int.size * 2, dtype=np.int16)
    interleaved[0::2] = l_int
    interleaved[1::2] = r_int
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(interleaved.tobytes())


def _synth_intro_wav(path: str) -> None:
    """Synthesize a sleek, futuristic camera-iris swirl + metallic glass-harmonic bloom (~4.1s)."""
    dur = 4.10
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0.0, dur, n, dtype=np.float32)
    left = np.zeros(n, dtype=np.float32)
    right = np.zeros(n, dtype=np.float32)

    # 1. Warm futuristic sub-bass & air pad (0.05s -> 2.60s)
    pad_env = np.exp(-(((t - 1.25) / 0.90) ** 2)) * np.clip(t / 0.22, 0.0, 1.0)
    pad_l = (
        np.sin(2.0 * math.pi * 110.0 * t) * 0.045
        + np.sin(2.0 * math.pi * 220.0 * t + 0.2) * 0.040
        + np.sin(2.0 * math.pi * 329.63 * t + 0.5) * 0.030
    )
    pad_r = (
        np.sin(2.0 * math.pi * 110.0 * t) * 0.045
        + np.sin(2.0 * math.pi * 220.5 * t - 0.2) * 0.040
        + np.sin(2.0 * math.pi * 330.1 * t) * 0.030
    )
    left += pad_l * pad_env
    right += pad_r * pad_env

    # 2. Silky camera-iris rotational harmonic glide (0.45s -> 2.45s)
    swirl_mask = (t >= 0.45) & (t <= 2.45)
    ts = np.clip((t - 0.45) / 2.00, 0.0, 1.0)
    ease_s = 1.0 - (1.0 - ts) ** 2.8
    inst_freq = 220.0 + 330.0 * ease_s
    phase = np.cumsum(2.0 * math.pi * inst_freq / SAMPLE_RATE)
    glide_env = (np.clip(np.sin(np.pi * ts), 0.0, 1.0) ** 1.5) * swirl_mask.astype(np.float32)
    pan = 0.5 + 0.28 * np.sin(2.0 * math.pi * ts)
    glide_sig = (
        np.sin(phase) * 0.055
        + np.sin(phase * 1.5) * 0.028
        + np.sin(phase * 2.0) * 0.015
    ) * glide_env
    left += glide_sig * pan
    right += glide_sig * (1.0 - pan)

    # 3. 6 machined metallic aperture micro-detents as the 6 blades uncurl
    detent_times = [0.64, 0.86, 1.10, 1.36, 1.64, 1.94]
    for idx, dt in enumerate(detent_times):
        dt_mask = (t >= dt) & (t < dt + 0.035)
        if not np.any(dt_mask):
            continue
        local_t = t[dt_mask] - dt
        env = np.sin(np.pi * np.clip(local_t / 0.003, 0.0, 0.5)) * np.exp(-local_t / 0.0055)
        freq = 920.0 + idx * 110.0
        # Metallic overtone ratio (1.0 + 2.41x)
        tick = (
            np.sin(2.0 * math.pi * freq * local_t)
            + 0.35 * np.sin(2.0 * math.pi * (freq * 2.41) * local_t)
        ) * env * 0.048
        p_idx = 0.32 + 0.07 * idx
        left[dt_mask] += tick * (1.0 - p_idx)
        right[dt_mask] += tick * p_idx

    # 4. Crystalline metallic-blue chord bloom when center lens opens (t = 2.00s -> 4.05s)
    bloom_start = 2.00
    b_mask = t >= bloom_start
    tb = np.maximum(0.0, t - bloom_start)
    attack = 1.0 - np.exp(-tb / 0.035)
    notes = [
        (293.66, 0.068, 1.45, 0.0),   # D4
        (440.00, 0.062, 1.35, 0.35),  # A4
        (659.25, 0.052, 1.20, -0.35), # E5
        (880.00, 0.042, 1.05, 0.65),  # A5
        (1108.73, 0.032, 0.90, -0.6), # C#6
        (1318.51, 0.024, 0.75, 0.4),  # E6 shimmer
    ]
    for freq, amp, decay_tau, stereo_phase in notes:
        env = attack * np.exp(-tb / decay_tau) * b_mask.astype(np.float32)
        sig_l = (
            np.sin(2.0 * math.pi * (freq + 0.4) * tb + stereo_phase)
            + 0.22 * np.sin(2.0 * math.pi * (freq * 2.0) * tb)
        ) * amp * env
        sig_r = (
            np.sin(2.0 * math.pi * (freq - 0.4) * tb - stereo_phase)
            + 0.22 * np.sin(2.0 * math.pi * (freq * 2.0) * tb + 0.3)
        ) * amp * env
        left += sig_l
        right += sig_r

    fade_out = np.clip((dur - t) / 0.25, 0.0, 1.0)
    _write_stereo_wav(path, left * fade_out, right * fade_out)


def _synth_futuristic_cue(
    path: str,
    notes: List[Tuple[float, float, float, float, float]],
    dur: float,
    glide_hz: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    """Synthesize a smooth, warm metallic-glass UI/gesture sound cue.

    Each note is (start_sec, freq_hz, amp, decay_tau, pan_0_to_1).
    """
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0.0, dur, n, dtype=np.float32)
    left = np.zeros(n, dtype=np.float32)
    right = np.zeros(n, dtype=np.float32)

    for start_s, freq, amp, decay_tau, pan in notes:
        mask = t >= start_s
        lt = np.maximum(0.0, t - start_s)
        # Gentle 5ms attack to eliminate clicks/transients
        attack = 1.0 - np.exp(-lt / 0.0055)
        decay = np.exp(-lt / decay_tau)
        env = attack * decay * mask.astype(np.float32)

        # Smooth fundamental + warm octave + soft fifth (natural warm acoustic overtones)
        tone_l = (
            np.sin(2.0 * math.pi * freq * lt) * env
            + 0.18 * np.sin(2.0 * math.pi * (freq * 2.0) * lt) * env
            + 0.08 * np.sin(2.0 * math.pi * (freq * 1.5) * lt) * env
        ) * amp
        tone_r = (
            np.sin(2.0 * math.pi * freq * lt + 0.15) * env
            + 0.18 * np.sin(2.0 * math.pi * (freq * 2.0) * lt + 0.15) * env
            + 0.08 * np.sin(2.0 * math.pi * (freq * 1.5) * lt - 0.15) * env
        ) * amp

        left += tone_l * (1.0 - pan * 0.45)
        right += tone_r * (0.55 + pan * 0.45)

    fade = np.clip((dur - t) / 0.02, 0.0, 1.0)
    _write_stereo_wav(path, left * fade, right * fade)


def ensure_sound_assets() -> Dict[str, str]:
    """Ensure smooth synthesized WAV sound assets exist on disk and return their paths."""
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    paths = {
        "intro": os.path.join(SOUNDS_DIR, "intro_swirl.wav"),
        "next": os.path.join(SOUNDS_DIR, "next_slide.wav"),
        "prev": os.path.join(SOUNDS_DIR, "prev_slide.wav"),
        "action": os.path.join(SOUNDS_DIR, "action_tap.wav"),
        "wake": os.path.join(SOUNDS_DIR, "wake_chime.wav"),
        "sleep": os.path.join(SOUNDS_DIR, "sleep_chime.wav"),
        "ui_click": os.path.join(SOUNDS_DIR, "ui_click.wav"),
        "ui_tab": os.path.join(SOUNDS_DIR, "ui_tab.wav"),
    }
    try:
        needs_regen = not os.path.exists(SOUND_VERSION_FILE)
        if needs_regen or not os.path.exists(paths["intro"]):
            _synth_intro_wav(paths["intro"])
        if needs_regen or not os.path.exists(paths["next"]):
            _synth_futuristic_cue(
                paths["next"],
                [
                    (0.000, 523.25, 0.12, 0.075, 0.40),
                    (0.035, 659.25, 0.13, 0.095, 0.60),
                ],
                dur=0.20,
            )
        if needs_regen or not os.path.exists(paths["prev"]):
            _synth_futuristic_cue(
                paths["prev"],
                [
                    (0.000, 659.25, 0.12, 0.075, 0.60),
                    (0.035, 523.25, 0.13, 0.095, 0.40),
                ],
                dur=0.20,
            )
        if needs_regen or not os.path.exists(paths["action"]):
            _synth_futuristic_cue(
                paths["action"],
                [
                    (0.000, 587.33, 0.12, 0.065, 0.45),
                    (0.030, 783.99, 0.13, 0.085, 0.55),
                ],
                dur=0.18,
            )
        if needs_regen or not os.path.exists(paths["wake"]):
            _synth_futuristic_cue(
                paths["wake"],
                [
                    (0.000, 440.00, 0.11, 0.075, 0.30),
                    (0.040, 554.37, 0.11, 0.085, 0.50),
                    (0.080, 659.25, 0.13, 0.120, 0.70),
                ],
                dur=0.28,
            )
        if needs_regen or not os.path.exists(paths["sleep"]):
            _synth_futuristic_cue(
                paths["sleep"],
                [
                    (0.000, 659.25, 0.11, 0.075, 0.70),
                    (0.040, 554.37, 0.11, 0.085, 0.50),
                    (0.080, 440.00, 0.13, 0.120, 0.30),
                ],
                dur=0.28,
            )
        if needs_regen or not os.path.exists(paths["ui_click"]):
            _synth_futuristic_cue(
                paths["ui_click"],
                [(0.000, 480.0, 0.08, 0.024, 0.50)],
                dur=0.04,
            )
        if needs_regen or not os.path.exists(paths["ui_tab"]):
            _synth_futuristic_cue(
                paths["ui_tab"],
                [(0.000, 520.0, 0.07, 0.028, 0.50)],
                dur=0.05,
            )
        if needs_regen:
            with open(SOUND_VERSION_FILE, "w", encoding="utf-8") as f:
                f.write("v3")
    except Exception as e:
        logger.debug(f"Could not synthesize audio assets: {e}")
    return paths


class SoundFeedback:
    """Dispatches futuristic, subtle audio feedback for the opening animation, UI controls, and gesture triggers."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._is_mac = platform.system() == "Darwin"
        self._sound_paths = ensure_sound_assets()
        self._intro_proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def play(self, sound_type: str = "next") -> None:
        if not self.enabled:
            return

        def _play() -> None:
            try:
                path = self._sound_paths.get(sound_type, self._sound_paths.get("next", ""))
                if self._is_mac and path and os.path.exists(path):
                    vol = "0.65" if sound_type == "intro" else "0.52"
                    proc = subprocess.Popen(
                        ["afplay", path, "-v", vol],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    if sound_type == "intro":
                        with self._lock:
                            self._intro_proc = proc
                elif platform.system() == "Windows":
                    import winsound

                    if path and os.path.exists(path):
                        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    else:
                        winsound.MessageBeep()
            except Exception as e:
                logger.debug(f"Could not play audio feedback: {e}")

        threading.Thread(target=_play, daemon=True).start()

    def play_intro(self) -> None:
        """Play the opening camera-iris swirl soundscape if audio feedback is enabled."""
        self.stop_intro()
        self.play("intro")

    def stop_intro(self) -> None:
        """Stop the opening soundscape early if the user skips the intro animation."""
        with self._lock:
            proc = self._intro_proc
            self._intro_proc = None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
