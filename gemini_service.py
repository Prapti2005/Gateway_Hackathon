
import json
import re

from google import genai
from google.genai import types

from config import GEMINI_API_KEY

try:
    from langdetect import detect
except ImportError:
    detect = None


# =========================================================
# GEMINI CONFIGURATION
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)

# Use a fast model for customer-support classification.
MODEL_NAME = "gemini-3.6-flash"


# =========================================================
# SUPPORTED CATEGORIES
# =========================================================

VALID_CATEGORIES = [
    "Billing",
    "Refund",
    "Technical Support",
    "Account Management",
    "Shipping",
    "General Inquiry",
    "Unknown"
]


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language(message):

    if not message or not message.strip():
        return "unknown"

    # Common English words that strongly indicate English
    english_words = {
        "the", "is", "are", "my", "i", "me",
        "how", "do", "can", "please", "want",
        "need", "change", "email", "address",
        "account", "login", "refund", "subscription",
        "charged", "payment", "order", "package"
    }

    words = set(message.lower().split())

    # If several common English words are present,
    # treat the message as English.
    english_matches = words.intersection(
        english_words
    )

    if len(english_matches) >= 2:
        return "en"

    if detect is None:
        return "en"

    try:
        detected = detect(message)

        return detected

    except Exception:
        return "unknown"
# =========================================================
# AMBIGUOUS / GARBAGE INPUT
# =========================================================

def is_ambiguous(message):

    if not message or not message.strip():
        return True

    cleaned = message.lower().strip()

    garbage_messages = {
        "asdf",
        "asdfghjkl",
        "test",
        "testing",
        "hello",
        "hi",
        "hey",
        "???",
        "...",
        "123",
        "abc"
    }

    if cleaned in garbage_messages:
        return True

    if len(cleaned.split()) < 3:
        return True

    meaningful_chars = re.sub(
        r"[^a-zA-Z]",
        "",
        cleaned
    )

    if len(meaningful_chars) < 3:
        return True

    return False


# =========================================================
# MULTI-ISSUE DETECTION
# =========================================================

def detect_multi_issue(message):

    msg = message.lower()

    issue_groups = {
        "billing": [
            "charged",
            "charge",
            "payment",
            "bill",
            "billing",
            "transaction"
        ],

        "refund": [
            "refund",
            "money back",
            "reimburse"
        ],

        "account": [
            "change my email",
            "change email",
            "update my email",
            "password",
            "profile",
            "username"
        ],

        "technical": [
            "crash",
            "crashes",
            "error",
            "bug",
            "not working",
            "broken"
        ],

        "shipping": [
            "delivery",
            "shipping",
            "shipment",
            "package",
            "parcel"
        ]
    }

    detected_groups = []

    for group, keywords in issue_groups.items():

        for keyword in keywords:

            if keyword in msg:
                detected_groups.append(group)
                break

    detected_groups = list(set(detected_groups))

    # Login + technical symptoms describe one
    # account-access problem, not necessarily two issues.
    if set(detected_groups) == {"account", "technical"}:
        return False

    return len(detected_groups) >= 2

# =========================================================
# OUT-OF-SCOPE DETECTION
# =========================================================

def is_out_of_scope(message):

    msg = message.lower().strip()

    out_of_scope_patterns = [
        "tell me a joke",
        "write a poem",
        "write a story",
        "what is the weather",
        "play a game",
        "sing a song",
        "solve my homework"
    ]

    return any(
        pattern in msg
        for pattern in out_of_scope_patterns
    )


# =========================================================
# FALLBACK ANALYSIS
# =========================================================

