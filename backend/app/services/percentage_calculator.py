import math


class PercentageCalculator:

    def __init__(self, analysis):

        self.analysis = analysis

    def _softmax(self, scores, temperature=0.1):

        scores = [s / temperature for s in scores]

        max_score = max(scores)

        exp_scores = [
            math.exp(score - max_score)
            for score in scores
        ]

        total = sum(exp_scores)

        return [
            score / total
            for score in exp_scores
        ]

    def calculate(self, top_k=3, temperature=0.1):

        if not self.analysis:
            return {}

        instruments = self.analysis[0]["scores"].keys()

        totals = {
            instrument: 0.0
            for instrument in instruments
        }

        for window in self.analysis:

            # Remove negative similarities
            positive_scores = {
                instrument: score
                for instrument, score in window["scores"].items()
                if score > 0
            }

            if not positive_scores:
                continue

            # Keep only Top-K instruments
            top_scores = sorted(
                positive_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]

            instruments_k = [
                instrument
                for instrument, _ in top_scores
            ]

            scores_k = [
                score
                for _, score in top_scores
            ]

            probabilities = self._softmax(
                scores_k,
                temperature
            )

            for instrument, probability in zip(
                instruments_k,
                probabilities
            ):
                totals[instrument] += probability

        grand_total = sum(totals.values())

        if grand_total == 0:
            return {}

        percentages = {}

        for instrument, total in totals.items():

            percentages[instrument] = round(
                total * 100 / grand_total,
                2
            )

        percentages = dict(
            sorted(
                percentages.items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        return percentages