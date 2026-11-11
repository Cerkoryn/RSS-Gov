"""Fit the unpaid model to chain history and test it on epochs it has not seen.

Nothing here knows about reward schemes. The output is a `Params` for the behaviour of
DReps and delegators as observed so far, plus a validation report: the model is started
from the observed state some epochs back and must reproduce what actually happened next.
"""

import numpy as np
import pandas as pd

from rss_gov import mechanisms, model
from rss_gov.dataset import ABSTAIN, NO_CONFIDENCE

FIRST_VOTING_EPOCH = 540  # DRep votes started counting with the Plomin hard fork (epoch 537)
HALF_LIVES = (5, 10, 20, 40, 1000)
POOL_EPOCHS = 80  # how far back the empirical pools for actions and DRep entry/exit reach


# ---------------------------------------------------------------- voting behaviour


def propensity(data, votes_until, power_epoch, half_life, strength):
    """Each DRep's probability of voting on an action, from votes on actions closed so far.

    A recency-weighted vote rate, shrunk toward the rate of DReps of similar size. Returns
    (vote probability, rationale probability) aligned with `data.power.columns`.
    """
    actions = data.closed(FIRST_VOTING_EPOCH, votes_until)
    eligible, voted, rationale = data.ballots(actions)
    weight = 0.5 ** ((votes_until - actions.close.values) / half_life)
    n, v, r = eligible @ weight, voted @ weight, rationale @ weight
    power = data.power.loc[power_epoch].values
    overall = v.sum() / max(n.sum(), 1e-9)
    prior = np.full(len(power), overall)
    held = np.flatnonzero(power > 0)
    decile = power[held].argsort().argsort() * 10 // max(len(held), 1)
    for k in range(10):
        members = held[decile == k]
        if n[members].sum() > 0:
            prior[members] = v[members].sum() / n[members].sum()
    p = (strength * prior + v) / (strength + n)
    q = (strength * r.sum() / max(v.sum(), 1e-9) + r) / (strength + v)
    return np.clip(p, 0.002, 0.998), np.clip(q, 0.002, 0.998)


def ahead(data, first, last, half_life, strength, lag):
    """Predict every action closing in (first, last] from votes cast `lag` epochs earlier.

    The lag is the distance the model has to forecast over: vote rates fitted today are
    applied to actions that close during the programme. `salience` is the common logit
    shift that reconciles the forecast with the turnout the action really drew; it carries
    both how much attention the action got and how far vote rates wandered over the lag.
    """
    key = (id(data), first, last, half_life, strength, lag)
    if key in _AHEAD:
        return _AHEAD[key]
    rows = []
    for epoch in sorted(data.closed(first + 1, last).close.unique().astype(int)):
        p, _ = propensity(data, epoch - lag, epoch, half_life, strength)
        actions = data.closed(epoch, epoch)
        eligible, voted, _ = data.ballots(actions)
        power = data.power.loc[epoch].values
        for j, proposal_id in enumerate(actions.proposal_id):
            e, v = eligible[:, j], voted[:, j]
            actual = power[v].sum() / power[e].sum()
            rows.append(
                dict(
                    proposal_id=proposal_id,
                    epoch=epoch,
                    log_loss=-np.mean(np.where(v[e], np.log(p[e]), np.log(1 - p[e]))),
                    predicted=float((power[e] * p[e]).sum() / power[e].sum()),
                    actual=float(actual),
                    salience=_salience(p[e], power[e], actual),
                )
            )
    _AHEAD[key] = pd.DataFrame(rows)
    return _AHEAD[key]


_AHEAD = {}


def _salience(p, power, turnout):
    """The common logit shift that makes expected stake-weighted turnout match the action."""
    lo, hi, base = -8.0, 8.0, model.logit(p)
    for _ in range(40):
        mid = (lo + hi) / 2
        if (power * model.expit(base + mid)).sum() / power.sum() < turnout:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def fit_voting(data, first, last, strength, lag):
    scores = {h: ahead(data, first, last, h, strength, lag) for h in HALF_LIVES}
    half_life = min(scores, key=lambda h: scores[h].log_loss.mean())
    best = scores[half_life]
    return dict(
        half_life=float(half_life),
        salience_sd=float(best.salience.std()),
        log_loss={str(h): round(float(s.log_loss.mean()), 4) for h, s in scores.items()},
        turnout_bias=float((best.predicted - best.actual).mean()),
        actions=len(best),
    )


# ---------------------------------------------------------------- delegation behaviour


