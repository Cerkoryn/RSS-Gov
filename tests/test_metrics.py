import numpy as np

from rss_gov import metrics


def test_tau_counts_holders_needed_to_exceed_the_threshold():
    assert metrics.tau([50, 30, 20], 0.5) == 2  # 50 is not more than half
    assert metrics.tau([60, 30, 10], 0.5) == 1
    assert metrics.tau([25, 25, 25, 25], 0.67) == 3


def test_effective_number_of_equal_holders_is_their_count():
    assert metrics.effective_number([1, 1, 1, 1]) == 4
    assert metrics.effective_number([1, 0, 0]) == 1


def test_gini_is_zero_for_equal_and_high_for_concentrated():
    assert metrics.gini([5, 5, 5]) == 0
    assert metrics.gini([0, 0, 0, 100]) == 0.75


def test_pareto_front_drops_dominated_points():
    points = [[1, 2], [2, 1], [1, 1], [2, 2]]
    assert metrics.pareto_front(points) == [3]
    assert metrics.pareto_front([[1, 2], [2, 1], [0, 0]]) == [0, 1]


def test_hypervolume_matches_hand_computed_areas():
    assert metrics.hypervolume([[1, 2], [2, 1]], [0, 0]) == 3
    assert metrics.hypervolume([[2, 2], [1, 1]], [0, 0]) == 4
    assert metrics.hypervolume([[1, 1, 1]], [0, 0, 0]) == 1
    assert metrics.hypervolume([[-1, 5]], [0, 0]) == 0  # worse than the reference on one axis


def test_hypervolume_agrees_with_monte_carlo_in_four_dimensions():
    rng = np.random.default_rng(0)
    points = rng.random((12, 4))
    samples = rng.random((200_000, 4))
    covered = (samples[:, None, :] <= points[None, :, :]).all(axis=2).any(axis=1).mean()
    assert abs(metrics.hypervolume(points, np.zeros(4)) - covered) < 0.005


def test_mean_ci_shrinks_with_more_seeds():
    rng = np.random.default_rng(1)
    _, few = metrics.mean_ci(rng.normal(size=10))
    _, many = metrics.mean_ci(rng.normal(size=1000))
    assert many < few


def test_hypervolume_agrees_with_monte_carlo_in_six_dimensions():
    rng = np.random.default_rng(2)
    points = rng.random((10, 6))
    samples = rng.random((300_000, 6))
    covered = (samples[:, None, :] <= points[None, :, :]).all(axis=2).any(axis=1).mean()
    assert abs(metrics.hypervolume(points, np.zeros(6)) - covered) < 0.004


def test_epsilon_front_ignores_differences_too_small_to_matter():
    points = [[1.0, 0.0], [0.99, 0.004], [0.0, 1.0], [0.5, 0.5], [0.2, 0.2]]
    assert metrics.epsilon_front(points, [0.05, 0.05]) == [0, 2, 3]
    assert metrics.epsilon_front(points, [0.001, 0.001]) == [0, 1, 2, 3]
