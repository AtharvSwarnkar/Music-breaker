from app.services.song_analyzer import SongAnalyzer

analyzer = SongAnalyzer()

analysis = analyzer.analyze(
    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\other.wav"
)

print()

print("First Window")
print(analysis[0])

print()

print("Second Window")
print(analysis[1])

print()

print(f"Total Windows : {len(analysis)}")