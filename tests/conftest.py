import json

import numpy as np
import pandas as pd
import pytest

from rss_gov import model


def make_params(**overrides):
    values = dict(
        hazard_large=0.01,
        hazard_small=0.005,
        theta=0.9,
        beta_activity=1.0,
        abstain_large=0.4,
        abstain_small=0.6,
        no_confidence_share=0.01,
        sigma_balance=0.005,
        drift_drep=0.0,
        drift_abstain=0.0,
        entry_rate=1.0,
        exit_rate=0.5,
        half_life=10.0,
    )
    return model.Params(**{**values, **overrides})


def make_world(n=60, accounts_each=8, seed=0):
    """A small synthetic world: n DReps with skewed stake and size-related vote rates."""
    rng = np.random.default_rng(seed)
    drep_stake = np.sort(rng.lognormal(13, 2, n))[::-1]
    target = np.repeat(np.arange(n), accounts_each)
    stake = (
        (drep_stake[target] / accounts_each)
        * rng.dirichlet(np.ones(accounts_each), n).ravel()
        * accounts_each
    )
    extra = 200
    target = np.concatenate(
        [target, np.full(extra, model.ABSTAIN), np.full(5, model.NO_CONFIDENCE)]
    )
    stake = np.concatenate([stake, rng.lognormal(12, 2, extra), rng.lognormal(10, 1, 5)])
    p = np.clip(np.linspace(0.9, 0.02, n), 0.002, 0.998)
    window = [(np.full(n, 2.0), np.round(2 * p), np.round(p)) for _ in range(12)]
    actions = np.array(
        [
            [0.67, 0.9, 0.05, 0.0],
            [0.67, 0.6, 0.1, -0.5],
            [np.nan, 0.8, 0.1, 0.3],
            [0.75, 0.95, 0.02, 0.5],
        ]
    )
    return model.World(
        epoch=100,
        ids=[f"drep{i}" for i in range(n)],
        p=p,
        q=np.full(n, 0.4),
        last_active=np.full(n, 100.0),
        pledge=drep_stake * 0.05,
        acct_stake=stake,
        acct_count=np.ones(len(stake)),
        acct_target=target.astype(int),
        window=window,
        closes=np.array([0, 1, 1, 2, 3]),
        actions=actions,
        entrant_stake=np.array([1000.0, 50_000.0]),
        entrant_p=np.array([0.1, 0.5]),
        entrant_q=np.array([0.3, 0.3]),
        exit_stake=np.array([500.0, 5000.0]),
    )


@pytest.fixture
def params():
    return make_params()


@pytest.fixture
def world():
    return make_world()


@pytest.fixture
def pull(tmp_path):
    """A tiny, internally consistent data pull on disk."""
    tables = tmp_path / "tables"
    tables.mkdir()
    dreps = [f"drep{i}" for i in range(6)]
    epochs = range(560, 571)
    power = [
        dict(drep_id=d, epoch_no=e, amount=int((i + 1) * 1e12))
        for e in epochs
        for i, d in enumerate(dreps)
        if not (d == "drep5" and e < 565)
    ]
    power += [dict(drep_id="drep_always_abstain", epoch_no=e, amount=int(5e12)) for e in epochs]
    power += [
        dict(drep_id="drep_always_no_confidence", epoch_no=e, amount=int(1e11)) for e in epochs
    ]
    pd.DataFrame(power).to_parquet(tables / "drep_power.parquet")
    proposals, votes, summary = [], [], []
    for k, close in enumerate([562, 564, 566, 568, 570]):
        pid = f"gov{k}"
        proposals.append(
            dict(
                proposal_id=pid, proposal_type="TreasuryWithdrawals", proposed_epoch=close - 6,
                ratified_epoch=float(close) if k % 2 == 0 else np.nan, enacted_epoch=np.nan,
                dropped_epoch=np.nan, expired_epoch=float(close) if k % 2 else np.nan,
                expiration=close, deposit=100_000_000_000, block_time=1_700_000_000 + k,
                withdrawal_lovelace=10**9, has_metadata=True,
            )
        )  # fmt: skip
        for i, d in enumerate(dreps[:5]):
            if i >= 2:  # the three largest of the first five always vote; drep0/1 never do
                votes.append(
                    dict(
                        vote_tx_hash=f"tx{k}{i}", voter_role="DRep", voter_id=d, proposal_id=pid,
                        epoch_no=close - 1, block_time=1_700_000_100 + 10 * k + i, vote="Yes",
                        has_rationale=i == 4,
                    )
                )  # fmt: skip
        summary.append(
            dict(
                proposal_id=pid, proposal_type="TreasuryWithdrawals", epoch_no=close,
                drep_yes_votes_cast=3, drep_active_yes_vote_power=str(int(12e12)),
                drep_yes_vote_power=str(int(12e12)), drep_yes_pct=80.0, drep_no_votes_cast=0,
                drep_active_no_vote_power="0", drep_no_vote_power=str(int(3e12)), drep_no_pct=20.0,
                drep_abstain_votes_cast=0, drep_active_abstain_vote_power="0",
            )
        )  # fmt: skip
    pd.DataFrame(proposals).to_parquet(tables / "proposals.parquet")
    pd.DataFrame(votes).to_parquet(tables / "votes.parquet")
    pd.DataFrame(summary).to_parquet(tables / "voting_summary.parquet")
    pd.DataFrame(
        [
            dict(
                drep_id=d,
                drep_status="registered",
                amount=int((i + 1) * 1e12),
                live_delegator_count=2,
            )
            for i, d in enumerate(dreps)
        ]
    ).to_parquet(tables / "dreps.parquet")
    pd.DataFrame(
        [dict(drep_id=d, epoch_no=550, action="registered", block_time=1) for d in dreps]
    ).to_parquet(tables / "drep_updates.parquet")
    pd.DataFrame(
        [
            dict(
                epoch_no=570,
                dvt_treasury_withdrawal=0.67,
                drep_deposit="500000000",
                drep_activity=20,
            )
        ]
    ).to_parquet(tables / "params.parquet")
    delegators = []
    for i, d in enumerate(dreps):
        delegators.append(
            dict(
                drep_id=d,
                stake_address=f"s{i}a",
                delegated_epoch=551,
                amount=int((i + 1) * 6e11),
                weight=1.0,
            )
        )
        delegators.append(
            dict(
                drep_id=d,
                stake_address=f"s{i}b",
                delegated_epoch=566,
                amount=int((i + 1) * 4e11),
                weight=1.0,
            )
        )
    delegators.append(
        dict(
            drep_id="drep_always_abstain",
            stake_address="sa",
            delegated_epoch=567,
            amount=int(5e12),
            weight=1.0,
        )
    )
    pd.DataFrame(delegators).to_parquet(tables / "delegators.parquet")
    (tmp_path / "manifest.json").write_text(json.dumps({"tip": {"epoch_no": 570}}))
    return tmp_path
