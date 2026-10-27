
from app.feature_extraction.audio.windowing import AudioWindowGenerator
from app.feature_extraction.instrument.detector import InstrumentDetector


class SongAnalyzer:
    def __init__(self, generator=None, detector=None, batch_size=16):
        self.generator = generator or AudioWindowGenerator()
        self.detector = detector or InstrumentDetector()
        self.batch_size = max(1, int(batch_size))

    def analyze(self, audio_path: str):
        print(f"[SongAnalyzer] Loading audio: {audio_path}", flush=True)

        # Step 1: Split audio into windows.
        windows = self.generator.generate(audio_path)

        total_windows = len(windows)

        print(
            f"[SongAnalyzer] Audio windowing complete. "
            f"Total windows: {total_windows}",
            flush=True,
        )

        if total_windows == 0:
            raise RuntimeError(
                "AudioWindowGenerator returned zero windows."
            )

        analysis = []
        total_batches = (
            total_windows + self.batch_size - 1
        ) // self.batch_size

        # Step 2: Process windows in batches using CLAP.
        for batch_number, batch_start in enumerate(
            range(0, total_windows, self.batch_size),
            start=1,
        ):
            batch = windows[
                batch_start:batch_start + self.batch_size
            ]

            print(
                f"[SongAnalyzer] Processing batch "
                f"{batch_number}/{total_batches}; "
                f"windows {batch_start + 1}-"
                f"{batch_start + len(batch)} of {total_windows}",
                flush=True,
            )

            # Step 3: Run CLAP instrument detection.
            batch_scores = self.detector.detect_batch(batch)

            print(
                f"[SongAnalyzer] Batch {batch_number} returned "
                f"{len(batch_scores)} score results.",
                flush=True,
            )

            if len(batch_scores) != len(batch):
                raise RuntimeError(
                    "Detector returned a different number of results "
                    f"than input windows. Input={len(batch)}, "
                    f"output={len(batch_scores)}."
                )

            # Step 4: Store predictions with their timestamps.
            for offset, scores in enumerate(batch_scores):
                index = batch_start + offset

                analysis.append({
                    "window": index,
                    "start_time": float(index),
                    "end_time": float(index + 1),
                    "scores": scores,
                })

        print(
            f"[SongAnalyzer] Analysis complete. "
            f"Processed {len(analysis)}/{total_windows} windows.",
            flush=True,
        )

        return analysis
