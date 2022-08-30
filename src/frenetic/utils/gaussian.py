import numpy as np
from scipy import stats


def gaussian_alteration(
    arr: list[float], center: int, std_dev: float = 1.0, size: int = 20, bound: float = None, soften: float = 1.0
) -> list[float]:
    l, u = max(center - size, 0), min(center + size, len(arr))
    x_values = np.arange(-(center - l), (u - center), 1)
    y_values = stats.norm(0, std_dev)
    mult = y_values.pdf(x_values)
    modified = arr.copy()
    for i, v in enumerate(range(l, u)):
        if bound:
            modified[v] = min(bound, max(-bound, modified[v] * (1.0 + mult[i] / soften)))
        else:
            modified[v] *= 1.0 + mult[i] / soften
    return modified
