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
EPOCHS_PER_YEAR = mechanisms.ROUNDS_PER_YEAR
ENTRY_CAP = 8.0  # registrations can rise to at most this multiple of the historical rate
HAZARD_CAP = 10.0  # likewise for the re-delegation rate of an account
MOVE_BATCH = 100  # accounts that re-delegate before pass-through yields are recomputed
# Shares of its wealth a wealthy newcomer weighs self-delegating each epoch (0: stay out).
WHALE_GRID = np.concatenate([[0.0], np.geomspace(1 / 4096, 1.0, 25)])
WHALE_VOTE = 0.99  # it votes, with a rationale, on nearly every action: that is what pays
WHALE_SPLITS = (1, 2, 3, 5, 8, 13, 20)  # how many DReps it weighs running, up to its limit
WHALE_RETHINK = 6  # epochs between reconsidering how many DReps to run (about a month)


@dataclass
class Params:
    # Fitted to history by calibrate.py
    hazard_large: float  # per-epoch probability that a large account re-delegates
    hazard_small: float  # the same for accounts below `large_ada`
    theta: float  # a mover picks a DRep with weight (voting power + floor) ** theta ...
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
    power_floor_ada: float = 1000.0
    activity_window: int = 12
    drep_activity: int = 20
    delegator_min_ada: float = 100.0
    vote_cost_ada: float = 50.0
    rationale_cost_ada: float = 100.0
    max_yield_pp: float = 50.0
    payout_fee_ada: float = 0.002  # cost of one payment: a CIP-159 direct deposit

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
    # DReps add pledge when a rule rewards it: the share of the missing pledge
    # that a DRep closes over the programme.
    pledge_response: float = 0.0
    # ...but under a pledge soft cap only while the extra award it brings is at least this
    # yearly return on the ADA added,
    pledge_min_return: float = 0.0
    # ...and only until its pledge is this multiple of the ADA in its linked accounts:
    # how much more it could buy (0: no limit).
    pledge_wealth_multiple: float = 0.0
    # Own ADA that cannot be traced on chain: a DRep's holdings are taken to be at least
    # this share of its voting power at the start.
    untraced_wealth_share: float = 0.0
    # A wealthy newcomer with this much ADA (0: none). Each epoch it self-delegates the part
    # of it that earns the most over its hurdle on that ADA and the cost of voting, and
    # votes on everything; while nothing pays, it stays out.
    whale_ada: float = 0.0
    # Its hurdle: the yearly return it wants on ADA it self-delegates (None: the same
    # pledge_min_return as DReps). ADA it already holds may cost it far less.
    whale_min_return: float | None = None
    # The most DReps it may run, splitting its ADA equally among those it uses.
    whale_identities: int = 1


