"""Reward formulas. Each one sees only quantities computable from chain data.

Rewards are paid for explicit votes only (Yes, No or Abstain all count): a DRep's weight
is always proportional to the share of recently closed actions it voted on. A `Scheme` is
a point in one parametric family that covers proportional, equal, power-law, capped,
exclude-K/pay-N (middle-out, with or without roll-down), top-m and threshold-share,
fixed pay per vote, equal-plus-power blends, activity-gated, rationale-bonus,
delegator-count, pledge-weighted and delegator-sharing designs. Amounts are ADA (floats); a pilot would round at payout.
"""

from dataclasses import asdict, dataclass, fields, replace
import math

import numpy as np


@dataclass
class Round:
    """What a formula may read for one reward round, one entry per registered DRep."""

    power: np.ndarray  # delegated voting power, ADA
    activity: np.ndarray  # share of recently closed actions the DRep voted on, 0..1
    rationale: np.ndarray  # share of those votes that carried a rationale anchor, 0..1
    delegators: np.ndarray  # delegating accounts holding at least the counting minimum
    pledge: np.ndarray  # the DRep's own ADA behind its votes (zero when no pledge programme exists)
    actions: float = 1.0  # actions closing per round on average: a full vote rate in votes


@dataclass(frozen=True)
class Scheme:
    name: str = "unpaid"
    budget_ada: float = 0.0  # whole programme, spread evenly over its epochs
    fee_ada: float = 0.0  # added to the pot by each governance action that closes
    alpha: float = 1.0  # weight grows as counted_power ** alpha (0 = equal, 1 = proportional)
    cap_ada: float = math.inf  # voting power counted for rewards is at most this
    k_exclude: int = 0  # the K largest DReps are weighted by top_weight (0: paid nothing)
    top_weight: float = 0.0  # weight of the K largest relative to everyone else
    n_pay: int = 0  # after the K largest, only the next N eligible ranks are paid (0 = all)
    roll_down: bool = False  # a rank's slot passes down when a DRep above does not vote
    min_power_ada: float = 0.0
    min_share: float = 0.0  # minimum share of all DRep voting power (1/k: Threshold(k))
    min_delegators: int = 0
    min_pledge_ada: float = 0.0  # a DRep needs at least this much pledge to be paid
    activity_gate: float = 0.0  # minimum recent vote rate to qualify
    rationale_bonus: float = 0.0  # weight multiplied by 1 + bonus * rationale share
    basis: str = "power"  # what alpha applies to: "power" or "delegators" (their count)
    equal_share: float = 0.0  # fraction of the DReps' pot split equally, the rest by weight
    per_vote_ada: float = 0.0  # fixed pay per vote (0: the pot is always split in full)
    max_award_share: float = 0.0  # no DRep gets more than this share of the DReps' pot
    delegator_share: float = 0.0  # fraction of the budget paid to delegators
    # How the delegators' part is split across DReps; each DRep's delegators then share it per
    # ADA delegated. "passthrough": by the DRep's award; "flat": the same yield per ADA through
    # every paid DRep; "per_drep": by counted power ** delegator_alpha, times the vote rate.
    delegator_mode: str = "passthrough"
    delegator_alpha: float = 1.0  # per_drep only: 1 = by counted power, 0 = equal per DRep
    delegator_k_exclude: int = 0  # delegators of the K largest DReps are not paid (the DReps are)
    # No DRep's delegators earn more than this multiple of the flat yield (0 = off); the excess
    # goes to the other delegators. 1 is the flat yield; larger leaves pots per DRep alone.
    delegator_yield_cap: float = 0.0
    # Counted power is at most leverage * pledge (0 = off): a pledge soft cap.
    pledge_leverage: float = 0.0
    hard_cap: bool = False  # also cap voting power at leverage * pledge
    # A pot that grows with pledge (0 = off): each round pays at most this yearly rate on the
    # pledge behind paid votes; the rest of the budget stays unspent.
    pledge_rate: float = 0.0

    def __post_init__(self):
        if self.delegator_mode not in {"passthrough", "flat", "per_drep"}:
            raise ValueError("delegator_mode must be 'passthrough', 'flat' or 'per_drep'")
        if not 0 <= self.delegator_alpha <= 1:
            raise ValueError("delegator_alpha must be in [0, 1]")
        if not 0 <= self.delegator_share <= 1:
            raise ValueError("delegator_share must be in [0, 1]")
        if self.alpha < 0 or self.rationale_bonus < 0:
            raise ValueError("alpha and rationale_bonus must be non-negative")
        if self.basis not in {"power", "delegators"}:
            raise ValueError("basis must be 'power' or 'delegators'")
        if self.hard_cap and self.pledge_leverage <= 0:
            raise ValueError("a hard cap needs pledge_leverage > 0")
        if self.roll_down and not self.n_pay:
            raise ValueError("roll_down needs n_pay > 0")
        if self.per_vote_ada and (self.alpha != 0 or self.delegator_share):
            raise ValueError("pay per vote is the same for every DRep: alpha 0, no delegator share")
        shares = (self.min_share, self.top_weight, self.equal_share, self.max_award_share)
        if not all(0 <= x <= 1 for x in shares):
            raise ValueError("min_share, top_weight, equal_share and max_award_share are in [0, 1]")
        amounts = (
            self.budget_ada,
            self.fee_ada,
            self.cap_ada,
            self.min_power_ada,
            self.min_pledge_ada,
            self.pledge_leverage,
            self.pledge_rate,
        )
        if min(*amounts, self.per_vote_ada) < 0:
            raise ValueError("amounts must be non-negative")
        if self.delegator_k_exclude < 0:
            raise ValueError("delegator_k_exclude must be non-negative")
        if self.delegator_yield_cap and self.delegator_yield_cap < 1:
            raise ValueError("delegator_yield_cap is 0 (off) or at least 1")

    @property
    def paid(self):
        return self.budget_ada > 0 or self.fee_ada > 0

    def income(self, epochs, actions):
        """ADA added to the pot in an epoch in which `actions` governance actions close."""
        return self.budget_ada / epochs + self.fee_ada * actions

    def feasibility(self):
        """What it would take to run this on Cardano, independent of any simulation."""
        inputs = ["DRep voting power per epoch", "DRep votes per governance action"]
        notes = []
        if self.rationale_bonus > 0:
            inputs.append("vote rationale anchors")
            notes.append("An anchor proves a rationale exists, not that it is good.")
        if self.min_delegators > 0 or self.delegator_share > 0 or self.basis == "delegators":
            inputs.append("per-account DRep delegation and balance per epoch")
        if self.basis == "delegators":
            notes.append("Accounts are cheap to create: paying by their number invites fake ones.")
        if self.delegator_share > 0:
            notes.append(
                "Pays every delegating account, however little: one CIP-159 direct deposit each."
            )
        if self.pledge_leverage > 0 or self.min_pledge_ada > 0 or self.pledge_rate > 0:
            inputs.append("DRep pledge accounts (signed declaration, checked on chain)")
            notes.append("Pledge is not a ledger concept: DReps must declare their accounts.")
        if self.hard_cap:
            notes.append("Capping voting power changes ratification rules: needs a hard fork.")
        if self.fee_ada > 0:
            notes.append(
                "Today every governance action deposit is returned: keeping part of it as a fee "
                "changes the ledger's rules and needs a hard fork."
            )
        if not self.paid:
            inputs, notes = [], []
        fork = self.hard_cap or self.fee_ada > 0
        return dict(
            requires_hard_fork=fork,
            pilot_testable=not fork,
            inputs=inputs,
            notes=notes,
        )

    def label(self):
        """A short description of the rule, readable in a table."""
        if not self.paid:
            return "unpaid"
        base = {0.0: "equal", 1.0: "linear"}.get(self.alpha, f"power^{self.alpha:g}")
        if self.basis == "delegators" and self.alpha:
            base = f"delegators^{self.alpha:g}"
        parts = [base]
        if self.per_vote_ada:
            parts.append(f"{self.per_vote_ada:g} ADA per vote")
        if self.equal_share:
            parts.append(f"{self.equal_share:.0%} equal")
        if not math.isinf(self.cap_ada):
            parts.append(f"cap {_ada(self.cap_ada)}")
        if self.max_award_share:
            parts.append(f"award cap {self.max_award_share:.0%}")
        if self.k_exclude:
            top = f"top {self.k_exclude}"
            parts.append(f"{top} at {self.top_weight:.0%}" if self.top_weight else f"skip {top}")
        if self.n_pay:
            parts.append(f"pay {self.n_pay}" + (" (roll-down)" if self.roll_down else ""))
        if self.min_power_ada:
            parts.append(f"min {_ada(self.min_power_ada)}")
        if self.min_share:
            parts.append(f"min {self.min_share:.2%} of power")
        if self.min_delegators:
            parts.append(f"min {self.min_delegators} delegators")
        if self.min_pledge_ada:
            parts.append(f"min pledge {_ada(self.min_pledge_ada)}")
        if self.activity_gate:
            parts.append(f"gate {self.activity_gate:.0%}")
        if self.rationale_bonus:
            parts.append(f"rationale +{self.rationale_bonus:.0%}")
        if self.delegator_share:
            mode = self.delegator_mode
            if mode == "per_drep":
                mode = {0.0: "equal per DRep", 0.5: "sqrt per DRep", 1.0: "by counted power"}.get(
                    self.delegator_alpha, f"power^{self.delegator_alpha:g} per DRep"
                )
            parts.append(f"{self.delegator_share:.0%} to delegators ({mode})")
            if self.delegator_k_exclude:
                parts.append(f"not via top {self.delegator_k_exclude}")
            if self.delegator_yield_cap and self.delegator_mode != "flat":
                parts.append(f"delegator yield at most {self.delegator_yield_cap:g}x flat")
        if self.pledge_leverage:
            kind = "hard" if self.hard_cap else "soft"
            parts.append(f"pledge {kind} cap {self.pledge_leverage:g}x")
        if self.pledge_rate:
            parts.append(f"pot at most {self.pledge_rate:.0%} of pledge a year")
        money = [f"{_ada(self.budget_ada)} ADA"] if self.budget_ada else []
        if self.fee_ada:
            money.append(f"{_ada(self.fee_ada)} ADA proposer fee")
        return ", ".join(parts) + "; " + " + ".join(money)

    def to_dict(self):
        d = asdict(self)
        d["cap_ada"] = None if math.isinf(self.cap_ada) else self.cap_ada
        return d