def fit_delegation(data, start, end, large_ada, floor_ada, half_life, strength):
    """Move rates and destination choice from accounts that (re)delegated in (start, end].

    The account table is a cross-section at the tip: each row carries the epoch of its
    current delegation. Under a constant move rate h, the share of delegations no older
    than k epochs is 1 - (1 - h) ** k. First-time delegations count as moves, so this
    leans high.
    """
    g = data.delegators
    g = g[g.delegated_epoch <= end]
    moved = g.delegated_epoch > start
    large = g.amount >= large_ada
    span = end - start
    out = {}
    for label, cls in (("large", large), ("small", ~large)):
        share = g.weight[cls & moved].sum() / g.weight[cls].sum()
        out[f"hazard_{label}"] = float(1 - (1 - share) ** (1 / span))
        movers = g[cls & moved]
        out[f"abstain_{label}"] = float(
            movers.weight[movers.drep_id == ABSTAIN].sum() / movers.weight.sum()
        )
    movers = g[moved]
    out["no_confidence_share"] = float(
        movers.weight[movers.drep_id == NO_CONFIDENCE].sum() / movers.weight.sum()
    )

    # Which DRep a large mover picked, against each DRep's size and vote rate at `start`.
    power = data.power.loc[start]
    p, _ = propensity(data, start, start, half_life, strength)
    held = power.values > 0
    x = np.log(power.values[held] + floor_ada)
    a = p[held]
    picks = g[moved & large]
    count = picks.groupby("drep_id").weight.sum().reindex(power.index[held]).fillna(0).values

    def log_likelihood(theta, beta):
        u = theta * x + beta * a
        return (count * u).sum() - count.sum() * (u.max() + np.log(np.exp(u - u.max()).sum()))

    grid = [
        (log_likelihood(t, b), t, b)
        for t in np.arange(0, 1.51, 0.05)
        for b in np.arange(0, 5.1, 0.25)
    ]
    _, theta, beta = max(grid)
    out.update(theta=float(theta), beta_activity=float(beta), choices=int(count.sum()))
    return out


def churn(data, epoch):
    """Recent DRep arrivals and departures: rates per epoch and the sizes involved."""
    lo = max(int(data.power.index.min()) + 1, epoch - POOL_EPOCHS)
    held = data.power.loc[:epoch] > 0
    first = held.idxmax()
    last = held[::-1].idxmax()
    ever = held.any()
    entered = ever & (first > lo)
    left = ever & (last >= lo) & (last < epoch)
    lookup = data.power.values
    rows = data.power.index.get_indexer
    cols = np.arange(data.power.shape[1])
    entry_stake = lookup[rows(first[entered]), cols[entered.values]]
    exit_stake = lookup[rows(last[left]), cols[left.values]]
    span = epoch - lo
    return dict(
        entry_rate=float(entered.sum() / span),
        exit_rate=float(left.sum() / span),
        entered=entered.values,
        entry_stake=entry_stake,
        exit_stake=exit_stake,
    )


# ---------------------------------------------------------------- starting state


