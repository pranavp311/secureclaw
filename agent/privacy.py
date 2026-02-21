"""
Confidential Privacy Layer — lightweight regex-based PII detector.

Scans user prompts for personally identifiable information and returns a
risk assessment that feeds into the hybrid routing decision. High-risk
prompts are recommended for local (on-device) processing to keep
sensitive data off the wire.

Zero external dependencies — pure stdlib regex patterns.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    STREET_ADDRESS = "street_address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    HEALTH = "health"
    FINANCIAL = "financial"
    PASSWORD = "password"
    NAME_CONTEXT = "name_context"


@dataclass
class PIIMatch:
    pii_type: PIIType
    matched_text: str
    confidence: float  # 0.0 – 1.0
    start: int
    end: int


@dataclass
class PrivacyResult:
    risk_level: RiskLevel
    pii_found: List[PIIMatch] = field(default_factory=list)
    recommendation: str = "auto"  # "local", "cloud", "auto"
    summary: str = ""

    @property
    def pii_types(self) -> List[str]:
        return list({m.pii_type.value for m in self.pii_found})


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

_PATTERNS: List[Tuple[PIIType, re.Pattern, float]] = [
    # Email
    (PIIType.EMAIL,
     re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
     0.95),

    # Phone numbers (international & US formats)
    (PIIType.PHONE,
     re.compile(
         r"(?<!\d)"
         r"(?:\+?\d{1,3}[\s\-.]?)?"
         r"(?:\(?\d{2,4}\)?[\s\-.]?)"
         r"\d{3,4}[\s\-.]?\d{3,4}"
         r"(?!\d)"
     ),
     0.85),

    # SSN (US)
    (PIIType.SSN,
     re.compile(r"\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b"),
     0.90),

    # Credit card numbers (13-19 digits, optional separators)
    (PIIType.CREDIT_CARD,
     re.compile(
         r"\b(?:\d[\s\-]?){12,18}\d\b"
     ),
     0.90),

    # IP addresses (IPv4)
    (PIIType.IP_ADDRESS,
     re.compile(
         r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
         r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
     ),
     0.80),

    # Date of birth patterns
    (PIIType.DATE_OF_BIRTH,
     re.compile(
         r"\b(?:born\s+(?:on\s+)?|dob[\s:]+|date\s+of\s+birth[\s:]+|birthday[\s:]+)"
         r"(?:\d{1,2}[\s/\-\.]\d{1,2}[\s/\-\.]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})",
         re.I
     ),
     0.90),

    # Passport number patterns
    (PIIType.PASSPORT,
     re.compile(
         r"\b(?:passport[\s#:]+)([A-Z]{1,2}\d{6,9})\b",
         re.I
     ),
     0.85),

    # Street address (number + street name + type)
    (PIIType.STREET_ADDRESS,
     re.compile(
         r"\b\d{1,6}[A-Za-z]?\s+(?:[A-Z][a-z]+\s+){1,4}"
         r"(?:St(?:reet)?|Ave(?:nue)?|Blvd|Boulevard|Dr(?:ive)?|"
         r"Ln|Lane|Rd|Road|Way|Ct|Court|Pl(?:ace)?|Cir(?:cle)?|"
         r"Pkwy|Parkway|Terr(?:ace)?|Hwy|Highway|Close|Crescent|Walk)"
         r"\.?\b",
         re.I
     ),
     0.85),

    # Postal / ZIP codes (US, UK, Singapore, Australia, Canada, EU)
    (PIIType.STREET_ADDRESS,
     re.compile(
         r"\b(?:"
         r"\d{5}(?:-\d{4})?|"                  # US ZIP: 12345 or 12345-6789
         r"\d{6}|"                              # SG/IN postal: 085201
         r"[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}|" # UK: SW1A 1AA
         r"[A-Z]\d[A-Z]\s*\d[A-Z]\d"            # CA: K1A 0B1
         r")\b"
     ),
     0.70),
]

# Keyword-based patterns (lower confidence, context-dependent)
_HEALTH_KEYWORDS = re.compile(
    r"\b(?:diagnosis|prescription|medication|patient\s+id|medical\s+record|"
    r"blood\s+type|allergy|allergies|symptoms?|treatment|surgery|"
    r"health\s+insurance|insurance\s+id|doctor\s+visit|hospital|"
    r"mental\s+health|therapy\s+session|hiv|std|pregnant|pregnancy)\b",
    re.I
)

_FINANCIAL_KEYWORDS = re.compile(
    r"\b(?:bank\s+account|routing\s+number|account\s+number|"
    r"tax\s+id|ein|tin|salary|income|net\s+worth|"
    r"social\s+security|iban|swift\s+code|pin\s+(?:number|code)|"
    r"cvv|cvc|expir(?:y|ation)\s+date)\b",
    re.I
)

_PASSWORD_KEYWORDS = re.compile(
    r"\b(?:(?:my\s+)?password\s+is|(?:my\s+)?password\s+to|"
    r"change\s+(?:my\s+)?password|reset\s+(?:my\s+)?password|"
    r"new\s+password|update\s+(?:my\s+)?password|"
    r"passwd[\s:]+|secret[\s:]+|api[\s_\-]?key[\s:]+|token[\s:]+|"
    r"private[\s_\-]?key[\s:]+|credentials?[\s:]+)\b",
    re.I
)

_NAME_CONTEXT_KEYWORDS = re.compile(
    r"\b(?:my\s+(?:full\s+)?name\s+is|i\s+am\s+called|"
    r"my\s+(?:real|legal)\s+name|"
    r"my\s+(?:home|mailing|billing)\s+address|"
    r"i\s+live\s+at|i\s+stay\s+at|my\s+address\s+is|"
    r"i\s+reside\s+at|deliver\s+to|ship\s+to)\b",
    re.I
)

_KEYWORD_PATTERNS: List[Tuple[PIIType, re.Pattern, float]] = [
    (PIIType.HEALTH, _HEALTH_KEYWORDS, 0.70),
    (PIIType.FINANCIAL, _FINANCIAL_KEYWORDS, 0.75),
    (PIIType.PASSWORD, _PASSWORD_KEYWORDS, 0.90),
    (PIIType.NAME_CONTEXT, _NAME_CONTEXT_KEYWORDS, 0.65),
]


# ---------------------------------------------------------------------------
# Luhn check for credit card validation
# ---------------------------------------------------------------------------

def _luhn_check(number_str: str) -> bool:
    """Validate a number string with the Luhn algorithm."""
    digits = [int(d) for d in number_str if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse = digits[::-1]
    for i, d in enumerate(reverse):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def scan_privacy(text: str) -> PrivacyResult:
    """
    Scan text for PII and return a privacy risk assessment.

    Returns:
        PrivacyResult with risk_level, pii_found list, and routing recommendation.
    """
    matches: List[PIIMatch] = []

    # Run regex patterns
    for pii_type, pattern, confidence in _PATTERNS:
        for m in pattern.finditer(text):
            matched = m.group()

            # Extra validation for credit cards (Luhn check)
            if pii_type == PIIType.CREDIT_CARD:
                digits_only = re.sub(r"\D", "", matched)
                if not _luhn_check(digits_only):
                    continue

            # Reduce SSN confidence if it could be a phone number
            adj_confidence = confidence
            if pii_type == PIIType.SSN:
                digits_only = re.sub(r"\D", "", matched)
                if len(digits_only) != 9:
                    continue

            matches.append(PIIMatch(
                pii_type=pii_type,
                matched_text=matched,
                confidence=adj_confidence,
                start=m.start(),
                end=m.end(),
            ))

    # Run keyword patterns
    for pii_type, pattern, confidence in _KEYWORD_PATTERNS:
        for m in pattern.finditer(text):
            matches.append(PIIMatch(
                pii_type=pii_type,
                matched_text=m.group(),
                confidence=confidence,
                start=m.start(),
                end=m.end(),
            ))

    # Determine risk level
    if not matches:
        return PrivacyResult(
            risk_level=RiskLevel.LOW,
            pii_found=[],
            recommendation="auto",
            summary="No PII detected.",
        )

    # Score based on severity
    high_risk_types = {
        PIIType.SSN, PIIType.CREDIT_CARD, PIIType.PASSWORD,
        PIIType.PASSPORT, PIIType.HEALTH, PIIType.FINANCIAL,
    }
    medium_risk_types = {
        PIIType.EMAIL, PIIType.PHONE, PIIType.DATE_OF_BIRTH,
        PIIType.STREET_ADDRESS, PIIType.NAME_CONTEXT,
    }

    has_high = any(m.pii_type in high_risk_types for m in matches)
    has_medium = any(m.pii_type in medium_risk_types for m in matches)

    # Upgrade to HIGH if address + context ("I live at") or address + postal code
    address_matches = [m for m in matches if m.pii_type == PIIType.STREET_ADDRESS]
    name_ctx_matches = [m for m in matches if m.pii_type == PIIType.NAME_CONTEXT]
    if len(address_matches) >= 2 or (address_matches and name_ctx_matches):
        has_high = True
    high_confidence_count = sum(1 for m in matches if m.confidence >= 0.85)

    if has_high or high_confidence_count >= 3:
        risk_level = RiskLevel.HIGH
        recommendation = "local"
    elif has_medium or high_confidence_count >= 1:
        risk_level = RiskLevel.MEDIUM
        recommendation = "local"
    else:
        risk_level = RiskLevel.LOW
        recommendation = "auto"

    pii_type_names = list({m.pii_type.value for m in matches})
    summary = f"Detected {len(matches)} PII instance(s): {', '.join(pii_type_names)}."

    return PrivacyResult(
        risk_level=risk_level,
        pii_found=matches,
        recommendation=recommendation,
        summary=summary,
    )


def redact_pii(text: str, result: PrivacyResult | None = None) -> str:
    """Redact detected PII from text, replacing with [REDACTED:type]."""
    if result is None:
        result = scan_privacy(text)
    if not result.pii_found:
        return text

    # Sort matches by position (reverse) to replace from end to start
    sorted_matches = sorted(result.pii_found, key=lambda m: m.start, reverse=True)
    redacted = text
    for m in sorted_matches:
        placeholder = f"[REDACTED:{m.pii_type.value}]"
        redacted = redacted[:m.start] + placeholder + redacted[m.end:]
    return redacted