def scheme(**kwargs):
    if kwargs.get("cap_ada") is None:
        kwargs.pop("cap_ada", None)
    unknown = set(kwargs) - {f.name for f in fields(Scheme)}
    if unknown:
        raise ValueError(f"unknown scheme fields: {sorted(unknown)}")
    return Scheme(**kwargs)


ROUNDS_PER_YEAR = 73  # one reward round per five-day epoch


def _pledge_behind(s, r, expected=None):
    """Each DRep's pledge behind paid votes: pledge (at most its voting power) times its
    vote rate and what its rank keeps. Zero for a DRep that is not paid."""
    ok = eligible(s, r)
    expected = r.activity * ok if expected is None else expected
    return _ranked(s, r, ok, expected) * r.activity * np.minimum(r.pledge, r.power)


def spendable(s, r, pot):
    """The part of the round's pot that may be paid: with `pledge_rate`, at most that
    yearly rate on all the pledge behind paid votes. The rest stays unspent."""
    if s.pledge_rate <= 0:
        return pot
    return min(pot, s.pledge_rate * float(_pledge_behind(s, r).sum()) / ROUNDS_PER_YEAR)


def _spendable_each(s, r, pot, now, then):
    """`spendable` for each DRep if only its own pledge behind paid votes went from `now`
    to `then` (both per DRep); others are held as they are."""
    if s.pledge_rate <= 0:
        return pot
    base = now.sum() - now + then
    return np.minimum(pot, s.pledge_rate * base / ROUNDS_PER_YEAR)


