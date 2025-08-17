import math


def solve(a: float, b: float, c: float) -> list[float]:
    EPSILON = 1e-9  # noqa: N806
    for coef in (a, b, c):
        if not math.isfinite(coef):
            raise ValueError("All coefficients must be finite numbers")
    if abs(a) < EPSILON:
        raise ValueError("'a' coefficient must not be zero")
    D = b * b - 4 * a * c  # noqa: N806
    if D < -EPSILON:
        return []
    if abs(D) < EPSILON:
        return [-b / (2 * a)]
    sqrtD = math.sqrt(D)  # noqa: N806
    return [(-b + sqrtD) / (2 * a), (-b - sqrtD) / (2 * a)]
