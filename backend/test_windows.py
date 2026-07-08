from app.feature_extraction.audio.windowing import AudioWindowGenerator

generator = AudioWindowGenerator()

windows = generator.generate(
    r"app\temp\htdemucs\beliver\other.wav"
)

print(f"Total Windows : {len(windows)}")

print(f"Window Shape : {windows[0].shape}")