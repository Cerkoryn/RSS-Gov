"""Search the scheme family for designs that trade the axes off well.

A plain evolutionary search: no language model in the loop. Schemes are compared on every
axis in config.yaml at once. A scheme stays on the front unless another is at least as
good on every axis and meaningfully better on one. Budget is one of the searched
parameters, so cost is a real axis: a cheaper programme can stay on the front.

Because a search over noisy runs will always "find" something, the finalists are re-run
on fresh seeds that the search never saw, and only those numbers are reported.
"""

from dataclasses import replace
import json

import numpy as np
import pandas as pd
import yaml

from rss_gov import experiment, mechanisms, proposals
from rss_gov.metrics import epsilon_front, hypervolume, mean_ci

HOLDOUT_OFFSET = 1_000_000  # holdout seeds never overlap search seeds
FINALISTS = 20
BOOTSTRAPS = 400
BASELINE = experiment.BASELINE

CHOICES = dict(
    alpha=[0.0, 0.25, 0.5, 0.75, 1.0],
    cap_ada=[None, None, 2e6, 1e7, 5e7, 2e8],
    k_exclude=[0, 0, 0, 5, 10, 20],
    n_pay=[0, 0, 0, 50, 100, 200, 400],
    min_stake_ada=[0.0, 1e4, 1e5, 1e6],
    min_delegators=[0, 0, 5, 10, 25, 50],
    activity_gate=[0.0, 0.0, 0.25, 0.5, 0.75],
    rationale_bonus=[0.0, 0.0, 0.5, 1.0, 2.0],
    delegator_share=[0.0, 0.0, 0.25, 0.5, 0.8],
    delegator_mode=["passthrough", "flat"],
    pledge_leverage=[0.0, 0.0, 0.0, 100.0, 1000.0, 10000.0],
)
HARD_FORK_CHOICES = dict(hard_cap=[False, False, True])


def _options(study):
    config = study.config["search"]
    options = dict(budget_ada=[float(b) for b in config["budgets_ada"]], **CHOICES)
    if config.get("allow_hard_fork", False):
        options.update(HARD_FORK_CHOICES)
    return options


def _make(values, name):
    values = dict(values)
    if values.get("cap_ada") is None:
        values.pop("cap_ada", None)
    if values.get("hard_cap") and not values.get("pledge_leverage"):
        values["hard_cap"] = False
    return mechanisms.Scheme(name=name, **values)


def random_scheme(rng, name, options):
    return _make({f: choices[rng.integers(len(choices))] for f, choices in options.items()}, name)


def mutate(scheme, rng, name, options):
    values = {f: getattr(scheme, f) for f in options}
    if np.isinf(values["cap_ada"]):
        values["cap_ada"] = None
    for field in rng.choice(list(options), size=rng.integers(1, 3), replace=False):
        values[field] = options[field][rng.integers(len(options[field]))]
    return _make(values, name)


def signature(scheme):
    return tuple(sorted((k, v) for k, v in scheme.to_dict().items() if k != "name"))


def per_seed(runs, axes, scenarios):
    """Axis values per scheme and seed, averaged over the given scenarios."""
    runs = runs[runs.scenario.isin(scenarios)]
    columns = [a.name for a in axes]
    table = runs.groupby(["scheme", "seed"])[columns].mean()
    names = list(table.index.get_level_values(0).unique())
    seeds = sorted(runs.seed.unique())
    cube = np.stack([table.loc[name].reindex(seeds).values for name in names])
    return names, cube  # cube: scheme x seed x axis


def scores(cube, names, axes):
    """Each scheme's seed-mean difference from unpaid on every axis, scaled to 0..1."""
    means = np.nanmean(cube, axis=1)
    diff = means - means[names.index(BASELINE)]
    return np.column_stack([a.score(diff[:, j]) for j, a in enumerate(axes)])


def front_of(points, names, axes, members=None):
    """Names on the front: not beaten on every axis by a meaningful margin.

    `members` limits the contest to those names (None: every name; an empty list: none).
    """
    members = [n for n in (names if members is None else members) if n in names]
    rows = [names.index(n) for n in members]
    keep = epsilon_front(points[rows], [a.step for a in axes])
    return [members[i] for i in keep]


