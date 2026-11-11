"""Command line: rss-gov data|calibrate|static|experiment|search|try|report|site|serve|all."""

import argparse
import json
from pathlib import Path
import sys
import time

import pandas as pd
import yaml


def _say(text=""):
    print(text, flush=True)


def cmd_data(args):
    from rss_gov import dataset, experiment, koios

    config = experiment.load_config(args.config)
    if args.action == "pull":
        koios.pull(args.out or config["data"], koios.api_key(), not args.no_delegators, _say)
    data = dataset.load(args.out or config["data"])
    series = data.series()
    closed = data.closed()
    _say(
        f"tip epoch {data.tip_epoch}; DRep power history {series.index.min()}..{series.index.max()}"
    )
    _say(
        f"governance actions {len(data.proposals)} ({len(closed)} closed); DRep ballots {len(data.votes)}"
    )
    last = series.iloc[-1]
    _say(
        f"DReps with power {int(last.dreps)}; delegated to DReps {last.drep_power / 1e9:.2f}B ADA; "
        f"always-abstain {last.abstain / 1e9:.2f}B; no-confidence {last.no_confidence / 1e9:.2f}B"
    )
    _say(
        f"DReps holding 2/3 of DRep power: {int(last.tau67)}; effective number {last.effective_n:.1f}"
    )
    if data.delegators is None:
        _say("no account table: run `rss-gov data pull` without --no-delegators")
    else:
        _say(f"delegating accounts represented {data.delegators.weight.sum():,.0f}")


