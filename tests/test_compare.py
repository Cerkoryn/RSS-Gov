import numpy as np

from rss_gov import search
from rss_gov.experiment import Axis

GAIN = Axis("participation", "Participation", "share voting", "higher", 0.01, (-0.05, 0.20))
COST = Axis("annual_cost_ada", "Reward sustainability", "cost", "lower", 5e5, (25e6, 0.0))


def test_a_verdict_needs_a_change_that_is_both_clear_and_large_enough():
    assert GAIN.verdict(0.02, 0.005) == 1
    assert GAIN.verdict(0.005, 0.001) == 0  # clear but too small to matter
    assert GAIN.verdict(0.02, 0.03) == 0  # large but not clear
    assert GAIN.verdict(-0.02, 0.005) == -1
    assert COST.verdict(1e6, 0.0) == -1  # costing more is worse
    assert COST.verdict(1e6, float("nan")) == -1  # exact quantities have no interval


def test_scores_run_from_worst_to_best_whatever_the_direction():
    assert GAIN.score([-0.05, 0.0, 0.20, 0.5]).tolist() == [0.0, 0.2, 1.0, 1.0]
    assert COST.score([0.0, 12.5e6, 25e6]).tolist() == [1.0, 0.5, 0.0]
    assert GAIN.step == 0.04


def _cube(rows):
    """Three seeds per scheme, identical, so means are the given values."""
    return np.repeat(np.array(rows, float)[:, None, :], 3, axis=1)


def test_front_keeps_trade_offs_and_drops_what_is_beaten_on_every_axis():
    names = ["unpaid", "cheap", "dear", "wasteful", "twin"]
    cube = _cube(
        [
            [0.25, 0.0],
            [0.28, 2e6],  # some participation for little money
            [0.31, 10e6],  # more for more
            [0.28, 10e6],  # what `cheap` buys at the price of `dear`
            [0.281, 2.1e6],  # differs from `cheap` by less than a meaningful amount
        ]
    )
    axes = [GAIN, COST]
    points = search.scores(cube, names, axes)
    front = search.front_of(points, names, axes)
    assert "wasteful" not in front
    assert {"unpaid", "dear"} <= set(front)
    assert len({"cheap", "twin"} & set(front)) == 1
    both = search.volume(cube, names, axes, ["cheap", "dear"])
    assert both > search.volume(cube, names, axes, ["cheap"]) > search.volume(cube, names, axes, [])
    assert search.volume(cube, names, axes, ["cheap", "wasteful"]) == search.volume(
        cube, names, axes, ["cheap"]
    )


def test_generated_names_are_told_apart_from_named_schemes():
    assert search.GENERATED.fullmatch("g3_17")
    assert not search.GENERATED.fullmatch("gated_sqrt")
