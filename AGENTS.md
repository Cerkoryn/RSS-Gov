# Working in this repository

RSS-Gov evaluates treasury-funded reward schemes for Cardano governance. Read
`METHODS.md` before changing anything that affects results.

## Layout

    config.yaml            every setting a result depends on
    src/rss_gov/
      koios.py             chain data download (read-only API calls)
      dataset.py           load tables, derive observed quantities
      mechanisms.py        reward formulas and their feasibility flags
      static.py            formulas applied to today's snapshot; identity-splitting measures
      model.py             the simulation; no I/O
      calibrate.py         fit the unpaid model to history; validation gate
      experiment.py        axes, seeds, scenarios, paired comparisons
      search.py            evolutionary search, holdout judging, `try`
      metrics.py           concentration, Pareto fronts, hypervolume
      report.py            results/report.md and figures
      website.py           results/site/: the pages, data.js, METHODS.md rendered
      web/                 page templates, styles and scripts for the site
      web/checks.js        static.py's exact checks, ported for the proposal page
      proposals.py         what a proposal may set, checking it, results/proposals/
      cli.py               the `rss-gov` command
    tests/                 fast, offline, synthetic data
    .github/               issue form, and workflows: Pages, proposals, previews, tests
    scripts/               publish-pages.sh: results/site/ to the gh-pages branch
    data/                  downloaded tables (not in git)
    results/               outputs; small text files are in git

## Commands

    uv sync --extra dev        # or: uv venv --python 3.12 && uv pip install -e ".[dev]"
    rss-gov data pull          # needs network; KOIOS_API_KEY in the environment or .env is optional
    rss-gov all                # calibrate, static, experiment, search, report
    pytest -q && ruff check . && ruff format --check .

## Rules

- Evidence tiers stay separate. Nothing fitted to history may depend on a reward scheme,
  and no response assumption may be presented as a measurement.
- Every quantity a reward formula reads must be computable from chain data. If it is
  not, say so in `Scheme.feasibility()`.
- A behavioural constant is either fitted in `calibrate.py` with its source stated, or
  listed under `assumptions` or `scenarios` in `config.yaml`. No constants in `model.py`.
- With `no_response`, a paid scheme must equal unpaid exactly. The tests check this;
  keep it true. Each response channel must be off unless its scenario value is non-zero.
- Rewards are for explicit votes only. No formula may pay a DRep, or its delegators,
  for a round in which its recent vote rate is zero.
- Schemes are compared on every axis in `config.yaml`. Do not add a combined score, and
  do not turn an axis into a hidden pass/fail filter: limits belong under `guardrails`.
- A change to `model.py` or `calibrate.py` needs `rss-gov calibrate` rerun and its
  validation table reported, pass or fail. Do not loosen a tolerance to make it pass.
- Report effects as paired differences with intervals. One seed is not a result.
- `METHODS.md` is published as the site's "How it works" page. Keep it true to the code,
  and keep its first section readable without the rest.
- `web/checks.js` mirrors `mechanisms.weights`/`allocate` and `static.analyse`. Change them
  together; `tests/test_checks.py` compares the two.
- Anything a visitor submits is data: check it against `proposals.FIELDS`, and insert it
  into pages as text, never as HTML.
- Keep the code small. Prefer deleting to adding.