def volume(cube, names, axes, members):
    """Hypervolume of `members` plus unpaid (doing nothing is always available)."""
    points = scores(cube, names, axes)
    rows = sorted({names.index(m) for m in members} | {names.index(BASELINE)})
    return hypervolume(points[rows], np.zeros(len(axes)))


def within_limit(cube, names, axes, limit, members=None):
    """Members whose splitting gain is inside the Sybil guardrail (it is exact, so seed-free)."""
    j = [a.name for a in axes].index("split_gain")
    gain = np.nanmean(cube[:, :, j], axis=1)
    members = names if members is None else members
    return [n for n in members if n != BASELINE and gain[names.index(n)] <= limit + 1e-12]


def bootstrap(cube, names, statistic, rng, draws=BOOTSTRAPS):
    """Resample seeds (the same seeds for every scheme) and recompute a statistic."""
    n = cube.shape[1]
    values = [statistic(cube[:, rng.integers(0, n, n), :], names) for _ in range(draws)]
    return np.quantile(values, [0.025, 0.975])


def run(study, log=print, processes=None):
    config = study.config["search"]
    axes = study.axes
    scenarios = study.ranking_scenarios
    options = _options(study)
    rng = np.random.default_rng(20260101)
    seeds = range(int(config["seeds"]))
    limit = study.config["guardrails"]["max_split_gain"]
    baseline = study.schemes([BASELINE])[0]

    presets = [s for s in study.schemes(study.config["experiment"]["schemes"]) if s.paid]
    presets = [s for s in presets if "hard_cap" in options or not s.hard_cap]
    population = presets + [
        random_scheme(rng, f"g0_{i}", options) for i in range(int(config["population"]))
    ]
    known, records = {}, []
    all_runs = [experiment.evaluate(study, [baseline], scenarios, seeds, processes)]
    history = []
    for generation in range(int(config["generations"]) + 1):
        fresh = []
        for scheme in population:
            if signature(scheme) not in known:
                known[signature(scheme)] = scheme
                fresh.append(scheme)
                records.append(dict(scheme=scheme.name, generation=generation, **scheme.to_dict()))
        if fresh:
            all_runs.append(experiment.evaluate(study, fresh, scenarios, seeds, processes))
        runs = pd.concat(all_runs, ignore_index=True)
        names, cube = per_seed(runs, axes, scenarios)
        points = scores(cube, names, axes)
        front = [n for n in front_of(points, names, axes) if n != BASELINE]
        size = volume(cube, names, axes, front)
        guarded = front_of(points, names, axes, within_limit(cube, names, axes, limit))
        guarded_size = volume(cube, names, axes, guarded)
        history.append(
            dict(
                generation=generation,
                evaluated=len(names) - 1,
                front=len(front),
                hypervolume=size,
                hypervolume_guarded=guarded_size,
            )
        )
        log(
            f"generation {generation}: {len(fresh)} new, {len(names) - 1} in total, "
            f"front {len(front)}, hypervolume {size:.5f} ({guarded_size:.5f} within the Sybil limit)"
        )
        by_name = {s.name: s for s in known.values()}
        parents = [by_name[n] for n in front] or presets
        population = [
            mutate(parents[rng.integers(len(parents))], rng, f"g{generation + 1}_{i}", options)
            if rng.random() < 0.8
            else random_scheme(rng, f"g{generation + 1}_{i}", options)
            for i in range(int(config["population"]))
        ]

    # Keep the finalists that add the most hypervolume, then judge them on unseen seeds.
    # The same again inside the Sybil guardrail, so the safer front is judged too.
    finalists = _largest_contributors(cube, names, axes, front, FINALISTS)
    for name in _largest_contributors(cube, names, axes, guarded, FINALISTS):
        if name not in finalists:
            finalists.append(name)
    for preset in presets:  # familiar schemes stay in for comparison
        if preset.name not in finalists:
            finalists.append(preset.name)
    schemes = [baseline] + [by_name[n] for n in finalists]
    holdout_seeds = range(HOLDOUT_OFFSET, HOLDOUT_OFFSET + int(config["holdout_seeds"]))
    holdout = experiment.evaluate(study, schemes, scenarios, holdout_seeds, processes)
    out = study.results
    pd.DataFrame(records).to_csv(out / "search_candidates.csv", index=False)
    holdout.to_parquet(out / "search_holdout_runs.parquet")
    (out / "search_finalists.yaml").write_text(
        yaml.safe_dump([s.to_dict() for s in schemes if s.paid], sort_keys=False)
    )
    (out / "search_history.json").write_text(json.dumps(history, indent=1, default=float))
    summary = rejudge(study, log)
    (out / "front.yaml").write_text(
        yaml.safe_dump([by_name[n].to_dict() for n in summary["front"]], sort_keys=False)
    )
    log(f"wrote {out / 'search_front.csv'} and {out / 'front.yaml'}")
    return summary