def fallback_analysis(message):

    msg = message.lower()

    # ---------------------------------------------
    # P0 - SECURITY
    # ---------------------------------------------

    security_words = [
        "hacked",
        "hack",
        "fraud",
        "breach",
        "stolen",
        "unauthorized",
        "security",
        "compromised"
    ]

    if any(word in msg for word in security_words):

        return {
            "category": "Account Management",
            "priority": "P0",
            "summary": "Possible security or unauthorized-access issue.",
            "suggested_action": "Escalate to human security support.",
            "needs_human": True,
            "confidence": 0.80,
            "escalation_reason": "Security-related request"
        }

    # ---------------------------------------------
    # TECHNICAL SUPPORT
    # ---------------------------------------------

    technical_words = [
        "crash",
        "crashes",
        "crashed",
        "error",
        "bug",
        "not working",
        "doesn't work",
        "does not work",
        "broken",
        "failed",
        "failure",
         "website down",
        "app down",
        "system down",
        "crash",
        "crashes",
        "error",
        "bug",
        "broken",
        "freezing",
        "freeze",
        "not working",
        "stopped working",
        "system"
]
    

    if any(word in msg for word in technical_words):

        return {
            "category": "Technical Support",
            "priority": "P2",
            "summary": "Customer is experiencing a technical problem.",
            "suggested_action": "Collect error details and troubleshoot the affected application or service.",
            "needs_human": True,
            "confidence": 0.90,
            "escalation_reason": None
        }

    # ---------------------------------------------
    # REFUND
    # ---------------------------------------------

    refund_words = [
        "refund",
        "money back",
        "reimburse",
        "reimbursement"
    ]

    if any(word in msg for word in refund_words):

        return {
            "category": "Refund",
            "priority": "P1",
            "summary": "Customer is requesting a refund.",
            "suggested_action": "Review the transaction and refund eligibility.",
            "needs_human": True,
            "confidence": 0.90,
            "escalation_reason": None
        }

    # ---------------------------------------------
    # BILLING
    # ---------------------------------------------

    billing_words = [
        "charged",
        "charge",
        "billing",
        "payment",
        "bill",
        "transaction",
        "subscription",
        "pricing",
    "price",
    "plans",
    "subscription plans",
    "payment methods",
    "service",
    "how does",
    "information",
    "features"
    ]

    if any(word in msg for word in billing_words):

        return {
            "category": "Billing",
            "priority": "P1",
            "summary": "Customer reports a billing or payment issue.",
            "suggested_action": "Review the customer's billing transaction.",
            "needs_human": False,
            "confidence": 0.90,
            "escalation_reason": None
        }

    # ---------------------------------------------
    # ACCOUNT MANAGEMENT
    # ---------------------------------------------

    account_words = [
        "password",
        "email address",
        "change my email",
        "update my email",
        "profile",
        "username",
        "account details"
    ]

    if any(word in msg for word in account_words):

        return {
            "category": "Account Management",
            "priority": "P2",
            "summary": "Customer wants to modify or manage account information.",
            "suggested_action": "Provide instructions for updating account information.",
            "needs_human": False,
            "confidence": 0.90,
            "escalation_reason": None
        }

    # ---------------------------------------------
    # LOGIN / ACCOUNT ACCESS
    # ---------------------------------------------

    login_words = [
        "login",
        "log in",
        "sign in",
        "signin",
        "cannot access my account",
        "can't access my account",
        "unable to access my account"
    ]

    if any(word in msg for word in login_words):

        return {
            "category": "Account Management",
            "priority": "P2",
            "summary": "Customer is experiencing an account access issue.",
            "suggested_action": "Verify account access and credentials.",
            "needs_human": True,
            "confidence": 0.85,
            "escalation_reason": None
        }

    # ---------------------------------------------
    # SHIPPING
    # ---------------------------------------------

    shipping_words = [
        "delivery",
        "shipping",
        "shipment",
        "package",
        "parcel",
        "delivered",
        "where is my order"
    ]

    if any(word in msg for word in shipping_words):

        return {
            "category": "Shipping",
            "priority": "P2",
            "summary": "Customer has a shipping or delivery issue.",
            "suggested_action": "Check the shipment and delivery status.",
            "needs_human": False,
            "confidence": 0.90,
            "escalation_reason": None
        }

    # ---------------------------------------------
    # UNKNOWN
    # ---------------------------------------------

    return {
        "category": "Unknown",
        "priority": "P2",
        "summary": "Unable to confidently classify the customer request.",
        "suggested_action": "Route the request to human support.",
        "needs_human": True,
        "confidence": 0.20,
        "escalation_reason": "Low Confidence"
    }
    # ---------------------------------------------
    # Security
    # ---------------------------------------------

    security_words = [
        "hacked",
        "hack",
        "fraud",
        "breach",
        "stolen",
        "unauthorized",
        "security"
    ]

    if any(
        word in msg
        for word in security_words
    ):

        return {
            "category": "Account Management",
            "priority": "P0",
            "summary": "Possible security or unauthorized-access issue.",
            "suggested_action": "Escalate to human security support.",
            "needs_human": True,
            "confidence": 0.45,
            "escalation_reason": "Security-related request"
        }

    # ---------------------------------------------
    # Refund
    # ---------------------------------------------

    if any(
        word in msg
        for word in [
            "refund",
            "money back",
            "reimburse"
        ]
    ):

        return {
            "category": "Refund",
            "priority": "P1",
            "summary": "Customer is requesting a refund.",
            "suggested_action": "Review the transaction and refund eligibility.",
            "needs_human": True,
            "confidence": 0.55,
            "escalation_reason": "Fallback classification"
        }

    # ---------------------------------------------
    # Billing
    # ---------------------------------------------

    if any(
        word in msg
        for word in [
            "charged",
            "charge",
            "billing",
            "payment",
            "bill"
        ]
    ):

        return {
            "category": "Billing",
            "priority": "P1",
            "summary": "Customer reports a billing or payment issue.",
            "suggested_action": "Review the customer's billing transaction.",
            "needs_human": True,
            "confidence": 0.55,
            "escalation_reason": "Fallback classification"
        }

    # ---------------------------------------------
    # Account
    # ---------------------------------------------

    if any(
        word in msg
        for word in [
            "login",
            "log in",
            "password",
            "account"
        ]
    ):

        return {
            "category": "Account Management",
            "priority": "P2",
            "summary": "Customer is experiencing an account access issue.",
            "suggested_action": "Verify the customer's account and access credentials.",
            "needs_human": True,
            "confidence": 0.50,
            "escalation_reason": "Fallback classification"
        }

    # ---------------------------------------------
    # Shipping
    # ---------------------------------------------

    if any(
        word in msg
        for word in [
            "delivery",
            "shipping",
            "shipment",
            "package",
            "parcel"
        ]
    ):

        return {
            "category": "Shipping",
            "priority": "P2",
            "summary": "Customer has a shipping or delivery issue.",
            "suggested_action": "Check the shipment and delivery status.",
            "needs_human": True,
            "confidence": 0.50,
            "escalation_reason": "Fallback classification"
        }

    # ---------------------------------------------
    # Unknown
    # ---------------------------------------------

    return {
        "category": "Unknown",
        "priority": "P2",
        "summary": "Unable to confidently classify the customer request.",
        "suggested_action": "Route the request to human support.",
        "needs_human": True,
        "confidence": 0.20,
        "escalation_reason": "AI unavailable or uncertain"
    }