def counted_power(s, r):
    power = np.minimum(r.power, s.cap_ada)
    if s.pledge_leverage > 0:
        power = np.minimum(power, s.pledge_leverage * r.pledge)
    return power


def eligible(s, r):
    """Who qualifies at all; ranks and weights come after."""
    ok = (
        (r.activity > 0)
        & (r.activity >= s.activity_gate)
        & (r.power >= s.min_power_ada)
        & (r.delegators >= s.min_delegators)
        & (r.pledge >= s.min_pledge_ada)
    )
    if s.min_share:
        ok &= r.power >= s.min_share * r.power.sum()
    return ok


def _ranked(s, r, ok, expected):
    """What a DRep's rank lets it keep: top_weight for the K largest, 1 for the next N.

    With roll-down, an action pays the first N voters below the K largest, so a rank keeps
    the share of a slot left after the DReps above it are expected to vote (`expected`
    holds their chances; this is the expected-value form of per-action roll-down).
    """
    keep = ok.astype(float)
    if not (s.k_exclude or s.n_pay):
        return keep
    order = np.argsort(-r.power, kind="stable")
    keep[order[: s.k_exclude]] *= s.top_weight
    rest = order[s.k_exclude :]
    rest = rest[ok[rest]]
    if s.roll_down:
        above = np.cumsum(expected[rest]) - expected[rest]
        keep[rest] = np.clip(s.n_pay - above, 0.0, 1.0)
    elif s.n_pay:
        keep[rest[s.n_pay :]] = 0.0
    return keep


