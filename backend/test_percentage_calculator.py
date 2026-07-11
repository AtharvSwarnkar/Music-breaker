from app.services.song_analyzer import SongAnalyzer
from app.services.percentage_calculator import PercentageCalculator

analyzer = SongAnalyzer()

analysis = analyzer.analyze(
    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\other.wav"
)

calculator = PercentageCalculator(analysis)

# -----------------------------
# Experiment Settings
# -----------------------------
TOP_K = 2
TEMPERATURE = 0.1

percentages = calculator.calculate(
    top_k=TOP_K,
    temperature=TEMPERATURE
)

print("\n")
print(f"Top K       : {TOP_K}")
print(f"Temperature : {TEMPERATURE}")
print("-" * 50)

for instrument, percentage in percentages.items():

    print(f"{instrument:30} {percentage:6.2f}%")