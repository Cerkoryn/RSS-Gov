"""Net benefit: one score per design, in ADA a year, to rank designs by.

What an improvement is worth is a judgement, kept in `config.yaml` under `ranking`: ADA a
year for a unit of participation, decentralisation and pledge backing. Cost counts as
itself, and the ADA one actor could take by splitting (`split_gain` of the yearly cost)
counts as lost on top of it. Paying nothing scores 0, so a negative score means a design
is not worth its cost at those values. The score is the mean over the ranking scenarios.

Every design is scored on the same seeds (the holdout), so intervals are paired. The
search's finalists and the proposals are simulated on them anyway; `fill` (`rss-gov rank`)
simulates every other design on them too. The site recomputes all of this in the browser
when a visitor changes a value (web/ranking.js); tests/test_ranking.py keeps the two equal.
"""

import hashlib
import json

import numpy as np
import pandas as pd

from rss_gov import experiment, mechanisms
from rss_gov.experiment import BASELINE

GAINS = ("participation", "tau67", "backing")
COLUMNS = (*GAINS, "annual_cost_ada")
SHAKE = 0.5  # the robustness check moves every value by up to this share, either way


RUNS = "ranking_runs.parquet"  # the designs `fill` simulated on the holdout seeds


def _key(study, scheme, seeds):
    """What a design's runs depend on: the calibration, the model settings, the rule, the seeds."""
    config = study.config
    blob = json.dumps(
        [
            (study.results / "calibration.json").read_text(),
            {name: config["scenarios"][name] for name in study.ranking_scenarios},
            config["assumptions"],
            config["programme"],
            scheme.to_dict(),
            [int(s) for s in seeds],
        ],
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _designs(study, holdout):
    """The experiment's paid designs that the holdout does not already hold, with their keys."""
    seeds = sorted(holdout.seed.unique())
    taken = set(holdout.scheme.unique())
    schemes = study.schemes(mechanisms.experiment_rows(study.config))
    return {s.name: (s, _key(study, s, seeds)) for s in schemes if s.paid and s.name not in taken}


def stored(study, holdout):
    """The runs `fill` kept that still match the holdout seeds and the current model."""
    path = study.results / RUNS
    if not path.exists():
        return holdout.iloc[:0]
    keys = {n: k for n, (_, k) in _designs(study, holdout).items()}
    runs = pd.read_parquet(path)
    return runs[runs.key == runs.scheme.map(keys)].drop(columns="key")


def fill(study, log=print, processes=None):
    """Simulate every design the holdout lacks on its seeds, so all can be ranked together.

    Runs that still match are kept; a new calibration, other holdout seeds or a changed
    rule make a design's runs stale, and it is simulated again.
    """
    out = study.results
    holdout = pd.read_parquet(out / "search_holdout_runs.parquet")
    designs = _designs(study, holdout)
    path = out / RUNS
    stored = pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=["scheme", "key"])
    kept = stored[stored.key == stored.scheme.map({n: k for n, (_, k) in designs.items()})]
    todo = [s for n, (s, _) in designs.items() if n not in set(kept.scheme)]
    log(f"{len(designs) - len(todo)} designs up to date, {len(todo)} to simulate")
    if not todo and len(kept) == len(stored) and path.exists():
        return  # nothing changed: leave the file as it is
    if todo:
        seeds = sorted(holdout.seed.unique())
        runs = experiment.evaluate(study, todo, study.ranking_scenarios, seeds, processes)
        runs["key"] = runs.scheme.map({n: k for n, (_, k) in designs.items()})
        kept = pd.concat([kept, runs], ignore_index=True) if len(kept) else runs
    kept.to_parquet(path)
    log(f"wrote {path}")


def values(config):
    """ADA a year one unit of each gain is worth, in the axis's own units; and the Sybil loss."""
    rows = config["ranking"]["value"]
    return [rows[a]["ada"] / rows[a]["per"] for a in GAINS], float(config["ranking"]["sybil_loss"])


def inputs(runs, scenarios):
    """Per design: mean paired differences from unpaid (scenario x COLUMNS), the covariance
    of those means over seeds (scenario-major, as one flat vector), and its split gain."""
    cols = list(COLUMNS)
    runs = runs[runs.scenario.isin(scenarios)]
    table = runs.groupby(["scheme", "scenario", "seed"])[[*cols, "split_gain"]].mean()
    base = table.loc[BASELINE, cols]
    out = {}
    for name in table.index.unique(level=0):
        own = table.loc[name]
        if name == BASELINE or set(own.index.unique(level=0)) != set(scenarios):
            continue
        diff = own[cols] - base.reindex(own.index)  # same scenario, same seed
        wide = np.hstack([diff.loc[s].sort_index().to_numpy() for s in scenarios])
        out[name] = dict(
            mean=wide.mean(axis=0).reshape(len(scenarios), len(cols)),
            cov=np.cov(wide, rowvar=False) / len(wide),
            split=float(own.split_gain.iloc[0]),
        )
    return out


def _weights(design, value, sybil_loss, k=1.0):
    """What one unit of each column is worth: the gains at k times their value, then cost."""
    return np.array([k * v for v in value] + [-(1 + sybil_loss * design["split"])])


def score(design, value, sybil_loss, k=1.0):
    """Net benefit in each scenario, their mean, and the 95% half-interval of the mean."""
    g = _weights(design, value, sybil_loss, k)
    by_scenario = design["mean"] @ g
    flat = np.tile(g, len(by_scenario)) / len(by_scenario)
    return (
        by_scenario,
        by_scenario.mean(),
        1.96 * float(np.sqrt(max(flat @ design["cov"] @ flat, 0))),
    )


def table(designs, value, sybil_loss, scenarios, draws=2000, seed=0):
    """Every design ranked by net benefit, with paying nothing as a row at zero.

    `behind`: the most it falls short of the best design in any one scenario (regret).
    `worth_from`: the share of the stated values at which its gains pay for its cost.
    `first`: how often it ranks first when every value moves by up to SHAKE either way.
    """
    names = list(designs)
    rows = []
    for name in names:
        by, mean, half = score(designs[name], value, sybil_loss)
        rows.append([name, *by, mean, half])
    frame = pd.DataFrame(rows, columns=["scheme", *scenarios, "score", "ci"])
    frame.loc[len(frame)] = [BASELINE, *[0.0] * len(scenarios), 0.0, 0.0]
    best = frame[scenarios].max()
    frame["behind"] = (best - frame[scenarios]).max(axis=1)
    avg = np.array([designs[n]["mean"].mean(axis=0) for n in names] + [np.zeros(len(COLUMNS))])
    split = np.array([designs[n]["split"] for n in names] + [0.0])
    gains = avg[:, :3] @ np.array(value)
    cost = -avg[:, 3] * (1 + sybil_loss * split)
    with np.errstate(divide="ignore", invalid="ignore"):
        frame["worth_from"] = np.where(gains > 0, -cost / gains, np.inf)
    frame.loc[frame.scheme == BASELINE, "worth_from"] = np.nan
    shake = np.random.default_rng(seed).uniform(1 - SHAKE, 1 + SHAKE, (draws, 4))
    scores = (avg[:, :3] * value) @ shake[:, :3].T - avg[:, 3:4] * (
        1 + sybil_loss * np.outer(split, shake[:, 3])
    )
    frame["first"] = np.bincount(scores.argmax(axis=0), minlength=len(frame)) / draws
    return frame.sort_values("score", ascending=False, ignore_index=True)