@dataclass
class World:
    """The starting state and the empirical pools a run resamples from."""

    epoch: int
    ids: list
    p: np.ndarray  # base probability of voting on an action
    q: np.ndarray  # probability that a vote carries a rationale
    last_active: np.ndarray  # epoch of the last vote or certificate
    pledge: np.ndarray  # the DRep's own ADA behind its votes: linked ADA delegated to itself
    holdings: np.ndarray  # ADA in the DRep's linked accounts, wherever delegated
    acct_ada: np.ndarray  # ADA represented by each account row (balance x weight)
    acct_count: np.ndarray  # accounts represented by each row
    acct_target: np.ndarray  # DRep slot, or NONE / ABSTAIN / NO_CONFIDENCE
    window: list  # recent epochs as (eligible, voted, rationale) count vectors
    closes: np.ndarray  # pool: actions closing per epoch
    actions: (
        np.ndarray
    )  # pool rows: threshold (nan = info action), support, abstain share, salience
    entrant_power: np.ndarray  # pool: first-epoch power of new DReps
    entrant_p: np.ndarray  # pool: vote propensity of recently registered DReps
    entrant_q: np.ndarray
    entrant_own: np.ndarray  # pool: pledge of new DReps, ADA
    exit_power: np.ndarray  # pool: power of DReps in their last epoch

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
    new_power = r_entry.choice(world.entrant_power, n_new)
    pick = r_entry.integers(0, len(world.entrant_p), n_new)
    n_exits = r_entry.poisson(params.exit_rate, epochs)
    exit_power = r_entry.choice(world.exit_power, max(1, int(n_exits.sum())))
    new_own = np.minimum(new_power, r_entry.choice(world.entrant_own, n_new))

    n0, a0 = len(world.p), len(world.acct_ada)
    # The wealthy newcomer's slots are the last ones; it has no account rows.
    whale = scenario.whale_identities if scenario.whale_ada > 0 else 0
    if scenario.whale_ada > 0 and not 1 <= whale <= max(WHALE_SPLITS):
        raise ValueError(f"whale_identities must be 1 to {max(WHALE_SPLITS)}")
    hurdle = (
        scenario.pledge_min_return
        if scenario.whale_min_return is None
        else scenario.whale_min_return
    )
    D, A = n0 + n_new + whale, a0 + n_new
    ws = np.arange(D - whale, D)
    registered = np.zeros(D, bool)
    registered[:n0] = True
    sure = np.full(whale, WHALE_VOTE)
    base_p = logit(np.concatenate([world.p, world.entrant_p[pick], sure]))
    base_q = logit(np.concatenate([world.q, world.entrant_q[pick], sure]))
    last_active = np.concatenate([world.last_active, np.zeros(n_new + whale)])
    pledge = np.concatenate([world.pledge, new_own, np.zeros(whale)])
    holdings = np.concatenate([world.holdings, new_own, np.zeros(whale)])
    if scenario.untraced_wealth_share > 0:
        start = np.concatenate(
            [_by_drep(world.acct_target, world.acct_ada, n0), new_power, np.zeros(whale)]
        )
        holdings = np.maximum(holdings, scenario.untraced_wealth_share * start)
    added = np.zeros(D)  # pledge added during the programme; it votes with the DRep
    acct_ada = np.concatenate([world.acct_ada, np.zeros(n_new)])
    acct_count = np.concatenate([world.acct_count, np.zeros(n_new)])
    target = np.concatenate([world.acct_target, np.full(n_new, NONE)])
    window = deque(
        (tuple(np.pad(x, (0, n_new + whale)) for x in row) for row in world.window),
        maxlen=params.activity_window,
    )
    activity, rationale_share = _activity(window, np.zeros(D), np.zeros(D))

    carry, entry_multiplier = 0.0, 1.0
    series, actions = [], []
    spent = paid = top10 = rounds = entrants = whale_paid = 0.0
    whale_k = 1  # how many DReps the newcomer runs with its ADA
    drep_total, acct_total = np.zeros(D), np.zeros(A)  # ADA earned over the programme
    top_up = 1 - (1 - scenario.pledge_response) ** (1 / epochs)
    action_i = candidate_i = exit_i = 0

    for t in range(epochs):
        epoch = world.epoch + 1 + t

        # 1. Balances drift and wobble.
        drift = np.where(target == ABSTAIN, params.drift_abstain, params.drift_drep)
        acct_ada = acct_ada * np.exp(
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
                acct_ada[account] = new_power[candidate_i]
                acct_count[account] = 1
                target[account] = slot
                entrants += 1
            candidate_i += 1
        delegated = _by_drep(target, acct_ada, D) + added
        for _ in range(n_exits[t]):
            live = np.flatnonzero(registered)
            gap = np.abs(np.log1p(delegated[live]) - np.log1p(exit_power[exit_i]))
            gone = live[np.argmin(gap)]
            registered[gone] = False
            target[target == gone] = NONE
            delegated[gone] = added[gone] = 0.0
            exit_i += 1
        live = np.flatnonzero(registered)

        # 3. The reward round, computed from what the chain shows at the start of the epoch.
        # A fee per action arrives with the actions that close, in lumps; behaviour (step 4)
        # follows the steady flow a DRep can count on: the fee times the average closings.
        pot = scheme.income(epochs, n_closing[t]) + carry
        seen = scheme.income(epochs, world.action_rate) + carry if scheme.fee_ada else pot
        delegators = np.zeros(len(live))  # read only through min_delegators or basis
        if scheme.min_delegators > 0 or scheme.basis == "delegators":
            counted = acct_count * (acct_ada >= params.delegator_min_ada * acct_count)
            delegators = _by_drep(target, counted, D)[live]
            mine = ws[registered[ws]]  # the last live slots
            if len(mine):  # its own ADA, in as many accounts as it likes
                delegators[-len(mine) :] += np.maximum(added[mine] / params.delegator_min_ada, 1)
        rnd = mechanisms.Round(
            power=delegated[live],
            activity=activity[live],
            rationale=rationale_share[live],
            delegators=delegators,
            pledge=pledge[live],
            actions=world.action_rate,
        )
        award, yields = mechanisms.allocate(scheme, rnd, pot)
        received = award + yields * rnd.power
        carry = pot - received.sum()
        mine = ws[registered[ws]]  # the last live slots: awards, and yield on its own ADA
        if len(mine):
            whale_paid += (award[-len(mine) :] + yields[-len(mine) :] * added[mine]).sum()
        drep_total[live] += award
        if scheme.delegator_share > 0:  # otherwise every yield is zero
            held = target >= 0
            yield_by_slot = np.zeros(D)
            yield_by_slot[live] = yields
            acct_total[held] += yield_by_slot[target[held]] * acct_ada[held]
        if received.sum() > 0:
            spent += received.sum()
            paid += (received > 0).sum()
            top10 += np.sort(received)[-10:].sum() / received.sum()
            rounds += 1
        if seen != pot:
            award, yields = mechanisms.allocate(scheme, rnd, seen)

        # 4. DReps respond to what one more vote is worth to them.
        shift, shift_rationale = np.zeros(D), np.zeros(D)
        entry_multiplier = 1.0
        reach = np.ones(D)
        upkeep = params.vote_cost_ada * world.action_rate  # voting on everything, per epoch
        if seen > 0 and scenario.reinvest_response > 0:
            reach[live] = np.power(1 + award / upkeep, scenario.reinvest_response)
        if seen > 0 and scheme.pledge_leverage > 0 and top_up > 0:
            # DReps whose voting power is capped by their pledge add some of what is
            # missing. Under a pledge soft cap, only what counts for rewards is missing, and a
            # DRep adds it only while the extra award pays the minimum return on it. Either
            # way it adds no more than it could buy, and the ADA added votes with it.
            wanted = (
                delegated[live] if scheme.hard_cap else np.minimum(delegated[live], scheme.cap_ada)
            )
            step = top_up * np.maximum(wanted / scheme.pledge_leverage - pledge[live], 0)
            if scenario.pledge_wealth_multiple > 0:
                room = scenario.pledge_wealth_multiple * holdings[live] - pledge[live]
                step = np.minimum(step, np.maximum(room, 0))
            gain = mechanisms.pledge_gain(scheme, rnd, seen, step) * EPOCHS_PER_YEAR
            pays = (gain > 0) & (gain >= scenario.pledge_min_return * step)
            step = step * (pays | scheme.hard_cap)
            if not scheme.hard_cap:
                # A DRep that adds nothing takes back some of what it added, at the same
                # pace, while that part earns less than the minimum return on it.
                out = top_up * added[live] * (step == 0) * (live < D - whale)
                if out.any():
                    loss = -mechanisms.pledge_gain(scheme, rnd, seen, -out) * EPOCHS_PER_YEAR
                    step = step - out * (loss < scenario.pledge_min_return * out)
            pledge[live] += step
            added[live] += step
            delegated[live] += step
        if whale and seen > 0:
            # The wealthy newcomer re-weighs how much of its ADA to self-delegate, and now
            # and then over how many DReps to split it. Its DReps keep their delegators.
            others = _without_last(rnd, int(registered[ws].sum()))
            from_others = delegated[ws] - added[ws]
            counts = (
                [k for k in WHALE_SPLITS if k <= whale] if t % WHALE_RETHINK == 0 else [whale_k]
            )
            best, best_k, best_net = 0.0, whale_k, 0.0
            for k in counts:
                used = registered[ws] | (np.arange(whale) < k)
                for own in scenario.whale_ada * WHALE_GRID[1:]:
                    each = np.where(np.arange(whale) < k, own / k, 0.0)[used]
                    earned = _entrant_take(
                        scheme,
                        others,
                        seen,
                        from_others[used] + each,
                        each,
                        params.delegator_min_ada,
                    )
                    net = (earned - upkeep * used.sum()) * EPOCHS_PER_YEAR - hurdle * own
                    if net > best_net:
                        best, best_k, best_net = own, k, net
            whale_k = best_k
            each = np.where(np.arange(whale) < whale_k, best / whale_k, 0.0) * (best > 0)
            new = ws[(each > 0) & ~registered[ws]]
            registered[new] = True
            last_active[new] = epoch
            entrants += len(new)
            delegated[ws] += each - added[ws]
            pledge[ws] = added[ws] = each  # they take part in the round from the next epoch
        if seen > 0 and scenario.drep_response > 0:
            value = mechanisms.vote_value(scheme, rnd, seen)
            shift[live] = scenario.drep_response * np.log1p(value / params.vote_cost_ada)
            if scheme.rationale_bonus > 0:
                extra = value * scheme.rationale_bonus / (1 + scheme.rationale_bonus)
                shift_rationale[live] = scenario.drep_response * np.log1p(
                    extra / params.rationale_cost_ada
                )
            newcomer = _newcomer_award(
                scheme, rnd, seen, float(np.median(world.entrant_power)), world.entrant_own
            )
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
            acct_ada,
            acct_count,
            delegated,
            registered,
            activity,
            yield_pp,
            reach,
        )
        delegated = _by_drep(target, acct_ada, D) + added
        power = np.where(registered, mechanisms.voting_power(scheme, delegated, pledge), 0.0)
        everything = acct_ada.sum() + added.sum()  # all delegated ADA, pledge top-ups included

        # 6. Actions closing this epoch are voted on.
        eligible = registered.astype(float)
        voted_n, rationale_n = np.zeros(D), np.zeros(D)
        no_confidence = acct_ada[target == NO_CONFIDENCE].sum()
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
                    participation=power[votes].sum() / everything,
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
        actors = live_power  # concentration counts the newcomer's DReps as one
        if whale and registered[ws].any():
            own_slots = registered.copy()
            own_slots[ws] = False
            actors = np.append(power[own_slots], power[ws[registered[ws]]].sum())
        series.append(
            dict(
                epoch=epoch,
                dreps=int((live_power > 0).sum()),
                drep_power=live_power.sum(),
                tau50=tau(actors, 0.5),
                tau67=tau(actors, 0.67),
                effective_n=effective_number(actors),
                abstain=acct_ada[target == ABSTAIN].sum(),
                no_confidence=no_confidence,
                represented_share=power[registered & (activity >= 0.5)].sum() / everything,
                backing=np.minimum(live_power, pledge[registered]).sum() / live_power.sum(),
                voting_dreps=int((registered & (activity >= 0.5)).sum()),
                whale_pledge=float(added[ws].sum()),
                whale_dreps=int((added[ws] > 0).sum()),
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
    # Delivery: one CIP-159 direct deposit per recipient of anything at all, however small.
    payments = (drep_total > 0).sum() + acct_count[acct_total > 0].sum()
    return dict(
        participation=action_mean("participation"),
        backing=late_mean("backing"),
        annual_cost_ada=float(
            (spent + payments * params.payout_fee_ada) * EPOCHS_PER_YEAR / epochs
        ),
        payments=float(payments),
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
        whale_take=whale_paid / spent if spent > 0 else 0.0,
        whale_pledge=late_mean("whale_pledge"),
        whale_dreps=late_mean("whale_dreps"),
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


def _without_last(rnd, n):
    if n == 0:
        return rnd
    return mechanisms.Round(
        power=rnd.power[:-n],
        activity=rnd.activity[:-n],
        rationale=rnd.rationale[:-n],
        delegators=rnd.delegators[:-n],
        pledge=rnd.pledge[:-n],
        actions=rnd.actions,
    )


def _entrant_take(scheme, rnd, pot, power, own, account_ada):
    """What more DReps that vote on everything, with a rationale, earn together per round:
    their awards and the delegator yield on their own ADA. Each holds its `own` ADA itself,
    in as many accounts as it likes, so a delegator minimum does not stop it."""
    power, own = np.atleast_1d(power), np.atleast_1d(own)
    n = len(power)
    plus = mechanisms.Round(
        power=np.append(rnd.power, power),
        activity=np.append(rnd.activity, np.ones(n)),
        rationale=np.append(rnd.rationale, np.ones(n)),
        delegators=np.append(rnd.delegators, np.maximum(own / account_ada, 1.0)),
        pledge=np.append(rnd.pledge, own),
        actions=rnd.actions,
    )
    award, yields = mechanisms.allocate(scheme, plus, pot)
    return float((award[-n:] + yields[-n:] * own).sum())


def _newcomer_award(scheme, rnd, pot, delegated, own):
    """Per-epoch award of one extra, fully active DRep of typical new-DRep size."""
    plus = mechanisms.Round(
        power=np.append(rnd.power, delegated),
        activity=np.append(rnd.activity, 1.0),
        rationale=np.append(rnd.rationale, 0.0),
        delegators=np.append(rnd.delegators, 1.0),
        pledge=np.append(rnd.pledge, min(delegated, float(np.median(own)))),
        actions=rnd.actions,
    )
    return float(mechanisms.allocate(scheme, plus, pot)[0][-1])


def _move(
    params,
    scheme,
    scenario,
    rng,
    target,
    acct_ada,
    acct_count,
    delegated,
    registered,
    activity,
    yield_pp,
    reach,
):
    """Each account re-delegates with a small probability and picks a new destination.

    Large and small accounts have their own fitted move rate and always-abstain share.
    """
    u_move, u_pick = rng.random((2, len(target)))
    unit = acct_ada / np.maximum(acct_count, 1)  # balance of one account in the row
    large = unit >= params.large_ada
    hazard = np.where(large, params.hazard_large, params.hazard_small)
    paying = yield_pp > 0
    responsive = scenario.delegator_response > 0 and paying.any()
    if responsive:
        # A typical paying DRep's yield, against what the account earns where it is now.
        reference = np.average(yield_pp[paying], weights=delegated[paying] + 1e-9)
        current = np.where(target >= 0, yield_pp[np.maximum(target, 0)], 0.0)
        gain = np.clip(reference - current, 0, params.max_yield_pp)
        hazard = hazard * np.minimum(HAZARD_CAP, 1 + scenario.delegator_response * gain)
    moving = (u_move < hazard) & (acct_ada > 0)
    if not moving.any():
        return target

    live = np.flatnonzero(registered)
    base = (
        np.power(delegated[live] + params.power_floor_ada, params.theta)
        * np.exp(params.beta_activity * activity[live])
        * reach[live]
    )
    base = base / base.sum()
    codes = np.concatenate([[ABSTAIN, NO_CONFIDENCE], live])
    abstain = np.where(large, params.abstain_large, params.abstain_small)
    target = target.copy()

    if not (responsive and scheme.delegator_mode != "flat"):
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

    # Pass-through or per-DRep yield: a DRep's delegator award is shared by everyone
    # delegating to it, so each arrival lowers the yield for the next. Movers are taken in small random
    # batches and the DRep totals are updated between batches.
    movers = np.flatnonzero(moving)
    movers = movers[np.argsort(u_move[movers] / hazard[movers])]
    position = np.full(len(registered), -1)
    position[live] = np.arange(len(live))
    power_now = delegated[live].copy()
    pool = yield_pp[live] * power_now  # annual percentage points x ADA on each DRep
    pays = np.flatnonzero(pool > 0)  # elsewhere nothing is offered and the boost is exp(0) = 1
    for chunk in np.array_split(movers, max(1, len(movers) // MOVE_BATCH)):
        weights = np.empty((len(chunk), len(codes)))
        weights[:, 0] = abstain[chunk]
        weights[:, 1] = params.no_confidence_share
        to_dreps = weights[:, 2:]
        np.multiply(
            (1 - abstain[chunk] - params.no_confidence_share)[:, None], base[None, :], out=to_dreps
        )
        offered = pool[None, pays] / (power_now[None, pays] + unit[chunk][:, None])
        to_dreps[:, pays] *= np.exp(
            scenario.delegator_response * np.minimum(offered, params.max_yield_pp)
        )
        cdf = np.cumsum(weights, axis=1)
        choice = (cdf < (u_pick[chunk] * cdf[:, -1])[:, None]).sum(axis=1)
        choice = np.minimum(choice, len(codes) - 1)
        left = position[np.maximum(target[chunk], 0)]
        left = np.where(target[chunk] >= 0, left, -1)
        np.subtract.at(power_now, left[left >= 0], acct_ada[chunk][left >= 0])
        joined = choice >= 2
        np.add.at(power_now, choice[joined] - 2, acct_ada[chunk][joined])
        target[chunk] = codes[choice]
    return target
