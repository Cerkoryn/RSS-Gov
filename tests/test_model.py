import pytest
import numpy as np

from rss_gov import mechanisms, model


def run(world, params, scheme="unpaid", response=(0.0, 0.0), seed=3, budget=200_000.0, **kw):
    scenario = model.Scenario("s", *response)
    return model.run(
        world, params, mechanisms.preset(scheme, budget), scenario, epochs=12, seed=seed, **kw
    )


def test_same_seed_same_result(world, params):
    assert run(world, params) == run(world, params)
    assert run(world, params) != run(world, params, seed=4)


def test_without_a_response_paying_changes_nothing(world, params):
    unpaid = run(world, params)
    for name in ("proportional", "equal", "delegator_flat", "delegator_passthrough_sqrt"):
        paid = run(world, params, name)
        for key in ("participation", "tau67", "supported_ratified", "backing", "drep_power"):
            assert paid[key] == unpaid[key], (name, key)
        assert paid["spent_ada"] > 0


def test_the_budget_is_never_overspent(world, params):
    for name in mechanisms.PRESETS:
        out = run(world, params, name, response=(1.0, 2.0, 0.5, 0.5))
        assert out["spent_ada"] <= 200_000.0 + 1e-6, name


def test_a_stronger_drep_response_never_lowers_ballots_under_an_activity_scheme(world, params):
    ballots = [run(world, params, "equal", response=(r, 0.0))["ballots"] for r in (0.0, 0.5, 2.0)]
    assert ballots[0] < ballots[1] < ballots[2]


def test_each_response_channel_is_off_unless_switched_on(world, params):
    """Reinvestment and pledge top-ups must not leak into the other scenarios."""
    scheme = mechanisms.Scheme(name="soft", budget_ada=200_000.0, pledge_leverage=5)

    def backing(*response):
        return model.run(world, params, scheme, model.Scenario("s", *response), 12, 3)["backing"]

    assert backing(0.0, 0.0) == run(world, params, "unpaid")["backing"]
    assert backing(0.0, 0.0, 0.0, 0.5) > backing(0.0, 0.0)


def test_reinvested_awards_concentrate_power_under_a_proportional_rule(world, params):
    def tau_gap(scheme):
        gaps = []
        for seed in range(6):
            base = run(world, params, "unpaid", seed=seed, budget=5e6)
            paid = run(world, params, scheme, (0.0, 0.0, 1.0), seed=seed, budget=5e6)
            gaps.append(paid["effective_n"] - base["effective_n"])
        return np.mean(gaps)

    assert tau_gap("proportional") < 0
    assert tau_gap("proportional") < tau_gap("equal")


def test_a_fee_per_action_pays_what_the_closing_actions_bring(world, params):
    fee = mechanisms.Scheme(name="fee", alpha=0.0, fee_ada=1_000.0)
    draw = np.random.default_rng(np.random.SeedSequence(3).spawn(5)[0])
    closing = draw.choice(world.closes, 12).sum()  # the run's own draw of closing actions
    out = model.run(world, params, fee, model.Scenario("s"), epochs=12, seed=3)
    assert closing > 0 and np.isclose(out["spent_ada"], 1_000.0 * closing)
    assert out["participation"] == run(world, params)["participation"]  # no response: no change


def test_a_fee_buys_the_reactions_of_a_budget_of_the_same_expected_size(world, params):
    """Behaviour follows the fee's average flow; only the money paid follows the lumps."""
    fee = mechanisms.Scheme(name="fee", alpha=0.0, fee_ada=1_000.0)
    budget = mechanisms.Scheme(
        name="budget", alpha=0.0, budget_ada=1_000.0 * world.action_rate * 12
    )
    scenario = model.Scenario("s", 1.0, 2.0, 0.5, 0.5)
    a, b = (model.run(world, params, s, scenario, epochs=12, seed=3) for s in (fee, budget))
    for key in ("participation", "tau67", "ballots", "drep_power"):
        assert np.isclose(a[key], b[key]), key
    assert not np.isclose(a["spent_ada"], b["spent_ada"])


def test_cost_counts_what_was_paid_plus_delivery(world, params):
    out = run(world, params, "delegator_flat", budget=200_000.0)
    paid = out["spent_ada"] + out["payments"] * params.payout_fee_ada
    assert out["annual_cost_ada"] == paid * model.EPOCHS_PER_YEAR / 12
    assert run(world, params)["annual_cost_ada"] == 0


def test_every_recipient_is_paid_however_little(world, params):
    """CIP-159 direct deposits: no minimum payout, so who is paid does not depend on how much."""
    tiny, large = (run(world, params, "delegator_flat", budget=b) for b in (1.0, 200_000.0))
    assert tiny["payments"] == large["payments"] > 0


def test_participation_counts_ada_outside_dreps_as_not_voting(world, params):
    out = run(world, params)
    assert 0 < out["participation"] < out["turnout"]


def test_delegator_rewards_pull_ada_out_of_abstain(world, params):
    base = run(world, params, "unpaid")
    paid = run(world, params, "delegator_flat", response=(0.0, 5.0), budget=5e7)
    assert paid["abstain"] < base["abstain"]


