"""The steps the workflows chain together, end to end on a tiny synthetic study."""

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from rss_gov import calibrate, dataset, experiment, model, proposals, report, search, static
from rss_gov import website
from tests.conftest import make_params

CONFIG = Path(__file__).parents[1] / "config.yaml"
QUIET = lambda *_: None  # noqa: E731
PROPOSAL = dict(name="Flat test", budget_ada=1_000_000, alpha=0.0, cap_ada=None, author="tester")


@pytest.fixture
def study(pull, monkeypatch):
    """The real config, shrunk: few epochs, seeds and search rounds on the synthetic pull."""
    monkeypatch.setattr(calibrate, "FIRST_VOTING_EPOCH", 560)
    monkeypatch.setattr(
        calibrate, "ahead", lambda data, *a: data.closed()[["proposal_id"]].assign(salience=0.0)
    )
    config = experiment.load_config(CONFIG)
    config.update(results=str(pull / "results"), data=str(pull))
    config["programme"]["epochs"] = 6
    config["experiment"]["seeds"] = 3
    config["search"].update(seeds=2, generations=1, population=4, holdout_seeds=3)
    data = dataset.load(pull)
    params = make_params()
    world = calibrate.build_world(data, data.tip_epoch, params)
    scenarios = {k: model.Scenario(k, **(v or {})) for k, v in config["scenarios"].items()}
    study = experiment.Study(config, data, params, world, scenarios, validation_passed=True)
    check = dict(
        metric="tau67", observed=3.0, simulated=3.1, low=2.9, high=3.3, error=0.03,
        kind="relative", tolerance=0.15, gated=True, passed=True,
    )  # fmt: skip
    validation = dict(start=565, end=570, seeds=2, passed=True, checks=[check])
    (study.results / "calibration.json").write_text(
        json.dumps(dict(tip_epoch=data.tip_epoch, validation=validation))
    )
    # `rss-gov static` and `rss-gov experiment`
    schemes = study.schemes(config["experiment"]["schemes"])
    static.analyse(study, schemes).to_csv(study.results / "static.csv", index=False)
    runs = experiment.evaluate(study, schemes, list(scenarios), range(3), processes=1)
    experiment.summarise(runs, study.axes).to_csv(
        study.results / "experiment_summary.csv", index=False
    )
    search.run(study, QUIET, processes=1)  # `rss-gov search`
    return study


def _try(study, row, monkeypatch=None):
    """`rss-gov submit` then `rss-gov try` on the stored file, as the proposal workflow does."""
    scheme, meta = proposals.accept(study.config, dict(row))
    path = proposals.submit(study.results, scheme, meta, "issue #1")
    rows = yaml.safe_load(path.read_text())
    search.try_candidates(study, rows, QUIET, processes=1)
    return scheme.name


def test_a_proposal_reaches_the_site_and_the_report(study):
    name = _try(study, PROPOSAL)
    entry = json.loads((study.results / "proposals" / f"{name}.json").read_text())
    assert entry["accepted"] in (True, False) and entry["reason"]

    data = website.build(study)
    (design,) = [d for d in data["schemes"] if d["name"] == name]
    assert design["kind"] == "proposed" and design["results"]
    assert data["meta"]["epochs_per_year"] == model.EPOCHS_PER_YEAR
    assert data["search"]["holdout_seeds"] == 3
    folder = website.write(study)
    assert (folder / "index.html").exists() and (folder / "data.js").exists()
    assert report.write(study).exists()


def test_an_accepted_proposal_is_judged_with_the_front(study, monkeypatch):
    """Acceptance widens the front; the judged finalists the site counts must include it."""
    monkeypatch.setattr(search, "bootstrap", lambda *a: (1.0, 1.0))  # a clear gain
    monkeypatch.setattr(
        search,
        "front_of",
        lambda points, names, axes, members=None: list(names if members is None else members),
    )  # every design distinct
    name = _try(study, PROPOSAL)
    assert json.loads((study.results / "proposals" / f"{name}.json").read_text())["accepted"]
    assert name in [s["name"] for s in yaml.safe_load((study.results / "front.yaml").read_text())]
    judged = pd.read_csv(study.results / "search_front.csv")
    assert name in set(judged.scheme)