def _parts(s, r, expected=None):
    """Reward weights as (fraction of the DReps' pot, weights); zero means not paid.

    Weight is linear in the vote rate, so every explicit vote earns the same increment
    and a DRep that has not voted earns nothing.
    """
    ok = eligible(s, r)
    expected = r.activity * ok if expected is None else expected
    votes = _ranked(s, r, ok, expected) * r.activity * (1 + s.rationale_bonus * r.rationale)
    size = r.delegators if s.basis == "delegators" else counted_power(s, r)
    base = np.ones_like(r.power) if s.alpha == 0 else np.power(size, s.alpha)
    if s.equal_share:
        return [(s.equal_share, votes), (1 - s.equal_share, votes * base)]
    return [(1.0, votes * base)]


def weights(s, r):
    """Unnormalised reward weights of the main part; zero means not paid this round."""
    return _parts(s, r)[-1][1]


def _awards(s, parts, totals, reps, actions):
    """Each part splits its fraction of the DReps' pot `reps` by weight over `totals`.

    Pay per vote sets the rate instead, scaled down only when the pot cannot cover it;
    what is not paid stays in the pot. A cap per DRep is never redistributed either.
    """
    award = 0.0
    for (fraction, w), total in zip(parts, totals):
        with np.errstate(divide="ignore", invalid="ignore"):
            rate = np.where(total > 0, fraction * reps / total, 0.0)
        if s.per_vote_ada:
            rate = np.minimum(rate, s.per_vote_ada * actions)
        award = award + w * rate
    if s.max_award_share:
        award = np.minimum(award, s.max_award_share * reps)
    return award


def allocate(s, r, pot):
    """Split one round's pot. Returns (DRep awards, delegator yield per ADA delegated).

    Delegators are paid only through a DRep that is paid, and not through the K largest
    with `delegator_k_exclude`: their part goes to the other delegators. `passthrough`
    shares each DRep's own award with its delegators; `flat` pays one yield per ADA and per
    unit of the DRep's vote rate, whatever the DRep's size or pledge; `per_drep` gives each
    DRep's delegators a pot by its counted power (capped, pledge-limited) ** delegator_alpha
    times its vote rate. Within a DRep, delegators always share per ADA delegated.
    """
    n = len(r.power)
    pot = spendable(s, r, pot)
    if pot <= 0:
        return np.zeros(n), np.zeros(n)
    parts = _parts(s, r)
    rep = _awards(s, parts, [w.sum() for _, w in parts], pot * (1 - s.delegator_share), r.actions)
    rep = np.zeros(n) + rep
    total = rep.sum()
    if total <= 0:
        return np.zeros(n), np.zeros(n)
    delegator_pot = pot * s.delegator_share
    yields = np.zeros(n)
    if delegator_pot > 0:
        paid = (rep > 0) & (r.power > 0)
        if s.delegator_k_exclude:
            paid[np.argsort(-r.power, kind="stable")[: s.delegator_k_exclude]] = False
        if s.delegator_mode == "flat":
            base = (r.power[paid] * r.activity[paid]).sum()
            if base > 0:
                yields[paid] = delegator_pot * r.activity[paid] / base
        elif s.delegator_mode == "per_drep":
            size = counted_power(s, r)[paid]
            w = np.power(size, s.delegator_alpha) if s.delegator_alpha else (size > 0) * 1.0
            w = w * r.activity[paid]
            if w.sum() > 0:
                yields[paid] = delegator_pot * w / w.sum() / r.power[paid]
        elif rep[paid].sum() > 0:
            yields[paid] = delegator_pot * rep[paid] / rep[paid].sum() / r.power[paid]
        if s.delegator_yield_cap and s.delegator_mode != "flat":
            yields = _cap_yields(yields, paid, r, delegator_pot, s.delegator_yield_cap)
    return rep, yields


