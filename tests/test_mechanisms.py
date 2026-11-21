import numpy as np
import pytest

from rss_gov import mechanisms as m


def make_round(n=5):
    return m.Round(
        power=np.array([100.0, 50.0, 20.0, 10.0, 0.5])[:n] * 1e6,
        activity=np.array([1.0, 0.5, 1.0, 0.0, 1.0])[:n],
        rationale=np.array([1.0, 0.0, 0.5, 0.0, 0.0])[:n],
        delegators=np.array([500.0, 100.0, 30.0, 5.0, 1.0])[:n],
        pledge=np.array([1.0, 0.1, 2.0, 0.0, 0.5])[:n] * 1e6,
    )


@pytest.mark.parametrize("name", [n for n in m.PRESETS if n != "unpaid"])
def test_every_preset_pays_out_at_most_the_pot(name):
    scheme = m.preset(name, 3600.0)
    r = make_round()
    award, yields = m.allocate(scheme, r, 100.0)
    total = award.sum() + (yields * r.power).sum()
    assert (award >= 0).all() and (yields >= 0).all()
    assert total <= 100.0 + 1e-9
    # These may leave money unspent; so may skipping the delegators of every DRep there is.
    ceiling = scheme.per_vote_ada or scheme.max_award_share or scheme.delegator_k_exclude >= 5
    if award.sum() > 0 and not ceiling:
        assert total == pytest.approx(100.0)


def test_unpaid_pays_nothing():
    award, yields = m.allocate(m.preset("unpaid", 1e6), make_round(), 0.0)
    assert award.sum() == 0 and yields.sum() == 0


def test_proportional_pays_by_power_times_activity():
    award, _ = m.allocate(m.Scheme(budget_ada=1, alpha=1), make_round(), 100.0)
    weights = np.array([100, 25, 20, 0, 0.5])
    assert award == pytest.approx(100 * weights / weights.sum())


def test_equal_pays_active_dreps_by_activity_only():
    award, _ = m.allocate(m.Scheme(budget_ada=1, alpha=0), make_round(), 70.0)
    assert award == pytest.approx([20, 10, 20, 0, 20])


def test_exclude_k_pay_n_skips_the_largest_and_inactive():
    scheme = m.Scheme(budget_ada=1, alpha=0, k_exclude=1, n_pay=2)
    award, _ = m.allocate(scheme, make_round(), 30.0)
    assert award[0] == 0 and award[3] == 0 and award[4] == 0
    assert award[1] > 0 and award[2] > 0


def test_cap_limits_counted_power():
    award, _ = m.allocate(m.Scheme(budget_ada=1, cap_ada=20e6), make_round(3), 90.0)
    assert award == pytest.approx([36, 18, 36])  # equal counted power, so by vote rate only


def test_floors_and_gate_exclude():
    scheme = m.Scheme(budget_ada=1, min_power_ada=15e6, min_delegators=50, activity_gate=0.75)
    award, _ = m.allocate(scheme, make_round(), 10.0)
    assert (award > 0).tolist() == [True, False, False, False, False]


def test_delegator_share_splits_the_pot():
    r = make_round()
    for mode in ("flat", "passthrough"):
        scheme = m.Scheme(budget_ada=1, delegator_share=0.8, delegator_mode=mode)
        award, yields = m.allocate(scheme, r, 100.0)
        assert award.sum() == pytest.approx(20.0)
        assert (yields * r.power).sum() == pytest.approx(80.0)
    scheme = m.Scheme(budget_ada=1, delegator_share=0.5, delegator_mode="flat")
    flat = m.allocate(scheme, r, 100.0)[1]
    per_vote = flat[flat > 0] / r.activity[flat > 0]
    assert per_vote == pytest.approx(per_vote[0])  # one yield per unit of vote rate
    assert flat[3] == 0  # delegators of a DRep that did not vote get nothing


def test_soft_pledge_limits_counted_power_but_not_voting_power():
    scheme = m.Scheme(budget_ada=1, pledge_leverage=10)
    r = make_round()
    assert m.counted_power(scheme, r)[1] == pytest.approx(1e6)
    assert (m.voting_power(scheme, r.power, r.pledge) == r.power).all()
    hard = m.Scheme(budget_ada=1, pledge_leverage=10, hard_cap=True)
    assert m.voting_power(hard, r.power, r.pledge)[1] == pytest.approx(1e6)


def test_feasibility_flags_hard_fork_only_designs():
    assert m.preset("proportional", 1).feasibility()["pilot_testable"]
    hard = m.preset("pledge_hard_cap", 1).feasibility()
    assert hard["requires_hard_fork"] and not hard["pilot_testable"]


