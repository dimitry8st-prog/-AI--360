"""Build 16:9 and 9:16 promo MP4s. No .env, tokens, or real PII."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from imageio_ffmpeg import get_ffmpeg_exe

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from music import SR, write_wav  # noqa: E402
from scenes import render_all  # noqa: E402

VIVALDI_SOURCE = ROOT / "audio" / "source" / "vivaldi-spring.oga"

VO_LINES = [
    (0.8, "Материалы разбросаны, прогресс трудно контролировать, а методист повторяет одно и то же."),
    (7.4, "ДИС помогает организовать обучение, практику и контроль знаний в единой системе."),
    (15.2, "Сотрудник проходит назначенные курсы в Telegram и получает поддержку по утверждённым материалам компании."),
    (25.2, "Обучение и проверка разделены. Экзаменационные правила утверждает человек, а кадровые решения не передаются нейросети."),
    (35.2, "Методист управляет программами, руководитель видит прогресс, а администратор контролирует систему."),
    (47.2, "Меньше рутины, единые стандарты и понятный результат для каждого сотрудника."),
]


def load_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        nch = w.getnchannels()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767
        if nch > 1:
            raw = raw.reshape(-1, nch).mean(axis=1)
        return raw, sr


def resample_linear(samples: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return samples
    x = np.linspace(0, 1, len(samples))
    n = int(len(samples) * dst_sr / src_sr)
    return np.interp(np.linspace(0, 1, n), x, samples).astype(np.float32)


async def speak_edge(text: str, dest: Path) -> None:
    import edge_tts

    dest.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, "ru-RU-DmitryNeural", rate="-8%")
    await communicate.save(str(dest))


def speak_windows(text: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    wav = str(dest).replace("'", "''")
    spoken = text.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.SelectVoice('Microsoft Irina Desktop'); "
        "$s.Rate = -1; "
        f"$s.SetOutputToWaveFile('{wav}'); "
        f"$s.Speak('{spoken}'); "
        "$s.Dispose()"
    )
    subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps], check=True)


def synthesize_line(text: str, dest_wav: Path, ffmpeg: str) -> None:
    mp3 = dest_wav.with_suffix(".mp3")
    try:
        asyncio.run(speak_edge(text, mp3))
        subprocess.run(
            [ffmpeg, "-y", "-i", str(mp3), "-ar", str(SR), "-ac", "1", str(dest_wav)],
            check=True,
            capture_output=True,
        )
        mp3.unlink(missing_ok=True)
        return
    except Exception:
        dest_wav.unlink(missing_ok=True)
    speak_windows(text, dest_wav)
    samples, sr = load_wav_mono(dest_wav)
    write_wav(dest_wav, resample_linear(samples, sr, SR).reshape(-1, 1))


def prepare_vivaldi(ffmpeg: str, duration: float) -> Path:
    """Cut a CC-licensed Vivaldi recording to the video length. No synthesis."""
    if not VIVALDI_SOURCE.exists():
        raise FileNotFoundError(
            f"Missing {VIVALDI_SOURCE}. Download Spring mvt. 1 (John Harrison, CC BY-SA) "
            "from Wikimedia Commons into that path."
        )
    out = ROOT / "audio" / "vivaldi-spring.wav"
    fade = 2.4
    fade_at = max(0.2, duration - fade)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(VIVALDI_SOURCE),
            "-t",
            f"{duration:.2f}",
            "-af",
            f"afade=t=out:st={fade_at:.2f}:d={fade:.2f}",
            "-ar",
            str(SR),
            "-ac",
            "2",
            str(out),
        ],
        check=True,
    )
    return out


def mix_audio(vo_dir: Path, music_path: Path, out_path: Path, duration: float) -> None:
    total = int(duration * SR)
    vo = np.zeros(total, dtype=np.float32)
    for i, (start, _text) in enumerate(VO_LINES):
        samples, sr = load_wav_mono(vo_dir / f"vo-{i + 1}.wav")
        samples = resample_linear(samples, sr, SR)
        a = int(start * SR)
        b = min(total, a + len(samples))
        vo[a:b] += samples[: b - a]
    music, msr = load_wav_mono(music_path)
    music = resample_linear(music, msr, SR)
    if len(music) < total:
        music = np.pad(music, (0, total - len(music)))
    music = music[:total] * 0.14
    duck = np.convolve(np.abs(vo) > 0.02, np.ones(int(0.25 * SR)) / (0.25 * SR), mode="same")
    music *= 1.0 - 0.55 * np.clip(duck, 0, 1)
    mix = np.clip(vo * 0.95 + music, -1, 1)
    write_wav(out_path, np.stack([mix, mix], axis=1))


def concat_video_fixed(ffmpeg: str, stills: list[tuple[Path, float]], size: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    w, h = size.split("x")
    args = [ffmpeg, "-y"]
    filters = []
    for i, (path, dur) in enumerate(stills):
        args += ["-loop", "1", "-t", f"{dur:.2f}", "-i", str(path)]
        fade_out = max(0.2, dur - 0.45)
        filters.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0xF8FAFC,"
            f"setsar=1,fps=30,format=yuv420p,"
            f"fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out:.2f}:d=0.4[v{i}]"
        )
    concat_in = "".join(f"[v{i}]" for i in range(len(stills)))
    filters.append(f"{concat_in}concat=n={len(stills)}:v=1:a=0[v]")
    args += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        str(dest),
    ]
    subprocess.run(args, check=True)


def mux(ffmpeg: str, video: Path, audio: Path, dest: Path) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(dest),
        ],
        check=True,
    )


def build_aspect(aspect: str) -> Path:
    ffmpeg = get_ffmpeg_exe()
    size = "1920x1080" if aspect == "16x9" else "1080x1920"
    w, h = (1920, 1080) if aspect == "16x9" else (1080, 1920)
    shots = ROOT / "screenshots" / aspect
    audio_dir = ROOT / "audio"
    cache = ROOT / "cache" / aspect
    cache.mkdir(parents=True, exist_ok=True)
    stills = render_all(shots, w, h)
    duration = sum(d for _, d in stills)

    music_path = prepare_vivaldi(ffmpeg, duration)
    vo_dir = audio_dir / "vo"
    vo_dir.mkdir(parents=True, exist_ok=True)
    for i, (_start, text) in enumerate(VO_LINES):
        dest = vo_dir / f"vo-{i + 1}.wav"
        if not dest.exists():
            synthesize_line(text, dest, ffmpeg)
    mix_path = audio_dir / f"mix-{aspect}.wav"
    mix_audio(vo_dir, music_path, mix_path, duration)

    silent = cache / "video-silent.mp4"
    concat_video_fixed(ffmpeg, stills, size, silent)
    dest = ROOT / "output" / f"ai-nastavnik-360-{aspect}.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    mux(ffmpeg, silent, mix_path, dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aspect", choices=["16x9", "9x16", "both"], default="both")
    args = parser.parse_args()
    aspects = ["16x9", "9x16"] if args.aspect == "both" else [args.aspect]
    for aspect in aspects:
        path = build_aspect(aspect)
        print(f"rendered {path}")


if __name__ == "__main__":
    main()
