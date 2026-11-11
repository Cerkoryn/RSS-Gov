"""The browser's exact checks (web/checks.js) give the same answers as static.analyse."""

import json
import math
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from rss_gov import mechanisms, static, website
from tests.conftest import make_params, make_world

RULES = [
    *(dict(mechanisms.PRESETS[name]) for name in mechanisms.PRESETS if name != "unpaid"),
    dict(alpha=0.25, k_exclude=3, n_pay=20, cap_ada=2e6),
    dict(alpha=1.0, activity_gate=0.5, rationale_bonus=2.0, min_stake_ada=50_000),
    dict(alpha=0.75, delegator_share=0.5, delegator_mode="flat", min_delegators=3),
    dict(alpha=1.0, delegator_share=0.3, pledge_leverage=50),
]


def study():
    world = make_world()
    world.acct_count[::3] = 2.5  # some accounts stand for several, as in the real table
    return SimpleNamespace(
        world=world,
        params=make_params(),
        data=SimpleNamespace(params={"drep_deposit": 500_000_000}),
        config={"sybil": {"newcomer_capital_ada": 1_000_000}},
        epochs=36,
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")
@pytest.mark.parametrize("budget", [5e5, 5e6])
def test_browser_checks_match_python(tmp_path, budget):
    s = study()
    schemes = [mechanisms.scheme(name=f"r{i}", budget_ada=budget, **r) for i, r in enumerate(RULES)]
    today, accounts = static.export(s)
    (tmp_path / "in.json").write_text(
        json.dumps(dict(today=today, accounts=accounts, schemes=[x.to_dict() for x in schemes]))
    )
    script = (
        f"const C = require({json.dumps(str(website.WEB / 'checks.js'))});"
        f"const d = JSON.parse(require('fs').readFileSync({json.dumps(str(tmp_path / 'in.json'))}));"
        "console.log(JSON.stringify(d.schemes.map((s) => [C.analyse(s, d.today, d.accounts), C.notes(s)])));"
    )
    out = json.loads(subprocess.run(["node", "-e", script], capture_output=True, check=True).stdout)
    table = static.analyse(s, schemes).set_index("scheme")
    for scheme, (row, notes) in zip(schemes, out):
        assert notes == scheme.feasibility()["notes"]
        for key in [*website.FACTS, "split_gain"]:
            want, got = table.loc[scheme.name, key], row[key]
            if key in ("incumbent_rank", "incumbent_parts"):
                continue  # which DRep gains most is arbitrary in a tie (equal pay ties them all)
            if want is None or (isinstance(want, float) and math.isnan(want)):
                assert got is None, (scheme.name, key, got)
            else:
                assert got == pytest.approx(float(want), rel=1e-9, abs=1e-12), (scheme.name, key)
