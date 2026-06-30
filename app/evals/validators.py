import json

from app.schemas.chat import EvalResult


def run_basic_evals(content: str, task_type: str | None) -> list[EvalResult]:
    evals = [
        EvalResult(
            name="response_length",
            passed=0 < len(content) <= 4000,
            score=1.0 if 0 < len(content) <= 4000 else 0.0,
        )
    ]

    if task_type == "document_extraction":
        try:
            json.loads(content)
            passed = True
        except json.JSONDecodeError:
            passed = False
        evals.append(
            EvalResult(
                name="json_validity",
                passed=passed,
                score=1.0 if passed else 0.0,
            )
        )

    return evals
