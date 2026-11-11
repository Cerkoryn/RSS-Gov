"""Load the downloaded tables and derive the observed quantities the study uses.

Everything in `Data` is an observation or simple arithmetic on observations. Amounts are
converted from lovelace to ADA here.
"""

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from rss_gov.koios import SPECIAL
from rss_gov.metrics import effective_number, tau

ABSTAIN, NO_CONFIDENCE = SPECIAL
THRESHOLD_COLUMN = {
    "TreasuryWithdrawals": "dvt_treasury_withdrawal",
    "NewConstitution": "dvt_update_to_constitution",
    "HardForkInitiation": "dvt_hard_fork_initiation",
    "NewCommittee": "dvt_committee_normal",
    "NoConfidence": "dvt_motion_no_confidence",
    "ParameterChange": "dvt_p_p_gov_group",  # the strictest group; payload groups are not parsed
}


@dataclass
class Data:
    tip_epoch: int
    proposals: pd.DataFrame  # one row per governance action, with close epoch and turnout
    votes: pd.DataFrame  # latest DRep ballot per (DRep, action)
    power: pd.DataFrame  # epoch x DRep voting power in ADA (registered DReps only)
    special: pd.DataFrame  # epoch x {abstain, no_confidence} in ADA
    dreps: pd.DataFrame  # current DRep registry, indexed by id
    updates: pd.DataFrame  # registration / update / deregistration events
    params: pd.Series  # protocol parameters at the tip
    delegators: pd.DataFrame | None  # current account-level delegation, or None
    own: pd.Series | None  # ADA in accounts linked to each DRep (funder or declared), or None
    manifest: dict
    treasury: float | None = None  # ADA in the treasury at the latest recorded epoch

    def series(self):
        """Per-epoch concentration and delegation totals: the facts a baseline must match."""
        rows = []
        for epoch, row in self.power.iterrows():
            p = row.values
            p = p[p > 0]
            rows.append(
                dict(
                    epoch=epoch,
                    dreps=len(p),
                    drep_power=p.sum(),
                    tau50=tau(p, 0.5),
                    tau67=tau(p, 0.67),
                    effective_n=effective_number(p),
                )
            )
        out = pd.DataFrame(rows).set_index("epoch")
        out["abstain"] = self.special[ABSTAIN].reindex(out.index).fillna(0)
        out["no_confidence"] = self.special[NO_CONFIDENCE].reindex(out.index).fillna(0)
        share = self.power.div(self.power.sum(axis=1), axis=0)
        out["turnover"] = share.diff().abs().sum(axis=1) / 2
        return out

    def closed(self, first=None, last=None):
        """Actions whose voting has ended, optionally by closing-epoch range."""
        p = self.proposals[self.proposals.outcome != "open"]
        if first is not None:
            p = p[p.close >= first]
        if last is not None:
            p = p[p.close <= last]
        return p

    def ballots(self, proposals):
        """Eligibility and vote matrices (DRep x action) for the given closed actions.

        A DRep is eligible for an action when it held voting power in the closing epoch.
        """
        ids = self.power.columns
        eligible = np.zeros((len(ids), len(proposals)), bool)
        voted = np.zeros_like(eligible)
        rationale = np.zeros_like(eligible)
        position = {d: i for i, d in enumerate(ids)}
        by_action = dict(tuple(self.votes.groupby("proposal_id")))
        for j, (_, p) in enumerate(proposals.iterrows()):
            eligible[:, j] = self.power.loc[int(p.close)].values > 0
            cast = by_action.get(p.proposal_id)
            if cast is None:
                continue
            rows = [position[d] for d in cast.voter_id if d in position]
            flags = [r for d, r in zip(cast.voter_id, cast.has_rationale) if d in position]
            voted[rows, j] = True
            rationale[rows, j] = flags
        voted &= eligible
        rationale &= voted
        return eligible, voted, rationale


