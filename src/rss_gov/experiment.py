"""Run schemes against the calibrated model, many seeds each, and compare them fairly.

Every scheme starts from the same chain snapshot and sees the same seeds, so comparisons
are paired: the reported effect of a scheme is the mean of (scheme - unpaid) within a
seed, with an interval across seeds. Schemes are compared on several axes at once (one
per objective family, declared in config.yaml); nothing here folds them into one score.
"""

from dataclasses import dataclass, replace
import json
import multiprocessing
import os
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from rss_gov import calibrate, dataset, mechanisms, model, static
from rss_gov.metrics import mean_ci

BASELINE = "unpaid"
_STUDY = None


@dataclass(frozen=True)
class Axis:
    """One measured dimension of the comparison."""

    name: str
    family: str
    label: str
    better: str  # "higher" or "lower"
    meaningful: float  # smallest difference from unpaid worth acting on
    scale: tuple  # (worst, best) as a difference from unpaid

    @property
    def sign(self):
        return 1.0 if self.better == "higher" else -1.0

    def score(self, diff):
        """Difference from unpaid on a 0..1 scale where 1 is best."""
        worst, best = self.scale
        return np.clip((np.asarray(diff, float) - worst) / (best - worst), 0.0, 1.0)

    @property
    def step(self):
        """The meaningful difference in score units."""
        return self.meaningful / abs(self.scale[1] - self.scale[0])

    def verdict(self, diff, half):
        """+1 better than unpaid, -1 worse, 0 no meaningful or no clear difference."""
        gain = self.sign * diff
        half = 0.0 if np.isnan(half) else half
        if gain - half > 0 and gain >= self.meaningful:
            return 1
        if gain + half < 0 and -gain >= self.meaningful:
            return -1
        return 0


@dataclass
class Study:
    config: dict
    data: dataset.Data
    params: model.Params
    world: model.World
    scenarios: dict
    validation_passed: bool

    @property
    def results(self):
        path = Path(self.config["results"])
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def budget(self):
        return float(self.config["programme"]["budget_ada"])

    @property
    def epochs(self):
        return int(self.config["programme"]["epochs"])

    @property
    def axes(self):
        return [
            Axis(
                name,
                row["family"],
                row["label"],
                row["better"],
                float(row["meaningful"]),
                tuple(float(x) for x in row["scale"]),
            )
            for name, row in self.config["axes"].items()
        ]

    @property
    def ranking_scenarios(self):
        return list(self.config["ranking_scenarios"])

    def schemes(self, rows):
        return [mechanisms.from_config(row, self.budget) for row in rows]


def load_config(path="config.yaml"):
    return yaml.safe_load(Path(path).read_text())


def open_study(config_path="config.yaml"):
    """Load data and the saved calibration, and build the starting state at the tip."""
    config = load_config(config_path)
    data = dataset.load(config["data"])
    saved = Path(config["results"]) / "calibration.json"
    if not saved.exists():
        raise FileNotFoundError("no calibration found; run `rss-gov calibrate` first")
    calibration = json.loads(saved.read_text())
    if calibration["tip_epoch"] != data.tip_epoch:
        raise ValueError(
            "the calibration belongs to a different data pull; run `rss-gov calibrate`"
        )
    # Assumptions come from the current config, so changing one needs no refit.
    fields = model.Params.__dataclass_fields__
    assumed = {k: v for k, v in config["assumptions"].items() if k in fields}
    params = replace(model.Params(**calibration["params"]), **assumed)
    world = calibrate.build_world(data, data.tip_epoch, params)
    scenarios = {
        name: model.Scenario(name, **(row or {})) for name, row in config["scenarios"].items()
    }
    return Study(config, data, params, world, scenarios, calibration["validation"]["passed"])


def _run(task):
    scheme, scenario, seed = task
    out = model.run(_STUDY.world, _STUDY.params, scheme, scenario, _STUDY.epochs, seed)
    return {"scheme": scheme.name, "scenario": scenario.name, "seed": seed, **out}


def evaluate(study, schemes, scenario_names, seeds, processes=None):
    """One row per (scheme, scenario, seed), with the scheme's exact static measures.

    Unpaid runs are shared across scenarios: nothing is paid, so no response can matter.
    """
    global _STUDY
    names = [s.name for s in schemes]
    if len(set(names)) != len(names):
        raise ValueError("scheme names must be unique")
    tasks = []
    for scheme in schemes:
        for name in scenario_names:
            if not scheme.paid and not scheme.hard_cap and name != scenario_names[0]:
                continue
            tasks += [(scheme, study.scenarios[name], seed) for seed in seeds]
    _STUDY = study
    processes = processes or max(1, (os.cpu_count() or 2) - 1)
    if processes == 1 or len(tasks) < 8:
        rows = [_run(task) for task in tasks]
    else:
        with multiprocessing.get_context("fork").Pool(processes) as pool:
            rows = pool.map(_run, tasks, chunksize=max(1, len(tasks) // (processes * 8)))
    runs = pd.DataFrame(rows)
    copies = []
    for scheme in schemes:
        if not scheme.paid and not scheme.hard_cap:
            mine = runs[runs.scheme == scheme.name]
            copies += [mine.assign(scenario=name) for name in scenario_names[1:]]
    runs = pd.concat([runs, *copies], ignore_index=True)
    checks = static.analyse(study, schemes).set_index("scheme")
    for column in STATIC:
        runs[column] = runs.scheme.map(checks[column]).astype(float)
    return runs


STATIC = ["split_gain", "newcomer_extra", "incumbent_extra"]  # exact properties of a rule
METRICS = [
    "participation",
    "tau67",
    "backing",
    "annual_cost_ada",
    "split_gain",
    "supported_ratified",
    "turnout",
    "represented_share",
    "effective_n",
    "drep_power",
    "abstain",
    "rationale_rate",
    "ballots_per_action",
    "voting_dreps",
    "dreps",
    "entrants",
    "paid_per_round",
    "top10_reward_share",
    "payments",
    "dust_share",
    "spent_ada",
]


def summarise(runs, axes=(), metrics=METRICS, baseline=BASELINE):
    """Mean per scheme and scenario, the paired difference from the baseline, and for
    each axis a verdict: +1 better than unpaid, -1 worse, 0 no meaningful difference."""
    base = runs[runs.scheme == baseline].set_index(["scenario", "seed"])
    by_name = {a.name: a for a in axes}
    rows = []
    for (scheme, scenario), group in runs.groupby(["scheme", "scenario"], sort=False):
        group = group.set_index(["scenario", "seed"])
        row = dict(scheme=scheme, scenario=scenario, seeds=len(group))
        for metric in metrics:
            mean, half = mean_ci(group[metric].values)
            row[metric] = mean
            row[f"{metric}_ci"] = half
            if len(base):
                diff = (group[metric] - base[metric].reindex(group.index)).values
                row[f"{metric}_diff"], row[f"{metric}_diff_ci"] = mean_ci(diff)
                if metric in by_name:
                    row[f"{metric}_verdict"] = by_name[metric].verdict(
                        row[f"{metric}_diff"], row[f"{metric}_diff_ci"]
                    )
        rows.append(row)
    return pd.DataFrame(rows)


def ranking(runs, scenarios):
    """Per scheme and seed, each metric averaged over the ranking scenarios."""
    runs = runs[runs.scenario.isin(scenarios)]
    mean = runs.groupby(["scheme", "seed"], sort=False)[METRICS].mean().reset_index()
    return mean.assign(scenario="ranking")