@pytest.mark.parametrize("name", [n for n in m.PRESETS if n != "unpaid"])
def test_only_explicit_votes_are_paid(name):
    """A DRep that did not vote earns nothing, and neither do its delegators."""
    r = make_round()
    award, yields = m.allocate(m.preset(name, 1), r, 100.0)
    assert award[3] == 0 and yields[3] == 0


def test_every_vote_earns_the_same_increment():
    r = make_round()
    half = m.weights(m.Scheme(budget_ada=1), m.replace_activity(r, np.full(5, 0.5)))
    full = m.weights(m.Scheme(budget_ada=1), m.replace_activity(r, np.ones(5)))
    assert full == pytest.approx(2 * half)


def test_one_more_vote_is_worth_something_to_a_drep_that_has_not_voted():
    r = make_round()
    value = m.vote_value(m.preset("proportional", 1), r, 100.0)
    assert value[3] > 0
    assert value[0] > value[2]


def test_a_fee_per_action_funds_the_pot_and_needs_a_hard_fork():
    fee = m.Scheme(name="fee", alpha=0.0, fee_ada=25_000)
    assert fee.paid and fee.income(36, 2) == 50_000 and fee.income(36, 0) == 0
    assert m.Scheme(name="mix", budget_ada=3.6e6, fee_ada=1e3).income(36, 1.5) == 101_500
    assert fee.label() == "equal; 25k ADA proposer fee"
    flags = fee.feasibility()
    assert flags["requires_hard_fork"] and not flags["pilot_testable"]
    with pytest.raises(ValueError):
        m.Scheme(fee_ada=-1)


def test_every_named_design_is_also_paid_by_each_fee():
    variation = {"name": "capped_1m", "preset": "capped", "budget_ada": 1e6}
    config = dict(experiment=dict(schemes=["unpaid", "capped", variation], fees_ada=[50_000]))
    rows = m.experiment_rows(config)
    assert rows[:3] == config["experiment"]["schemes"]
    (fee,) = (m.from_config(row, 5e6) for row in rows[3:])
    assert fee.name == "capped_fee_50k" and fee.budget_ada == 0 and fee.fee_ada == 50_000
    assert fee.cap_ada == m.preset("capped", 5e6).cap_ada
    assert m.experiment_rows(dict(experiment=dict(schemes=["capped"]))) == ["capped"]


def test_labels_describe_the_rule():
    assert m.preset("unpaid", 1).label() == "unpaid"
    assert m.preset("capped", 5e6).label() == "linear, cap 20M; 5M ADA"
    assert "pledge hard cap 1000x" in m.preset("pledge_hard_cap", 5e6).label()


def test_from_config_accepts_names_and_overrides():
    assert m.from_config("sqrt", 10).alpha == 0.5
    custom = m.from_config({"preset": "sqrt", "name": "mine", "min_delegators": 5}, 10)
    assert (custom.name, custom.alpha, custom.min_delegators, custom.budget_ada) == (
        "mine",
        0.5,
        5,
        10,
    )
    uncapped = m.from_config({"preset": "capped", "name": "uncapped", "cap_ada": None}, 10)
    assert uncapped.cap_ada == float("inf")  # null removes the preset's cap
    assert m.from_config({"preset": "capped", "name": "kept"}, 10).cap_ada == 20_000_000
    with pytest.raises(ValueError):
        m.preset("nope", 1)
    with pytest.raises(ValueError):
        m.Scheme(hard_cap=True)


def test_min_share_pays_only_dreps_over_that_share_of_all_power():
    r = make_round()  # total 180.5M: 10% is 18.05M
    award, _ = m.allocate(m.Scheme(budget_ada=1, alpha=0, min_share=0.1), r, 30.0)
    assert (award > 0).tolist() == [True, True, True, False, False]


def test_threshold_k_pays_at_most_one_kth_each_and_keeps_the_rest():
    scheme = m.preset("threshold_k", 1)
    r = make_round()
    award, _ = m.allocate(m.replace(scheme, min_share=0.1, max_award_share=0.1), r, 100.0)
    assert award == pytest.approx([10, 10, 10, 0, 0])  # B/k each; 70 stays in the pot


def test_pay_per_vote_is_a_rate_until_the_pot_runs_out():
    r = m.replace(make_round(), actions=4.0)
    scheme = m.Scheme(budget_ada=1, alpha=0, per_vote_ada=2.0)
    award, _ = m.allocate(scheme, r, 1000.0)
    assert award == pytest.approx([8, 4, 8, 0, 8])  # 2 ADA x 4 actions x vote rate
    short, _ = m.allocate(scheme, r, 14.0)
    assert short == pytest.approx(np.array([8, 4, 8, 0, 8]) * 14 / 28)
    assert m.vote_value(scheme, r, 1000.0) == pytest.approx([2, 2, 2, 2, 2])
    with pytest.raises(ValueError):
        m.Scheme(budget_ada=1, alpha=1, per_vote_ada=2.0)


