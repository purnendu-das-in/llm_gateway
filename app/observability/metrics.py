from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class GatewayMetrics:
    requests_total: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    fallback_total: int = 0
    provider_errors_total: dict[tuple[str, str], int] = field(
        default_factory=lambda: defaultdict(int)
    )
    tokens_total: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    latency_ms: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))

    def record_request(self, tenant_id: str, model_name: str, status: str) -> None:
        self.requests_total[(tenant_id, status)] += 1
        if status == "fallback":
            self.fallback_total += 1

    def record_provider_error(self, model_name: str, status_code: int) -> None:
        self.provider_errors_total[(model_name, str(status_code))] += 1

    def record_tokens(self, tenant_id: str, input_tokens: int, output_tokens: int) -> None:
        self.tokens_total[(tenant_id, "input")] += input_tokens
        self.tokens_total[(tenant_id, "output")] += output_tokens

    def record_latency(self, model_name: str, latency_ms: int) -> None:
        self.latency_ms[model_name].append(latency_ms)

    def render_prometheus(self) -> str:
        lines = [
            "# HELP llm_gateway_requests_total Requests handled by tenant and status.",
            "# TYPE llm_gateway_requests_total counter",
        ]
        for (tenant_id, status), value in sorted(self.requests_total.items()):
            lines.append(
                f'llm_gateway_requests_total{{tenant_id="{tenant_id}",status="{status}"}} {value}'
            )

        lines.extend(
            [
                "# HELP llm_gateway_fallback_total Requests served by a fallback model.",
                "# TYPE llm_gateway_fallback_total counter",
                f"llm_gateway_fallback_total {self.fallback_total}",
                "# HELP llm_gateway_provider_errors_total Upstream provider errors.",
                "# TYPE llm_gateway_provider_errors_total counter",
            ]
        )
        for (model_name, status_code), value in sorted(self.provider_errors_total.items()):
            lines.append(
                "llm_gateway_provider_errors_total"
                f'{{model="{model_name}",status_code="{status_code}"}} {value}'
            )

        lines.extend(
            [
                "# HELP llm_gateway_tokens_total Token usage by tenant.",
                "# TYPE llm_gateway_tokens_total counter",
            ]
        )
        for (tenant_id, token_type), value in sorted(self.tokens_total.items()):
            lines.append(
                f'llm_gateway_tokens_total{{tenant_id="{tenant_id}",type="{token_type}"}} {value}'
            )

        lines.extend(
            [
                "# HELP llm_gateway_latency_ms_avg Average provider latency in milliseconds.",
                "# TYPE llm_gateway_latency_ms_avg gauge",
            ]
        )
        for model_name, values in sorted(self.latency_ms.items()):
            average = sum(values) / len(values)
            lines.append(f'llm_gateway_latency_ms_avg{{model="{model_name}"}} {average:.2f}')

        return "\n".join(lines) + "\n"

    def clear(self) -> None:
        self.requests_total.clear()
        self.fallback_total = 0
        self.provider_errors_total.clear()
        self.tokens_total.clear()
        self.latency_ms.clear()


gateway_metrics = GatewayMetrics()
