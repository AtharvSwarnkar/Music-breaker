import librosa


class AudioWindowGenerator:

    def __init__(self, sample_rate=48000, window_duration=1.0):
        self.sample_rate = sample_rate
        self.window_size = int(sample_rate * window_duration)

    def generate(self, audio_path):

        audio, sr = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True
        )

        windows = []

        for start in range(0, len(audio), self.window_size):

            end = start + self.window_size

            chunk = audio[start:end]

            if len(chunk) < self.window_size:
                break

            windows.append(chunk)

        return windows
    