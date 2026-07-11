from app.services.song_analyzer import SongAnalyzer
from app.services.analysis_engine import AnalysisEngine


class AnalysisService:

    def __init__(self):

        self.song_analyzer = SongAnalyzer()

    def analyze(self, other_wav):

        print("USING NEW ANALYSIS SERVICE")

        analysis = self.song_analyzer.analyze(other_wav)

        engine = AnalysisEngine(analysis)

        result = {
            "analysis": analysis,
            "timelines": engine.get_timelines(),
            "presence": engine.get_presence(),
            "contribution": engine.get_contribution()
        }

        print(result.keys())

        return result