def test_award_cap_is_not_passed_on_to_others():
    award, _ = m.allocate(m.Scheme(budget_ada=1, alpha=1, max_award_share=0.3), make_round(), 100)
    weights = np.array([100, 25, 20, 0, 0.5])
    assert award == pytest.approx(np.minimum(100 * weights / weights.sum(), 30))


def test_top_weight_pays_the_largest_a_fraction_instead_of_nothing():
    r = make_round()
    award, _ = m.allocate(m.Scheme(budget_ada=1, alpha=0, k_exclude=1, top_weight=0.5), r, 35)
    assert award == pytest.approx(np.array([5, 5, 10, 0, 10]) * 35 / 30)


def test_roll_down_passes_a_slot_down_when_a_drep_above_may_not_vote():
    r = make_round()  # by power: 0 (votes always), 1 (half), 2, 3 (never), 4
    hard = m.weights(m.Scheme(budget_ada=1, alpha=0, n_pay=2), r)
    rolled = m.weights(m.Scheme(budget_ada=1, alpha=0, n_pay=2, roll_down=True), r)
    assert hard == pytest.approx([1, 0.5, 0, 0, 0])
    assert rolled == pytest.approx([1, 0.5, 0.5, 0, 0])  # 1.5 voters expected above rank 3
    with pytest.raises(ValueError):
        m.Scheme(budget_ada=1, roll_down=True)


def test_equal_share_blends_equal_and_power_parts():
    r = make_round()
    award, _ = m.allocate(m.Scheme(budget_ada=1, alpha=1, equal_share=0.5), r, 100)
    votes = r.activity
    weights = r.power * r.activity
    want = 50 * votes / votes.sum() + 50 * weights / weights.sum()
    assert award == pytest.approx(want)


def test_delegator_basis_weighs_by_delegator_count():
    r = make_round()
    award, _ = m.allocate(m.Scheme(budget_ada=1, alpha=1, basis="delegators"), r, 100)
    weights = r.delegators * r.activity
    assert award == pytest.approx(100 * weights / weights.sum())
    assert "invites fake ones" in " ".join(
        m.preset("delegator_count_sqrt", 1).feasibility()["notes"]
    )


def test_pledge_gain_counts_only_while_pledge_limits_the_reward():
    r = make_round()
    scheme = m.Scheme(budget_ada=1, pledge_leverage=1)
    gain = m.pledge_gain(scheme, r, 1000.0, np.full(len(r.power), 1e5))
    limited = r.pledge < r.power
    assert (gain[limited & (r.activity > 0)] > 0).all() and (gain[~limited] <= 0).all()
    equal = m.Scheme(budget_ada=1, alpha=0.0, pledge_leverage=1)
    assert not m.pledge_gain(equal, r, 1000.0, 1e5).any()


def test_delegators_of_the_largest_are_not_paid_but_their_dreps_are():
    r = make_round()
    plain = m.scheme(budget_ada=1, alpha=1.0, delegator_share=0.5)
    skip = m.scheme(budget_ada=1, alpha=1.0, delegator_share=0.5, delegator_k_exclude=1)
    award, yields = m.allocate(skip, r, 100.0)
    assert award[0] > 0 and yields[0] == 0  # the largest DRep is paid, its delegators are not
    assert np.allclose(award, m.allocate(plain, r, 100.0)[0])
    assert (yields * r.power).sum() == pytest.approx(50.0)  # their part goes to the others
    assert yields[2] > m.allocate(plain, r, 100.0)[1][2]
    flat = m.scheme(
        budget_ada=1, alpha=1.0, delegator_share=0.5, delegator_mode="flat", delegator_k_exclude=1
    )
    assert m.allocate(flat, r, 100.0)[1][0] == 0


def test_a_minimum_pledge_keeps_drep_and_delegators_unpaid():
    r = make_round()
    scheme = m.scheme(budget_ada=1, alpha=1.0, delegator_share=0.5, min_pledge_ada=500_000)
    award, yields = m.allocate(scheme, r, 100.0)
    assert award[1] == 0 and yields[1] == 0  # 100k pledge: below the floor
    assert award[0] > 0 and yields[0] > 0
    assert "Pledge is not a ledger concept" in " ".join(scheme.feasibility()["notes"])
