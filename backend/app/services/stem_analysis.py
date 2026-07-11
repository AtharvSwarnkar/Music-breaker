import librosa
import numpy as np


class StemAnalysis:

    def __init__(self, sample_rate=48000):

        self.sample_rate = sample_rate

    def _get_rms(self, audio_path):

        audio, _ = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True
        )

        return np.sqrt(np.mean(audio ** 2))

    def analyze(
        self,
        other_wav,
        bass_wav,
        drums_wav
    ):

        other = self._get_rms(other_wav)
        bass = self._get_rms(bass_wav)
        drums = self._get_rms(drums_wav)

        total = other + bass + drums

        if total == 0:
            return {
                "other": 0.0,
                "bass": 0.0,
                "drums": 0.0
            }

        return {

            "other": other / total,

            "bass": bass / total,

            "drums": drums / total
        }