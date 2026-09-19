import re
from app.schemas import Analysis

BASE_DONT = ["Share an OTP, PIN, password, or bank details", "Click links in the message", "Send money before independently verifying the request"]
BASE_ACTIONS = ["Pause and do not reply right away", "Verify using an official app, saved phone number, or website you type yourself"]


def analyze_text(text: str, source: str = "message") -> Analysis:
    clean = " ".join(text.strip().split())
    lowered = clean.lower()
    signals: list[str] = []
    category = "SUSPICIOUS_MESSAGE"
    score = 0
    checks = [
        (r"\b(otp|pin|cvv|password|bank details|card number)\b", "It asks for private banking or login information.", 3, "OTP_OR_CREDENTIAL_SCAM"),
        (r"\b(urgent|immediately|today|blocked|suspend|expire|last chance)\b", "It pressures you to act quickly.", 1, category),
        (r"\b(upi|pay|payment|transfer|send.{0,20}(money|₹|rs))\b", "It asks for money or a payment.", 2, "PAYMENT_SCAM"),
        (r"\b(kyc|bank|sbi|account)\b", "It may be pretending to be a bank or official service.", 1, "BANKING_PHISHING"),
        (r"\b(won|lottery|prize|lakh|processing fee)\b", "It offers an unexpected prize or reward.", 2, "LOTTERY_PRIZE_SCAM"),
        (r"\b(don'?t call|in trouble|emergency|papa|mom)\b", "It uses an emergency or emotional request.", 2, "FAMILY_IMPERSONATION"),
        (r"https?://|www\.|\.xyz\b|\.top\b|bit\.ly", "It includes a link that should be checked carefully.", 2, "PHISHING_LINK"),
        (r"\b(remote access|anydesk|teamviewer|customer support)\b", "It may be asking for remote access or posing as support.", 2, "TECH_SUPPORT_SCAM"),
    ]
    for pattern, reason, points, found_category in checks:
        if re.search(pattern, lowered, re.I):
            signals.append(reason)
            score += points
            if found_category != "SUSPICIOUS_MESSAGE": category = found_category
    if score >= 4:
        level, summary = "HIGH", "This message has several strong warning signs. Please stop for a moment."
    elif score >= 2:
        level, summary = "MEDIUM", "We found some warning signs. Check before taking any action."
    else:
        level, summary = "LOW", "No major warning signs were detected. Unexpected messages still deserve care."
    if level == "LOW":
        signals = ["There are no obvious scam patterns in this text."]
    detail = "The message is being treated as untrusted content. " + ("Its requests and wording are worth verifying independently." if level != "LOW" else "Do not share information just because a message sounds official.")
    return Analysis(risk_level=level, category=category, summary=summary, warning_signs=signals[:5], do_not=BASE_DONT if level != "LOW" else ["Share private details unless you expected the request"], recommended_actions=BASE_ACTIONS, detail=detail, technical_detail=f"Heuristic check found {len(signals)} warning pattern(s) in the {source}. This is not a guarantee that a message is fraudulent.")
