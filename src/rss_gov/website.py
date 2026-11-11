"""Write the results site: results/site/, a folder of static pages.

    index.html     results: every design on every axis, with charts
    methods.html   how it works: METHODS.md rendered, so the site never disagrees with it
    propose.html   a form for proposing a reward scheme
    data.js        every number the pages show
    today.js       today's DReps, for the exact checks on the proposal page (checks.js)
    accounts.js    their delegating accounts; loaded only for rules that pay delegators

The folder can be opened from disk, served by `rss-gov serve`, or published on any static
host. Named schemes carry the numbers of the experiment (as in report.md); designs found by
the search and community proposals carry their numbers from the holdout seeds.
"""

import hashlib
import json
import os
from pathlib import Path
import re

import markdown
import numpy as np
import pandas as pd
import yaml

from rss_gov import experiment, mechanisms, proposals, report, search, static

WEB = Path(__file__).with_name("web")
PAGES = [
    "index.html",
    "propose.html",
    "site.css",
    "common.js",
    "dashboard.js",
    "propose.js",
    "checks.js",
]
ASSET = re.compile(r'(src|href)="([\w.-]+\.(?:js|css))"')
BASELINE = experiment.BASELINE
# Per axis: plain name, the question it answers, what a change is measured in, unit, decimals.
DISPLAY = dict(
    participation=(
        "Participation", "How much delegated ADA casts a vote", "change in points", " pts", 1
    ),
    tau67=(
        "Decentralisation", "How many DReps it takes to hold 2/3 of the voting power",
        "change in DReps", "", 1,
    ),
    backing=(
        "Skin in the game", "How much voting power is backed by DReps' own ADA",
        "change in points", " pts", 2,
    ),
    annual_cost_ada=("Cost", "ADA paid from the treasury each year", "M ADA a year", "M", 1),
    split_gain=(
        "Sybil risk", "How much of the budget one actor gains by posing as many DReps",
        "% of budget", "%", 0,
    ),
)  # fmt: skip
CHANNELS = dict(
    voting_only="DReps vote more",
    yield_only="Delegators chase yield",
    reinvest_only="Awards buy reach",
    pledge_only="DReps add own stake",
)
FACTS = [
    "paid_dreps", "max_award", "top10_award_share", "newcomer_capture", "newcomer_extra",
    "newcomer_identities", "incumbent_extra", "incumbent_rank", "incumbent_parts", "power_kept",
    "delegator_claimants", "delegator_dust_share",
]  # fmt: skip
EXACT = ("annual_cost_ada", "split_gain")
CHECKS = dict(
    report.LABELS,
    dreps="DReps with voting power",
    turnover="Delegation share moving per epoch",
    turnout="Turnout of active DRep power",
    supported_ratified="Supported actions ratified",
    ratified="Actions ratified",
    ballots="Ballots per action",
)


SHAPES = {
    0.0: "Equal",
    0.25: "Near-equal",
    0.5: "Square-root",
    0.75: "Near-proportional",
    1.0: "Proportional",
}


def _amount(ada):
    ada = float(ada)
    if ada >= 1e6:
        return f"{ada / 1e6:g}M"
    return f"{ada / 1e3:g}k" if ada >= 1e3 else f"{ada:g}"


def _features(s):
    """What sets a rule apart, most telling first."""
    out = []
    share, cap = s["delegator_share"], s["cap_ada"]
    small_cap = cap is not None and np.isfinite(cap) and cap <= 2e6
    if share >= 0.5:
        out.append("half to delegators" if share == 0.5 else f"{share:.0%} to delegators")
    k, n = int(s["k_exclude"]), int(s["n_pay"])
    if k and n:
        out.append(f"ranks {k + 1}–{k + n}")
    elif k:
        out.append(f"skip top {k}")
    elif n:
        out.append(f"top {n} only")
    if small_cap:
        out.append(f"{_amount(cap)} cap")
    if s["rationale_bonus"] >= 1:
        out.append(f"rationales ×{1 + s['rationale_bonus']:g}")
    if s["pledge_leverage"]:
        out.append(f"≤{s['pledge_leverage']:g}× own stake")
    if 0 < share < 0.5:
        out.append(f"{share:.0%} to delegators")
    if 0 < s["rationale_bonus"] < 1:
        out.append(f"rationales ×{1 + s['rationale_bonus']:g}")
    if s["activity_gate"]:
        out.append(f"{s['activity_gate']:.0%} turnout")
    if s["min_stake_ada"]:
        out.append(f"min {_amount(s['min_stake_ada'])}")
    if s["min_delegators"]:
        out.append(f"{int(s['min_delegators'])}+ delegators")
    if cap is not None and np.isfinite(cap) and not small_cap:
        out.append(f"{_amount(cap)} cap")
    return out


