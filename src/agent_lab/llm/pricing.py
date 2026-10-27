import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelPricing:
    """
    Token pricing for a model.

    Prices are expressed in USD per 1 million tokens.
    None means pricing is not configured.

    On the Gemini free tier the real cost is $0. These prices give an
    "equivalent cost if you were on the paid tier" so architectures
    can be compared in money as well as tokens.
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

    @classmethod
    def from_file(cls, path: Path) -> "PricingRegistry":
        registry = cls()

        if not path.exists():
            return registry

        data = json.loads(path.read_text(encoding="utf-8"))

        for model, prices in data.get("models", {}).items():
            registry.register(
                model=model,
                pricing=ModelPricing(
                    input_per_million_usd=prices.get(
                        "input_per_million_usd"
                    ),
                    output_per_million_usd=prices.get(
                        "output_per_million_usd"
                    ),
                ),
            )

        return registry

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