def rejudge(study, log=print):
    """Judge the saved holdout runs again, e.g. after a guardrail or an axis scale moved.

    Nothing is simulated: the verdicts are recomputed from the stored runs.
    """
    out = study.results
    holdout = pd.read_parquet(out / "search_holdout_runs.parquet")
    rows = yaml.safe_load((out / "search_finalists.yaml").read_text())
    schemes = study.schemes([BASELINE]) + study.schemes(rows)
    summary = judge(study, holdout, schemes, log)
    summary["table"].to_csv(out / "search_front.csv", index=False)
    history = json.loads((out / "search_history.json").read_text())
    (out / "search.json").write_text(
        json.dumps(
            dict(history=history, **{k: v for k, v in summary.items() if k != "table"}),
            indent=2,
            default=float,
        )
    )
    return summary


def _largest_contributors(cube, names, axes, front, limit):
    chosen = []
    remaining = list(front)
    while remaining and len(chosen) < limit:
        best = max(remaining, key=lambda n: volume(cube, names, axes, chosen + [n]))
        chosen.append(best)
        remaining.remove(best)
    return chosen


def breaks(split_gain, worst, axes, guard):
    """The guardrails a design crosses, given its worst verdict per axis over the scenarios."""
    out = ["sybil resistance"] if split_gain > guard["max_split_gain"] else []
    if guard.get("no_axis_worse_than_unpaid", True):
        exact = ("annual_cost_ada", "split_gain")
        out += [a.family.lower() for a in axes if a.name not in exact and worst[a.name] == -1]
    return ", ".join(out)


