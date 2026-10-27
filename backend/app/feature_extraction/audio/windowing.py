"""Load audio and split it into fixed-duration windows, padding the last one."""
import librosa
import numpy as np


class AudioWindowGenerator:
    def __init__(self, sample_rate=48_000, window_duration=1.0):
        if sample_rate <= 0 or window_duration <= 0:
            raise ValueError("sample_rate and window_duration must be positive")
        self.sample_rate = int(sample_rate)
        self.window_size = int(self.sample_rate * window_duration)

    def generate(self, audio_path):
        audio, _ = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        if audio.size == 0:
            raise ValueError("The uploaded audio contains no decodable samples.")
        windows = []
        for start in range(0, len(audio), self.window_size):
            chunk = audio[start:start + self.window_size]
            if chunk.size < self.window_size:
                chunk = np.pad(chunk, (0, self.window_size - chunk.size))
            windows.append(chunk.astype(np.float32, copy=False))
        return windows
