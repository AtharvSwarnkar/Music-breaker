
"""Aggregate CLAP instrument scores across an entire song."""

from __future__ import annotations


class AnalysisEngine:
    def __init__(self, analysis):
        self.analysis = analysis or []

    def normalize_scores(self):
        """Validate and bound each window's independent match scores."""
        normalized = []

        for window in self.analysis:
            scores = window.get("scores", {})

            clean = {
                key: max(0.0, min(1.0, float(value)))
                for key, value in scores.items()
            }

            normalized.append({
                "window": int(window.get("window", len(normalized))),
                "start_time": float(
                    window.get("start_time", len(normalized))
                ),
                "end_time": float(
                    window.get("end_time", len(normalized) + 1)
                ),
                "scores": clean,
            })

        return normalized

    def get_timelines(self):
        """Return per-window scores for timeline visualizations."""
        timelines = {}

        for window in self.normalize_scores():
            for instrument, score in window["scores"].items():
                timelines.setdefault(instrument, []).append(score)

        return timelines

    def get_song_level_scores(self):
        """
        Calculate one overall score per instrument for the whole song.

        Formula:
            song_score = mean(window_scores) * 100

        The result is an adjusted match index, not a probability,
        calibrated confidence, loudness measurement, or mix contribution.
        """
        windows = self.normalize_scores()

        if not windows:
            return {}

        instruments = windows[0]["scores"].keys()
        total_windows = len(windows)
        song_scores = {}

        for instrument in instruments:
            score_sum = sum(
                window["scores"].get(instrument, 0.0)
                for window in windows
            )

            mean_score = score_sum / total_windows
            song_scores[instrument] = round(mean_score * 100, 2)

        return dict(
            sorted(
                song_scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    def get_window_coverage(self):
        """
        Percentage of windows where an instrument passed the detector's
        existing match thresholds and received a non-zero score.

        This is evidence coverage, not a calibrated probability of presence.
        """
        windows = self.normalize_scores()

        if not windows:
            return {}

        instruments = windows[0]["scores"].keys()
        total_windows = len(windows)
        coverage = {}

        for instrument in instruments:
            matched_windows = sum(
                window["scores"].get(instrument, 0.0) > 0.0
                for window in windows
            )

            coverage[instrument] = round(
                100 * matched_windows / total_windows,
                2,
            )

        return dict(
            sorted(
                coverage.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    def get_presence(self):
        """Backward-compatible alias for window evidence coverage."""
        return self.get_window_coverage()

    def get_contribution(self):
        """Backward-compatible alias; values are now song-level scores."""
        return self.get_song_level_scores()