def build_world(data, epoch, params):
    """The observed state at `epoch`, using nothing recorded after it except account sizes.

    DRep totals, votes and registrations are the real values for that epoch. How a DRep's
    total splits into accounts is only known at the tip, so for earlier epochs today's
    split is rescaled to the DRep's total at the time.
    """
    power = data.power.loc[epoch]
    held = power.values > 0
    ids = list(power.index[held])
    p_all, q_all = propensity(data, epoch, epoch, params.half_life, params.prior_strength)

    seen = pd.concat(
        [
            data.votes[data.votes.epoch_no <= epoch].groupby("voter_id").epoch_no.max(),
            data.updates[data.updates.epoch_no <= epoch].groupby("drep_id").epoch_no.max(),
        ],
        axis=1,
    ).max(axis=1)
    last_active = seen.reindex(ids).fillna(epoch - 1000).values.astype(float)

    wanted = dict(zip(ids, power.values[held]))
    wanted[ABSTAIN] = float(data.special.loc[epoch, ABSTAIN])
    wanted[NO_CONFIDENCE] = float(data.special.loc[epoch, NO_CONFIDENCE])
    code = {d: i for i, d in enumerate(ids)}
    code[ABSTAIN], code[NO_CONFIDENCE] = model.ABSTAIN, model.NO_CONFIDENCE
    pledge = np.zeros(len(ids))
    stake, count, target = [np.zeros(0)] * 3
    covered = set()
    if data.delegators is not None:
        g = data.delegators[data.delegators.drep_id.isin(code.keys())]
        effective = g.amount * g.weight
        scale = g.drep_id.map(wanted) / effective.groupby(g.drep_id).transform("sum")
        stake = (effective * scale).values
        count = g.weight.values
        target = g.drep_id.map(code).values
        covered = set(g.drep_id)
        if data.own is None:  # no linked accounts: the earliest delegator stands in
            first = g.assign(balance=g.amount * scale)
            first = first[~first.drep_id.isin([ABSTAIN, NO_CONFIDENCE])]
            first = first.sort_values(["delegated_epoch", "balance"], ascending=[True, False])
            first = first.drop_duplicates("drep_id")
            pledge[first.drep_id.map(code).values] = first.balance.values
    if data.own is not None:
        pledge = data.own.reindex(ids).fillna(0.0).values
    alone = [d for d in wanted if d not in covered and wanted[d] > 0]
    stake = np.concatenate([stake, [wanted[d] for d in alone]])
    count = np.concatenate([count, np.ones(len(alone))])
    target = np.concatenate([target, [code[d] for d in alone]]).astype(int)

    window = []
    for e in range(epoch - params.activity_window + 1, epoch + 1):
        actions = data.closed(e, e) if e in data.power.index else data.proposals.iloc[:0]
        if len(actions):
            eligible, voted, rationale = data.ballots(actions)
            window.append(
                tuple(m.sum(axis=1)[held].astype(float) for m in (eligible, voted, rationale))
            )
        else:
            window.append(tuple(np.zeros(len(ids)) for _ in range(3)))

    lo = max(FIRST_VOTING_EPOCH, epoch - POOL_EPOCHS)
    closed = data.closed(lo, epoch)
    closes = closed.groupby("close").size().reindex(range(lo, epoch + 1), fill_value=0).values
    # Actions are resampled whole, so that support, abstentions and attention stay linked.
    scored = ahead(
        data,
        max(lo, FIRST_VOTING_EPOCH + params.forecast_lag + 3),
        epoch,
        params.half_life,
        params.prior_strength,
        params.forecast_lag,
    )
    pool = closed.merge(scored[["proposal_id", "salience"]], on="proposal_id").dropna(
        subset=["support"]
    )
    actions = np.column_stack(
        [pool.threshold, pool.support, pool.abstain_share.fillna(0), pool.salience]
    )
    moves = churn(data, epoch)
    entrants = moves["entered"] if moves["entered"].any() else held
    return model.World(
        epoch=epoch,
        ids=ids,
        p=p_all[held],
        q=q_all[held],
        last_active=last_active,
        pledge=pledge,
        acct_stake=stake,
        acct_count=count,
        acct_target=target,
        window=window,
        closes=closes,
        actions=actions,
        entrant_stake=moves["entry_stake"] if len(moves["entry_stake"]) else np.array([1000.0]),
        entrant_p=p_all[entrants],
        entrant_q=q_all[entrants],
        exit_stake=moves["exit_stake"] if len(moves["exit_stake"]) else np.array([1000.0]),
    )


# ---------------------------------------------------------------- simulated moments


def trace(world, params, epochs, seed):
    """One unpaid run as a per-epoch table, with the turnover of DRep power shares."""
    series, actions = model.run(
        world, params, mechanisms.Scheme(), epochs=epochs, seed=seed, trace=True
    )
    before = dict(zip(range(len(world.p)), _initial_shares(world)))
    turnover = []
    for row in series:
        now = row.pop("shares")
        keys = set(before) | set(now)
        turnover.append(sum(abs(now.get(k, 0) - before.get(k, 0)) for k in keys) / 2)
        before = now
    frame = pd.DataFrame(series).set_index("epoch")
    frame["turnover"] = turnover
    return frame, pd.DataFrame(actions)


def _initial_shares(world):
    stake = np.bincount(
        world.acct_target[world.acct_target >= 0],
        weights=world.acct_stake[world.acct_target >= 0],
        minlength=len(world.p),
    )
    return stake / stake.sum()


