from app.feature_extraction.audio.windowing import AudioWindowGenerator
from app.feature_extraction.instrument.detector import InstrumentDetector


class SongAnalyzer:

    def __init__(self):

        self.generator = AudioWindowGenerator()
        self.detector = InstrumentDetector()

    def analyze(self, other_wav: str):

        windows = self.generator.generate(other_wav)

        analysis = []

        batch_size = 32

        print(f"Analyzing {len(windows)} windows...")

        for batch_start in range(0, len(windows), batch_size):

            batch = windows[batch_start:batch_start + batch_size]

            print(
                f"Processing windows {batch_start + 1}-{min(batch_start + batch_size, len(windows))}/{len(windows)}",
                end="\r"
            )

            batch_scores = self.detector.detect_batch(batch)

            for i, scores in enumerate(batch_scores):

                window_index = batch_start + i

                analysis.append({

                    "window": window_index,

                    "start_time": float(window_index),

                    "end_time": float(window_index + 1),

                    "scores": scores

                })

        print("\nAnalysis Complete!")

        return analysis