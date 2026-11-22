"""The steps the workflows chain together, end to end on a tiny synthetic study."""

import json
from pathlib import Path
import sys

import pandas as pd
import pytest
import yaml

from rss_gov import calibrate, dataset, experiment, mechanisms, model, proposals, report, search
from rss_gov import static
from rss_gov import cli, research, website
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
    config["experiment"].update(seeds=3, fees_ada=[50_000])
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
    schemes = study.schemes(mechanisms.experiment_rows(config))
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


def _accept(study, monkeypatch):
    monkeypatch.setattr(search, "bootstrap", lambda *a: (1.0, 1.0))
    monkeypatch.setattr(
        search,
        "front_of",
        lambda points, names, axes, members=None: list(names if members is None else members),
    )
    name = _try(study, PROPOSAL)
    monkeypatch.undo()
    return name


def test_an_accepted_proposal_tried_again_is_judged_again_not_copied(study, monkeypatch):
    name = _accept(study, monkeypatch)
    search.try_candidates(study, search.stored_rows(study.results), QUIET, processes=1)
    assert sorted(p.stem for p in (study.results / "proposals").glob("*.yaml")) == [name]
    assert [e["rerun"] for e in search.ledger(study.results)] == [False, True]
    finalists = yaml.safe_load((study.results / "search_finalists.yaml").read_text())
    assert [r["name"] for r in finalists].count(name) <= 1
    holdout = pd.read_parquet(study.results / "search_holdout_runs.parquet")
    assert len(holdout[holdout.scheme == name]) in (0, len(holdout[holdout.scheme == "unpaid"]))


def test_an_accepted_proposal_is_not_counted_as_a_named_design(study, monkeypatch):
    name = _accept(study, monkeypatch)
    assert name not in search.named(study) and "capped" in search.named(study)
    named = report.write(study).read_text().split("### Where the named schemes end up")[1]
    assert name not in named.split("\n\n##")[0]


def test_all_re_tries_the_stored_proposals_before_the_report():
    assert (
        cli.ALL.index(cli.cmd_search) < cli.ALL.index(cli.cmd_try) < cli.ALL.index(cli.cmd_report)
    )


def test_a_stored_proposal_is_refreshed_in_place_after_the_family_grows(study):
    """The refresh workflow re-tries every stored file: one written before a field existed
    must keep its name, not come back as a copy."""
    name = _try(study, PROPOSAL)
    path = study.results / "proposals" / f"{name}.yaml"
    row = yaml.safe_load(path.read_text())[0]
    del row["per_vote_ada"], row["top_weight"]  # as if stored before these fields existed
    path.write_text(yaml.safe_dump([row], sort_keys=False))
    search.try_candidates(study, yaml.safe_load(path.read_text()), QUIET, processes=1)
    assert sorted(p.stem for p in path.parent.glob("*.yaml")) == [name]


def _agent(study, monkeypatch, accept):
    """One attempt by the research agent, accepted or not."""
    if accept:
        monkeypatch.setattr(search, "bootstrap", lambda *a: (1.0, 1.0))
        monkeypatch.setattr(
            search,
            "front_of",
            lambda points, names, axes, members=None: list(names if members is None else members),
        )
    else:
        monkeypatch.setattr(search, "bootstrap", lambda *a: (-1.0, 1.0))
    row = dict(PROPOSAL, name="agent_idea", hypothesis="because")
    del row["author"]
    search.try_candidates(study, [row], QUIET, processes=1, source=proposals.AGENT)
    monkeypatch.undo()
    return "agent_idea"


def test_a_rejected_agent_attempt_is_only_in_the_ledger(study, monkeypatch):
    name = _agent(study, monkeypatch, accept=False)
    (entry,) = search.ledger(study.results)
    assert entry["scheme"]["name"] == name and entry["source"] == proposals.AGENT
    assert entry["holdout"] == search.HOLDOUT_OFFSET
    assert not (study.results / "proposals" / f"{name}.yaml").exists()
    assert name not in [d["name"] for d in website.build(study)["schemes"]]


