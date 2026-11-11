# Contributing

RSS-Gov exists so that the trade-offs of rewarding Cardano governance are in plain view.
That only works if the people affected (DReps, delegators, SPOs, the Constitutional
Committee) can check the method and add to it. There are three ways to help.

## 1. Propose a reward scheme

A proposal is a rule in the reward family described in `METHODS.md`: how pay grows with
voting power, caps, who qualifies, what share goes to delegators, how pay is tied to a
DRep's own stake, and the budget. Every rule pays only for explicit votes.

**On the site.** The [Propose a scheme](https://cerkoryn.github.io/RSS-Gov/propose.html)
page builds the rule with a form and shows the exact checks at once (who would be paid,
how much splitting gains). **Submit on GitHub** opens a filled-in issue; you need a GitHub
account. A maintainer reads it and adds the `approved` label, which starts the simulation
on GitHub's servers. The result is posted on the issue with a preview of the site, and
appears on the results page once its pull request is merged, next to every other design,
whether or not it beats them.

**As a file.** Download the YAML from the form, or write it by hand:

```yaml
- name: capped_20m_floor_50
  hypothesis: A floor of 50 delegators per DRep makes splitting costly while keeping
    the participation a cap buys.
  author: your-handle            # optional, shown publicly
  alpha: 1.0
  cap_ada: 20000000
  min_delegators: 50
```

Then run `rss-gov static --schemes your.yaml` (instant, exact) and `rss-gov try your.yaml`
(a few minutes). To have it published, open a proposal issue with the YAML.

**What makes a useful proposal.** Say what it should improve and what it is willing to
give up: every design gives something up. A proposal that fails is a result too: it
rules an idea out, and it stays listed.

**Ideas outside the family** (a new eligibility rule, a different way to pay delegators, a
rule using data the model does not have) need code: see section 3. Open an issue first
describing the rule and the on-chain data it would read.

## 2. Improve the method

`METHODS.md` is the method. The "How it works" page of the site is generated from it, so a
change there is a change to the public explanation.

- **Unclear or wrong explanation**: edit `METHODS.md` and say what was misleading.
- **Disagree with an assumption** (a response strength, a cost, a guardrail): these live in
  `config.yaml` under `assumptions`, `scenarios`, `axes` and `guardrails`. Propose a new
  value with its source or argument. Changing a guardrail needs no new simulation: run
  `rss-gov report`.
- **Disagree with the model** (how DReps vote, how delegators move): describe the evidence
  from chain data. A change to `model.py` or `calibrate.py` must come with a rerun of
  `rss-gov calibrate` and its validation table, pass or fail.
- **Missing objective**: an axis needs a measure that can be computed from chain data, a
  direction, a meaningful difference, and an argument for why a programme should weigh it.

## 3. Code

```
uv venv --python 3.12 && uv pip install -e ".[dev]"
pytest -q && ruff check . && ruff format --check .
```

`AGENTS.md` holds the rules every change follows. The main ones:

- Evidence tiers stay separate. Nothing fitted to history may depend on a reward scheme,
  and no assumption may be presented as a measurement.
- Every quantity a reward formula reads must be computable from chain data.
- With every response switched off, a paid scheme must equal unpaid exactly.
- No combined score; limits belong under `guardrails`.
- Do not loosen a validation tolerance to make it pass.
- Keep the code small.

## What reviewers check

1. The result can be reproduced from the data pull, `config.yaml` and the code.
2. Every new number says whether it is exact, fitted (from what) or assumed.
3. Tests pass, and the validation table is reported if the model changed.
4. The explanation in `METHODS.md` still matches the code.

## Running the site

```
rss-gov site                 # rebuild results/site/ from the current results
rss-gov serve                # serve it on every interface, port 8000
rss-gov serve --read-only    # the same, without accepting proposals
```

`rss-gov serve` has no login: anyone who can reach the port can queue simulations on your
machine. Use it on networks you trust.

## How the site is published

Everything runs on GitHub, with no server of our own:

| Workflow | When | What it does |
|---|---|---|
| `pages.yml` | `results/site/` changes on `main` | copies it to the `gh-pages` branch, which GitHub Pages serves |
| `proposal.yml` | the `approved` label is added to a `proposal` issue | checks the rule, runs `rss-gov try` and `rss-gov site`, opens a pull request, publishes a preview under `pr-preview/pr-N/`, comments on the issue |
| `refresh.yml` | the 1st of each month, or by hand | pulls the latest mainnet data, refits and checks the model, re-runs the search and every proposal, publishes the data release and opens a pull request with a preview |
| `preview-cleanup.yml` | a proposal or refresh pull request is merged or closed | removes its preview |
| `tests.yml` | every push and pull request | tests and lint |

**Data.** Runs use the mainnet data the calibration was fitted to, published as a release
named `data-epoch-<tip>` (`data.tar.gz`: `manifest.json`, `tip.json`, `tables/`).
`rss-gov data verify` checks it against the hashes in `results/calibration.json`.

**Monthly refresh.** `refresh.yml` takes a few hours on GitHub's runners and does nothing
when mainnet has not reached a new epoch. Its pull request says whether the model check
passed; if it failed, read the validation table before merging. After merging, re-run any
proposal pull requests that were opened before it. The Koios API key, if any, is the
repository secret `KOIOS_API_KEY`. GitHub pauses scheduled workflows in a repository with
no activity for 60 days; **Actions → Refresh the data → Enable workflow** resumes it.

After a data pull and calibration on your own machine, publish the release yourself
before merging the new results:

```
tar -czf data.tar.gz -C data/pull manifest.json tip.json tables
gh release create data-epoch-<tip> data.tar.gz --title "Mainnet data, epoch <tip>"
```

**Reviewing a proposal.** Read the issue; add `approved` to simulate it (anything else:
comment or close). Each proposal's pull request changes only its own files in
`results/proposals/`, `results/ledger.jsonl` and `results/site/`. Two proposals simulated
before either is merged conflict in those last two; merge one, then re-run the other with
**Actions → Simulate a proposal → Run workflow** and its issue number. The same re-runs a
proposal whose rule was edited in the issue.

**Why the runs can be trusted.** Python and package versions come from `uv.lock`, the data
is checked by hash, and every run is seeded, so a workflow run reproduces what
`rss-gov try` gives locally. Its log is public.
