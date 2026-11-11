# Contributing

RSS-Gov exists so that the trade-offs of rewarding Cardano governance are in plain view.
That only works if the people affected (DReps, delegators, SPOs, the Constitutional
Committee) can check the method and add to it. There are three ways to help.

## 1. Propose a reward scheme

A proposal is a rule in the reward family described in `METHODS.md`: how pay grows with
voting power, caps, who qualifies, what share goes to delegators, how pay is tied to a
DRep's own stake, and the budget. Every rule pays only for explicit votes.

**On the site.** When the site is served with `rss-gov serve`, the "Propose a scheme" page
builds the rule with a form, shows the exact checks at once (who would be paid, how much
splitting gains), and queues it for simulation. It appears on the results page a few
minutes later, next to every other design, whether or not it beats them.

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
(a few minutes). If the repository is on a code host, open an issue with the YAML, or a
pull request that adds it to `candidates.yaml`; a maintainer runs it.

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

`rss-gov serve` has no login: anyone who can reach the port can queue simulations. Use it
on networks you trust. To publish results for everyone, put `results/site/` on any static
host: every page works without the server, and the proposal form then offers the YAML and,
with `site.repository` set in `config.yaml`, a pre-filled issue.
