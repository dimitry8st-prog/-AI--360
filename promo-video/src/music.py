"""Classical bed: original synthesized performance of a PD work.

Beethoven — Piano Sonata No. 14, 1st movement (Moonlight).
The composition is public domain. This is a new synthesized performance,
not a copy of any commercial recording.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SR = 44100


def _piano(freq: float, length: int, vol: float) -> np.ndarray:
    t = np.arange(length, dtype=np.float32) / SR
    wave = (
        np.sin(2 * np.pi * freq * t)
        + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
        + 0.12 * np.sin(2 * np.pi * freq * 3 * t)
        + 0.05 * np.sin(2 * np.pi * freq * 4 * t)
    )
    env = np.exp(-t * 2.4)
    attack = min(int(0.012 * SR), length)
    env[:attack] *= np.linspace(0, 1, attack)
    return (wave * env * vol).astype(np.float32)


def render_classical(seconds: float = 60.0) -> np.ndarray:
    """Simplified Moonlight Sonata I texture in C# minor, 60s."""
    n = int(seconds * SR)
    out = np.zeros(n, dtype=np.float32)
    # Triplet eighths ~ adagio (~50 bpm for dotted quarter ≈ 0.4s per triplet group)
    group = 0.42
    gs3, cs4, e4 = 207.65, 277.18, 329.63
    bass_pattern = [
        69.30,   # C#2
        103.83,  # G#2
        138.59,  # C#3
        103.83,  # G#2
        82.41,   # E2
        103.83,
        130.81,  # C3
        103.83,
    ]
    t = 0.0
    step = 0
    while t < seconds - 0.05:
        phase = t / seconds
        dens = 0.55 + 0.45 * min(1.0, phase / 0.2) if phase < 0.82 else 0.9
        i0 = int(t * SR)
        trip = int(group / 3 * SR)
        for k, f in enumerate((gs3, cs4, e4)):
            j = i0 + k * trip
            if j + trip <= n:
                out[j : j + trip] += _piano(f, trip, 0.09 * dens)
        if step % 2 == 0:
            bass = bass_pattern[(step // 2) % len(bass_pattern)]
            blen = int(group * 2 * SR)
            if i0 + blen <= n:
                out[i0 : i0 + blen] += _piano(bass, blen, 0.14 * dens)
        t += group
        step += 1

    fade = int(2.4 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(out)) or 1.0
    stereo = np.stack([out, out], axis=1)
    return np.clip(stereo / peak * 0.62, -1, 1).astype(np.float32)


def write_wav(path: Path, samples: np.ndarray, sr: int = SR) -> None:
    import wave

    pcm = np.clip(samples, -1, 1)
    if pcm.ndim == 1:
        pcm = pcm.reshape(-1, 1)
    pcm = (pcm * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