def fit_dynamics(data, params, start, end, seeds, rounds=8):
    """Fit what the account cross-section cannot pin down, by matching simulated history.

    Balance drift matches the end totals, balance volatility matches the turnover of DRep
    power shares, and `theta` (how strongly movers favour large DReps) matches the average
    effective number of DReps over (start, end]. The cross-section estimate of theta is
    kept only as a diagnostic: real inflows are lumpier than any size rule, so a size rule
    fitted to individual choices lets concentration drift.
    """
    observed = data.series().loc[start:end]
    span = end - start
    params = model.Params(**{**params.to_dict(), "sigma_balance": 0.02})
    low, high = 0.0, 1.6
    for _ in range(rounds):
        params.theta = (low + high) / 2
        world = build_world(data, start, params)
        runs = [trace(world, params, span, seed)[0] for seed in range(seeds)]
        last = pd.concat([r.iloc[[-1]] for r in runs]).mean()
        turnover = np.mean([r.turnover.mean() for r in runs])
        effective_n = np.mean([r.effective_n.mean() for r in runs])
        if effective_n > observed.effective_n.iloc[1:].mean():
            low = params.theta  # too dispersed: movers must favour large DReps more
        else:
            high = params.theta
        params.drift_drep += float(np.log(observed.drep_power.iloc[-1] / last.drep_power) / span)
        params.drift_abstain += float(np.log(observed.abstain.iloc[-1] / last.abstain) / span)
        ratio = observed.turnover.iloc[1:].mean() / turnover
        params.sigma_balance = float(np.clip(params.sigma_balance * np.clip(ratio, 0.5, 2), 0, 0.3))
    params.theta = float((low + high) / 2)
    return params


def fit(data, start, end, conventions, seeds=12, log=print):
    """All fitted parameters from the window (start, end]."""
    strength = conventions.get("prior_strength", 2.0)
    lag = int(conventions.get("forecast_lag", 18))
    voting = fit_voting(data, start, end, strength, lag)
    log(f"  voting: half-life {voting['half_life']:.0f}, salience sd {voting['salience_sd']:.2f}")
    delegation = fit_delegation(
        data,
        start,
        end,
        conventions.get("large_ada", 100_000.0),
        conventions.get("stake_floor_ada", 1000.0),
        voting["half_life"],
        strength,
    )
    log(
        f"  delegation: move rate {delegation['hazard_large']:.4f} large / "
        f"{delegation['hazard_small']:.4f} small, cross-section theta "
        f"{delegation['theta']:.2f}, activity {delegation['beta_activity']:.2f}"
    )
    moves = churn(data, end)
    keep = {k: v for k, v in conventions.items() if k in model.Params.__dataclass_fields__}
    params = model.Params(
        hazard_large=delegation["hazard_large"],
        hazard_small=delegation["hazard_small"],
        theta=delegation["theta"],
        beta_activity=delegation["beta_activity"],
        abstain_large=delegation["abstain_large"],
        abstain_small=delegation["abstain_small"],
        no_confidence_share=delegation["no_confidence_share"],
        sigma_balance=0.0,
        drift_drep=0.0,
        drift_abstain=0.0,
        entry_rate=moves["entry_rate"],
        exit_rate=moves["exit_rate"],
        half_life=voting["half_life"],
        **keep,
    )
    params = fit_dynamics(data, params, start, end, seeds)
    delegation["theta_cross_section"] = delegation.pop("theta")
    log(
        f"  dynamics: theta {params.theta:.2f}, balance sd {params.sigma_balance:.4f}, drift {params.drift_drep:+.5f} DRep / "
        f"{params.drift_abstain:+.5f} abstain"
    )
    return params, dict(voting=voting, delegation=delegation)


# ---------------------------------------------------------------- validation


