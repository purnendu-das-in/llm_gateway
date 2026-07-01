from datetime import UTC, datetime, timedelta

from pydantic import BaseModel


class CircuitState(BaseModel):
    failure_count: int = 0
    opened_until: datetime | None = None


class InMemoryCircuitBreaker:
    def __init__(self, failure_threshold: int = 2, cooldown_seconds: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._states: dict[str, CircuitState] = {}

    def is_open(self, model_name: str) -> bool:
        state = self._states.get(model_name)
        if state is None or state.opened_until is None:
            return False
        if datetime.now(UTC) >= state.opened_until:
            state.opened_until = None
            state.failure_count = 0
            return False
        return True

    def record_success(self, model_name: str) -> None:
        self._states[model_name] = CircuitState()

    def record_failure(self, model_name: str) -> None:
        state = self._states.setdefault(model_name, CircuitState())
        state.failure_count += 1
        if state.failure_count >= self.failure_threshold:
            state.opened_until = datetime.now(UTC) + self.cooldown

    def snapshot(self) -> dict[str, dict[str, object]]:
        return {model: state.model_dump(mode="json") for model, state in self._states.items()}

    def clear(self) -> None:
        self._states.clear()


circuit_breaker = InMemoryCircuitBreaker()