def titles(schemes):
    """Short readable names for generated designs: shape, its most telling feature, budget.

    Designs that would share a name each gain their first feature the others lack.
    """
    parts = {}
    for name, scheme in schemes.items():
        s = scheme.to_dict()
        shape = SHAPES.get(float(s["alpha"]), f"Power {float(s['alpha']):g}")
        feats = _features(s)
        parts[name] = (shape, feats, feats[:1], f"{_amount(s['budget_ada'])} ADA")
    name_of = {n: ", ".join([p[0], *p[2], p[3]]) for n, p in parts.items()}
    groups = {}
    for n, title in name_of.items():
        groups.setdefault(title, []).append(n)
    for members in groups.values():
        if len(members) < 2:
            continue
        for n in members:
            shape, feats, chosen, budget = parts[n]
            others = [set(parts[o][1]) for o in members if o != n]
            extra = next(
                (f for f in feats if f not in chosen and any(f not in o for o in others)), None
            )
            if extra:
                name_of[n] = ", ".join([shape, *chosen, extra, budget])
    return name_of


def _plain(value):
    """Numpy and pandas values as JSON types, six significant digits, NaN as null."""
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray, pd.Series, pd.Index)):
        return [_plain(v) for v in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(f"{value:.6g}") if np.isfinite(value) else None
    return value


def _axes(study):
    rows = []
    for axis in study.axes:
        short, question, change, unit, digits = DISPLAY.get(
            axis.name, (axis.label, axis.label, "change", "", 2)
        )
        basis, pilot = report.EVIDENCE.get(axis.name, ("simulated", ""))
        factor, long_unit = report._scale(axis)
        rows.append(
            dict(
                name=axis.name,
                family=axis.family,
                label=axis.label,
                better=axis.better,
                short=short,
                question=question,
                change=change,
                unit=unit,
                digits=digits,
                factor=factor,
                meaningful=f"{axis.meaningful * factor:g} {long_unit}".strip(),
                threshold=axis.meaningful * factor,
                exact=axis.name in EXACT,
                basis=basis,
                pilot=pilot,
            )
        )
    return rows


def _proposals(study, holdout):
    """Simulated proposals whose runs match the current calibration and holdout seeds."""
    out = study.results
    current = proposals.fingerprint(out)
    seeds = set(holdout.seed.unique())
    found = {}
    for path in sorted(proposals.folder(out).glob("*.json")):
        entry = json.loads(path.read_text())
        runs_path = path.with_suffix(".parquet")
        if entry.get("calibration") != current or not runs_path.exists():
            continue
        runs = pd.read_parquet(runs_path)
        if set(runs.seed.unique()) != seeds:
            continue
        row, _ = proposals.split(entry["scheme"])
        found[path.stem] = (mechanisms.from_config(row, 0), entry, runs)
    return found


def _scores(study, runs):
    """Each design's five scaled scores, the points the coverage is measured on.

    The page ranks designs by what each adds to coverage with these, for whichever
    designs are switched on. Unpaid is the origin of every axis.
    """
    names, cube = search.per_seed(runs, study.axes, study.ranking_scenarios)
    points = search.scores(cube, names, study.axes)
    return {n: [round(float(v), 9) for v in points[i]] for i, n in enumerate(names)}


def _judged(summary, name, axes, ranking, guard, split_gain):
    worst = {
        a.name: min(int(summary.loc[(name, s), f"{a.name}_verdict"]) for s in ranking) for a in axes
    }
    return search.breaks(split_gain, worst, axes, guard)


def build(study):
    """Everything the pages show, as one JSON-ready dictionary."""
    out = study.results
    axes = study.axes
    names = [a.name for a in axes]
    ranking = study.ranking_scenarios
    config = study.config
    guard = config["guardrails"]
    rows = config["experiment"]["schemes"]
    schemes = {s.name: s for s in study.schemes(rows) if s.name != BASELINE}
    named = set(schemes)
    ladder = [r["name"] for r in rows if isinstance(r, dict) and "budget_ada" in r]
    parent = next((r["preset"] for r in rows if isinstance(r, dict) and r.get("preset")), None)
    summary = pd.read_csv(out / "experiment_summary.csv")
    base = summary[(summary.scheme == BASELINE) & (summary.scenario == ranking[0])].iloc[0]

    flags, found, community = None, None, {}
    if (out / "search_front.csv").exists():  # written by `rss-gov report` / `rss-gov search`
        flags = pd.read_csv(out / "search_front.csv").fillna({"breaks": ""}).set_index("scheme")
        found = json.loads((out / "search.json").read_text())
        holdout = pd.read_parquet(out / "search_holdout_runs.parquet")
        community = _proposals(study, holdout)
        finalists = study.schemes(yaml.safe_load((out / "search_finalists.yaml").read_text()))
        extra = {s.name: s for s in finalists if s.name not in schemes and s.name not in community}
        pool = [holdout[holdout.scheme.isin([*extra, BASELINE])]]
        pool += [runs for _, _, runs in community.values()]
        judged = experiment.summarise(pd.concat(pool), axes, metrics=names + ["payments"])
        summary = pd.concat([summary, judged[judged.scheme != BASELINE]], ignore_index=True)
        schemes.update(extra)
        schemes.update({name: scheme for name, (scheme, _, _) in community.items()})
    summary = summary.set_index(["scheme", "scenario"])
    facts = static.analyse(study, list(schemes.values())).set_index("scheme")

    generated = titles({n: s for n, s in schemes.items() if search.GENERATED.fullmatch(n)})
    designs = []
    for name, scheme in schemes.items():
        results = {}
        for scenario in summary.loc[name].index:
            row = summary.loc[(name, scenario)]
            results[scenario] = {a: [row[f"{a}_diff"], row[f"{a}_diff_ci"]] for a in names}
            results[scenario]["payments"] = row["payments"]
        marks = {
            a: report._mark([summary.loc[(name, s), f"{a}_verdict"] for s in ranking]).strip()
            for a in names
        }
        if name in community:
            kind = "proposed"
        elif search.GENERATED.fullmatch(name):
            kind = "search"
        elif name in ladder:
            kind = "ladder"
        elif name in named:
            kind = "named"
        else:
            kind = "proposed"
        feasibility = scheme.feasibility()
        judged = flags.loc[name] if flags is not None and name in flags.index else None
        design = dict(
            name=name,
            title=generated.get(name),
            rule=scheme.label(),
            kind=kind,
            budget=scheme.budget_ada,
            pilot=feasibility["pilot_testable"],
            notes=feasibility["notes"],
            breaks=None if judged is None else judged.breaks,
            unbeaten=None if judged is None else judged.on_front,
            marks=marks,
            results=results,
            facts=facts.loc[name, FACTS].to_dict(),
            scheme={k: v for k, v in scheme.to_dict().items() if k != "name"},
        )
        if name in community:
            _, entry, _ = community[name]
            design["breaks"] = _judged(
                summary, name, axes, ranking, guard, float(facts.loc[name, "split_gain"])
            )
            design["proposal"] = {
                k: entry.get(k) for k in ("hypothesis", "author", "accepted", "reason", "evaluated")
            }
        designs.append(design)

    calibration = json.loads((out / "calibration.json").read_text())["validation"]
    checks = []
    for check in calibration["checks"]:
        scale = 1e9 if check["metric"] in ("drep_power", "abstain") else 1.0
        label = CHECKS.get(check["metric"], check["metric"].replace("_", " "))
        scaled = {k: check[k] / scale for k in ("observed", "simulated", "low", "high")}
        checks.append({**check, **scaled, "metric": label})
    bands = None
    if (out / "validation_bands.csv").exists():
        table = pd.read_csv(out / "validation_bands.csv", index_col=0)
        bands = dict(epochs=table.index, panels=[])
        for name, label in report.LABELS.items():
            scale = 1e9 if name in ("drep_power", "abstain") else 1.0
            series = {k: table[f"{name}_{k}"] / scale for k in ("observed", "mean", "low", "high")}
            bands["panels"].append(dict(label=label, **series))

    search_note = None
    if found is not None:
        search_note = dict(
            evaluated=found["history"][-1]["evaluated"],
            generations=len(found["history"]) - 1,
            finalists=len(flags),
            unbeaten=len(found["front"]),
            acceptable=int(flags.acceptable.sum()),
            holdout_seeds=found["holdout_seeds"],
            hypervolume=found["hypervolume"],
            hypervolume_ci=found.get("hypervolume_ci"),
            hypervolume_unpaid=found["hypervolume_unpaid"],
            baseline=BASELINE,
            search_gain=found.get("search_gain"),
            history=[
                dict(
                    generation=h["generation"],
                    evaluated=h["evaluated"],
                    hypervolume=h["hypervolume"],
                    hypervolume_guarded=h.get("hypervolume_guarded"),
                )
                for h in found["history"]
            ],
            scores=_scores(
                study, pd.concat([holdout, *[runs for _, _, runs in community.values()]])
            ),
            hypervolume_guarded=found.get("hypervolume_guarded"),
            hypervolume_guarded_ci=found.get("hypervolume_guarded_ci"),
            hypervolume_named_guarded=found.get("hypervolume_named_guarded"),
        )
    site = config.get("site") or {}
    defaults = {k: v for k, v in mechanisms.Scheme().to_dict().items() if k != "name"}
    return _plain(
        dict(
            meta=dict(
                tip_epoch=study.data.tip_epoch,
                budget=study.budget,
                epochs=study.epochs,
                treasury=study.data.treasury,
                seeds=int(base.seeds),
                scenarios=ranking,
                channels=[
                    dict(name=k, label=CHANNELS.get(k, k))
                    for k in study.scenarios
                    if k.endswith("_only")
                ],
                validation_passed=study.validation_passed,
                validation=calibration,
                split_limit=guard["max_split_gain"],
                capital=config["sybil"]["newcomer_capital_ada"],
                min_payout=study.params.min_payout_ada,
                ladder_parent=parent,
                repository=site.get("repository"),
                built=proposals.now(),
            ),
            today=report.today(study),
            baseline={a: base[a] for a in names},
            axes=_axes(study),
            schemes=designs,
            checks=checks,
            bands=bands,
            search=search_note,
            form=dict(
                fields=proposals.FIELDS,
                meta=proposals.META,
                defaults={**defaults, "budget_ada": study.budget},
                presets={
                    name: {
                        **defaults,
                        "budget_ada": study.budget,
                        **mechanisms.PRESETS[name],
                    }
                    for name in mechanisms.PRESETS
                    if name != BASELINE
                },
            ),
            proposals=proposals.listing(out),
        )
    )


def methods(path="METHODS.md", repository=None):
    """METHODS.md as HTML: (contents list, body)."""
    text = Path(path).read_text()
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "2-3", "permalink": "#"}},
    )
    body = md.convert(text).replace("<table>", '<div class="tablewrap"><table>')
    body = body.replace("</table>", "</table></div>")
    return md.toc, body