def judge(study, holdout, schemes, log=print):
    """Score finalists on holdout seeds: every axis with its interval and a verdict.

    Verdicts compare with unpaid: +1 better, -1 worse, 0 no meaningful or no clear
    difference. `breaks` lists the guardrails a scheme crosses: the splitting limit, and
    any axis on which it is worse than unpaid in some ranking scenario. Schemes that break
    nothing and are unbeaten form the shortlist. Because every design gives something up,
    `best_of_its_kind` also marks the unbeaten schemes among those with the same `breaks`:
    the best available for someone willing to accept that particular downside.
    """
    axes = study.axes
    scenarios = study.ranking_scenarios
    guard = study.config["guardrails"]
    names, cube = per_seed(holdout, axes, scenarios)
    base = names.index(BASELINE)
    points = scores(cube, names, axes)
    candidates = [n for n in names if n != BASELINE]
    front = [n for n in front_of(points, names, axes) if n != BASELINE]
    by_name = {s.name: s for s in schemes}
    each = {s: per_seed(holdout, axes, [s]) for s in scenarios}
    rows = []
    for name in candidates:
        i = names.index(name)
        scheme = by_name[name]
        row = dict(scheme=name, rule=scheme.label(), on_front=name in front)
        worst = {}
        for scenario, (scenario_names, scenario_cube) in each.items():
            a, b = scenario_names.index(name), scenario_names.index(BASELINE)
            for j, axis in enumerate(axes):
                diff, half = mean_ci(scenario_cube[a, :, j] - scenario_cube[b, :, j])
                row[f"{axis.name}_diff_{scenario}"] = diff
                verdict = axis.verdict(diff, half)
                worst[axis.name] = min(worst.get(axis.name, 1), verdict)
        for j, axis in enumerate(axes):
            diff, half = mean_ci(cube[i, :, j] - cube[base, :, j])
            row[axis.name] = float(np.nanmean(cube[i, :, j]))
            row[f"{axis.name}_diff"], row[f"{axis.name}_diff_ci"] = diff, half
            row[f"{axis.name}_verdict"] = axis.verdict(diff, half)
            row[f"{axis.name}_robust"] = worst[axis.name]  # worst verdict in any scenario
        behaviour = [a.name for a in axes if a.name not in ("annual_cost_ada", "split_gain")]
        row.update(
            better_everywhere=sum(worst[a] == 1 for a in behaviour),
            worse_somewhere=sum(worst[a] == -1 for a in behaviour),
            pilot_testable=scheme.feasibility()["pilot_testable"],
        )
        row["breaks"] = breaks(row["split_gain"], worst, axes, guard)
        row["acceptable"] = not row["breaks"]
        rows.append({**row, **{k: v for k, v in scheme.to_dict().items() if k != "name"}})
    table = pd.DataFrame(rows)
    acceptable = list(table.scheme[table.acceptable])
    pilot = list(table.scheme[table.acceptable & table.pilot_testable])
    table["shortlist"] = table.scheme.isin(front_of(points, names, axes, acceptable + [BASELINE]))
    table["pilot_shortlist"] = table.scheme.isin(front_of(points, names, axes, pilot + [BASELINE]))
    best = []
    for _, group in table.groupby(["breaks", "pilot_testable"]):
        best += front_of(points, names, axes, list(group.scheme))
    table["best_of_its_kind"] = table.scheme.isin(best)
    table = table.sort_values(
        ["pilot_shortlist", "shortlist", "on_front", "better_everywhere"], ascending=False
    )

    rng = np.random.default_rng(7)
    size = volume(cube, names, axes, candidates)
    low, high = bootstrap(cube, names, lambda c, n: volume(c, n, axes, candidates), rng)
    presets = [n for n in candidates if not proposals.GENERATED.fullmatch(n)]
    gain = size - volume(cube, names, axes, presets)
    gain_low, gain_high = bootstrap(
        cube,
        names,
        lambda c, n: volume(c, n, axes, candidates) - volume(c, n, axes, presets),
        rng,
    )
    nothing = volume(cube, names, axes, [])
    limit = guard["max_split_gain"]
    safe = within_limit(cube, names, axes, limit, candidates)
    safe_presets = [n for n in safe if n in presets]
    guarded = volume(cube, names, axes, safe)
    guarded_low, guarded_high = bootstrap(cube, names, lambda c, n: volume(c, n, axes, safe), rng)
    named_guarded = volume(cube, names, axes, safe_presets)
    log(
        f"holdout: {len(front)} of {len(candidates)} finalists on the front, "
        f"{int(table.shortlist.sum())} shortlisted ({int(table.pilot_shortlist.sum())} pilot-testable)"
    )
    log(
        f"hypervolume {size:.5f} (95% {low:.5f}..{high:.5f}; unpaid alone {nothing:.5f}); "
        f"search adds {gain:.5f} over the named schemes (95% {gain_low:.5f}..{gain_high:.5f})"
    )
    return dict(
        table=table,
        front=front,
        shortlist=list(table.scheme[table.shortlist]),
        pilot_shortlist=list(table.scheme[table.pilot_shortlist]),
        axes=[a.name for a in axes],
        scenarios=scenarios,
        baseline={a.name: float(np.nanmean(cube[base, :, j])) for j, a in enumerate(axes)},
        hypervolume=size,
        hypervolume_ci=[low, high],
        hypervolume_unpaid=nothing,
        search_gain=gain,
        search_gain_ci=[gain_low, gain_high],
        hypervolume_guarded=guarded,
        hypervolume_guarded_ci=[guarded_low, guarded_high],
        hypervolume_named_guarded=named_guarded,
        holdout_seeds=int(cube.shape[1]),
    )


