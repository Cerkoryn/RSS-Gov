# RSS-Gov

Research tool for governance reward designs on Cardano. Every way of paying
DReps and their delegators trades something off: proportional pay feeds concentration,
equal pay invites fake DReps, paying delegators spreads money thin, and ignoring a DRep's
own stake rewards power with nothing at risk. RSS-Gov measures each payment rule on all
of those dimensions at once, says how sure it is, and shortlists the rules that are not
beaten across the board, so that the trade-offs of any reward design are in plain view.

It replaces the earlier simulator (archived next to this folder as `OLD_RSS-Gov`). The
design goal is that every number can be traced to chain data, to a stated assumption, or
to both, and that the two are never confused.

**The results are online at <https://cerkoryn.github.io/RSS-Gov/>.** Anyone can propose a
reward rule there; it is simulated on GitHub's servers and listed with its results.

## The five axes

| Family | Measure | Better |
|---|---|---|
| Participation | Share of all delegated stake that casts an explicit vote | higher |
| Decentralisation | DReps needed for two thirds of DRep voting power | higher |
| Skin in the game | Share of voting power backed by the DRep's own stake | higher |
| Reward sustainability | Treasury cost a year | lower |
| Sybil resistance | Share of the budget gained by splitting one identity | lower |

Decision quality is deliberately left out: it cannot be observed on chain. Proposal
completion is left out too: too few actions close during one programme to compare schemes
on it. Every scheme pays only for explicit votes (Yes, No and Abstain count alike).

## What it does

| Step | Command | Evidence |
|---|---|---|
| Download governance history from Koios | `rss-gov data pull` | chain data |
| Fit a model of unpaid behaviour and test it on held-out epochs | `rss-gov calibrate` | chain data |
| Apply each rule to today's real DReps: who is paid, what splitting earns | `rss-gov static` | chain data |
| Simulate each rule over many seeds and response scenarios | `rss-gov experiment` | chain data + assumed response |
| Search the rule family; judge finalists on unseen seeds | `rss-gov search` | chain data + assumed response |
| Test designs proposed by a person or an AI agent | `rss-gov try candidates.yaml` | same |
| Write `results/report.md` with figures, and the results site in `results/site/` | `rss-gov report` | |
| Check and store a proposal (YAML or a GitHub issue) | `rss-gov submit` | |

`rss-gov all` runs everything after the download. On a 16-core desktop the whole run takes
about half an hour; one simulated six-month programme takes 0.1–0.4 seconds.

## Quick start

    uv sync --extra dev      # the versions in uv.lock; or: uv venv && uv pip install -e ".[dev]"
    rss-gov data pull        # about 30 minutes; KOIOS_API_KEY in the environment or .env is optional
    rss-gov all
    pytest -q

To work on the published results instead of a fresh pull, download the data they were
computed from: `gh release download data-epoch-666 -p data.tar.gz` (the epoch is
`tip_epoch` in `results/calibration.json`), unpack it into `data/pull/`, and check it with
`rss-gov data verify`. To replace it with the latest data, run `rss-gov data pull --fresh`.

Settings live in `config.yaml`: the programme budget and length, the axes and what counts
as a meaningful difference on each, the response scenarios, the guardrails, and the
validation tolerances.

## Reading the results

The results site in `results/site/` has three pages:

- **Results**: a scorecard of every design on every axis, a trade-off chart for any two
  axes, which assumption each result rests on, what more money buys, and the check
  against history.
- **How it works**: `METHODS.md`, starting with a plain-language summary.
- **Propose a scheme**: a form that builds a rule in the reward family, shows its exact
  checks at once (computed in the browser) and submits it for simulation. Every proposal
  is listed with its results.

The site is published on GitHub Pages from the `gh-pages` branch (see "How the site is
published" in `CONTRIBUTING.md`). Locally, open `results/site/index.html` from disk.
Proposals go through GitHub issues and are simulated on GitHub's runners.
`results/report.md` has the same results as tables. `METHODS.md` explains how each number is produced and what it does not
show. Things to keep in mind:

1. **The unpaid model is fitted and tested.** Started 40 epochs back from data it was not
   fitted on, it has to reproduce what then happened to concentration, delegation totals,
   turnout and ratification. `rss-gov calibrate` prints the result of each check.
2. **The response to money is assumed.** Nobody has been paid yet. Four response channels
   (DReps voting more, delegators chasing yield, awards buying reach, DReps adding own
   stake) each run from "no reaction" to "strong reaction". A verdict counts only if it
   holds from `low` to `high`, and the report shows which channel each result rests on.
3. **Noise is measured.** Schemes are compared on the same seeds, and effects come with
   95% intervals. Finalists of the search are re-run on seeds the search never saw.
4. **Measurement and judgement are separate.** The axes are measured. The lines a design
   must not cross are `guardrails` in `config.yaml`; moving one re-labels the shortlist
   without re-running anything.

## Scope and limits

- DReps and their delegators only. SPO and Constitutional Committee votes are not
  modelled.
- Vote direction and decision quality are not modelled; only whether DReps vote and
  publish a rationale.
- A DRep's own stake is read from accounts linked to it on chain (the funder of its
  registration, its declared payment address). That is a proxy with errors in both
  directions; a real programme needs signed declarations.
- The insider splitting gain assumes a DRep's delegators follow it into its new
  identities. It is an upper bound.
- Rules that change voting power itself (a hard cap) need a hard fork. They are simulated
  and flagged, and delegators leaving a capped DRep are not modelled.
- The model cannot foresee one-off events such as a very large account moving.

## Working with an AI agent

`program.md` is the brief for an agent (Claude Code, Codex) that proposes designs. The
agent edits `candidates.yaml` and runs `rss-gov try`; the evaluator is frozen, and a
proposal is accepted only if it differs meaningfully from the designs already on the
front and widens it on holdout seeds by more than noise. Each proposal is logged with its
change on every axis. This uses a coding subscription a few times an hour, not once per
simulation.

`AGENTS.md` has the rules for changing the code.

## Contributing

Anyone can propose a reward scheme (on the site, or as a YAML file) or challenge the
method. `CONTRIBUTING.md` explains how, and what reviewers check.

## Licence

Apache-2.0. See `LICENSE` and `NOTICE`.
