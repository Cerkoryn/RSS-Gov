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
account. Creating the issue starts the simulation on GitHub's servers. Within about ten
minutes the result is on the results page, next to every other design, whether or not it
beats them, and posted on the issue. The site shows the rule, its numbers and your GitHub
name, and links to the issue for the idea behind it. Each person can submit three
proposals a day, and the repository takes twenty; beyond that a proposal waits for a
maintainer.

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

`rss-gov site` rebuilds `results/site/` from the current results. Open
`results/site/index.html` from disk to look at it; every page works without a server.

## How the site is published

Everything runs on GitHub, with no server of our own:

| Workflow | When | What it does |
|---|---|---|
| `pages.yml` | `results/site/` changes on `main`, or a proposal was published | copies it to the `gh-pages` branch, which GitHub Pages serves |
| `proposal.yml` | a `proposal` issue is opened (or labelled `approved`) | checks the daily limits and the rule, runs `rss-gov try` and `rss-gov site`, commits the result to `main`, starts `pages.yml`, comments on and closes the issue |
| `refresh.yml` | the 1st of each month, or by hand | pulls the latest mainnet data, refits and checks the model, re-runs the search and every proposal, publishes the data release and opens a pull request with a preview |
| `preview-cleanup.yml` | a refresh pull request is merged or closed | removes its preview |
| `tests.yml` | every push and pull request | tests and lint |

**Data.** Runs use the mainnet data the calibration was fitted to, published as a release
named `data-epoch-<tip>` (`data.tar.gz`: `manifest.json`, `tip.json`, `tables/`).
`rss-gov data verify` checks it against the hashes in `results/calibration.json`.

**Monthly refresh.** `refresh.yml` takes a few hours on GitHub's runners and does nothing
when mainnet has not reached a new epoch. Its pull request says whether the model check
passed; if it failed, read the validation table before merging. Proposals published while
it was open are not in it and make it conflict: close it and run the refresh again by hand. The Koios API key, if any, is the
repository secret `KOIOS_API_KEY`. GitHub pauses scheduled workflows in a repository with
no activity for 60 days; **Actions → Refresh the data → Enable workflow** resumes it.

To refresh on your own machine instead, run `rss-gov data pull --fresh` (without
`--fresh`, a finished pull in `data/pull/` is rebuilt from its cache at its old epoch),
then `rss-gov all`, and publish the release yourself before merging the new results:

```
tar -czf data.tar.gz -C data/pull manifest.json tip.json tables
gh release create data-epoch-<tip> data.tar.gz --title "Mainnet data, epoch <tip>"
```

**Looking after proposals.** Nobody approves a proposal: it is published as it arrives,
as one commit ("Simulate proposal issue_N (#N)") that changes only `results/`; the job
refuses to push anything else. To take one down, revert its commit. A proposal over the
daily limit waits with a comment; add the `approved` label to run it anyway. **Actions →
Simulate a proposal → Run workflow** with the issue number runs one that failed for a
reason outside it (an edited rule is a new proposal: open a new issue). A proposal is
stored as `issue_N` under its author's GitHub name, whatever the YAML says.

**Why the runs can be trusted.** Python and package versions come from `uv.lock`, the data
is checked by hash, and every run is seeded, so a workflow run reproduces what
`rss-gov try` gives locally. Its log is public.
