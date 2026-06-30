import re

from pydantic import BaseModel


class MaskedText(BaseModel):
    text: str
    masked_count: int
    mapping: dict[str, str]


PII_PATTERNS = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("PHONE_NUMBER", re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]*?){13,19}\b")),
    ("AADHAAR", re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
]


def mask_pii(text: str) -> MaskedText:
    mapping: dict[str, str] = {}
    masked_text = text

    for label, pattern in PII_PATTERNS:
        matches = list(pattern.finditer(masked_text))
        for index, match in enumerate(matches, start=1):
            token = f"[{label}_{len(mapping) + index}]"
            mapping[token] = match.group(0)
            masked_text = masked_text.replace(match.group(0), token, 1)

    return MaskedText(text=masked_text, masked_count=len(mapping), mapping=mapping)