def _cap_yields(yields, paid, r, pot, k):
    """Hold every paid DRep's delegator yield to k times the flat yield at its vote rate, and
    share what that frees among the others by their pots, until none is above the line."""
    base = (r.power[paid] * r.activity[paid]).sum()
    if base <= 0 or (yields[paid] * r.power[paid]).sum() <= 0:
        return yields
    yields = yields.copy()
    line = k * pot * r.activity / base
    held = np.zeros(len(yields), bool)
    while True:
        over = paid & ~held & (yields > line * (1 + 1e-12))
        if not over.any():
            return yields
        held |= over
        yields[held] = line[held]
        rest = paid & ~held
        pots = yields[rest] * r.power[rest]
        free = pot - (line[held] * r.power[held]).sum()
        if pots.sum() <= 0 or free <= 0:
            return yields
        yields[rest] = free * pots / pots.sum() / r.power[rest]


def vote_value(s, r, pot):
    """Each DRep's reward for one more vote: its award at a full vote rate, per vote.

    Others are held at their current activity.
    """
    if pot <= 0:
        return np.zeros(len(r.power))
    expected = r.activity * eligible(s, r)
    everyone = replace_activity(r, np.ones_like(r.activity))
    full = _parts(s, everyone, expected)
    now = _parts(s, r)
    totals = [w_now.sum() - w_now + w_full for (_, w_full), (_, w_now) in zip(full, now)]
    pot = _spendable_each(s, r, pot, _pledge_behind(s, r), _pledge_behind(s, everyone, expected))
    award = _awards(s, full, totals, pot * (1 - s.delegator_share), r.actions)
    return np.zeros(len(r.power)) + award / max(r.actions, 1e-9)


def pledge_gain(s, r, pot, extra):
    """Each DRep's gain in award per round from adding `extra` pledge.

    Others are held as they are.
    """
    if pot <= 0:
        return np.zeros(len(r.power))
    plus = replace(r, pledge=r.pledge + extra)
    now = _parts(s, r)
    more = _parts(s, plus)
    alone = [w_now.sum() - w_now + w_more for (_, w_more), (_, w_now) in zip(more, now)]
    reps = spendable(s, r, pot) * (1 - s.delegator_share)
    before = _awards(s, now, [w.sum() for _, w in now], reps, r.actions)
    pots = _spendable_each(s, r, pot, _pledge_behind(s, r), _pledge_behind(s, plus))
    after = _awards(s, more, alone, pots * (1 - s.delegator_share), r.actions)
    return np.zeros(len(r.power)) + after - before


def replace_activity(r, activity):
    return replace(r, activity=activity)


def voting_power(s, power, pledge):
    """Power used for ratification and concentration. Only a hard cap changes it."""
    return np.minimum(power, s.pledge_leverage * pledge) if s.hard_cap else power


