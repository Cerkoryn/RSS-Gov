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
| Serve the site on the network, with a form for proposing schemes | `rss-gov serve` | |

`rss-gov all` runs everything after the download. On a 16-core desktop the whole run takes
about half an hour; one simulated six-month programme takes 0.1–0.4 seconds.

## Quick start

    uv venv --python 3.12 && uv pip install -e ".[dev]"
    rss-gov data pull        # about 30 minutes; KOIOS_API_KEY in the environment or .env is optional
    rss-gov all
    pytest -q

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
  checks at once and queues it for simulation. Every proposal is listed with its results.

Run `rss-gov serve` and open the address it prints. It listens on every interface
(0.0.0.0, port 8000; see `site` in `config.yaml`), so other machines on your network or VPN
can use it. There is no login: anyone who can reach the port can queue simulations, so
serve it only on networks you trust, or add `--read-only`. If a firewall is active, allow
the port from your network, for example `sudo ufw allow from 192.168.0.0/24 to any port
8000 proto tcp`.

The same folder also works as a static site (open `index.html` from disk, or upload the
folder to any static host): everything but the instant checks and the submission queue
works without the server. `results/report.md` has the same results as tables. `METHODS.md` explains how each number is produced and what it does not
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

## What the current run says

Chain data to epoch 666, a 5M ADA programme over 36 epochs, 100 seeds per scheme. Full
tables are in `results/report.md`. Changes are against unpaid, in the `central` scenario,
with the low-to-high range where it matters. Everything about behaviour under payment is
conditional on the assumed responses; cost and splitting gains are exact.

- **Today, voting power has almost nothing behind it.** Accounts linked on chain to DReps
  hold 51M ADA against 5.4B ADA of voting power: 0.87% backing, about 115 times leverage.
  Most of the 20 largest DReps show under 0.001%.
- **Every vote-based rule buys participation, and most differ little in how much**: +2.6
  to +4.6 points of delegated stake voting (from 25.3%), +1.5 to +3.2 with a low response,
  +3.9 to +6.9 with a high one. Most of it comes from DReps voting more, not from stake
  moving.
- **Proportional pay concentrates power**: 2 fewer DReps hold two thirds of the vote (1 to
  3.4 fewer across scenarios), entirely through awards buying reach. It cannot be gamed by
  splitting.
- **Equal pay cannot be defended**: an outsider with 1M ADA and fake DReps takes 88% of
  the budget.
- **Caps, square roots and "skip the largest" look like the middle way and are not
  free**: they stop the concentration, but an existing large DRep gains 15–30% of the
  budget by splitting into several, the way stake pools did. This insider side of the
  Sybil problem was invisible in the first version.
- **Paying delegators** moves about one extra point of stake into voting DReps, sends two
  thirds of delegator claims below 5 ADA, and needs some 23,000 payments instead of a few
  hundred. Spread flat across all voting DReps it concentrates power as much as
  proportional pay does.
- **A soft own-stake rule at 1000x barely moves backing** (+0.02 points). **A hard cap at
  1000x** raises it by 2 points and removes 82% of today's voting power, which costs 17
  points of participation and hands the remaining power to the few DReps with real own
  stake. Both rest on the linked-account proxy.
- **More money buys little more**: 1M ADA buys +3.1 points of participation, 10M buys
  +5.0. The cost per point rises from 0.6M to 4.0M ADA a year.
- **Three designs stay inside both guardrails, all at small budgets.** Of 34 finalists,
  three neither gain more than 10% by splitting nor do measurably worse than unpaid on any
  axis in any scenario. The best for participation (`g10_2`: linear, counted stake capped
  at 2M, the 200 largest paid, half the budget to delegators flat; 2.5M ADA) gives +3.4
  points of participation for 5.1M ADA a year. The only one that also spreads power
  (`g9_19`: skip the 20 largest, pay the next 400, own-stake limit 100x; 1M ADA) gives
  +1.6 DReps but only +0.9 points of participation. They pass partly because their losses
  in decentralisation (0.2 to 0.8 fewer DReps) are below the 1-DRep `meaningful` threshold,
  and the delegator-sharing ones send most delegator claims below 5 ADA. Designs that
  spread power much further (+7 to +16 DReps) carry splitting gains of 15–32%.

The choice any reward programme has to make is therefore which downside to accept, and the
response most worth measuring is whether awards really turn into reach, because the case against
proportional pay rests on that one assumption.

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
