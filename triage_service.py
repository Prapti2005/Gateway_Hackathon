import json

from services.gemini_service import (
    analyze_message,
    detect_multi_issue,
    is_ambiguous
)


# ---------------------------------------------------------
# PRIORITY CALCULATION
# ---------------------------------------------------------

def calculate_priority(category, message):

    msg = message.lower()

    # P0 - Critical security issues
    security_keywords = [
        "security",
        "hacked",
        "hack",
        "fraud",
        "breach",
        "stolen",
        "unauthorized",
        "account compromised"
    ]

    if any(word in msg for word in security_keywords):
        return "P0"

    # P1 - Financial / critical support
    if category in [
        "Billing",
        "Refund"
    ]:

        return "P1"

    critical_technical_keywords = [
        "system down",
        "cannot access",
        "completely broken",
        "critical",
        "urgent"
    ]

    if any(word in msg for word in critical_technical_keywords):
        return "P1"

    # P2 - Normal customer issues
    if category in [
        "Technical Support",
        "Account Management",
        "Shipping"
    ]:

        return "P2"

    # P3 - General / low priority
    return "P3"


# ---------------------------------------------------------
# HUMAN ESCALATION
# ---------------------------------------------------------

def apply_escalation_rules(prediction, message):

    confidence = prediction.get("confidence", 0.0)

    # Low confidence
    if confidence < 0.75:

        prediction["needs_human"] = True
        prediction["escalation_reason"] = "Low Confidence"

    # Ambiguous input
    if is_ambiguous(message):

        prediction["needs_human"] = True
        prediction["escalation_reason"] = "Ambiguous Input"

    # Multiple issues
    if detect_multi_issue(message):

        prediction["needs_human"] = True
        prediction["escalation_reason"] = "Multi Issue Request"

    # P0 cases should always be reviewed
    if prediction.get("priority") == "P0":

        prediction["needs_human"] = True

        if not prediction.get("escalation_reason"):
            prediction["escalation_reason"] = "Critical Security Issue"

    return prediction


# ---------------------------------------------------------
# PROCESS DATASET
# ---------------------------------------------------------

def process_dataset():

    with open("data/dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    for item in dataset:

        message = item.get("message", "")

        # AI analysis
        prediction = analyze_message(message)

        # Make sure category exists
        category = prediction.get(
            "category",
            "Unknown"
        )

        # Override priority using deterministic rules
        prediction["priority"] = calculate_priority(
            category,
            message
        )

        # Apply escalation logic
        prediction = apply_escalation_rules(
            prediction,
            message
        )

        # Add dataset information
        prediction["id"] = item.get("id")
        prediction["message"] = message

        results.append(prediction)

    # Save predictions
    with open(
        "data/results.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False
        )

    return results

if __name__ == "__main__":
    results = process_dataset()
    print(f"Processed {len(results)} messages.")
