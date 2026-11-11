"""Write results/report.md and its figures from whatever results exist."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"
BLUE, ORANGE = "#2a78d6", "#eb6834"  # validated together for colour-vision deficiency
NEUTRAL = "#a3a19a"
GENERATED = r"g\d+_\d+"  # names the search gives its own designs
LABELS = dict(
    tau67="DReps needed for 2/3 of power",
    effective_n="Effective number of DReps",
    drep_power="Delegated to DReps (B ADA)",
    abstain="Always-abstain (B ADA)",
)
# Per axis: what the number rests on, and how a real programme would show it.
EVIDENCE = dict(
    participation=(
        "simulated; rests on the voting and yield responses",
        "on chain: votes and delegation each epoch",
    ),
    tau67=(
        "simulated; rests on the yield and reinvestment responses",
        "on chain: DRep voting power each epoch",
    ),
    backing=(
        "starts from accounts linked on chain; changes rest on the own-stake response",
        "needs DReps to declare their accounts and sign for them",
    ),
    annual_cost_ada=("accounting; exact for a given budget", "the programme's own books"),
    split_gain=(
        "exact property of the formula on today's DReps",
        "indirectly: new look-alike DReps and delegation splits",
    ),
)
SHARES = ("participation", "backing")


def _scale(axis):
    """Display multiplier and unit for an axis."""
    if axis.name in SHARES:
        return 100.0, "points"
    if axis.name == "annual_cost_ada":
        return 1e-6, "M ADA a year"
    if axis.name == "split_gain":
        return 100.0, "% of budget"
    return 1.0, ""


def _value(axis, value, signed=True):
    if value is None or np.isnan(value):
        return ""
    if axis.name == "annual_cost_ada":
        return f"{value / 1e6:.1f}M"
    if axis.name == "split_gain":
        return f"{value:.0%}"
    digits = 2 if axis.name == "backing" else 1
    scaled = value * _scale(axis)[0]
    return f"{scaled:+.{digits}f}" if signed else f"{scaled:.{digits}f}"


def _mark(verdicts):
    """Solid when the verdict holds in every scenario, hollow when in some."""
    verdicts = [int(v) for v in verdicts if not np.isnan(v)]
    if verdicts and all(v == 1 for v in verdicts):
        return " ▲"
    if verdicts and all(v == -1 for v in verdicts):
        return " ▼"
    if any(v == -1 for v in verdicts):
        return " ▽"
    if any(v == 1 for v in verdicts):
        return " △"
    return ""


def _style():
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.size": 10,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "axes.edgecolor": GRID,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.titlesize": 10.5,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 1,
            "axes.axisbelow": True,
        }
    )


def figure_validation(bands, path):
    """Held-out history against the model started before it."""
    panels = [("tau67", 1), ("effective_n", 1), ("drep_power", 1e9), ("abstain", 1e9)]
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.4), sharex=True)
    for ax, (name, scale) in zip(axes.flat, panels):
        x = bands.index
        ax.fill_between(
            x,
            bands[f"{name}_low"] / scale,
            bands[f"{name}_high"] / scale,
            color=BLUE,
            alpha=0.12,
            lw=0,
        )
        ax.plot(x, bands[f"{name}_mean"] / scale, color=BLUE, lw=2, solid_capstyle="round")
        ax.plot(x, bands[f"{name}_observed"] / scale, color=INK, lw=2, solid_capstyle="round")
        ax.set_title(LABELS[name])
        ax.grid(axis="x", visible=False)
        low = min(bands[f"{name}_low"].min(), bands[f"{name}_observed"].min()) / scale
        high = max(bands[f"{name}_high"].max(), bands[f"{name}_observed"].max()) / scale
        ax.set_ylim(low - 0.25 * (high - low), high + 0.25 * (high - low))
    first = axes.flat[0]
    end = bands.index[-1]
    first.annotate(
        "observed", (end, bands.tau67_observed.iloc[-1]), xytext=(-4, -14),
        textcoords="offset points", ha="right", color=INK,
    )  # fmt: skip
    first.annotate(
        "model (mean, 95% of runs)", (end, bands.tau67_high.iloc[-1]), xytext=(-4, 6),
        textcoords="offset points", ha="right", color=INK,
    )  # fmt: skip
    for ax in axes[1]:
        ax.set_xlabel("epoch")
    fig.suptitle(
        "Unpaid model started at the first epoch shown, against what then happened",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )  # fmt: skip
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def figure_scorecard(summary, axes, scenarios, path, names):
    """Every axis for every named scheme: change against unpaid, with its uncertainty."""
    low, central, high = (summary[summary.scenario == s].set_index("scheme") for s in scenarios)
    fig, panels = plt.subplots(2, 3, figsize=(13.5, 0.62 * len(names) + 3.0), sharey=True)
    rows = np.arange(len(names))[::-1]
    for ax in panels.flat[len(axes) :]:
        ax.axis("off")
    for ax, axis in zip(panels.flat, axes):
        scale, unit = _scale(axis)
        key = f"{axis.name}_diff"
        ax.axvline(0, color=MUTED, lw=1)
        exact = axis.name in ("annual_cost_ada", "split_gain")
        colours = []
        for name in names:
            verdicts = [frame.loc[name, f"{axis.name}_verdict"] for frame in (low, central, high)]
            mark = _mark(verdicts).strip()
            colours.append(NEUTRAL if exact else {"▲": BLUE, "▼": ORANGE}.get(mark, NEUTRAL))
        if exact:
            ax.barh(rows, central.loc[names, key] * scale, height=0.5, color=NEUTRAL)
        else:
            ax.hlines(
                rows, low.loc[names, key] * scale, high.loc[names, key] * scale,
                color=colours, alpha=0.35, lw=6, capstyle="round",
            )  # fmt: skip
            ax.errorbar(
                central.loc[names, key] * scale, rows, xerr=central.loc[names, f"{key}_ci"] * scale,
                fmt="none", ecolor=INK, elinewidth=1,
            )  # fmt: skip
            ax.scatter(
                central.loc[names, key] * scale, rows, s=46, c=colours, edgecolors=SURFACE,
                linewidths=1.5, zorder=3,
            )  # fmt: skip
        ax.set_title(f"{axis.family}: {axis.better} is better", fontsize=10)
        ax.set_xlabel(f"{axis.label}\nchange against unpaid" + (f", {unit}" if unit else ""))
        ax.grid(axis="y", visible=False)
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.set_yticks(rows)
        ax.set_yticklabels(names, color=INK)
        ax.tick_params(length=0)
    handles = [
        plt.Line2D([], [], marker="o", ls="", color=BLUE, ms=7, label="better than unpaid in every scenario"),
        plt.Line2D([], [], marker="o", ls="", color=ORANGE, ms=7, label="worse in every scenario"),
        plt.Line2D([], [], marker="o", ls="", color=NEUTRAL, ms=7, label="no meaningful or no consistent difference; exact quantities"),
    ]  # fmt: skip
    fig.legend(handles=handles, loc="lower left", ncol=3, frameon=False, bbox_to_anchor=(0.01, 0.0))
    fig.suptitle(
        "Change against unpaid on each axis. Dot: central response (line: 95% interval). "
        "Band: low to high response.",
        x=0.01, ha="left", fontsize=11.5, fontweight="bold",
    )  # fmt: skip
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def figure_front(front, path, limit):
    """The trade-off no formula escapes: resisting splitting against spreading power."""
    fig, ax = plt.subplots(figsize=(9.6, 6.0))
    groups = (
        (front.pilot_testable, BLUE, "o", "works on today's Cardano"),
        (~front.pilot_testable, NEUTRAL, "D", "needs a hard fork"),
    )
    for mask, colour, marker, label in groups:
        part = front[mask]
        if len(part):
            ax.scatter(
                part.split_gain * 100, part.tau67_diff, s=70, color=colour, marker=marker,
                edgecolors=SURFACE, linewidths=1.8, label=label, zorder=3,
            )  # fmt: skip
    ax.axhline(0, color=MUTED, lw=1)
    top = max(front.tau67_diff.max() * 1.08, 1.0)
    ax.set_ylim(min(front.tau67_diff.min() - 1.2, -1.0), top)
    ax.axvspan(
        -3,
        limit * 100,
        ymin=(0 - ax.get_ylim()[0]) / (top - ax.get_ylim()[0]),
        color=BLUE,
        alpha=0.07,
        lw=0,
    )
    ax.annotate(
        "inside both guardrails", (limit * 50 - 1.5, top), xytext=(0, -6), textcoords="offset points",
        ha="center", va="top", fontsize=8.5, color=MUTED, rotation=90,
    )  # fmt: skip
    ax.set_xlim(-3, max(front.split_gain.max() * 100 + 12, 60))
    # One label per cluster of points that sit on top of each other.
    fig.canvas.draw()
    named = ~front.scheme.str.fullmatch(GENERATED) & ~front.scheme.str.fullmatch(r".*_\d+m\d*")
    wanted = front[named | (front.best_of_its_kind & (front.tau67_diff > 2))]
    pixels = ax.transData.transform(wanted[["split_gain", "tau67_diff"]].values * [100, 1])
    clusters = []
    for name, (x, y) in sorted(zip(wanted.scheme, pixels), key=lambda item: -item[1][1]):
        for cluster in clusters:
            if abs(cluster["x"] - x) < 16 and abs(cluster["y"] - y) < 13 * (
                1 + len(cluster["names"]) / 3
            ):
                cluster["names"].append(name)
                break
        else:
            clusters.append(dict(x=x, y=y, names=[name]))
    for cluster in clusters:
        names = cluster["names"]
        lines = [", ".join(names[k : k + 3]) for k in range(0, len(names), 3)]
        ax.annotate(
            "\n".join(lines), ax.transData.inverted().transform((cluster["x"], cluster["y"])),
            xytext=(8, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK,
        )  # fmt: skip
    ax.set_xlabel("share of the budget gained by splitting one identity, % (left: harder to game)")
    ax.set_ylabel("change in DReps needed for 2/3 of voting power (up: power more spread)")
    ax.set_title(
        "Resisting splitting against spreading power: holdout seeds, mean of the scenarios"
    )
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _table(frame, formats=None):
    """A GitHub-flavoured markdown table."""
    formats = formats or {}

    def cell(column, value):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return ""
        if column in formats:
            return formats[column].format(value)
        if isinstance(value, (bool, np.bool_)):
            return "yes" if value else "no"
        if isinstance(value, (float, np.floating)):
            return f"{value:,.3f}"
        return str(value)

    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "|" + "|".join("---" for _ in frame.columns) + "|",
    ]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(cell(c, v) for c, v in zip(frame.columns, row)) + " |")
    return "\n".join(lines)


def _cells(frame, axis, marks=None):
    """Change against unpaid, ± its 95% interval, with a verdict mark."""
    scale = _scale(axis)[0]
    digits = 2 if axis.name == "backing" else 1
    out = []
    for i, (diff, half) in enumerate(
        zip(frame[f"{axis.name}_diff"], frame[f"{axis.name}_diff_ci"])
    ):
        if axis.name in ("annual_cost_ada", "split_gain"):
            out.append(_value(axis, diff))
            continue
        text = _value(axis, diff)
        if not np.isnan(half):
            text += f" ± {half * scale:.{digits}f}"
        out.append(text + (marks[i] if marks is not None else ""))
    return out


def _design_tables(part, axes, scenarios):
    """Two tables for a set of designs: every axis, then the main axes by scenario."""
    part = part.reset_index(drop=True)
    table = pd.DataFrame({"scheme": part.scheme, "rule": part.rule})
    for axis in axes:
        marks = [{1: " ▲", -1: " ▼"}.get(int(v), "") for v in part[f"{axis.name}_robust"]]
        table[axis.family] = _cells(part, axis, marks)
    by_scenario = pd.DataFrame({"scheme": part.scheme})
    for axis in [a for a in axes if a.name in ("participation", "tau67")]:
        for scenario in scenarios:
            by_scenario[f"{axis.family} ({scenario})"] = [
                _value(axis, v) for v in part[f"{axis.name}_diff_{scenario}"]
            ]
    return [_table(table), "", "By response scenario:", "", _table(by_scenario), ""]


RECENT_EPOCHS = 12  # window for today's observed participation


def today(study):
    """Facts about the chain at the snapshot every scheme starts from."""
    data, world = study.data, study.world
    last = data.series().iloc[-1]
    on_drep = world.acct_target >= 0
    stake = np.bincount(
        world.acct_target[on_drep], weights=world.acct_stake[on_drep], minlength=len(world.p)
    )
    # Participation as the model defines it: voting power that voted on an action, over all
    # delegated stake (always-abstain and no-confidence included), for recently closed actions.
    series = data.series()
    recent = data.closed(int(series.index[-1]) - RECENT_EPOCHS + 1)
    participation = None
    if len(recent):
        _, voted, _ = data.ballots(recent)
        shares = []
        for j, close in enumerate(recent.close.astype(int)):
            power = data.power.loc[close].values
            row = series.loc[close]
            shares.append(
                power[voted[:, j]].sum() / (power.sum() + row.abstain + row.no_confidence)
            )
        participation = float(np.mean(shares))
    return dict(
        participation=participation,
        participation_actions=len(recent),
        recent_epochs=RECENT_EPOCHS,
        dreps=int(last.dreps),
        tau67=int(last.tau67),
        effective_n=float(last.effective_n),
        drep_power=float(last.drep_power),
        abstain=float(last.abstain),
        no_confidence=float(last.no_confidence),
        closed_actions=len(data.closed()),
        ballots=len(data.votes),
        own_stake=float(world.pledge.sum()),
        linked_dreps=int(((world.pledge > 0) & (stake > 0)).sum()),
        dreps_with_stake=int((stake > 0).sum()),
        backing=float(np.minimum(stake, world.pledge).sum() / stake.sum()),
    )


def write(study):
    _style()
    out = study.results
    figures = out / "figures"
    figures.mkdir(exist_ok=True)
    axes = study.axes
    ranking = study.ranking_scenarios
    guard = study.config["guardrails"]
    calibration = json.loads((out / "calibration.json").read_text())
    validation = calibration["validation"]
    data = study.data
    now = today(study)
    text = [
        "# RSS-Gov results",
        "",
        f"Chain data to epoch {data.tip_epoch}. Default programme: "
        f"{study.budget:,.0f} ADA over {study.epochs} epochs. "
        "Regenerate with `rss-gov all`; method in `METHODS.md`. Interactive charts: "
        "`site/index.html` in this folder.",
        "",
        "## The chain today",
        "",
        f"- {now['dreps']} DReps hold voting power; {now['tau67']} of them hold two thirds of it "
        f"(effective number {now['effective_n']:.1f}).",
        f"- {now['drep_power'] / 1e9:.2f}B ADA is delegated to DReps, {now['abstain'] / 1e9:.2f}B "
        f"to always-abstain and {now['no_confidence'] / 1e9:.2f}B to always-no-confidence.",
        f"- {now['closed_actions']} governance actions have closed; {now['ballots']:,} DRep ballots.",
        f"- Accounts that funded a DRep's registration or that it declares as its payment address "
        f"hold {now['own_stake'] / 1e6:.1f}M ADA in total, for {now['linked_dreps']} of "
        f"{now['dreps_with_stake']} DReps. That backs **{now['backing']:.2%}** of DRep voting "
        f"power: the average vote is cast with about {1 / now['backing']:,.0f} times the voter's "
        "own stake.",
        "",
        "## How schemes are compared",
        "",
        "Every scheme starts from the same chain snapshot, runs on the same random seeds, and "
        "pays only for explicit votes (Yes, No and Abstain count alike). Named schemes get the "
        "same budget. Each is then measured on one axis per objective family; nothing is "
        "folded into a single score.",
        "",
    ]
    rows = []
    for axis in axes:
        scale, unit = _scale(axis)
        basis, pilot = EVIDENCE.get(axis.name, ("simulated", ""))
        rows.append(
            {
                "family": axis.family,
                "measure": axis.label,
                "better": axis.better,
                "meaningful change": f"{axis.meaningful * scale:g} {unit}".strip(),
                "what the number rests on": basis,
                "how a real programme would show it": pilot,
            }
        )
    text += [
        _table(pd.DataFrame(rows)),
        "",
        "A change smaller than `meaningful change` counts as no difference even when it is "
        "statistically clear. Marks in the tables: ▲ better than unpaid in every response "
        "scenario, ▼ worse in every one, △ / ▽ better / worse in some. No mark: no meaningful "
        "difference.",
        "",
        "## Does the unpaid model reproduce history?",
        "",
        f"Fitted on epochs {validation['start'] - (validation['end'] - validation['start']) + 1}"
        f"–{validation['start']}, started from the observed state at epoch {validation['start']}, "
        f"and compared with epochs {validation['start'] + 1}–{validation['end']} "
        f"({validation['seeds']} runs). "
        + (
            "**Every gated check passed.**"
            if validation["passed"]
            else "**At least one gated check failed; treat everything below as provisional.**"
        ),
        "",
    ]
    checks = pd.DataFrame(validation["checks"])
    for name in ("drep_power", "abstain"):  # show stake in billions of ADA
        mask = checks.metric == name
        checks.loc[mask, ["observed", "simulated", "low", "high"]] /= 1e9
        checks.loc[mask, "metric"] = f"{name} (B ADA)"
    checks["result"] = [
        "context" if not g else "pass" if p else "FAIL" for g, p in zip(checks.gated, checks.passed)
    ]
    columns = ["metric", "observed", "simulated", "low", "high", "error", "kind", "tolerance"]
    text += [
        _table(
            checks[columns + ["result"]],
            {c: "{:,.3f}" for c in ("observed", "simulated", "low", "high")} | {"error": "{:+.3f}"},
        ),
        "",
        "`error` is relative unless `kind` says absolute. `context` rows depend on which "
        "proposals get submitted, which the model takes from history rather than predicts.",
        "",
    ]
    bands_path = out / "validation_bands.csv"
    if bands_path.exists():
        figure_validation(pd.read_csv(bands_path, index_col=0), figures / "validation.png")
        text += ["![validation](figures/validation.png)", ""]

    static_path = out / "static.csv"
    if static_path.exists():
        static = pd.read_csv(static_path)
        view = pd.DataFrame(
            {
                "scheme": static.scheme,
                "rule": static.rule,
                "DReps paid": static.paid_dreps,
                "largest award / epoch": static.max_award.map("{:,.0f}".format),
                "to 10 largest": static.top10_award_share.map("{:.0%}".format),
                "outsider's take": static.newcomer_capture.map("{:.0%}".format),
                "of which from splitting": static.newcomer_extra.map("{:.0%}".format),
                "insider split gain": static.incumbent_extra.map("{:.0%}".format),
                "voting power kept": static.power_kept.map("{:.0%}".format),
                "dust claims": [
                    "" if np.isnan(v) else f"{v:.0%}" for v in static.delegator_dust_share
                ],
            }
        )
        capital = study.config["sybil"]["newcomer_capital_ada"]
        text += [
            "## What each formula does to today's DReps (no behaviour change)",
            "",
            "Exact arithmetic on the current snapshot. `outsider's take` is the share of the "
            f"budget an outsider gets by bringing {capital:,.0f} ADA and voting on everything, "
            "using as many fake DReps as pays best; the next column is how much of that comes "
            "from splitting rather than from simply taking part. `insider split gain` is the "
            "most any existing DRep adds by splitting into 2–20 DReps with its delegators "
            "following (an upper bound: delegators may not follow). The Sybil axis is the larger "
            "of the two splitting gains. `dust claims` is the share of delegator claims below "
            f"{study.params.min_payout_ada:g} ADA over the programme.",
            "",
            _table(view[static.paid_dreps > 0]),
            "",
        ]

    summary_path = out / "experiment_summary.csv"
    if summary_path.exists():
        summary = pd.read_csv(summary_path)
        base = summary[(summary.scheme == "unpaid") & (summary.scenario == "central")].iloc[0]
        ladder = [
            row["name"]
            for row in study.config["experiment"]["schemes"]
            if isinstance(row, dict) and "budget_ada" in row
        ]
        names = [n for n in summary.scheme.unique() if n != "unpaid" and n not in ladder]
        by_scenario = {s: summary[summary.scenario == s].set_index("scheme") for s in ranking}
        central = by_scenario["central"].loc[names].reset_index()
        text += [
            "## Scorecard: named schemes at the same budget",
            "",
            f"{int(base.seeds)} seeds per scheme and scenario. Unpaid baseline: "
            + "; ".join(
                f"{a.label} {_value(a, base[a.name], signed=False)}"
                + (" points" if a.name in SHARES else "")
                for a in axes
                if a.name not in ("annual_cost_ada", "split_gain")
            )
            + ". Cells are the change against unpaid in the `central` scenario ± 95%; the marks "
            "use all of " + ", ".join(f"`{s}`" for s in ranking) + ".",
            "",
        ]
        table = pd.DataFrame({"scheme": names})
        for axis in axes:
            marks = [
                _mark([by_scenario[s].loc[n, f"{axis.name}_verdict"] for s in ranking])
                for n in names
            ]
            table[f"{axis.family} ({_scale(axis)[1] or 'DReps'})"] = _cells(central, axis, marks)
        text += [_table(table), ""]
        figure_scorecard(summary, axes, ranking, figures / "scorecard.png", names)
        text += ["![scorecard](figures/scorecard.png)", ""]

        channels = [s for s in study.scenarios if s.endswith("_only")]
        if channels:
            text += [
                "### Which assumption each result rests on",
                "",
                "Each column switches on one response channel at its central strength and leaves "
                "the others off. A scheme whose result comes from one channel stands or falls "
                "with that assumption. With every channel off, paying changes nothing "
                "(a hard cap on voting power excepted).",
                "",
            ]
            for axis in [a for a in axes if a.name in ("participation", "tau67", "backing")]:
                table = pd.DataFrame({"scheme": names})
                for scenario in channels + ["central"]:
                    view = summary[summary.scenario == scenario].set_index("scheme")
                    table[scenario.replace("_only", " only")] = [
                        _value(axis, view.loc[n, f"{axis.name}_diff"]) for n in names
                    ]
                unit = _scale(axis)[1] or "DReps"
                text += [
                    f"{axis.family}: change in {axis.label} ({unit})",
                    "",
                    _table(table),
                    "",
                ]

        if ladder:
            parent = next(
                row["preset"]
                for row in study.config["experiment"]["schemes"]
                if isinstance(row, dict) and row.get("name") == ladder[0]
            )
            steps = by_scenario["central"].loc[[*ladder, parent]].sort_values("annual_cost_ada")
            table = pd.DataFrame({"scheme": steps.index})
            cost = steps.annual_cost_ada.values
            table["cost a year"] = [f"{c / 1e6:.1f}M" for c in cost]
            if data.treasury:
                table["share of treasury"] = [f"{c / data.treasury:.2%}" for c in cost]
            for axis in [a for a in axes if a.name in ("participation", "tau67")]:
                table[axis.family] = _cells(steps.reset_index(), axis)
            gain = steps.participation_diff.values * 100
            table["ADA a year per point of participation"] = [
                f"{c / g:,.0f}" if g > 0 else "" for c, g in zip(cost, gain)
            ]
            text += [
                "### What more money buys",
                "",
                f"The `{parent}` rule at four budgets, `central` scenario. The response to a "
                "reward is assumed to grow with its logarithm, so doubling the budget buys much "
                "less than double.",
                "",
                _table(table),
                "",
            ]

    if (out / "search_holdout_runs.parquet").exists():
        from rss_gov import search as search_module

        search_module.rejudge(study, log=lambda *_: None)  # applies the current guardrails
        front = pd.read_csv(out / "search_front.csv").fillna({"breaks": ""})
        search = json.loads((out / "search.json").read_text())
        low, high = search["hypervolume_ci"]
        gain_low, gain_high = search["search_gain_ci"]
        limit = guard["max_split_gain"]
        text += [
            "## Search over the scheme family",
            "",
            f"{search['history'][-1]['evaluated']} designs simulated over "
            f"{len(search['history']) - 1} generations, with the budget as one of the searched "
            f"parameters. The finalists were re-run on {search['holdout_seeds']} seeds the search "
            "never saw; all numbers here are from those seeds, averaged over "
            + ", ".join(f"`{s}`" for s in search["scenarios"])
            + ". Marks: ▲ better than unpaid in every scenario, ▼ worse in at least one.",
            "",
            f"- {len(search['front'])} of {len(front)} finalists are unbeaten: no other design is "
            f"at least as good on all {len(axes)} axes.",
            f"- Guardrails: splitting an identity may gain at most {limit:.0%} of the budget, and "
            "no axis other than cost may be worse than unpaid in any scenario. "
            f"**{int(front.acceptable.sum())} of {len(front)} finalists stay inside both.**",
            f"- Hypervolume of the front (progress measure, in the units of `axes.scale`): "
            f"**{search['hypervolume']:.5f}** (95% {low:.5f}–{high:.5f}); unpaid alone "
            f"{search['hypervolume_unpaid']:.5f}. The search adds **{search['search_gain']:.5f}** "
            f"over the named schemes (95% {gain_low:.5f}–{gain_high:.5f})."
            + ("" if gain_low > 0 else " The interval includes zero: no clear gain."),
            "",
        ]
        shortlist = front[front.shortlist]
        if len(shortlist):
            text += ["### Shortlist: inside every guardrail and unbeaten", ""]
            text += _design_tables(shortlist, axes, search["scenarios"])
        else:
            text += [
                "No design is free of a downside. The tables below therefore group the "
                "unbeaten designs by the downside they accept, which is the choice a "
                "programme has to make.",
                "",
            ]
        best = front[front.best_of_its_kind & ~front.acceptable]
        groups = sorted(
            best.groupby(["pilot_testable", "breaks"], sort=False),
            key=lambda item: (not item[0][0], item[0][1].count(","), item[0][1]),
        )
        for (pilot, breaks), part in groups:
            part = part.assign(split=part.split_gain.round(2)).sort_values(
                ["split", "participation_diff"], ascending=[True, False]
            )
            title = f"### Accepting a cost in {breaks}" + ("" if pilot else " (needs a hard fork)")
            note = f"{len(part)} unbeaten among the finalists that give up exactly this"
            if len(part) > 10:
                note += "; the 10 that are hardest to game by splitting are shown"
            text += [title, "", note + ".", ""]
            text += _design_tables(part.head(10), axes, search["scenarios"])
        named = front[~front.scheme.str.fullmatch(GENERATED)]
        table = pd.DataFrame(
            {
                "scheme": named.scheme.values,
                "gives up": [b or "nothing" for b in named.breaks],
                "unbeaten among designs giving up the same": named.best_of_its_kind.values,
            }
        )
        text += [
            "### Where the named schemes end up",
            "",
            _table(table),
            "",
            "The guardrails are judgement calls in `config.yaml`. Moving one and running "
            "`rss-gov report` regroups these tables without simulating anything.",
            "",
        ]
        figure_front(front, figures / "front.png", limit)
        text += ["![front](figures/front.png)", ""]

    text += [
        "## How to read this",
        "",
        "- The unpaid world is fitted to chain history and tested on held-out epochs. How people "
        "react to money is **assumed**: four response channels, each at low, central and high "
        "strength. A result that holds only in `high` is a hope, not a finding.",
        "- Cost and the gain from splitting are exact for a given formula. The other axes "
        "are conditional on the response assumptions.",
        "- Own stake comes from accounts linked to a DRep on chain (the funder of its "
        "registration, its declared payment address). That misses own stake held elsewhere and "
        "can count stake that is not the DRep's. A real programme needs signed declarations.",
        "- A hard cap on voting power is simulated mechanically: delegators of a capped DRep "
        "are not modelled as moving away, so its cost in participation is an upper bound.",
        "- Differences smaller than their ± are not differences.",
        "- Only real-world data can measure the responses. `METHODS.md` describes how a "
        "programme could be set up to measure them.",
        "",
    ]
    path = out / "report.md"
    path.write_text("\n".join(text))
    return path