# =========================================================
# MAIN AI ANALYSIS
# =========================================================

def analyze_message(message):

    # ---------------------------------------------
    # Empty input
    # ---------------------------------------------

    if not message or not message.strip():

        return {
            "category": "Unknown",
            "priority": "P2",
            "summary": "Empty customer message.",
            "suggested_action": "Request a valid customer message.",
            "needs_human": True,
            "confidence": 0.10,
            "language": "unknown",
            "escalation_reason": "Empty message"
        }


    # ---------------------------------------------
    # Language detection
    # ---------------------------------------------

    language = detect_language(message)


    # ---------------------------------------------
    # Non-English
    # ---------------------------------------------

    if language != "en" and language != "unknown":

        return {
            "category": "Unknown",
            "priority": "P2",
            "summary": "Customer message is not in English.",
            "suggested_action": "Route to multilingual support.",
            "needs_human": True,
            "confidence": 0.30,
            "language": language,
            "escalation_reason": "Non-English message"
        }


    # ---------------------------------------------
    # Ambiguous input
    # ---------------------------------------------

    if is_ambiguous(message):

        return {
            "category": "Unknown",
            "priority": "P2",
            "summary": "Customer message is too short or unclear.",
            "suggested_action": "Ask the customer for more information.",
            "needs_human": True,
            "confidence": 0.20,
            "language": language,
            "escalation_reason": "Ambiguous input"
        }


    # ---------------------------------------------
    # Out-of-scope
    # ---------------------------------------------

    if is_out_of_scope(message):

        return {
            "category": "Unknown",
            "priority": "P3",
            "summary": "Request is outside the supported customer service scope.",
            "suggested_action": "Inform the customer that this request is outside the support scope.",
            "needs_human": False,
            "confidence": 0.90,
            "language": language,
            "escalation_reason": None
        }


    # ---------------------------------------------
    # Multi-issue
    # ---------------------------------------------

    multi_issue = detect_multi_issue(message)


    # =====================================================
    # GEMINI PROMPT
    # =====================================================

    prompt = f"""
You are an enterprise AI Customer Support Triage Agent.

Analyze the customer message and classify it accurately.

SUPPORTED CATEGORIES:

Billing
Refund
Technical Support
Account Management
Shipping
General Inquiry
Unknown

PRIORITY RULES:

P0:
Security, fraud, hacking, account compromise,
data breach, stolen account, unauthorized access.

P1:
Serious billing, payment, refund, or critical
technical support issues.

P2:
Normal account, shipping, or technical support issues.

P3:
General inquiries or low urgency requests.

IMPORTANT:

- Do not guess.
- If evidence is weak, use Unknown.
- Detect the actual problem even if the customer
  uses sarcasm.
- If multiple issues are present, explain that
  multiple issues exist.
- Out-of-scope requests should be Unknown.
- Confidence must be between 0 and 1.
- Confidence below 0.75 requires human review.
- Return ONLY valid JSON.

Customer Message:

{message}
"""


    # =====================================================
    # CALL GEMINI
    # =====================================================

    try:

        response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

        text = response.text.strip()

        # Remove accidental Markdown fences
        text = re.sub(
            r"```json",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = text.replace(
            "```",
            ""
        ).strip()

        result = json.loads(text)


    except Exception as error:

        print(
            f"Gemini API error: {error}"
        )

        result = fallback_analysis(
            message
        )

        result["language"] = language

        if multi_issue:

            result["needs_human"] = True

            result["escalation_reason"] = (
                "Multi Issue Request"
            )

        return result


    # =====================================================
    # VALIDATE RESULT
    # =====================================================

    category = result.get(
        "category",
        "Unknown"
    )

    if category not in VALID_CATEGORIES:

        result["category"] = "Unknown"


    # ---------------------------------------------
    # Validate confidence
    # ---------------------------------------------

    try:

        confidence = float(
            result.get(
                "confidence",
                0.0
            )
        )

    except (
        ValueError,
        TypeError
    ):

        confidence = 0.0


    confidence = max(
        0.0,
        min(
            1.0,
            confidence
        )
    )

    result["confidence"] = confidence


    # ---------------------------------------------
    # Multi-issue escalation
    # ---------------------------------------------

    if multi_issue:

        result["needs_human"] = True

        result["escalation_reason"] = (
            "Multi Issue Request"
        )


    # ---------------------------------------------
    # Low-confidence escalation
    # ---------------------------------------------

    if confidence < 0.75:

        result["needs_human"] = True

        if not result.get(
            "escalation_reason"
        ):

            result["escalation_reason"] = (
                "Low Confidence"
            )


    # ---------------------------------------------
    # Add language
    # ---------------------------------------------

    result["language"] = language


    return result

