from app.services.analysis_service import AnalysisService

service = AnalysisService()

result = service.analyze(
    r"D:\MusicAI\backend\app\temp\htdemucs\beliver\other.wav"
)

print(result.keys())