def try_candidates(study, rows, log=print, processes=None):
    """Test proposed schemes against the current front on the holdout seeds.

    A proposal is accepted when it is allowed by the hard-fork setting, differs from every
    design on the front by a meaningful amount on some axis without being beaten by one,
    and raises the front's hypervolume by an amount whose 95% interval excludes zero.
    Every proposal, accepted or not, is appended to results/ledger.jsonl with its change
    on each axis, and kept in results/proposals/ with its runs so the site can show it.
    """
    out = study.results
    if not (out / "search_holdout_runs.parquet").exists():
        raise FileNotFoundError("no front to compare with; run `rss-gov search` first")
    holdout = pd.read_parquet(out / "search_holdout_runs.parquet")
    front = yaml.safe_load((out / "front.yaml").read_text()) or []
    axes = study.axes
    scenarios = study.ranking_scenarios
    allow = bool(study.config["search"].get("allow_hard_fork", False))
    limit = study.config["guardrails"]["max_split_gain"]
    seeds = sorted(holdout.seed.unique())
    stored = proposals.submitted(out)
    taken = set(holdout.scheme.unique())
    rng = np.random.default_rng(11)
    widened = False
    for row in rows:
        row, meta = proposals.split(row)
        scheme = study.schemes([row])[0]
        holder = stored.get(scheme.name)
        if (
            holder is not None
            and scheme.name not in taken
            and proposals.split(holder)[0] == scheme.to_dict()
        ):
            meta = {**proposals.split(holder)[1], **meta}  # the same proposal: refresh its results
        elif scheme.name in taken or holder is not None:
            scheme = replace(scheme, name=proposals.unique(scheme.name, taken | set(stored)))
        taken.add(scheme.name)
        stored[scheme.name] = scheme.to_dict()
        entry = dict(scheme=scheme.to_dict(), rule=scheme.label())
        runs = None
        if not scheme.paid:
            entry.update(accepted=False, reason="pays nothing")
        elif scheme.hard_cap and not allow:
            entry.update(accepted=False, reason="needs a hard fork (search.allow_hard_fork is off)")
        else:
            runs = experiment.evaluate(study, [scheme], scenarios, seeds, processes)
            both = pd.concat([holdout, runs], ignore_index=True)
            names, cube = per_seed(both, axes, scenarios)
            members = [s["name"] for s in front]

            def gain(c, n):
                return volume(c, n, axes, members + [scheme.name]) - volume(c, n, axes, members)

            value = gain(cube, names)
            low, high = bootstrap(cube, names, gain, rng)
            pool = members + [scheme.name, BASELINE]
            distinct = scheme.name in front_of(scores(cube, names, axes), names, axes, pool)
            accepted = bool(low > 0 and distinct)
            means = np.nanmean(cube, axis=1)
            change = means[names.index(scheme.name)] - means[names.index(BASELINE)]
            split = float(runs.split_gain.iloc[0])
            entry.update(
                accepted=accepted,
                hypervolume_gain=float(value),
                hypervolume_gain_ci=[float(low), float(high)],
                reason="widens the front"
                if accepted
                else "no clear gain over the front"
                if low <= 0
                else "matched or beaten by a design already on the front",
                change_from_unpaid={a.name: float(c) for a, c in zip(axes, change)},
                within_split_guardrail=bool(split <= limit),
                pilot_testable=scheme.feasibility()["pilot_testable"],
            )
            if accepted:
                widened = True
                holdout = both
                front.append(scheme.to_dict())
                finalists = yaml.safe_load((out / "search_finalists.yaml").read_text())
                (out / "search_finalists.yaml").write_text(
                    yaml.safe_dump(finalists + [scheme.to_dict()], sort_keys=False)
                )
        with (out / "ledger.jsonl").open("a") as ledger:
            ledger.write(json.dumps(entry, default=float) + "\n")
        proposals.record(out, scheme, entry, runs, meta)
        log(f"{scheme.name}: {'ACCEPTED' if entry['accepted'] else 'rejected'} - {entry['reason']}")
        if "hypervolume_gain" in entry:
            low, high = entry["hypervolume_gain_ci"]
            log(f"  hypervolume gain {entry['hypervolume_gain']:.6f} (95% {low:.6f}..{high:.6f})")
            log(
                "  change from unpaid: "
                + ", ".join(f"{k} {v:+.4g}" for k, v in entry["change_from_unpaid"].items())
            )
            if not entry["within_split_guardrail"]:
                log(f"  outside the split-gain guardrail ({split:.2f} > {limit})")
    holdout.to_parquet(out / "search_holdout_runs.parquet")
    (out / "front.yaml").write_text(yaml.safe_dump(front, sort_keys=False))
    if widened:  # the site's coverage and front counts come from the judged finalists
        rejudge(study, log=lambda *_: None)
        log("the front changed: re-judged the finalists with the accepted proposals")