def test_an_accepted_agent_design_is_shown_with_the_search(study, monkeypatch):
    name = _agent(study, monkeypatch, accept=True)
    data = website.build(study)
    (design,) = [d for d in data["schemes"] if d["name"] == name]
    assert design["kind"] == "search" and design["proposal"]["hypothesis"] == "because"
    assert data["proposals"] == []
    assert [r["name"] for r in search.stored_rows(study.results)] == [name]


def test_used_holdout_seeds_are_replaced_and_proposals_tried_again(study, monkeypatch):
    community = _try(study, PROPOSAL)
    _agent(study, monkeypatch, accept=False)
    assert not search.rotate(study, QUIET, processes=1)  # one attempt does not use them up
    study.config["search"]["tries_per_holdout"] = 1
    fresh = search.holdout_seeds(study)
    assert fresh[0] == search.HOLDOUT_OFFSET + 3
    assert search.rotate(study, QUIET, processes=1)
    holdout = pd.read_parquet(study.results / "search_holdout_runs.parquet")
    assert set(holdout.seed) == set(fresh)
    runs = pd.read_parquet(study.results / "proposals" / f"{community}.parquet")
    assert set(runs.seed) == set(fresh)
    assert community in [d["name"] for d in website.build(study)["schemes"]]


def test_research_runs_the_agent_command_with_its_source(study, tmp_path):
    marker = tmp_path / "source"
    script = f"import os, pathlib; pathlib.Path({str(marker)!r}).write_text(os.environ['RSS_GOV_SOURCE'])"
    study.config["research"] = dict(
        program=str(CONFIG.with_name("program.md")),
        agent=[sys.executable, "-c", script, "{prompt}"],
    )
    research.run(study, 1, QUIET, processes=1)
    assert marker.read_text() == proposals.AGENT


def test_a_named_variation_is_titled_and_listed_with_its_settings(study):
    data = website.build(study)
    (design,) = [d for d in data["schemes"] if d["name"] == "capped_1m"]
    assert design["kind"] == "named" and design["parent"] == "capped"
    assert design["changed"] == ["budget_ada"] and design["title"] == "Capped · 1M ADA"


def test_an_issue_proposal_shows_no_text_of_its_own(study):
    """Published with nobody reviewing it: titled from its rule, the idea linked, not shown."""
    name = _try(study, dict(PROPOSAL, hypothesis="anything at all"))
    data = website.build(study)
    (design,) = [d for d in data["schemes"] if d["name"] == name]
    assert design["proposal"]["issue"] == 1 and design["proposal"]["hypothesis"] is None
    assert design["title"] and "Flat test" not in design["title"]
    (listed,) = data["proposals"]
    assert (
        listed["issue"] == 1 and listed["hypothesis"] == "" and listed["title"] == design["title"]
    )


def test_rerunning_a_stored_proposal_does_not_use_up_the_holdout_seeds(study):
    _try(study, PROPOSAL)
    search.try_candidates(study, search.stored_rows(study.results), QUIET, processes=1)
    assert [e["rerun"] for e in search.ledger(study.results)] == [False, True]
    study.config["search"]["tries_per_holdout"] = 2
    assert search.holdout_seeds(study)[0] == search.HOLDOUT_OFFSET


def test_rank_simulates_every_design_on_the_holdout_seeds_once(study):
    from rss_gov import ranking

    said = []
    ranking.fill(study, said.append, processes=1)
    holdout = pd.read_parquet(study.results / "search_holdout_runs.parquet")
    runs = ranking.stored(study, holdout)
    paid = {s.name for s in study.schemes(mechanisms.experiment_rows(study.config)) if s.paid}
    assert paid <= set(holdout.scheme) | set(runs.scheme)
    assert set(runs.seed) == set(holdout.seed)
    assert set(runs.scenario) == set(study.ranking_scenarios)
    # the site ranks every one of them
    designs = website.build(study)["ranking"]["designs"]
    assert paid <= set(designs)
    # nothing to do a second time; other holdout seeds make every stored run stale
    ranking.fill(study, said.append, processes=1)
    assert said[-2].endswith(" 0 to simulate")
    assert ranking.stored(study, holdout.assign(seed=holdout.seed + 1)).empty


def test_all_ranks_after_the_proposals_and_before_the_report():
    assert cli.ALL.index(cli.cmd_try) < cli.ALL.index(cli.cmd_rank) < cli.ALL.index(cli.cmd_report)
