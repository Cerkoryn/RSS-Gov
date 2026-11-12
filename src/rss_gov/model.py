"""A small stochastic model of DRep voting and delegation, vectorised over DReps and accounts.

One run is one possible future of `epochs` epochs under one reward scheme. Everything about
the unpaid world is fitted to chain history (`calibrate.py`). How strongly people react to
money is not knowable from history, so it enters as an explicit `Scenario`.

Runs with the same seed share their random draws across schemes (common random numbers),
so the difference between two schemes is much less noisy than either run alone.
"""

from collections import deque
from dataclasses import asdict, dataclass

import numpy as np

from rss_gov import mechanisms
from rss_gov.metrics import effective_number, tau

NONE, ABSTAIN, NO_CONFIDENCE = -1, -2, -3  # account targets that are not a DRep slot
EPOCHS_PER_YEAR = 73
ENTRY_CAP = 8.0  # registrations can rise to at most this multiple of the historical rate
HAZARD_CAP = 10.0  # likewise for the re-delegation rate of an account
MOVE_BATCH = 100  # accounts that re-delegate before pass-through yields are recomputed


@dataclass
class Params:
    # Fitted to history by calibrate.py
    hazard_large: float  # per-epoch probability that a large account re-delegates
    hazard_small: float  # the same for accounts below `large_ada`
    theta: float  # a mover picks a DRep with weight (stake + floor) ** theta ...
    beta_activity: float  # ... times exp(beta * the DRep's recent vote rate)
    abstain_large: float  # share of large-account moves that go to always-abstain
    abstain_small: float
    no_confidence_share: float
    sigma_balance: float  # per-epoch log-sd of an account balance
    drift_drep: float  # per-epoch log growth of balances delegated to DReps
    drift_abstain: float  # the same for always-abstain balances
    entry_rate: float  # DRep registrations per epoch
    exit_rate: float  # DRep retirements per epoch
    half_life: float  # epochs; recency weighting of a DRep's vote history
    # Conventions and assumptions (config.yaml)
    prior_strength: float = 2.0
    forecast_lag: int = 18  # epochs ahead that fitted vote rates must hold for
    large_ada: float = 100_000.0
    stake_floor_ada: float = 1000.0
    activity_window: int = 12
    drep_activity: int = 20
    delegator_min_ada: float = 100.0
    vote_cost_ada: float = 50.0
    rationale_cost_ada: float = 100.0
    max_yield_pp: float = 50.0
    min_payout_ada: float = 5.0  # smaller programme totals are not worth a transaction
    payout_fee_ada: float = 0.3  # cost of one payment output

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Scenario:
    """How strongly behaviour reacts to rewards. All zero means rewards change nothing.

    Each field is a separate channel, so that a scheme's results can be traced to the
    assumption they depend on.
    """

    name: str = "no_response"
    # DReps vote more: logit shift in vote probability per log(1 + reward per vote / cost).
    drep_response: float = 0.0
    # Delegators chase yield: mover log-weight per percentage point of annual yield.
    delegator_response: float = 0.0
    # DReps turn awards into reach (staff, tooling, promotion): a DRep's weight among
    # movers is multiplied by (1 + award / upkeep) ** reinvest_response.
    reinvest_response: float = 0.0
    # DReps add own stake when a rule rewards it: the share of the missing own stake
    # that a DRep closes over the programme.
    pledge_response: float = 0.0


@dataclass
class World:
    """The starting state and the empirical pools a run resamples from."""

    epoch: int
    ids: list
    p: np.ndarray  # base probability of voting on an action
    q: np.ndarray  # probability that a vote carries a rationale
    last_active: np.ndarray  # epoch of the last vote or certificate
    pledge: np.ndarray  # the DRep's own stake as far as chain data shows it, ADA
    acct_stake: np.ndarray  # ADA represented by each account row (balance x weight)
    acct_count: np.ndarray  # accounts represented by each row
    acct_target: np.ndarray  # DRep slot, or NONE / ABSTAIN / NO_CONFIDENCE
    window: list  # recent epochs as (eligible, voted, rationale) count vectors
    closes: np.ndarray  # pool: actions closing per epoch
    actions: (
        np.ndarray
    )  # pool rows: threshold (nan = info action), support, abstain share, salience
    entrant_stake: np.ndarray  # pool: first-epoch power of new DReps
    entrant_p: np.ndarray  # pool: vote propensity of recently registered DReps
    entrant_q: np.ndarray
    exit_stake: np.ndarray  # pool: power of DReps in their last epoch

    @property
    def action_rate(self):
        return float(max(self.closes.mean(), 0.05))