def load(folder):
    folder = Path(folder)
    tables = folder / "tables"
    if not (folder / "manifest.json").exists():
        raise FileNotFoundError(f"no completed data pull in {folder}; run `rss-gov data pull`")
    manifest = json.loads((folder / "manifest.json").read_text())
    tip = manifest["tip"]["epoch_no"]

    def read(name):
        return pd.read_parquet(tables / f"{name}.parquet")

    raw = read("drep_power")
    wide = raw.pivot(index="epoch_no", columns="drep_id", values="amount").fillna(0) / 1e6
    special = wide.reindex(columns=list(SPECIAL), fill_value=0.0)
    power = wide.drop(columns=[c for c in SPECIAL if c in wide.columns])

    votes = read("votes")
    votes = (
        votes[votes.voter_role == "DRep"]
        .sort_values("block_time")
        .drop_duplicates(["voter_id", "proposal_id"], keep="last")
    )

    params = read("params").set_index("epoch_no").iloc[-1]
    proposals = read("proposals")
    summary = read("voting_summary")
    for column in summary.columns:
        if column.endswith("_power"):
            summary[column] = summary[column].astype(float) / 1e6
    summary["voted_power"] = (
        summary.drep_active_yes_vote_power
        + summary.drep_active_no_vote_power
        + summary.drep_active_abstain_vote_power
    )
    summary["active_power"] = (
        summary.drep_yes_vote_power
        + summary.drep_no_vote_power
        + summary.drep_active_abstain_vote_power
    )
    summary["turnout"] = summary.voted_power / summary.active_power.where(summary.active_power > 0)
    cast = summary.drep_active_yes_vote_power + summary.drep_active_no_vote_power
    summary["support"] = summary.drep_active_yes_vote_power / cast.where(cast > 0)
    summary["abstain_share"] = summary.drep_active_abstain_vote_power / summary.voted_power.where(
        summary.voted_power > 0
    )
    summary["yes_share"] = summary.drep_yes_pct / 100
    summary["ballots"] = (
        summary.drep_yes_votes_cast + summary.drep_no_votes_cast + summary.drep_abstain_votes_cast
    )
    proposals = proposals.merge(
        summary[
            [
                "proposal_id",
                "turnout",
                "yes_share",
                "support",
                "abstain_share",
                "ballots",
                "active_power",
                "voted_power",
            ]
        ],
        on="proposal_id",
        how="left",
    )
    proposals["close"] = proposals.ratified_epoch.fillna(proposals.expired_epoch).fillna(
        proposals.dropped_epoch
    )
    proposals["outcome"] = np.select(
        [
            proposals.ratified_epoch.notna(),
            proposals.expired_epoch.notna(),
            proposals.dropped_epoch.notna(),
        ],
        ["ratified", "expired", "dropped"],
        "open",
    )
    # Voting must have ended inside the power history for an action to be usable.
    usable = proposals.close.between(power.index.min(), power.index.max())
    proposals.loc[~usable & (proposals.outcome != "open"), "outcome"] = "outside_history"
    proposals["threshold"] = [
        float(params.get(THRESHOLD_COLUMN.get(kind, ""), np.nan))
        for kind in proposals.proposal_type
    ]
    proposals["withdrawal_ada"] = proposals.pop("withdrawal_lovelace") / 1e6

    dreps = read("dreps").set_index("drep_id")
    dreps["amount"] = dreps["amount"] / 1e6

    delegators = None
    if (tables / "delegators.parquet").exists():
        delegators = read("delegators")
        delegators["amount"] = delegators["amount"].clip(lower=0) / 1e6
        delegators = delegators[delegators.amount > 0].reset_index(drop=True)

    own = None
    if (tables / "drep_own.parquet").exists():
        links = read("drep_own").drop_duplicates(["drep_id", "stake_address"])
        # Koios reports a negative balance for the odd account; treat it as empty.
        own = links.balance.clip(lower=0).groupby(links.drep_id).sum() / 1e6

    treasury = None
    if (tables / "totals.parquet").exists():
        totals = read("totals").sort_values("epoch_no")
        treasury = float(totals.treasury.iloc[-1]) / 1e6

    return Data(
        tip_epoch=tip,
        proposals=proposals,
        votes=votes,
        power=power,
        special=special,
        dreps=dreps,
        updates=read("drep_updates"),
        params=params,
        delegators=delegators,
        own=own,
        manifest=manifest,
        treasury=treasury,
    )
