from urllib.parse import urlparse
from app.schemas import Analysis


def analyze_url(value: str) -> Analysis:
    raw = value.strip()
    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    if not parsed.hostname:
        raise ValueError("Please enter a complete website address, such as example.com.")
    host = parsed.hostname.lower()
    flags = []
    if parsed.scheme != "https": flags.append("The address does not use a secure HTTPS connection.")
    if host.startswith("xn--"): flags.append("The address uses an unusual encoded domain name.")
    if any(x in host for x in ("login", "secure", "verify", "bank")) and host.split(".")[-1] in {"xyz", "top", "click", "site"}: flags.append("The address combines sensitive words with an unusual domain ending.")
    if host.count(".") >= 4: flags.append("The address has many subdomains, which can hide the real website name.")
    if len(raw) > 150 or "@" in raw: flags.append("The address is unusually complex.")
    level = "HIGH" if len(flags) >= 2 else "MEDIUM" if flags else "LOW"
    return Analysis(risk_level=level, category="URL_CHECK", summary={"HIGH":"This website address looks suspicious. Do not open it from the message.","MEDIUM":"This website needs a careful check before you open it.","LOW":"No obvious warning signs were detected in this website address."}[level], warning_signs=flags or ["No obvious warning signs were found from the address alone."], do_not=["Open the link from an unexpected message", "Enter passwords, OTPs, or payment details"] if level != "LOW" else ["Assume a website is genuine only from this check"], recommended_actions=["Visit the organisation's official website by typing its known address yourself", "Use a saved official phone number if you need to check"], trusted_contact_recommended=level == "HIGH", detail="We checked the address only. We did not open or visit this website.", technical_detail=f"Static URL review of host: {host}. No reputation lookup or website visit was performed.")
