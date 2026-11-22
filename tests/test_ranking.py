"""Net benefit: the score, its interval, and the browser's copy (web/ranking.js)."""

import json
import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest

from rss_gov import ranking, website

SCENARIOS = ["low", "central", "high"]
VALUE = [1e8, 1.25e6, 4.5e8]  # ADA a year per unit: participation share, DRep, backing share


def runs(seeds=30):
    """Paired runs: unpaid, a design that buys gains, and a cheap one that splitting can game."""
    rng = np.random.default_rng(7)
    rows = []
    for scenario, strength in zip(SCENARIOS, [0.5, 1.0, 2.0]):
        for seed in range(seeds):
            luck = rng.normal(0, 0.01)
            base = dict(participation=0.25 + luck, tau67=19 + 10 * luck, backing=0.007)
            rows.append(
                dict(
                    scheme="unpaid",
                    scenario=scenario,
                    seed=seed,
                    **base,
                    annual_cost_ada=0.0,
                    split_gain=0.0,
                )
            )
            rows.append(
                dict(
                    scheme="buys",
                    scenario=scenario,
                    seed=seed,
                    participation=base["participation"] + 0.04 * strength + rng.normal(0, 0.005),
                    tau67=base["tau67"] + 3 * strength,
                    backing=0.009,
                    annual_cost_ada=5e6 + rng.normal(0, 1e5),
                    split_gain=0.0,
                )
            )
            rows.append(
                dict(
                    scheme="gamed",
                    scenario=scenario,
                    seed=seed,
                    participation=base["participation"] + 0.01,
                    tau67=base["tau67"] - 1,
                    backing=0.007,
                    annual_cost_ada=2e6,
                    split_gain=0.4,
                )
            )
    return pd.DataFrame(rows)


def test_net_benefit_is_gains_at_the_stated_values_minus_cost_and_what_splitting_takes():
    designs = ranking.inputs(runs(), SCENARIOS)
    assert set(designs) == {"buys", "gamed"}
    d = designs["gamed"]
    by, mean, half = ranking.score(d, VALUE, sybil_loss=1.0)
    # +1 point of participation, -1 DRep, no pledge change; 2M ADA cost plus 0.8M taken by splitting
    assert by == pytest.approx([1e6 - 1.25e6 - 2e6 - 0.8e6] * 3)
    assert mean == pytest.approx(by.mean()) and half == pytest.approx(0, abs=1e-3)
    # paying nothing is the zero line, and a cost that buys nothing ranks below it
    table = ranking.table(designs, VALUE, 1.0, SCENARIOS)
    assert list(table.scheme) == ["buys", "unpaid", "gamed"]
    unpaid = table.set_index("scheme").loc["unpaid"]
    assert unpaid.score == 0 and np.isnan(unpaid.worth_from)
    # gains worth k times as much: the break-even k is where the score crosses zero
    buys = table.set_index("scheme").loc["buys"]
    assert ranking.score(designs["buys"], VALUE, 1.0, k=buys.worth_from)[1] == pytest.approx(
        0, abs=1
    )
    assert table["first"].sum() == pytest.approx(1)


def test_the_interval_comes_from_the_paired_seeds():
    designs = ranking.inputs(runs(), SCENARIOS)
    d = designs["buys"]
    _, mean, half = ranking.score(d, VALUE, 1.0)
    frame = runs()
    per_seed = []
    for seed in range(30):
        total = 0.0
        for scenario in SCENARIOS:
            row = frame[(frame.seed == seed) & (frame.scenario == scenario)].set_index("scheme")
            cols = [*ranking.COLUMNS]
            diff = row.loc["buys", cols] - row.loc["unpaid", cols]
            total += diff.participation * VALUE[0] + diff.tau67 * VALUE[1]
            total += diff.backing * VALUE[2] - diff.annual_cost_ada
        per_seed.append(total / 3)
    assert mean == pytest.approx(np.mean(per_seed))
    assert half == pytest.approx(1.96 * np.std(per_seed, ddof=1) / np.sqrt(30))


def test_config_values_are_ada_a_year_per_unit():
    config = {
        "ranking": {
            "value": {
                "participation": {"per": 0.01, "ada": 1e6},
                "tau67": {"per": 1, "ada": 2e6},
                "backing": {"per": 0.01, "ada": 3e6},
            },
            "sybil_loss": 2,
        }
    }
    assert ranking.values(config) == ([1e8, 2e6, 3e8], 2.0)


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")
def test_browser_ranking_matches_python(tmp_path):
    designs = ranking.inputs(runs(), SCENARIOS)
    upper = np.triu_indices(len(SCENARIOS) * len(ranking.COLUMNS))
    exported = {
        n: dict(m=d["mean"].tolist(), c=d["cov"][upper].tolist(), s=d["split"])
        for n, d in designs.items()
    }
    (tmp_path / "in.json").write_text(json.dumps(exported))
    script = (
        f"const R = require({json.dumps(str(website.WEB / 'ranking.js'))});"
        f"const d = JSON.parse(require('fs').readFileSync({json.dumps(str(tmp_path / 'in.json'))}));"
        f"console.log(JSON.stringify(R.table(d, {json.dumps(VALUE)}, 1.5, {ranking.SHAKE})"
        ".map((r) => ({ ...r, worthFrom: r.worthFrom === Infinity ? 'inf' : r.worthFrom }))));"
    )
    got = json.loads(subprocess.run(["node", "-e", script], capture_output=True, check=True).stdout)
    want = ranking.table(designs, VALUE, 1.5, SCENARIOS)
    assert [r["name"] or "unpaid" for r in got] == list(want.scheme)
    for row, (_, ref) in zip(got, want.iterrows()):
        assert row["score"] == pytest.approx(ref.score, rel=1e-9)
        assert row["ci"] == pytest.approx(ref.ci, rel=1e-9, abs=1e-6)
        assert row["by"] == pytest.approx(list(ref[SCENARIOS]), rel=1e-9)
        assert row["behind"] == pytest.approx(ref.behind, rel=1e-9)
        if row["worthFrom"] is None:
            assert np.isnan(ref.worth_from)
        elif row["worthFrom"] == "inf":
            assert np.isinf(ref.worth_from)
        else:
            assert row["worthFrom"] == pytest.approx(ref.worth_from, rel=1e-9)
        assert row["first"] == pytest.approx(ref["first"], abs=0.05)  # different random draws