def logit(x):
    return np.log(x / (1 - x))


def expit(x):
    return 1 / (1 + np.exp(-x))


def run(world, params, scheme, scenario=Scenario(), epochs=36, seed=0, trace=False):
    """Simulate one future. Returns summary metrics, or the per-epoch trace on request."""
    streams = np.random.SeedSequence(seed).spawn(5)
    r_action, r_vote, r_move, r_balance, r_entry = (np.random.default_rng(s) for s in streams)

    # Everything random about the outside world is drawn up front, identically per seed.
    n_closing = r_action.choice(world.closes, epochs).astype(int)
    drawn = world.actions[r_action.integers(0, len(world.actions), n_closing.sum())]
    n_candidates = r_entry.poisson(params.entry_rate * ENTRY_CAP, epochs)
    n_new = int(n_candidates.sum())
    marks = r_entry.random(n_new)
    new_stake = r_entry.choice(world.entrant_stake, n_new)
    pick = r_entry.integers(0, len(world.entrant_p), n_new)
    n_exits = r_entry.poisson(params.exit_rate, epochs)
    exit_stake = r_entry.choice(world.exit_stake, max(1, int(n_exits.sum())))

    n0, a0 = len(world.p), len(world.acct_stake)
    D, A = n0 + n_new, a0 + n_new
    registered = np.zeros(D, bool)
    registered[:n0] = True
    base_p = logit(np.concatenate([world.p, world.entrant_p[pick]]))
    base_q = logit(np.concatenate([world.q, world.entrant_q[pick]]))
    last_active = np.concatenate([world.last_active, np.zeros(n_new)])
    pledge = np.concatenate([world.pledge, new_stake])
    acct_stake = np.concatenate([world.acct_stake, np.zeros(n_new)])
    acct_count = np.concatenate([world.acct_count, np.zeros(n_new)])
    target = np.concatenate([world.acct_target, np.full(n_new, NONE)])
    window = deque(
        (tuple(np.pad(x, (0, n_new)) for x in row) for row in world.window),
        maxlen=params.activity_window,
    )
    activity, rationale_share = _activity(window, np.zeros(D), np.zeros(D))

    budget_per_epoch = scheme.budget_ada / epochs if scheme.paid else 0.0
    carry, entry_multiplier = 0.0, 1.0
    series, actions = [], []
    spent = paid = top10 = rounds = entrants = 0.0
    drep_total, acct_total = np.zeros(D), np.zeros(A)  # ADA earned over the programme
    top_up = 1 - (1 - scenario.pledge_response) ** (1 / epochs)
    action_i = candidate_i = exit_i = 0

    for t in range(epochs):
        epoch = world.epoch + 1 + t

        # 1. Balances drift and wobble.
        drift = np.where(target == ABSTAIN, params.drift_abstain, params.drift_drep)
        acct_stake = acct_stake * np.exp(
            drift
            + params.sigma_balance * r_balance.standard_normal(A)
            - 0.5 * params.sigma_balance**2
        )

        # 2. Registrations (thinned from a fixed candidate list) and retirements.
        for _ in range(n_candidates[t]):
            if marks[candidate_i] < entry_multiplier / ENTRY_CAP:
                slot, account = n0 + candidate_i, a0 + candidate_i
                registered[slot] = True
                last_active[slot] = epoch
                acct_stake[account] = new_stake[candidate_i]
                acct_count[account] = 1
                target[account] = slot
                entrants += 1
            candidate_i += 1
        stake = _by_drep(target, acct_stake, D)
        for _ in range(n_exits[t]):
            live = np.flatnonzero(registered)
            gap = np.abs(np.log1p(stake[live]) - np.log1p(exit_stake[exit_i]))
            gone = live[np.argmin(gap)]
            registered[gone] = False
            target[target == gone] = NONE
            stake[gone] = 0.0
            exit_i += 1
        live = np.flatnonzero(registered)

        # 3. The reward round, computed from what the chain shows at the start of the epoch.
        pot = budget_per_epoch + carry
        delegators = np.zeros(len(live))  # read by a rule only through min_delegators
        if scheme.min_delegators > 0:
            counted = acct_count * (acct_stake >= params.delegator_min_ada * acct_count)
            delegators = _by_drep(target, counted, D)[live]
        rnd = mechanisms.Round(
            stake=stake[live],
            activity=activity[live],
            rationale=rationale_share[live],
            delegators=delegators,
            pledge=pledge[live],
        )
        award, yields = mechanisms.allocate(scheme, rnd, pot)
        received = award + yields * rnd.stake
        carry = pot - received.sum()
        drep_total[live] += award
        if scheme.delegator_share > 0:  # otherwise every yield is zero
            held = target >= 0
            yield_by_slot = np.zeros(D)
            yield_by_slot[live] = yields
            acct_total[held] += yield_by_slot[target[held]] * acct_stake[held]
        if received.sum() > 0:
            spent += received.sum()
            paid += (received > 0).sum()
            top10 += np.sort(received)[-10:].sum() / received.sum()
            rounds += 1

        # 4. DReps respond to what one more vote is worth to them.
        shift, shift_rationale = np.zeros(D), np.zeros(D)
        entry_multiplier = 1.0
        reach = np.ones(D)
        upkeep = params.vote_cost_ada * world.action_rate  # voting on everything, per epoch
        if pot > 0 and scenario.reinvest_response > 0:
            reach[live] = np.power(1 + award / upkeep, scenario.reinvest_response)
        if pot > 0 and scheme.pledge_leverage > 0 and top_up > 0:
            # DReps whose counted stake is limited by their own stake add some: paid DReps
            # under a reward cap, every DRep when voting power itself is capped.
            missing = np.maximum(stake[live] / scheme.pledge_leverage - pledge[live], 0)
            pledge[live] += top_up * missing * ((award > 0) | scheme.hard_cap)
        if pot > 0 and scenario.drep_response > 0:
            value = mechanisms.vote_value(scheme, rnd, pot, world.action_rate)
            shift[live] = scenario.drep_response * np.log1p(value / params.vote_cost_ada)
            if scheme.rationale_bonus > 0:
                extra = value * scheme.rationale_bonus / (1 + scheme.rationale_bonus)
                shift_rationale[live] = scenario.drep_response * np.log1p(
                    extra / params.rationale_cost_ada
                )
            newcomer = _newcomer_award(scheme, rnd, pot, float(np.median(world.entrant_stake)))
            entry_multiplier = min(
                ENTRY_CAP, 1 + scenario.drep_response * np.log1p(newcomer / upkeep)
            )

        # 5. Accounts re-delegate.
        yield_pp = np.zeros(D)
        yield_pp[live] = yields * EPOCHS_PER_YEAR * 100
        target = _move(
            params,
            scheme,
            scenario,
            r_move,
            target,
            acct_stake,
            acct_count,
            stake,
            registered,
            activity,
            yield_pp,
            reach,
        )
        stake = _by_drep(target, acct_stake, D)
        power = np.where(registered, mechanisms.voting_power(scheme, stake, pledge), 0.0)

        # 6. Actions closing this epoch are voted on.
        eligible = registered.astype(float)
        voted_n, rationale_n = np.zeros(D), np.zeros(D)
        no_confidence = acct_stake[target == NO_CONFIDENCE].sum()
        for _ in range(n_closing[t]):
            threshold, support, abstain, salience = drawn[action_i]
            u_vote, u_rationale, u_choice = r_vote.random((3, D))
            votes = registered & (u_vote < expit(base_p + shift + salience))
            with_rationale = votes & (u_rationale < expit(base_q + shift_rationale))
            abstains = votes & (u_choice < abstain)
            yes = votes & ~abstains & (u_choice < abstain + (1 - abstain) * support)
            active = registered & ((epoch - last_active <= params.drep_activity) | votes)
            denominator = power[active & ~abstains].sum() + no_confidence
            ratified = bool(
                not np.isnan(threshold)
                and denominator > 0
                and power[yes].sum() / denominator >= threshold
            )
            actions.append(
                dict(
                    epoch=epoch,
                    turnout=power[votes].sum() / max(power.sum(), 1e-9),
                    participation=power[votes].sum() / acct_stake.sum(),
                    turnout_active=power[votes].sum() / max(power[active].sum(), 1e-9),
                    ballots=int(votes.sum()),
                    rationales=int(with_rationale.sum()),
                    binding=not np.isnan(threshold),
                    supported=bool(support >= threshold),
                    ratified=ratified,
                )
            )
            last_active[votes] = epoch
            voted_n += votes
            rationale_n += with_rationale
            action_i += 1
        window.append((eligible * n_closing[t], voted_n, rationale_n))
        activity, rationale_share = _activity(window, activity, rationale_share)

        # 7. Where things stand at the end of the epoch.
        live_power = power[registered]
        everything = acct_stake.sum()
        series.append(
            dict(
                epoch=epoch,
                dreps=int((live_power > 0).sum()),
                drep_power=live_power.sum(),
                tau50=tau(live_power, 0.5),
                tau67=tau(live_power, 0.67),
                effective_n=effective_number(live_power),
                abstain=acct_stake[target == ABSTAIN].sum(),
                no_confidence=no_confidence,
                represented_share=power[registered & (activity >= 0.5)].sum() / everything,
                backing=np.minimum(live_power, pledge[registered]).sum() / live_power.sum(),
                voting_dreps=int((registered & (activity >= 0.5)).sum()),
                shares=None,
            )
        )
        if trace:
            series[-1]["shares"] = dict(
                zip(np.flatnonzero(registered), live_power / live_power.sum())
            )

    if trace:
        return series, actions
    for row in series:
        row.pop("shares")
    late = series[epochs // 2 :]

    def late_mean(key):
        return float(np.mean([row[key] for row in late]))

    def action_mean(key, where=lambda a: True):
        values = [a[key] for a in actions if where(a)]
        return float(np.mean(values)) if values else np.nan

    ballots = sum(a["ballots"] for a in actions)
    # Delivery: one payment per recipient whose programme total is worth sending.
    claim = acct_total / np.maximum(acct_count, 1)
    payable = (claim >= params.min_payout_ada) & (acct_count > 0)
    payments = (drep_total >= params.min_payout_ada).sum() + acct_count[payable].sum()
    dust = drep_total[drep_total < params.min_payout_ada].sum() + acct_total[~payable].sum()
    return dict(
        participation=action_mean("participation"),
        backing=late_mean("backing"),
        annual_cost_ada=float(
            (spent + payments * params.payout_fee_ada) * EPOCHS_PER_YEAR / epochs
        ),
        payments=float(payments),
        dust_share=float(dust / spent) if spent > 0 else 0.0,
        turnout=action_mean("turnout"),
        turnout_active=action_mean("turnout_active"),
        tau67=late_mean("tau67"),
        tau50=late_mean("tau50"),
        effective_n=late_mean("effective_n"),
        represented_share=late_mean("represented_share"),
        supported_ratified=action_mean("ratified", lambda a: a["binding"] and a["supported"]),
        ratified_share=action_mean("ratified", lambda a: a["binding"]),
        rationale_rate=sum(a["rationales"] for a in actions) / max(ballots, 1),
        ballots_per_action=ballots / max(len(actions), 1),
        ballots=float(ballots),
        voting_dreps=late_mean("voting_dreps"),
        dreps=late_mean("dreps"),
        drep_power=late_mean("drep_power"),
        abstain=late_mean("abstain"),
        entrants=float(entrants),
        spent_ada=float(spent),
        paid_per_round=paid / max(rounds, 1),
        top10_reward_share=top10 / rounds if rounds else np.nan,
    )


def _by_drep(target, values, size):
    """Sum per DRep slot. The codes below zero are shifted into bins of their own and dropped,
    which sums every slot in the same order as selecting its rows first, without the copy."""
    shift = -NO_CONFIDENCE  # the lowest code
    return np.bincount(target + shift, weights=values, minlength=size + shift)[shift:]


def _activity(window, activity, rationale_share):
    """Vote rate over the window. DReps with no closed action in it keep their last value."""
    if not window:
        return activity, rationale_share
    eligible = sum(row[0] for row in window)
    voted = sum(row[1] for row in window)
    with_rationale = sum(row[2] for row in window)
    seen = eligible > 0
    activity = np.where(seen, voted / np.maximum(eligible, 1), activity)
    rationale_share = np.where(voted > 0, with_rationale / np.maximum(voted, 1), rationale_share)
    return np.minimum(activity, 1.0), rationale_share


def _newcomer_award(scheme, rnd, pot, stake):
    """Per-epoch award of one extra, fully active DRep of typical new-DRep size."""
    plus = mechanisms.Round(
        stake=np.append(rnd.stake, stake),
        activity=np.append(rnd.activity, 1.0),
        rationale=np.append(rnd.rationale, 0.0),
        delegators=np.append(rnd.delegators, 1.0),
        pledge=np.append(rnd.pledge, stake),
    )
    return float(mechanisms.allocate(scheme, plus, pot)[0][-1])


def _move(
    params,
    scheme,
    scenario,
    rng,
    target,
    acct_stake,
    acct_count,
    stake,
    registered,
    activity,
    yield_pp,
    reach,
):
    """Each account re-delegates with a small probability and picks a new destination.

    Large and small accounts have their own fitted move rate and always-abstain share.
    """
    u_move, u_pick = rng.random((2, len(target)))
    unit = acct_stake / np.maximum(acct_count, 1)  # balance of one account in the row
    large = unit >= params.large_ada
    hazard = np.where(large, params.hazard_large, params.hazard_small)
    paying = yield_pp > 0
    responsive = scenario.delegator_response > 0 and paying.any()
    if responsive:
        # A typical paying DRep's yield, against what the account earns where it is now.
        reference = np.average(yield_pp[paying], weights=stake[paying] + 1e-9)
        current = np.where(target >= 0, yield_pp[np.maximum(target, 0)], 0.0)
        gain = np.clip(reference - current, 0, params.max_yield_pp)
        hazard = hazard * np.minimum(HAZARD_CAP, 1 + scenario.delegator_response * gain)
    moving = (u_move < hazard) & (acct_stake > 0)
    if not moving.any():
        return target

    live = np.flatnonzero(registered)
    base = (
        np.power(stake[live] + params.stake_floor_ada, params.theta)
        * np.exp(params.beta_activity * activity[live])
        * reach[live]
    )
    base = base / base.sum()
    codes = np.concatenate([[ABSTAIN, NO_CONFIDENCE], live])
    abstain = np.where(large, params.abstain_large, params.abstain_small)
    target = target.copy()

    if not (responsive and scheme.delegator_mode == "passthrough"):
        # Every mover of a size class faces the same odds. Under a flat delegator yield
        # the paying DReps are simply more attractive by a common factor.
        if responsive:
            capped = np.minimum(yield_pp[live], params.max_yield_pp)
            base = base * np.exp(scenario.delegator_response * capped)
        for is_large in (True, False):
            movers = np.flatnonzero(moving & (large == is_large))
            share = params.abstain_large if is_large else params.abstain_small
            special = np.array([share, params.no_confidence_share])
            cdf = np.cumsum(np.concatenate([special, (1 - special.sum()) * base]))
            choice = np.searchsorted(cdf / cdf[-1], u_pick[movers], side="right")
            target[movers] = codes[np.minimum(choice, len(codes) - 1)]
        return target

    # Pass-through yield: a DRep's delegator award is shared by everyone delegating to it,
    # so each arrival lowers the yield for the next. Movers are taken in small random
    # batches and the DRep totals are updated between batches.
    movers = np.flatnonzero(moving)
    movers = movers[np.argsort(u_move[movers] / hazard[movers])]
    position = np.full(len(registered), -1)
    position[live] = np.arange(len(live))
    stake_now = stake[live].copy()
    pool = yield_pp[live] * stake_now  # annual percentage points x ADA on each DRep
    pays = np.flatnonzero(pool > 0)  # elsewhere nothing is offered and the boost is exp(0) = 1
    for chunk in np.array_split(movers, max(1, len(movers) // MOVE_BATCH)):
        weights = np.empty((len(chunk), len(codes)))
        weights[:, 0] = abstain[chunk]
        weights[:, 1] = params.no_confidence_share
        to_dreps = weights[:, 2:]
        np.multiply(
            (1 - abstain[chunk] - params.no_confidence_share)[:, None], base[None, :], out=to_dreps
        )
        offered = pool[None, pays] / (stake_now[None, pays] + unit[chunk][:, None])
        to_dreps[:, pays] *= np.exp(
            scenario.delegator_response * np.minimum(offered, params.max_yield_pp)
        )
        cdf = np.cumsum(weights, axis=1)
        choice = (cdf < (u_pick[chunk] * cdf[:, -1])[:, None]).sum(axis=1)
        choice = np.minimum(choice, len(codes) - 1)
        left = position[np.maximum(target[chunk], 0)]
        left = np.where(target[chunk] >= 0, left, -1)
        np.subtract.at(stake_now, left[left >= 0], acct_stake[chunk][left >= 0])
        joined = choice >= 2
        np.add.at(stake_now, choice[joined] - 2, acct_stake[chunk][joined])
        target[chunk] = codes[choice]
    return target