def cmd_calibrate(args):
    from rss_gov import calibrate, dataset, experiment

    config = experiment.load_config(args.config)
    data = dataset.load(config["data"])
    if data.delegators is None:
        sys.exit("calibration needs the account table: run `rss-gov data pull`")
    result, bands = calibrate.run(data, config, _say)
    result["data"] = {k: v["sha256"] for k, v in data.manifest.get("tables", {}).items()}
    out = Path(config["results"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "calibration.json").write_text(json.dumps(result, indent=2, default=float))
    bands.to_csv(out / "validation_bands.csv")
    verdict = "passed" if result["validation"]["passed"] else "FAILED at least one check"
    _say(f"validation {verdict}; wrote {out / 'calibration.json'}")


def _study(args):
    from rss_gov import experiment

    study = experiment.open_study(args.config)
    if not study.validation_passed:
        _say("warning: the model failed part of its validation; see results/calibration.json")
    return study


def cmd_static(args):
    from rss_gov import static

    study = _study(args)
    rows = _scheme_rows(study, args.schemes)
    table = static.analyse(study, study.schemes(rows))
    table.to_csv(study.results / "static.csv", index=False)
    columns = [
        "scheme", "paid_dreps", "max_award", "top10_award_share", "newcomer_capture",
        "newcomer_extra", "incumbent_extra", "split_gain", "power_kept", "delegator_dust_share",
        "pilot_testable",
    ]  # fmt: skip
    with pd.option_context("display.width", 250, "display.float_format", "{:,.3f}".format):
        _say(table[[c for c in columns if c in table]].to_string(index=False))
    _say(f"wrote {study.results / 'static.csv'}")


def _scheme_rows(study, path):
    if not path:
        return study.config["experiment"]["schemes"]
    rows = yaml.safe_load(Path(path).read_text())
    return rows["schemes"] if isinstance(rows, dict) else rows


def cmd_experiment(args):
    from rss_gov import experiment

    study = _study(args)
    rows = _scheme_rows(study, args.schemes)
    schemes = study.schemes(rows)
    if all(s.name != experiment.BASELINE for s in schemes):
        schemes = study.schemes([experiment.BASELINE]) + schemes
    seeds = range(args.seeds or study.config["experiment"]["seeds"])
    started = time.time()
    runs = experiment.evaluate(study, schemes, list(study.scenarios), seeds, args.processes)
    summary = experiment.summarise(runs, study.axes)
    runs.to_parquet(study.results / "experiment_runs.parquet")
    summary.to_csv(study.results / "experiment_summary.csv", index=False)
    _say(f"{len(runs)} runs in {time.time() - started:.0f}s")
    scenario = "central" if "central" in study.scenarios else list(study.scenarios)[-1]
    view = summary[summary.scenario == scenario]
    with pd.option_context("display.width", 250, "display.float_format", "{:,.4g}".format):
        _say(f"change against unpaid on each axis, scenario `{scenario}` (mean paired difference)")
        _say(view[["scheme"] + [f"{a.name}_diff" for a in study.axes]].to_string(index=False))
    _say(f"wrote {study.results / 'experiment_summary.csv'}")


def cmd_search(args):
    from rss_gov import search

    study = _study(args)
    search.run(study, _say, args.processes)


def cmd_try(args):
    from rss_gov import search

    study = _study(args)
    search.try_candidates(study, _scheme_rows(study, args.file), _say, args.processes)


def cmd_report(args):
    from rss_gov import report, website

    study = _study(args)
    _say(f"wrote {report.write(study)}")
    _say(f"wrote {website.write(study)}/ (open index.html, or run `rss-gov serve`)")


def cmd_site(args):
    from rss_gov import website

    _say(f"wrote {website.write(_study(args))}/")


def cmd_serve(args):
    from rss_gov import experiment, server

    site = experiment.load_config(args.config).get("site") or {}
    server.serve(
        args.config,
        args.host or site.get("host", "0.0.0.0"),
        args.port if args.port is not None else int(site.get("port", 8000)),
        bool(site.get("submissions", True)) and not args.read_only,
        int(site.get("max_queue", 20)),
        _say,
    )


def cmd_all(args):
    args.action, args.out, args.no_delegators = "summary", None, False
    args.schemes = args.seeds = None
    for step in (cmd_data, cmd_calibrate, cmd_static, cmd_experiment, cmd_search, cmd_report):
        _say(f"\n== {step.__name__[4:]} ==")
        step(args)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="rss-gov", description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--processes", type=int, default=None, help="worker processes")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("data", help="download or summarise the chain data")
    p.add_argument("action", choices=["pull", "summary"])
    p.add_argument("--out", help="data folder (default: `data` in the config)")
    p.add_argument("--no-delegators", action="store_true", help="skip the account table")
    p.set_defaults(run=cmd_data)

    p = sub.add_parser("calibrate", help="fit the unpaid model and validate it on held-out epochs")
    p.set_defaults(run=cmd_calibrate)

    p = sub.add_parser("static", help="apply schemes to today's real DReps, no behaviour")
    p.add_argument("--schemes", help="YAML list of schemes (default: the config's list)")
    p.set_defaults(run=cmd_static)

    p = sub.add_parser("experiment", help="simulate schemes over many seeds and scenarios")
    p.add_argument("--schemes", help="YAML list of schemes (default: the config's list)")
    p.add_argument("--seeds", type=int)
    p.set_defaults(run=cmd_experiment)

    p = sub.add_parser("search", help="optimise the scheme family and report the Pareto front")
    p.set_defaults(run=cmd_search)

    p = sub.add_parser("try", help="test proposed schemes against the current front")
    p.add_argument("file", help="YAML list of schemes")
    p.set_defaults(run=cmd_try)

    p = sub.add_parser("report", help="write results/report.md with figures, and the site")
    p.set_defaults(run=cmd_report)

    p = sub.add_parser("site", help="rebuild the results site in results/site/")
    p.set_defaults(run=cmd_site)

    p = sub.add_parser("serve", help="serve the site on the network, with proposal submission")
    p.add_argument("--host", help="address to listen on (default: site.host, 0.0.0.0)")
    p.add_argument("--port", type=int, help="port (default: site.port, 8000)")
    p.add_argument("--read-only", action="store_true", help="show checks, accept no proposals")
    p.set_defaults(run=cmd_serve)

    p = sub.add_parser("all", help="calibrate, analyse, experiment, search and report")
    p.set_defaults(run=cmd_all)

    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
