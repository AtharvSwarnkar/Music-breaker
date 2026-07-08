from app.feature_extraction.instrument.detector import InstrumentDetector

detector = InstrumentDetector()

results = detector.detect(
    r"app\temp\htdemucs\beliver\other.wav"
)

for instrument, score in results:
    print(f"{instrument:35} {score:.4f}") 