def validate(data, params, start, end, seeds, tolerances):
    """Start from the observed state at `start` and compare with what happened by `end`."""
    world = build_world(data, start, params)
    span = end - start
    runs = [trace(world, params, span, seed) for seed in range(seeds)]
    observed = data.series().loc[start + 1 : end]
    columns = ["tau67", "tau50", "effective_n", "drep_power", "abstain", "dreps", "turnover"]
    stack = np.stack([r[0][columns].values for r in runs])
    bands = pd.DataFrame(index=observed.index)
    for i, c in enumerate(columns):
        bands[f"{c}_observed"] = observed[c].values
        bands[f"{c}_mean"] = stack[:, :, i].mean(axis=0)
        bands[f"{c}_low"] = np.quantile(stack[:, :, i], 0.025, axis=0)
        bands[f"{c}_high"] = np.quantile(stack[:, :, i], 0.975, axis=0)

    actions = data.closed(start + 1, end)
    eligible, voted, _ = data.ballots(actions)
    turnout, ballots = [], []
    for j, close in enumerate(actions.close.astype(int)):
        power = data.power.loc[close].values
        turnout.append(power[voted[:, j]].sum() / power[eligible[:, j]].sum())
        ballots.append(voted[:, j].sum())
    simulated_actions = pd.concat([r[1] for r in runs])
    binding = actions[actions.threshold.notna()]
    supported = binding[binding.support >= binding.threshold]

    def check(name, observed_value, simulated_values, kind, gated=True):
        """`gated=False` marks context: reported, but driven by inputs the model takes as given."""
        simulated = float(np.mean(simulated_values))
        error = simulated - observed_value if kind == "absolute" else simulated / observed_value - 1
        return dict(
            metric=name,
            observed=float(observed_value),
            simulated=simulated,
            low=float(np.quantile(simulated_values, 0.025)),
            high=float(np.quantile(simulated_values, 0.975)),
            error=float(error),
            kind=kind,
            tolerance=tolerances[name] if gated else None,
            gated=gated,
            passed=bool(abs(error) <= tolerances[name]) if gated else None,
        )

    def per_seed(column, how):
        i = columns.index(column)
        return stack[:, :, i].mean(axis=1) if how == "mean" else stack[:, -1, i]

    rows = [
        check("tau67", observed.tau67.mean(), per_seed("tau67", "mean"), "relative"),
        check(
            "effective_n", observed.effective_n.mean(), per_seed("effective_n", "mean"), "relative"
        ),
        check(
            "drep_power", observed.drep_power.iloc[-1], per_seed("drep_power", "end"), "relative"
        ),
        check("abstain", observed.abstain.iloc[-1], per_seed("abstain", "end"), "relative"),
        check("dreps", observed.dreps.iloc[-1], per_seed("dreps", "end"), "relative"),
        check("turnover", observed.turnover.mean(), per_seed("turnover", "mean"), "relative"),
        check(
            "turnout",
            np.mean(turnout),
            [r[1].turnout.mean() for r in runs if len(r[1])],
            "absolute",
        ),
        check(
            "supported_ratified",
            (supported.outcome == "ratified").mean(),
            [
                r[1][r[1].binding & r[1].supported].ratified.mean()
                for r in runs
                if len(r[1]) and (r[1].binding & r[1].supported).any()
            ],
            "absolute",
        ),
        check(
            "ratified",
            (binding.outcome == "ratified").mean(),
            [r[1][r[1].binding].ratified.mean() for r in runs if len(r[1]) and r[1].binding.any()],
            "absolute",
            gated=False,
        ),
        check(
            "ballots",
            np.mean(ballots),
            [r[1].ballots.mean() for r in runs if len(r[1])],
            "relative",
        ),
    ]
    report = pd.DataFrame(rows)
    return dict(
        start=start,
        end=end,
        seeds=seeds,
        passed=bool(report[report.gated].passed.all()),
        checks=report,
        bands=bands,
        observed_actions=pd.DataFrame(
            dict(close=actions.close.values, turnout=turnout, ballots=ballots)
        ),
        simulated_turnout_sd=float(simulated_actions.turnout.std()),
    )


def run(data, config, log=print):
    """Fit on an earlier window, test on the latest one, then refit on both for use."""
    tip = data.tip_epoch
    span = int(config["calibration"]["window_epochs"])
    seeds = int(config["calibration"]["fit_seeds"])
    settings = {**config["conventions"], **config["assumptions"]}
    log(f"fit on epochs {tip - 2 * span + 1}..{tip - span}")
    held_back, held_back_detail = fit(data, tip - 2 * span, tip - span, settings, seeds, log)
    log(f"validate on epochs {tip - span + 1}..{tip} (not used in that fit)")
    report = validate(
        data,
        held_back,
        tip - span,
        tip,
        int(config["calibration"]["validation_seeds"]),
        config["calibration"]["tolerances"],
    )
    for row in report["checks"].itertuples():
        mark = "note" if not row.gated else "ok  " if row.passed else "FAIL"
        limit = f"limit {row.tolerance}" if row.gated else "not gated"
        log(
            f"  {mark} {row.metric:<18} observed {row.observed:,.3f} simulated "
            f"{row.simulated:,.3f} ({row.kind} error {row.error:+.3f}, {limit})"
        )
    # Forward use gets both windows: a single large account leaving can dominate the trend
    # of one 40-epoch window.
    log(f"refit on epochs {tip - 2 * span + 1}..{tip} for forward use")
    params, detail = fit(data, tip - 2 * span, tip, settings, seeds, log)
    result = dict(
        tip_epoch=tip,
        params=params.to_dict(),
        detail=detail,
        validation=dict(
            start=report["start"],
            end=report["end"],
            seeds=report["seeds"],
            passed=report["passed"],
            checks=report["checks"].to_dict("records"),
            params=held_back.to_dict(),
            detail=held_back_detail,
        ),
    )
    return result, report["bands"]
