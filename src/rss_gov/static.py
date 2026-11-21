"""What a formula does to today's real DReps, before anyone changes behaviour.

No simulation and no assumptions about responses: the scheme is applied to the observed
snapshot. This is where payability, capture by the largest DReps and the reward for
splitting one identity into many show up. These numbers are exact properties of a rule.
"""

import numpy as np
import pandas as pd

from rss_gov import mechanisms, model
from rss_gov.metrics import gini

NEWCOMER_SPLITS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000)
INCUMBENT_SPLITS = (2, 5, 10, 20)
INCUMBENT_RANKS = tuple(range(20)) + (49, 99, 199)  # which existing DReps try splitting


def snapshot(study):
    """Today's reward round."""
    w, p = study.world, study.params
    on_drep = w.acct_target >= 0
    n = len(w.p)
    power = np.bincount(w.acct_target[on_drep], weights=w.acct_ada[on_drep], minlength=n)
    counted = w.acct_count * (w.acct_ada >= p.delegator_min_ada * w.acct_count)
    activity, rationale = model._activity(w.window, np.zeros(n), np.zeros(n))
    return mechanisms.Round(
        power=power,
        activity=activity,
        rationale=rationale,
        delegators=np.bincount(w.acct_target[on_drep], weights=counted[on_drep], minlength=n),
        pledge=w.pledge,
        actions=w.action_rate,
    )


def _take(scheme, rnd, pot, rows):
    """Share of the pot going to these DReps and their delegators."""
    award, yields = mechanisms.allocate(scheme, rnd, pot)
    return float((award[rows].sum() + (yields[rows] * rnd.power[rows]).sum()) / pot)


def _with(rnd, drop, power, activity, rationale, delegators, pledge, copies):
    """The round with DRep `drop` removed (or nobody) and `copies` identical DReps added."""

    def join(values, new):
        values = values if drop is None else np.delete(values, drop)
        return np.concatenate([values, np.full(copies, new)])

    return mechanisms.Round(
        power=join(rnd.power, power),
        activity=join(rnd.activity, activity),
        rationale=join(rnd.rationale, rationale),
        delegators=join(rnd.delegators, delegators),
        pledge=join(rnd.pledge, pledge),
        actions=rnd.actions,
    )


def newcomer_split(scheme, rnd, pot, capital, deposit, delegator_min):
    """An outsider splits its own ADA over fake DReps that vote on everything.

    Each fake DRep pays its deposit, attaches a rationale to every vote, holds its power
    in minimum-size accounts, and counts it as pledge. Returns the best share of
    the pot, the number of identities that achieves it, and the share with one identity.
    """
    best, best_m, single = 0.0, 1, 0.0
    for m in NEWCOMER_SPLITS:
        each = capital / m - deposit
        if each < max(scheme.min_power_ada, scheme.min_delegators * delegator_min, 1.0):
            break
        plus = _with(rnd, None, each, 1.0, 1.0, np.floor(each / delegator_min), each, m)
        share = _take(scheme, plus, pot, slice(len(rnd.power), None))
        if m == 1:
            single = share
        if share > best:
            best, best_m = share, m
    return best, best_m, single


def incumbent_split(scheme, rnd, pot):
    """The most any existing DRep gains by splitting into equal parts, as a share of the pot.

    Its delegators and pledge are assumed to follow in equal parts. That takes
    cooperation a real DRep may not get, so this is an upper bound on the temptation.
    Returns (extra share, power rank of the DRep, number of parts).
    """
    order = np.argsort(-rnd.power, kind="stable")
    best = (0.0, None, 1)
    for rank in INCUMBENT_RANKS:
        if rank >= len(order):
            break
        i = order[rank]
        whole = _take(scheme, rnd, pot, [i])
        for m in INCUMBENT_SPLITS:
            parts = _with(
                rnd, i, rnd.power[i] / m, rnd.activity[i], rnd.rationale[i],
                rnd.delegators[i] / m, rnd.pledge[i] / m, m,
            )  # fmt: skip
            extra = _take(scheme, parts, pot, slice(len(rnd.power) - 1, None)) - whole
            if extra > best[0]:
                best = (extra, rank + 1, m)
    return best