PRESETS = {
    "unpaid": dict(),
    "proportional": dict(alpha=1.0),
    "equal": dict(alpha=0.0),
    "sqrt": dict(alpha=0.5),
    "capped": dict(alpha=1.0, cap_ada=20_000_000),
    "middle_out": dict(alpha=0.0, k_exclude=10, n_pay=100),
    "activity_gate": dict(alpha=1.0, activity_gate=0.7),
    "rationale_bonus": dict(alpha=0.5, rationale_bonus=1.0),
    "small_drep_floor": dict(alpha=0.5, min_delegators=10, min_power_ada=100_000),
    "delegator_flat": dict(alpha=1.0, delegator_share=0.8, delegator_mode="flat"),
    "delegator_passthrough_sqrt": dict(alpha=0.5, delegator_share=0.8),
    "pledge_soft_cap": dict(alpha=1.0, pledge_leverage=1000),
    "pledge_hard_cap": dict(alpha=1.0, pledge_leverage=1000, hard_cap=True),
    # Named designs from the literature and from other DAOs (METHODS.md lists the sources).
    "top_m_equal": dict(alpha=0.0, n_pay=100),
    "top_m_proportional": dict(alpha=1.0, n_pay=100),
    "threshold_k": dict(alpha=0.0, min_share=0.01, max_award_share=0.01),
    "threshold_k_proportional": dict(alpha=1.0, min_share=0.01),
    "equal_plus_power": dict(alpha=1.0, equal_share=0.5),
    "exclude_k_pay_n": dict(alpha=0.0, k_exclude=10, n_pay=200, roll_down=True, per_vote_ada=10),
    "top_haircut": dict(
        alpha=1.0, k_exclude=20, top_weight=0.25, activity_gate=0.7, min_delegators=10
    ),
    "top_100_gated": dict(alpha=0.0, n_pay=100, activity_gate=0.7),
    "delegators_first": dict(
        alpha=1.0,
        activity_gate=0.7,
        max_award_share=0.1,
        delegator_share=0.9,
        delegator_mode="flat",
    ),
    "delegator_count_sqrt": dict(alpha=0.5, basis="delegators", max_award_share=0.05),
    # Simple pledge soft caps: pay for the pledge behind the votes (METHODS.md, "Named designs").
    "pledge_soft_cap_skip20": dict(alpha=1.0, k_exclude=20, pledge_leverage=1.0),
    "pledge_soft_cap_skip10": dict(alpha=1.0, k_exclude=10, pledge_leverage=2.0),
    "pledge_soft_cap_capped": dict(alpha=1.0, cap_ada=5_000_000, pledge_leverage=1.0),
    # Paying delegators to move away from the largest DReps (METHODS.md, "Named designs").
    "pledge_backed_delegators": dict(
        alpha=1.0, cap_ada=5_000_000, pledge_leverage=1.0, delegator_share=0.8
    ),
    "skip_top20_delegators": dict(
        alpha=1.0,
        k_exclude=20,
        activity_gate=0.7,
        pledge_leverage=2.0,
        delegator_share=0.8,
        delegator_mode="flat",
    ),
    "haircut_top20_delegators": dict(
        alpha=1.0,
        k_exclude=20,
        top_weight=0.25,
        activity_gate=0.7,
        pledge_leverage=2.0,
        delegator_share=0.8,
        delegator_mode="flat",
    ),
    "small_drep_delegators": dict(
        alpha=0.5,
        min_delegators=10,
        min_power_ada=100_000,
        pledge_leverage=1.0,
        delegator_share=0.8,
    ),
    "delegators_not_top20": dict(
        alpha=1.0, delegator_share=0.5, delegator_mode="flat", delegator_k_exclude=20
    ),
    "top100_delegators_not_top20": dict(
        alpha=1.0, n_pay=100, delegator_share=0.5, delegator_mode="flat", delegator_k_exclude=20
    ),
    # The 100 largest compete for the whole pot with their pledge: each is paid by its voting
    # power counted only up to its pledge, so a DRep with no pledge earns nothing, and one
    # pledged DRep alone would take everything.
    "pledge_contest": dict(alpha=1.0, n_pay=100, pledge_leverage=1.0),
    "pledge_contest_delegators": dict(
        alpha=1.0, n_pay=100, pledge_leverage=1.0, delegator_share=0.5, delegator_mode="per_drep"
    ),
}


def _ada(amount):
    for size, unit in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if amount >= size:
            return f"{amount / size:g}{unit}"
    return f"{amount:g}"


def preset(name, budget_ada):
    if name not in PRESETS:
        raise ValueError(f"unknown preset {name!r}; choose from {sorted(PRESETS)}")
    return Scheme(name=name, budget_ada=0.0 if name == "unpaid" else budget_ada, **PRESETS[name])


def experiment_rows(config):
    """The config's schemes, plus every named design in it paid instead by each fee per
    governance action in `experiment.fees_ada`, with no budget."""
    rows = list(config["experiment"]["schemes"])
    named = [r for r in rows if isinstance(r, str) and r != "unpaid"]
    fees = config["experiment"].get("fees_ada") or []
    return rows + [
        dict(name=f"{n}_fee_{_ada(fee).lower()}", preset=n, budget_ada=0, fee_ada=fee)
        for n in named
        for fee in fees
    ]


def from_config(row, default_budget):
    """A config entry is a preset name, or a mapping with optional `preset` and overrides."""
    if isinstance(row, str):
        return preset(row, default_budget)
    row = dict(row)
    base = (
        preset(row.pop("preset"), default_budget)
        if "preset" in row
        else Scheme(budget_ada=default_budget)
    )
    if "cap_ada" in row and row["cap_ada"] is None:  # null: no cap, even over a preset's
        row["cap_ada"] = math.inf
    return replace(base, **row)
