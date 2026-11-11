"""Concentration measures, Pareto dominance and hypervolume. Pure functions."""

import numpy as np


def tau(power, threshold=0.67):
    """Smallest number of holders controlling strictly more than `threshold` of the total."""
    power = np.asarray(power, float)
    total = power.sum()
    if total <= 0:
        return np.nan
    ordered = np.sort(power)[::-1]
    return int(np.searchsorted(np.cumsum(ordered), threshold * total, side="right") + 1)


def effective_number(power):
    """Inverse Herfindahl index: the number of equal holders with the same concentration."""
    power = np.asarray(power, float)
    total = power.sum()
    if total <= 0:
        return np.nan
    share = power / total
    return float(1.0 / np.square(share).sum())


def gini(values):
    values = np.sort(np.asarray(values, float))
    n, total = len(values), values.sum()
    if n == 0 or total <= 0:
        return np.nan
    return float((2 * np.arange(1, n + 1) - n - 1).dot(values) / (n * total))


def dominates(a, b):
    """All objectives are maximised."""
    return bool(np.all(a >= b) and np.any(a > b))


def pareto_front(points):
    """Indices of non-dominated rows."""
    points = np.asarray(points, float)
    keep = []
    for i, p in enumerate(points):
        if not any(dominates(q, p) for j, q in enumerate(points) if j != i):
            keep.append(i)
    return keep


def epsilon_front(points, eps):
    """A Pareto front thinned to points that differ by a meaningful amount (maximised).

    Each axis is cut into boxes `eps` wide. A point is dropped when another point's box is
    at least as good on every axis and better on one; of several points in one box the
    one nearest the box's best corner is kept. Returns indices into `points`.
    """
    points = np.asarray(points, float)
    eps = np.asarray(eps, float)
    front = pareto_front(points)
    boxes = np.floor(points[front] / eps + 1e-9)
    best = {}
    for row, i in enumerate(front):
        if any(dominates(boxes[other], boxes[row]) for other in range(len(front))):
            continue
        key = tuple(boxes[row])
        slack = ((boxes[row] + 1) * eps - points[i]) / eps  # distance to the best corner
        if key not in best or slack.sum() < best[key][0]:
            best[key] = (slack.sum(), i)
    return sorted(i for _, i in best.values())


def hypervolume(points, reference):
    """Exact dominated hypervolume above `reference`, all objectives maximised.

    Points are clipped to the reference, so a point worse than the reference on an axis
    contributes nothing on that axis. Uses the WFG exclusive-volume recursion, which
    handles six objectives and a few dozen points in well under a second.
    """
    points = np.asarray(points, float)
    reference = np.asarray(reference, float)
    if points.size == 0:
        return 0.0
    points = np.maximum(points, reference) - reference
    points = points[np.all(points > 0, axis=1)]
    return _hv(_nondominated(points))


def _hv(points):
    """Volume dominated by mutually non-dominated points, measured from the origin."""
    if len(points) == 0:
        return 0.0
    if len(points) == 1:
        return float(np.prod(points[0]))
    if points.shape[1] == 1:
        return float(points[:, 0].max())
    points = points[np.argsort(points[:, -1])]
    total = 0.0
    for k in range(len(points)):
        # What point k adds beyond the points after it: its box minus the overlap.
        overlap = np.minimum(points[k + 1 :], points[k])
        total += float(np.prod(points[k])) - _hv(_nondominated(overlap))
    return total


def _nondominated(points):
    if len(points) <= 1:
        return points
    points = np.unique(points, axis=0)
    covers = (points[:, None, :] >= points[None, :, :]).all(axis=2)
    np.fill_diagonal(covers, False)
    return points[~covers.any(axis=0)]


def mean_ci(values, z=1.96):
    """Mean and normal-approximation half-width across independent seeds."""
    values = np.asarray(values, float)
    values = values[~np.isnan(values)]
    n = len(values)
    if n == 0:
        return np.nan, np.nan
    if n == 1:
        return float(values[0]), np.nan
    return float(values.mean()), float(z * values.std(ddof=1) / np.sqrt(n))