def _constants(study):
    return dict(
        deposit=float(study.data.params.get("drep_deposit", 500_000_000)) / 1e6,
        capital=float(study.config["sybil"]["newcomer_capital_ada"]),
        delegator_min=float(study.params.delegator_min_ada),
        min_payout=float(study.params.min_payout_ada),
        epochs=int(study.epochs),
    )


def export(study):
    """Today's round as plain lists, for the same checks in the browser (web/checks.js).

    Returns (round, accounts). Values keep full precision so the browser gets the same
    answers; tests/test_checks.py holds the two implementations together. The accounts
    are only needed for delegator payouts: per DRep, its accounts' ADA per account in
    ascending order, with the account count as an index into a short list of values.
    """
    rnd = snapshot(study)
    w = study.world
    on_drep = w.acct_target >= 0
    target, count = w.acct_target[on_drep], w.acct_count[on_drep]
    unit = w.acct_ada[on_drep] / np.maximum(count, 1)
    order = np.lexsort((unit, target))
    palette, which = np.unique(count, return_inverse=True)
    today = dict(
        {k: getattr(rnd, k).tolist() for k in ("power", "activity", "rationale", "delegators")},
        pledge=rnd.pledge.tolist(),
        actions=rnd.actions,
        top10=np.argsort(-rnd.power)[:10].tolist(),
        **_constants(study),
    )
    accounts = dict(
        per_drep=np.bincount(target, minlength=len(rnd.power)).tolist(),
        unit=unit[order].tolist(),
        palette=palette.tolist(),
        count=which[order].tolist(),
    )
    return today, accounts


def analyse(study, schemes):
    """One row per scheme: who would be paid today, how much, and what splitting earns."""
    rnd = snapshot(study)
    w = study.world
    c = _constants(study)
    deposit, capital, min_payout, epochs = c["deposit"], c["capital"], c["min_payout"], c["epochs"]
    on_drep = w.acct_target >= 0
    unit = w.acct_ada[on_drep] / np.maximum(w.acct_count[on_drep], 1)
    top10 = np.argsort(-rnd.power)[:10]
    rows = []
    for scheme in schemes:
        feasibility = scheme.feasibility()
        power = mechanisms.voting_power(scheme, rnd.power, rnd.pledge)
        row = dict(
            scheme=scheme.name,
            rule=scheme.label(),
            budget_ada=scheme.budget_ada,
            fee_ada=scheme.fee_ada,
            pilot_testable=feasibility["pilot_testable"],
            power_kept=float(power.sum() / rnd.power.sum()),
            paid_dreps=0,
            split_gain=0.0,
            newcomer_extra=0.0,
            incumbent_extra=0.0,
            fee_share=0.0,
        )
        if scheme.paid:
            # A fee per action is counted at the average pace of closing actions in history.
            pot = scheme.income(epochs, rnd.actions)
            award, yields = mechanisms.allocate(scheme, rnd, pot)
            paid = award[award > 0]
            best, identities, single = newcomer_split(
                scheme, rnd, pot, capital, deposit, c["delegator_min"]
            )
            extra, rank, parts = incumbent_split(scheme, rnd, pot)
            claims = yields[w.acct_target[on_drep]] * unit * epochs
            holders = w.acct_count[on_drep]
            claimants = holders[claims > 0].sum()
            row.update(
                paid_dreps=int(len(paid)),
                median_award=float(np.median(paid)) if len(paid) else 0.0,
                max_award=float(paid.max()) if len(paid) else 0.0,
                top10_award_share=float(award[top10].sum() / max(award.sum(), 1e-9)),
                award_gini=gini(paid) if len(paid) else np.nan,
                newcomer_capture=best,
                newcomer_identities=identities,
                newcomer_extra=best - single,
                incumbent_extra=extra,
                incumbent_rank=rank,
                incumbent_parts=parts,
                split_gain=max(best - single, extra),
                fee_share=float(scheme.fee_ada * rnd.actions / pot),
                delegator_claimants=float(claimants),
                delegator_dust_share=float(
                    holders[(claims > 0) & (claims < min_payout)].sum() / claimants
                )
                if claimants
                else np.nan,
            )
        row["notes"] = " ".join(feasibility["notes"])
        rows.append(row)
    return pd.DataFrame(rows)
