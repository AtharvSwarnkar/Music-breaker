from app.services.stem_analysis import StemAnalysis

stem_analysis = StemAnalysis()

result = stem_analysis.analyze(

    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\other.wav",

    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\bass.wav",

    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\drums.wav"

)

print()

print("Stem Distribution")
print("-----------------")

for stem, value in result.items():

    print(f"{stem:10} : {value*100:.2f}%")