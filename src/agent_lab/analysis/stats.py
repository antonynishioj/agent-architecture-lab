import random
from statistics import fmean


BOOTSTRAP_SAMPLES = 2000


def mean(values: list[float]) -> float | None:
    if not values:
        return None

    return fmean(values)


def bootstrap_ci(
    values: list[float],
    seed: str,
    confidence: float = 0.95,
) -> tuple[float | None, float | None]:
    """
    Percentile bootstrap confidence interval of the mean.

    The seed is fixed so that recomputing a summary from the raw
    files gives exactly the same numbers (needed for verification).
    """

    if not values:
        return None, None

    if len(values) == 1:
        return values[0], values[0]

    rng = random.Random(seed)
    size = len(values)

    means = sorted(
        fmean(rng.choices(values, k=size))
        for _ in range(BOOTSTRAP_SAMPLES)
    )

    alpha = (1 - confidence) / 2
    low = means[int(alpha * BOOTSTRAP_SAMPLES)]
    high = means[min(BOOTSTRAP_SAMPLES - 1, int((1 - alpha) * BOOTSTRAP_SAMPLES))]

    return low, high


def r4(value: float | None) -> float | None:
    if value is None:
        return None

    return round(value, 4)
