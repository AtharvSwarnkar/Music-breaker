from app.services.song_analyzer import SongAnalyzer
from app.services.percentage_calculator import PercentageCalculator
from app.services.stem_analysis import StemAnalysis
from app.services.final_percentage import FinalPercentage


TOP_K = 2
TEMPERATURE = 0.1


# -------------------------
# Analyze other.wav
# -------------------------

analyzer = SongAnalyzer()

analysis = analyzer.analyze(
    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\other.wav"
)

calculator = PercentageCalculator(analysis)

instrument_percentages = calculator.calculate(
    top_k=TOP_K,
    temperature=TEMPERATURE
)

# -------------------------
# Stem Analysis
# -------------------------

stem = StemAnalysis()

stem_distribution = stem.analyze(

    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\other.wav",

    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\bass.wav",

    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\drums.wav"
)

# -------------------------
# Final Merge
# -------------------------

final = FinalPercentage(
    instrument_percentages,
    stem_distribution
).calculate()

print("\nFinal Instrument Distribution")
print("-" * 50)

for instrument, percentage in final.items():

    print(f"{instrument:25} {percentage:6.2f}%")