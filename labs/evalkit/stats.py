"""Small, dependency-free statistics helpers.

The point: a single pass-rate number from 20 cases is noisy. Always ask
"how big is the error bar?" before believing a change helped.
"""

from __future__ import annotations

import math
import random


def mean(xs):
    # list(xs) accepts any iterable (a list, a generator...) and makes a real list.
    # True/False count as 1/0, so mean([True, False, True]) == 0.666...
    xs = list(xs)
    # float("nan") = "not a number", returned for an empty list instead of crashing.
    return sum(xs) / len(xs) if xs else float("nan")


def bootstrap_ci(values, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0):
    """95% confidence interval for the mean, by resampling cases."""
    # How the bootstrap works:
    #   1. Pretend your cases are the whole world.
    #   2. Draw a new "dataset" of the same size from them WITH replacement
    #      (some cases appear twice, some not at all) and compute its mean.
    #   3. Repeat 2000 times. The middle 95% of those means is the interval.
    values = list(values)
    if not values:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)  # fixed seed: the same input always gives the same CI
    k = len(values)
    # rng.choices(values, k=k) draws k items with replacement. sorted(...) of a
    # generator expression builds and sorts all 2000 resampled means.
    means = sorted(mean(rng.choices(values, k=k)) for _ in range(n_boot))  # `_` = "loop variable I don't use"
    # With alpha=0.05: take the values at the 2.5th and 97.5th percentile.
    return means[int(alpha / 2 * n_boot)], means[int((1 - alpha / 2) * n_boot) - 1]


def paired_bootstrap_delta(a, b, n_boot: int = 2000, seed: int = 0):
    """CI on mean(b) - mean(a) where a[i] and b[i] are the SAME case.

    Pairing removes case-difficulty noise, so it detects real changes with
    far fewer cases than comparing two independent averages.
    """
    assert len(a) == len(b)  # crash early if the lists don't line up case-for-case
    # zip(a, b) walks both lists together: (a[0], b[0]), (a[1], b[1]), ...
    diffs = [y - x for x, y in zip(a, b)]
    # Returns (average difference, (low, high)): a number plus a nested tuple.
    return mean(diffs), bootstrap_ci(diffs, n_boot=n_boot, seed=seed)


def wilson(k: int, n: int, z: float = 1.96):
    """Confidence interval for a pass rate k/n (better than +/- for small n)."""
    # A formula alternative to the bootstrap for "k passed out of n".
    # z = 1.96 corresponds to 95% confidence. You don't need to memorise the maths.
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def cohens_kappa(a, b):
    """Agreement between two raters beyond what chance would produce."""
    # a and b are two raters' labels for the same items, in the same order.
    labels = sorted(set(a) | set(b))  # set(...) removes duplicates; | is set union
    n = len(a)
    # po = observed agreement: the fraction of items where the raters match.
    po = sum(x == y for x, y in zip(a, b)) / n
    # pe = agreement you'd expect by pure chance, given how often each rater
    # uses each label. (a.count(l) = how many times label l appears in a.)
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    # Kappa: 1 = perfect, 0 = no better than chance. Guard against dividing by zero.
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def percentile(xs, p):
    # Simple "nearest rank" percentile: sort, then pick the item p% of the way along.
    # percentile(latencies, 95) = the latency that 95% of calls were faster than.
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = min(len(xs) - 1, max(0, round(p / 100 * (len(xs) - 1))))
    return xs[i]
