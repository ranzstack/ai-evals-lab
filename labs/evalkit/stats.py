"""Small, dependency-free statistics helpers.

The point: a single pass-rate number from 20 cases is noisy. Always ask
"how big is the error bar?" before believing a change helped.
"""

from __future__ import annotations

import math
import random


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def bootstrap_ci(values, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0):
    """95% confidence interval for the mean, by resampling cases."""
    values = list(values)
    if not values:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    k = len(values)
    means = sorted(mean(rng.choices(values, k=k)) for _ in range(n_boot))
    return means[int(alpha / 2 * n_boot)], means[int((1 - alpha / 2) * n_boot) - 1]


def paired_bootstrap_delta(a, b, n_boot: int = 2000, seed: int = 0):
    """CI on mean(b) - mean(a) where a[i] and b[i] are the SAME case.

    Pairing removes case-difficulty noise, so it detects real changes with
    far fewer cases than comparing two independent averages.
    """
    assert len(a) == len(b)
    diffs = [y - x for x, y in zip(a, b)]
    return mean(diffs), bootstrap_ci(diffs, n_boot=n_boot, seed=seed)


def wilson(k: int, n: int, z: float = 1.96):
    """Confidence interval for a pass rate k/n (better than +/- for small n)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def cohens_kappa(a, b):
    """Agreement between two raters beyond what chance would produce."""
    labels = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def percentile(xs, p):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = min(len(xs) - 1, max(0, round(p / 100 * (len(xs) - 1))))
    return xs[i]
