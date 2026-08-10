import json


def get_stats():

    try:

        with open(
            "data/results.json",
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        total = len(data)

        if total == 0:

            return {
                "total": 0,
                "escalated": 0,
                "avg_confidence": 0
            }

        # -----------------------------------------
        # Count human escalations
        # Supports both field names
        # -----------------------------------------

        escalated = 0

        for item in data:

            needs_human = item.get(
                "needs_human",
                item.get(
                    "requires_human_review",
                    False
                )
            )

            if needs_human:
                escalated += 1

        # -----------------------------------------
        # Average confidence
        # -----------------------------------------

        confidence_values = []

        for item in data:

            try:

                confidence = float(
                    item.get(
                        "confidence",
                        0
                    )
                )

                confidence_values.append(
                    confidence
                )

            except (
                ValueError,
                TypeError
            ):

                continue

        if confidence_values:

            avg_confidence = round(
                sum(confidence_values)
                / len(confidence_values)
                * 100,
                2
            )

        else:

            avg_confidence = 0

        # -----------------------------------------
        # Return statistics
        # -----------------------------------------

        return {
            "total": total,
            "escalated": escalated,
            "avg_confidence": avg_confidence
        }

    except Exception as error:

        print(
            f"Statistics error: {error}"
        )

        return {
            "total": 0,
            "escalated": 0,
            "avg_confidence": 0
        }