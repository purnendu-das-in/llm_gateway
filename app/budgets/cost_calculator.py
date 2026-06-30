MODEL_PRICING_PER_1K = {
    "mock-fast": {"input": 0.0001, "output": 0.0002},
    "mock-quality": {"input": 0.0003, "output": 0.0006},
}


def estimate_cost_usd(model_name: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING_PER_1K.get(model_name, MODEL_PRICING_PER_1K["mock-fast"])
    cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
    return round(cost, 6)
