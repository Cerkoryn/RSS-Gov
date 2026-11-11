"""Reward formulas. Each one sees only quantities computable from chain data.

Rewards are paid for explicit votes only (Yes, No or Abstain all count): a DRep's weight
is always proportional to the share of recently closed actions it voted on. A `Scheme` is
a point in one parametric family that covers proportional, equal, power-law, capped,
exclude-K/pay-N (middle-out), activity-gated, rationale-bonus, pledge-weighted and
delegator-sharing designs. Amounts are ADA (floats); a pilot would round at payout.
"""

from dataclasses import asdict, dataclass, fields, replace
import math

import numpy as np


@dataclass
class Round:
    """What a formula may read for one reward round, one entry per registered DRep."""

    stake: np.ndarray  # delegated voting power, ADA
    activity: np.ndarray  # share of recently closed actions the DRep voted on, 0..1
    rationale: np.ndarray  # share of those votes that carried a rationale anchor, 0..1
    delegators: np.ndarray  # delegating accounts holding at least the counting minimum
    pledge: np.ndarray  # declared own stake, ADA (zero when no pledge programme exists)


@dataclass(frozen=True)
class Scheme:
    name: str = "unpaid"
    budget_ada: float = 0.0  # whole programme, spread evenly over its epochs
    alpha: float = 1.0  # weight grows as counted_stake ** alpha (0 = equal, 1 = proportional)
    cap_ada: float = math.inf  # stake counted for rewards is at most this
    k_exclude: int = 0  # the K largest DReps receive nothing
    n_pay: int = 0  # after exclusion, only the next N eligible ranks are paid (0 = all)
    min_stake_ada: float = 0.0
    min_delegators: int = 0
    activity_gate: float = 0.0  # minimum recent vote rate to qualify
    rationale_bonus: float = 0.0  # weight multiplied by 1 + bonus * rationale share
    delegator_share: float = 0.0  # fraction of the budget paid to delegators
    delegator_mode: str = "passthrough"  # "passthrough": follows the DRep's award; "flat": same yield for all qualifying DReps
    pledge_leverage: float = 0.0  # counted stake is at most leverage * pledge (0 = off)
    hard_cap: bool = False  # also cap voting power at leverage * pledge

    def __post_init__(self):
        if self.delegator_mode not in {"passthrough", "flat"}:
            raise ValueError("delegator_mode must be 'passthrough' or 'flat'")
        if not 0 <= self.delegator_share <= 1:
            raise ValueError("delegator_share must be in [0, 1]")
        if self.alpha < 0 or self.rationale_bonus < 0:
            raise ValueError("alpha and rationale_bonus must be non-negative")
        if self.hard_cap and self.pledge_leverage <= 0:
            raise ValueError("a hard cap needs pledge_leverage > 0")
        if min(self.budget_ada, self.cap_ada, self.min_stake_ada, self.pledge_leverage) < 0:
            raise ValueError("amounts must be non-negative")

    @property
    def paid(self):
        return self.budget_ada > 0

    def feasibility(self):
        """What it would take to run this on Cardano, independent of any simulation."""
        inputs = ["DRep voting power per epoch", "DRep votes per governance action"]
        notes = []
        if self.rationale_bonus > 0:
            inputs.append("vote rationale anchors")
            notes.append("An anchor proves a rationale exists, not that it is good.")
        if self.min_delegators > 0 or self.delegator_share > 0:
            inputs.append("per-account DRep delegation and balance per epoch")
        if self.delegator_share > 0:
            notes.append("Many small delegator claims: needs a claim contract or minimum payout.")
        if self.pledge_leverage > 0:
            inputs.append("DRep own-stake accounts (signed declaration, checked on chain)")
            notes.append("Own stake is not a ledger concept: DReps must declare their accounts.")
        if self.hard_cap:
            notes.append("Capping voting power changes ratification rules: needs a hard fork.")
        if not self.paid:
            inputs, notes = [], []
        return dict(
            requires_hard_fork=self.hard_cap,
            pilot_testable=not self.hard_cap,
            inputs=inputs,
            notes=notes,
        )

    def label(self):
        """A short description of the rule, readable in a table."""
        if not self.paid:
            return "unpaid"
        base = {0.0: "equal", 1.0: "linear"}.get(self.alpha, f"stake^{self.alpha:g}")
        parts = [base]
        if not math.isinf(self.cap_ada):
            parts.append(f"cap {_ada(self.cap_ada)}")
        if self.k_exclude:
            parts.append(f"skip top {self.k_exclude}")
        if self.n_pay:
            parts.append(f"pay {self.n_pay}")
        if self.min_stake_ada:
            parts.append(f"min {_ada(self.min_stake_ada)}")
        if self.min_delegators:
            parts.append(f"min {self.min_delegators} delegators")
        if self.activity_gate:
            parts.append(f"gate {self.activity_gate:.0%}")
        if self.rationale_bonus:
            parts.append(f"rationale +{self.rationale_bonus:.0%}")
        if self.delegator_share:
            parts.append(f"{self.delegator_share:.0%} to delegators ({self.delegator_mode})")
        if self.pledge_leverage:
            kind = "power cap" if self.hard_cap else "reward cap"
            parts.append(f"{kind} {self.pledge_leverage:g}x own stake")
        return ", ".join(parts) + f"; {_ada(self.budget_ada)} ADA"

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