def test_a_hard_cap_cuts_voting_power_even_without_a_response(world, params):
    base = run(world, params, "unpaid")
    scheme = mechanisms.Scheme(name="cap", budget_ada=1.0, pledge_leverage=10, hard_cap=True)
    capped = model.run(world, params, scheme, model.Scenario(), epochs=12, seed=3)
    assert capped["represented_share"] < base["represented_share"]


def test_trace_returns_one_row_per_epoch(world, params):
    series, actions = run(world, params, trace=True)
    assert len(series) == 12
    assert abs(sum(series[-1]["shares"].values()) - 1) < 1e-9
    assert all(0 <= a["turnout"] <= 1 for a in actions)


def test_unpaid_concentration_stays_near_its_start(world, params):
    """Guards against the old model's failure: a baseline that dissolves on its own."""
    start = np.bincount(
        world.acct_target[world.acct_target >= 0], weights=world.acct_ada[world.acct_target >= 0]
    )
    from rss_gov.metrics import effective_number

    out = model.run(world, params, mechanisms.Scheme(), epochs=36, seed=1)
    assert abs(out["effective_n"] / effective_number(start) - 1) < 0.35


def test_pass_through_yield_dilutes_as_delegation_arrives(params):
    """Two DReps share the same delegator award. Arrivals must not all pile into the
    smaller one: its yield falls as it fills."""
    from tests.conftest import make_params

    params = make_params(hazard_large=0.1, hazard_small=0.1, abstain_large=0.05, abstain_small=0.05)
    n = 2000
    target = np.concatenate([[0, 1], np.full(n, model.ABSTAIN)])
    acct_ada = np.concatenate([[1_000.0, 100_000.0], np.full(n, 1_000.0)])
    power = np.array([1_000.0, 100_000.0])
    yield_pp = 50_000.0 / power  # the same award (in points x ADA) behind both DReps
    scheme = mechanisms.Scheme(budget_ada=1.0, delegator_share=0.8)
    moved = model._move(
        params, scheme, model.Scenario("s", 0.0, 1.0), np.random.default_rng(0), target,
        acct_ada, np.ones(n + 2), power, np.array([True, True]), np.zeros(2), yield_pp,
        np.ones(2),
    )  # fmt: skip
    after = np.bincount(moved[moved >= 0], weights=acct_ada[moved >= 0], minlength=2)
    assert after.sum() > 300_000  # the yield pulled abstaining accounts in
    assert after[0] > 20 * power[0]  # the high-yield DRep grew a lot ...
    assert after[0] < 0.5 * after.sum()  # ... but stopped attracting once its yield fell


def test_pledge_is_added_only_where_it_pays(world, params):
    """Under a pledge soft cap, a DRep adds pledge only for a return; under equal pay, never."""

    def backing(scheme, hurdle=0.0):
        scenario = model.Scenario("s", pledge_response=0.5, pledge_min_return=hurdle)
        return model.run(world, params, scheme, scenario, epochs=12, seed=3)["backing"]

    base = run(world, params, "unpaid")["backing"]
    soft = mechanisms.Scheme(name="soft", budget_ada=200_000.0, pledge_leverage=5)
    assert backing(soft) > base
    assert backing(soft, hurdle=1e9) == base
    equal = mechanisms.Scheme(name="eq", alpha=0.0, budget_ada=200_000.0, pledge_leverage=5)
    assert backing(equal) == base
    capped = mechanisms.Scheme(name="capped", budget_ada=200_000.0, pledge_leverage=5, cap_ada=1.0)
    assert backing(capped) < backing(soft)


def test_pledge_added_is_limited_by_wealth_and_votes_with_the_drep(world, params):
    soft = mechanisms.Scheme(name="soft", budget_ada=200_000.0, pledge_leverage=5)

    def out(multiple):
        scenario = model.Scenario("s", pledge_response=0.5, pledge_wealth_multiple=multiple)
        return model.run(world, params, soft, scenario, epochs=12, seed=3)

    base, poor, free = run(world, params, "unpaid"), out(1.0), out(0.0)
    assert base["backing"] < poor["backing"] < free["backing"]
    assert free["drep_power"] > poor["drep_power"] > base["drep_power"]


def test_untraced_wealth_raises_what_a_drep_can_add_and_nothing_else(world, params):
    soft = mechanisms.Scheme(name="soft", budget_ada=200_000.0, pledge_leverage=1)

    def out(scheme, share):
        scenario = model.Scenario(
            "s", pledge_response=0.5, pledge_wealth_multiple=1.0, untraced_wealth_share=share
        )
        return model.run(world, params, scheme, scenario, epochs=12, seed=3)

    traced, rich = out(soft, 0.0), out(soft, 0.5)
    assert rich["backing"] > traced["backing"]
    assert out(soft, 1e-12)["backing"] == pytest.approx(traced["backing"])
    plain = mechanisms.Scheme(name="plain", budget_ada=200_000.0)  # no pledge in the rule
    assert out(plain, 0.5) == out(plain, 0.0)


def test_pledge_added_counts_in_the_ada_participation_is_measured_against(world, params):
    soft = mechanisms.Scheme(name="soft", budget_ada=200_000.0, pledge_leverage=1)
    scenario = model.Scenario("s", pledge_response=0.99)
    _, actions = model.run(world, params, soft, scenario, epochs=12, seed=3, trace=True)
    assert all(a["participation"] <= a["turnout"] + 1e-12 for a in actions)
