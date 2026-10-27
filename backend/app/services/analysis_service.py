
from app.services.song_analyzer import SongAnalyzer
from app.services.analysis_engine import AnalysisEngine


class AnalysisService:
    def __init__(self, song_analyzer=None):
        self.song_analyzer = song_analyzer or SongAnalyzer()

    def analyze(self, audio_path):
        # Generate the existing per-window CLAP analysis.
        analysis = self.song_analyzer.analyze(audio_path)

        # Aggregate the results into one overall score per instrument.
        engine = AnalysisEngine(analysis)

        song_level_scores = engine.get_song_level_scores()
        window_coverage = engine.get_window_coverage()

        return {
            # Detailed data remains available for timeline visualizations.
            "analysis": analysis,
            "timelines": engine.get_timelines(),

            # Overall score for the entire song, scaled to 0-100.
            "song_level_scores": song_level_scores,

            # Compatibility aliases for existing frontend code.
            # These now contain song-level match scores, not contributions.
            "contribution": song_level_scores,
            "instrument_contribution": song_level_scores,

            # Percentage of analyzed windows with a non-zero score.
            "window_coverage_percent": window_coverage,
            "presence": window_coverage,

            "score_semantics": (
                "Song-Level Instrument Match Index (0-100): "
                "the mean of per-window CLAP adjusted similarity scores, "
                "scaled by 100. Not a probability, calibrated confidence, "
                "loudness measurement, or physical mix contribution."
            ),
        }
