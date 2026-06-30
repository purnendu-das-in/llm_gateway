from app.security.pii_masker import mask_pii
from app.security.prompt_validator import validate_prompt


def test_pii_masker_masks_email_phone_and_pan() -> None:
    result = mask_pii("Email rahul@example.com, call 9876543210, PAN ABCDE1234F.")

    assert "rahul@example.com" not in result.text
    assert "9876543210" not in result.text
    assert "ABCDE1234F" not in result.text
    assert result.masked_count == 3


def test_prompt_validator_allows_normal_prompt() -> None:
    result = validate_prompt("Classify this support ticket.", "classification")

    assert result.allowed is True


def test_prompt_validator_rejects_unsupported_task() -> None:
    result = validate_prompt("Do work.", "unsupported")

    assert result.allowed is False
    assert "Unsupported task type" in str(result.reason)