def counted_stake(s, r):
    stake = np.minimum(r.stake, s.cap_ada)
    if s.pledge_leverage > 0:
        stake = np.minimum(stake, s.pledge_leverage * r.pledge)
    return stake


def weights(s, r):
    """Unnormalised DRep reward weights; zero means not paid this round.

    Weight is linear in the vote rate, so every explicit vote earns the same increment
    and a DRep that has not voted earns nothing.
    """
    eligible = (
        (r.activity > 0)
        & (r.activity >= s.activity_gate)
        & (r.stake >= s.min_stake_ada)
        & (r.delegators >= s.min_delegators)
    )
    if s.k_exclude or s.n_pay:
        order = np.argsort(-r.stake, kind="stable")
        ranked = np.zeros(len(r.stake), bool)
        candidates = order[s.k_exclude :]
        candidates = candidates[eligible[candidates]]
        ranked[candidates[: s.n_pay] if s.n_pay else candidates] = True
        eligible &= ranked
    counted = counted_stake(s, r)
    base = np.ones_like(r.stake) if s.alpha == 0 else np.power(counted, s.alpha)
    return np.where(eligible, base * r.activity * (1 + s.rationale_bonus * r.rationale), 0.0)


def allocate(s, r, pot):
    """Split one round's pot. Returns (DRep awards, delegator yield per ADA delegated).

    Delegators are paid only through a DRep that voted. `passthrough` shares each DRep's
    own award with its delegators; `flat` pays one yield per ADA and per unit of the
    DRep's vote rate, whatever the DRep's size.
    """
    n = len(r.stake)
    if pot <= 0:
        return np.zeros(n), np.zeros(n)
    w = weights(s, r)
    total = w.sum()
    if total <= 0:
        return np.zeros(n), np.zeros(n)
    share = w / total
    rep = pot * (1 - s.delegator_share) * share
    delegator_pot = pot * s.delegator_share
    yields = np.zeros(n)
    if delegator_pot > 0:
        paid = (w > 0) & (r.stake > 0)
        if s.delegator_mode == "flat":
            base = (r.stake[paid] * r.activity[paid]).sum()
            if base > 0:
                yields[paid] = delegator_pot * r.activity[paid] / base
        else:
            yields[paid] = delegator_pot * share[paid] / r.stake[paid]
    return rep, yields


def vote_value(s, r, pot, votes_per_round):
    """Each DRep's reward for one more vote: its award at a full vote rate, per vote.

    Others are held at their current activity.
    """
    if pot <= 0:
        return np.zeros(len(r.stake))
    w_full = weights(s, replace_activity(r, np.ones_like(r.activity)))
    w_now = weights(s, r)
    others = w_now.sum() - w_now
    with np.errstate(divide="ignore", invalid="ignore"):
        award = np.where(w_full > 0, w_full / (others + w_full), 0.0)
    return pot * (1 - s.delegator_share) * award / max(votes_per_round, 1e-9)


def replace_activity(r, activity):
    return Round(r.stake, activity, r.rationale, r.delegators, r.pledge)


def voting_power(s, stake, pledge):
    """Power used for ratification and concentration. Only a hard cap changes it."""
    return np.minimum(stake, s.pledge_leverage * pledge) if s.hard_cap else stake


PRESETS = {
    "unpaid": dict(),
    "proportional": dict(alpha=1.0),
    "equal": dict(alpha=0.0),
    "sqrt": dict(alpha=0.5),
    "capped": dict(alpha=1.0, cap_ada=20_000_000),
    "middle_out": dict(alpha=0.0, k_exclude=10, n_pay=100),
    "activity_gate": dict(alpha=1.0, activity_gate=0.7),
    "rationale_bonus": dict(alpha=0.5, rationale_bonus=1.0),
    "small_drep_floor": dict(alpha=0.5, min_delegators=10, min_stake_ada=100_000),
    "delegator_flat": dict(alpha=1.0, delegator_share=0.8, delegator_mode="flat"),
    "delegator_passthrough_sqrt": dict(alpha=0.5, delegator_share=0.8),
    "pledge_soft": dict(alpha=1.0, pledge_leverage=1000),
    "pledge_hard_cap": dict(alpha=1.0, pledge_leverage=1000, hard_cap=True),
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
    if row.get("cap_ada") is None:
        row.pop("cap_ada", None)
    return replace(base, **row)
