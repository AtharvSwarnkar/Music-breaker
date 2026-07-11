class FinalPercentage:

    def __init__(
        self,
        instrument_percentages,
        stem_distribution
    ):

        self.instrument_percentages = instrument_percentages
        self.stem_distribution = stem_distribution

    def calculate(self):

        final = {}

        other_weight = self.stem_distribution["other"]

        # Scale every instrument inside other.wav
        for instrument, percentage in self.instrument_percentages.items():

            if instrument in ["bass", "drums_percussion"]:
                continue

            final[instrument] = round(
                percentage * other_weight,
                2
            )

        # Replace with actual separated stems
        final["bass"] = round(
            self.stem_distribution["bass"] * 100,
            2
        )

        final["drums_percussion"] = round(
            self.stem_distribution["drums"] * 100,
            2
        )

        total = sum(final.values())

        if total > 0:

            for instrument in final:

                final[instrument] = round(
                    final[instrument] * 100 / total,
                    2
                )

        final = dict(
            sorted(
                final.items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        return final