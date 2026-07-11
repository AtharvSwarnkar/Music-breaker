from app.feature_extraction.audio.windowing import AudioWindowGenerator
from app.feature_extraction.instrument.detector import InstrumentDetector

generator = AudioWindowGenerator()
detector = InstrumentDetector()

windows = generator.generate(
    r"app\temp\htdemucs\beliver\other.wav"
)

print(f"Total windows: {len(windows)}")

results = detector.detect(windows[0])

for instrument, score in results:
    print(f"{instrument:35} {score:.4f}")