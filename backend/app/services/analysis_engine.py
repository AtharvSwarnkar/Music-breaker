class AnalysisEngine:

    def __init__(self, analysis):
        self.analysis = analysis

    # --------------------------------------------------
    # Normalize scores for every window
    # --------------------------------------------------
    def normalize_scores(self):

        normalized = []

        for window in self.analysis:

            scores = window["scores"]

            total = sum(max(score, 0.0) for score in scores.values())

            if total == 0:
                total = 1

            normalized_scores = {}

            for instrument, score in scores.items():

                normalized_scores[instrument] = max(score, 0.0) / total

            normalized.append({
                "window": window["window"],
                "start_time": window["start_time"],
                "end_time": window["end_time"],
                "scores": normalized_scores
            })

        return normalized

    # --------------------------------------------------
    # Timeline
    # --------------------------------------------------
    def get_timelines(self):

        normalized = self.normalize_scores()

        timelines = {}

        for window in normalized:

            for instrument, score in window["scores"].items():

                if instrument not in timelines:
                    timelines[instrument] = []

                timelines[instrument].append(score)

        return timelines

    # --------------------------------------------------
    # Presence
    # --------------------------------------------------
    def get_presence(self, threshold=0.15):

        normalized = self.normalize_scores()

        presence = {}

        total_windows = len(normalized)

        for instrument in normalized[0]["scores"]:

            active = 0

            for window in normalized:

                if window["scores"][instrument] >= threshold:
                    active += 1

            presence[instrument] = round(
                active * 100 / total_windows,
                2
            )

        return presence

    # --------------------------------------------------
    # Contribution
    # --------------------------------------------------
    def get_contribution(self):

        normalized = self.normalize_scores()

        contribution = {}

        total_windows = len(normalized)

        for instrument in normalized[0]["scores"]:

            total = 0

            for window in normalized:

                total += window["scores"][instrument]

            contribution[instrument] = total / total_windows

        contribution = dict(
            sorted(
                contribution.items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        return contribution
    

