from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    """
    Token pricing for a model.

    Prices are expressed in USD per 1 million tokens.
    None means pricing is not configured.
    """

    input_per_million_usd: float | None = None
    output_per_million_usd: float | None = None

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float | None:
        if (
            self.input_per_million_usd is None
            or self.output_per_million_usd is None
        ):
            return None

        input_cost = (
            input_tokens / 1_000_000
        ) * self.input_per_million_usd

        output_cost = (
            output_tokens / 1_000_000
        ) * self.output_per_million_usd

        return input_cost + output_cost


class PricingRegistry:
    """
    Provider-independent model pricing registry.

    The experiment framework does not need to know which provider
    a model belongs to. It only asks this registry for pricing.
    """

    def __init__(self):
        self._pricing: dict[str, ModelPricing] = {}

    def register(
        self,
        model: str,
        pricing: ModelPricing,
    ) -> None:
        self._pricing[model] = pricing

    def get(self, model: str) -> ModelPricing | None:
        return self._pricing.get(model)

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float | None:
        pricing = self.get(model)

        if pricing is None:
            return None

        return pricing.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )