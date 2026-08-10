
import json


# ---------------------------------------------------------
# LOAD JSON FILE
# ---------------------------------------------------------

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ---------------------------------------------------------
# CALCULATE ACCURACY
# ---------------------------------------------------------

def calculate_accuracy():

    try:

        results = load_json(
            "data/results.json"
        )

        truth = load_json(
            "data/ground_truth.json"
        )

        # Create fast lookup:
        # MSG-001 -> Billing
        truth_map = {
            item["id"]: item["category"]
            for item in truth
        }

        total = 0
        correct = 0
        incorrect = 0

        incorrect_predictions = []

        for result in results:

            result_id = result.get("id")

            predicted_category = result.get(
                "category",
                "Unknown"
            )

            expected_category = truth_map.get(
                result_id
            )

            # Ignore predictions without ground truth
            if expected_category is None:
                continue

            total += 1

            if predicted_category == expected_category:

                correct += 1

            else:

                incorrect += 1

                incorrect_predictions.append({
                    "id": result_id,
                    "predicted": predicted_category,
                    "expected": expected_category,
                    "message": result.get(
                        "message",
                        ""
                    )
                })

        if total == 0:
            return 0.0

        accuracy = (
            correct / total
        ) * 100

        return round(
            accuracy,
            2
        )

    except Exception as error:

        print(
            f"Evaluation error: {error}"
        )

        return 0.0


# ---------------------------------------------------------
# DETAILED EVALUATION
# ---------------------------------------------------------

def calculate_metrics():

    try:

        results = load_json(
            "data/results.json"
        )

        truth = load_json(
            "data/ground_truth.json"
        )

        truth_map = {
            item["id"]: item["category"]
            for item in truth
        }

        total = 0
        correct = 0
        incorrect = 0
        human_escalations = 0

        category_stats = {}

        incorrect_predictions = []

        for result in results:

            result_id = result.get("id")

            predicted = result.get(
                "category",
                "Unknown"
            )

            expected = truth_map.get(
                result_id
            )

            if expected is None:
                continue

            total += 1

            # -----------------------------------------
            # Accuracy
            # -----------------------------------------

            if predicted == expected:

                correct += 1

            else:

                incorrect += 1

                incorrect_predictions.append({
                    "id": result_id,
                    "message": result.get(
                        "message",
                        ""
                    ),
                    "predicted": predicted,
                    "expected": expected
                })

            # -----------------------------------------
            # Human escalation
            # -----------------------------------------

            if result.get(
                "needs_human",
                False
            ):

                human_escalations += 1

            # -----------------------------------------
            # Category statistics
            # -----------------------------------------

            if expected not in category_stats:

                category_stats[expected] = {
                    "total": 0,
                    "correct": 0
                }

            category_stats[expected]["total"] += 1

            if predicted == expected:

                category_stats[expected]["correct"] += 1

        # -----------------------------------------
        # Overall accuracy
        # -----------------------------------------

        accuracy = (
            correct / total * 100
            if total > 0
            else 0
        )

        # -----------------------------------------
        # Category accuracy
        # -----------------------------------------

        for category in category_stats:

            stats = category_stats[category]

            if stats["total"] > 0:

                stats["accuracy"] = round(
                    stats["correct"]
                    / stats["total"]
                    * 100,
                    2
                )

            else:

                stats["accuracy"] = 0

        # -----------------------------------------
        # Return metrics
        # -----------------------------------------

        return {

            "total_samples": total,

            "correct_predictions": correct,

            "incorrect_predictions": incorrect,

            "accuracy": round(
                accuracy,
                2
            ),

            "human_escalations": human_escalations,

            "category_accuracy": category_stats,

            "incorrect_cases": incorrect_predictions
        }

    except Exception as error:

        print(
            f"Evaluation error: {error}"
        )

        return {

            "total_samples": 0,

            "correct_predictions": 0,

            "incorrect_predictions": 0,

            "accuracy": 0,

            "human_escalations": 0,

            "category_accuracy": {},

            "incorrect_cases": []
        }


# ---------------------------------------------------------
# TEST THE FILE DIRECTLY
# ---------------------------------------------------------

if __name__ == "__main__":

    metrics = calculate_metrics()

    print("\n===== EVALUATION RESULTS =====")

    print(
        f"Total Samples: "
        f"{metrics['total_samples']}"
    )

    print(
        f"Correct Predictions: "
        f"{metrics['correct_predictions']}"
    )

    print(
        f"Incorrect Predictions: "
        f"{metrics['incorrect_predictions']}"
    )

    print(
        f"Accuracy: "
        f"{metrics['accuracy']}%"
    )

    print(
        f"Human Escalations: "
        f"{metrics['human_escalations']}"
    )

    print("\nCategory Accuracy:")

    for category, stats in metrics[
        "category_accuracy"
    ].items():

        print(
            f"{category}: "
            f"{stats['accuracy']}%"
        )
metrics = calculate_metrics()

print("\nIncorrect Cases:\n")

for case in metrics["incorrect_cases"]:

    print(
        f'{case["id"]} | '
        f'Expected={case["expected"]} | '
        f'Predicted={case["predicted"]}'
    )

