import json

import numpy as np
import pytest

from rss_gov import calibrate, dataset, experiment, koios, model, static
from tests.conftest import make_params


def test_a_retry_after_date_falls_back_to_the_default_wait():
    assert koios._seconds("7", 2) == 7.0
    assert koios._seconds("Wed, 21 Oct 2026 07:28:00 GMT", 2) == 2
    assert koios._seconds(None, 4) == 4


def test_a_pull_never_mixes_epochs(tmp_path, monkeypatch):
    (tmp_path / "tables").mkdir()
    (tmp_path / "manifest.json").write_text(json.dumps({"tip": {"epoch_no": 600}}))
    (tmp_path / "tip.json").write_text(json.dumps({"epoch_no": 600}))
    with pytest.raises(FileExistsError, match="--fresh"):  # tables without their pages
        koios.pull(tmp_path, log=lambda *_: None)

    class Stop(Exception):
        pass

    def tip(out):
        raise Stop

    monkeypatch.setattr(koios, "k_tip", tip)
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw" / "page.json.gz").write_bytes(b"")
    with pytest.raises(Stop):
        koios.pull(tmp_path, log=lambda *_: None, fresh=True)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["raw"]  # the cache, empty again
    assert not any((tmp_path / "raw").iterdir())


def test_epoch_arithmetic():
    assert koios.epoch_of(koios.SHELLEY_START) == 208
    assert koios.epoch_of(koios.SHELLEY_START + 432000 * 10 + 5) == 218


def test_load_derives_outcomes_and_support(pull):
    data = dataset.load(pull)
    assert data.tip_epoch == 570
    assert list(data.proposals.outcome) == [
        "ratified",
        "expired",
        "ratified",
        "expired",
        "ratified",
    ]
    assert data.proposals.support.iloc[0] == 1.0  # every active vote was Yes
    assert data.proposals.abstain_share.iloc[0] == 0.0
    assert data.proposals.threshold.iloc[0] == 0.67
    assert data.special.loc[570, dataset.ABSTAIN] == 5e6
    assert data.series().loc[570, "dreps"] == 6


def test_ballots_only_count_dreps_with_power_at_the_close(pull):
    data = dataset.load(pull)
    eligible, voted, rationale = data.ballots(data.closed())
    assert eligible[:, 0].sum() == 5 and eligible[:, -1].sum() == 6  # drep5 appears at 565
    assert voted.sum(axis=1).tolist() == [0, 0, 5, 5, 5, 0]
    assert rationale.sum(axis=1).tolist() == [0, 0, 0, 0, 5, 0]


def test_propensity_separates_voters_from_non_voters(pull, monkeypatch):
    monkeypatch.setattr(calibrate, "FIRST_VOTING_EPOCH", 560)
    data = dataset.load(pull)
    p, q = calibrate.propensity(data, 570, 570, half_life=10, strength=2)
    assert p[0] < 0.2 and p[2] > 0.8
    assert q[4] > q[2]


def test_world_matches_observed_totals(pull, monkeypatch):
    monkeypatch.setattr(calibrate, "FIRST_VOTING_EPOCH", 560)
    monkeypatch.setattr(
        calibrate, "ahead", lambda data, *a: data.closed()[["proposal_id"]].assign(salience=0.0)
    )
    data = dataset.load(pull)
    world = calibrate.build_world(data, 570, make_params())
    on_drep = world.acct_target >= 0
    stake = np.bincount(world.acct_target[on_drep], weights=world.acct_stake[on_drep])
    assert np.allclose(stake, data.power.loc[570].values)
    assert world.acct_stake[world.acct_target == model.ABSTAIN].sum() == 5e6
    assert world.acct_stake[world.acct_target == model.NO_CONFIDENCE].sum() == 1e5
    assert world.pledge[0] == 0.6e6  # the earliest delegator stands in for own stake
    assert world.actions.shape[1] == 4

    study = experiment.Study(
        config=dict(
            results=str(pull / "results"),
            programme=dict(budget_ada=36_000.0, epochs=36),
            sybil=dict(newcomer_capital_ada=1e6),
        ),
        data=data, params=make_params(), world=world, scenarios={}, validation_passed=True,
    )  # fmt: skip
    table = static.analyse(study, study.schemes(["unpaid", "proportional", "equal", "capped"]))
    table = table.set_index("scheme")
    assert table.loc["unpaid", "split_gain"] == 0
    assert table.loc["proportional", "split_gain"] < 1e-9  # splitting never helps a linear rule
    assert table.loc["equal", "newcomer_extra"] > 0.5  # fake DReps swamp an equal split
    assert table.loc["equal", "newcomer_identities"] > 100


def test_linked_accounts_replace_the_stand_in_for_own_stake(pull, monkeypatch):
    import pandas as pd

    monkeypatch.setattr(calibrate, "FIRST_VOTING_EPOCH", 560)
    monkeypatch.setattr(
        calibrate, "ahead", lambda data, *a: data.closed()[["proposal_id"]].assign(salience=0.0)
    )
    rows = [
        dict(drep_id="drep0", stake_address="s0a", source="funder", balance=int(7e9)),
        dict(drep_id="drep0", stake_address="s0a", source="declared", balance=int(7e9)),
        dict(drep_id="drep0", stake_address="x", source="declared", balance=int(1e9)),
        dict(drep_id="drep1", stake_address="y", source="funder", balance=-5),
    ]
    pd.DataFrame(rows).assign(delegated_drep=None).to_parquet(pull / "tables" / "drep_own.parquet")
    data = dataset.load(pull)
    world = calibrate.build_world(data, 570, make_params())
    assert world.pledge[:3].tolist() == [8000.0, 0.0, 0.0]  # an account counts once


def test_an_incumbent_above_a_cap_gains_by_splitting():
    import numpy as np

    from rss_gov import mechanisms

    rnd = mechanisms.Round(
        stake=np.array([400.0, 30.0, 20.0, 10.0]) * 1e6,
        activity=np.ones(4),
        rationale=np.zeros(4),
        delegators=np.full(4, 100.0),
        pledge=np.zeros(4),
    )
    capped = static.incumbent_split(mechanisms.preset("capped", 1), rnd, 100.0)
    linear = static.incumbent_split(mechanisms.preset("proportional", 1), rnd, 100.0)
    assert capped[0] > 0.3 and capped[1] == 1  # the largest DRep is the one that gains
    assert linear[0] < 1e-9