def _put(path, text):
    """Replace a file in one step, so a server never hands out half of it."""
    part = path.with_name(path.name + ".part")
    part.write_text(text)
    os.replace(part, path)


def _version(text):
    return hashlib.sha256(text.encode()).hexdigest()[:10]


def _script(variable, value):
    return f"window.{variable} = {json.dumps(value, allow_nan=False, separators=(',', ':'))};\n"


def write(study, folder=None):
    """Write every page of the site; returns the folder."""
    folder = Path(folder or study.results / "site")
    folder.mkdir(parents=True, exist_ok=True)
    files = {name: (WEB / name).read_text() for name in PAGES if not name.endswith(".html")}
    files["data.js"] = _script("RSS", build(study))
    today, accounts = static.export(study)
    files["accounts.js"] = _script("RSS_ACCOUNTS", accounts)
    today["accounts"] = f"accounts.js?v={_version(files['accounts.js'])}"
    files["today.js"] = _script("RSS_TODAY", today)
    site = study.config.get("site") or {}
    toc, body = methods(site.get("methods", "METHODS.md"))
    edit = ""
    if site.get("repository"):
        url = f"{site['repository'].rstrip('/')}/edit/main/METHODS.md"
        edit = f'<a class="button" href="{url}">Suggest a change to this page</a>'
    pages = {name: (WEB / name).read_text() for name in PAGES if name.endswith(".html")}
    page = (WEB / "methods.html").read_text()
    page = page.replace("<!--TOC-->", toc).replace("<!--METHODS-->", body)
    pages["methods.html"] = page.replace("<!--EDIT-->", edit)
    # Each page asks for its scripts and styles by content hash, so a browser or a cache
    # (GitHub Pages keeps files for ten minutes) never mixes a new page with an old file.
    versions = {name: _version(text) for name, text in files.items()}
    for name, page in pages.items():
        files[name] = ASSET.sub(
            lambda m: f'{m[1]}="{m[2]}?v={versions[m[2]]}"' if m[2] in versions else m[0], page
        )
    files[".nojekyll"] = ""  # GitHub Pages: serve the files as they are
    for name, text in files.items():
        _put(folder / name, text)
    return folder
