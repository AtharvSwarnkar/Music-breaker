import json

from app.services.song_analyzer import SongAnalyzer

analyzer = SongAnalyzer()

analysis = analyzer.analyze(
    r"D:\MusicAI\backend\app\temp\htdemucs\attention\other.wav"
)

with open(
    "analysis.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        analysis,
        f,
        indent=4
    )

print("Analysis exported successfully.")