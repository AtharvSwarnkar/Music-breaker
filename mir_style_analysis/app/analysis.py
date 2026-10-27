"""Deterministic low-level music analysis. Labels are explicitly heuristic, not ML claims."""
from __future__ import annotations
import math
from pathlib import Path
import librosa
import numpy as np
from .schema import TrackFeatures

KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
MINOR = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])

def _finite(value: float, default: float = 0.0) -> float:
    return float(value) if math.isfinite(float(value)) else default

def _key(chroma: np.ndarray) -> tuple[str | None, str | None, float]:
    profile = chroma.sum(axis=1)
    if profile.sum() <= 1e-8: return None, None, 0.0
    profile = (profile - profile.mean()) / (profile.std() + 1e-9)
    candidates = []
    for i in range(12):
        candidates.append((float(np.dot(profile, np.roll(MAJOR, i) - MAJOR.mean()) / (np.linalg.norm(MAJOR - MAJOR.mean()) + 1e-9)), KEYS[i], "major"))
        candidates.append((float(np.dot(profile, np.roll(MINOR, i) - MINOR.mean()) / (np.linalg.norm(MINOR - MINOR.mean()) + 1e-9)), KEYS[i], "minor"))
    score, key, mode = max(candidates)
    return key, mode, max(0.0, min(1.0, (score + 1) / 2))

def _genre(bpm: float, centroid: float, rolloff: float, flatness: float, harmonic_ratio: float) -> tuple[str, float]:
    # Transparent decision rules, deliberately not presented as trained genre prediction.
    if flatness > .18 and bpm >= 105: return "electronic", .42
    if harmonic_ratio < .42 and bpm >= 95: return "rock", .38
    if bpm < 92 and harmonic_ratio > .55: return "acoustic", .35
    if 75 <= bpm <= 115 and centroid < 2600: return "pop", .32
    return "unknown", 0.0

def _mood(bpm: float, rms_db: float, centroid: float, mode: str | None) -> str:
    if mode == "minor" and bpm < 105: return "reflective"
    if bpm > 125 and centroid > 1800: return "energetic"
    if rms_db < -28: return "calm"
    return "neutral"

def _instruments(low: float, mid: float, high: float, percussive: float, harmonic: float) -> dict[str, float]:
    # Contribution-like spectral evidence index (not source-separated mix percentages).
    raw = {"bass": low * harmonic, "drums_percussion": high * percussive,
           "harmonic_instruments": mid * harmonic, "bright_instruments": high * harmonic}
    total = sum(max(0., x) for x in raw.values())
    return {name: round(100 * max(0., value) / total, 1) for name, value in raw.items()} if total else {}

def extract(path: str | Path, max_seconds: float = 300.0) -> TrackFeatures:
    path = Path(path)
    y, sr = librosa.load(path, sr=22050, mono=True, duration=max_seconds)
    if y.size < sr // 4: raise ValueError("Audio must contain at least 0.25 seconds of decodable samples.")
    duration = len(y) / sr
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    bpm = _finite(np.asarray(tempo).reshape(-1)[0]) if np.size(tempo) else None
    rms = librosa.feature.rms(y=y)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    harmonic, percussive = librosa.effects.hpss(y)
    harm_energy, perc_energy = np.mean(harmonic**2), np.mean(percussive**2)
    h_ratio = _finite(harm_energy / (harm_energy + perc_energy + 1e-12))
    key, mode, key_confidence = _key(chroma)
    bands = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    # octave bands from FFT; robustly avoid hard source-identification claims
    spectrum = np.abs(librosa.stft(y)) ** 2; freqs = librosa.fft_frequencies(sr=sr)
    total = spectrum.sum() + 1e-12
    low = float(spectrum[(freqs < 250)].sum() / total); mid = float(spectrum[(freqs >= 250) & (freqs < 3000)].sum() / total); high = float(spectrum[freqs >= 3000].sum() / total)
    numeric = {"rms_db": _finite(librosa.amplitude_to_db(np.array([np.mean(rms) + 1e-12]))[0]), "dynamic_range_db": _finite(np.percentile(librosa.amplitude_to_db(rms + 1e-12),95)-np.percentile(librosa.amplitude_to_db(rms + 1e-12),5)), "spectral_centroid_hz": _finite(np.mean(centroid)), "spectral_rolloff_hz": _finite(np.mean(rolloff)), "spectral_bandwidth_hz": _finite(np.mean(bands)), "spectral_flatness": _finite(np.mean(flatness)), "zero_crossing_rate": _finite(np.mean(zcr)), "harmonic_ratio": h_ratio, "percussive_ratio": 1-h_ratio, "beat_count": float(len(beats)), "key_confidence": key_confidence, **{f"mfcc_{i+1}_mean": _finite(np.mean(mfcc[i])) for i in range(13)}}
    label, genre_conf = _genre(bpm or 0, numeric["spectral_centroid_hz"], numeric["spectral_rolloff_hz"], numeric["spectral_flatness"], h_ratio)
    warnings = ["Genre, mood, and instrument labels use documented audio heuristics; replace with evaluated models before treating them as classifier outputs."]
    if duration >= max_seconds: warnings.append(f"Analysis used the first {max_seconds:g} seconds only.")
    return TrackFeatures(round(duration,3), round(bpm,2) if bpm else None, key, mode, label, "heuristic-v1", genre_conf or None, _mood(bpm or 0,numeric["rms_db"],numeric["spectral_centroid_hz"],mode), "heuristic-v1", _instruments(low,mid,high,1-h_ratio,h_ratio), numeric, warnings)
