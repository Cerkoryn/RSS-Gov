# Research programme for an AI agent

You are improving reward schemes for Cardano governance. The evaluator is fixed; your job
is to propose better designs and to explain why they should work.

## The loop

1. Read `results/report.md` and `results/search_front.csv`: which trade-offs the current
   shortlist offers and which it lacks. Read `results/ledger.jsonl` and
   `results/proposals/*.json`: what has been tried, by you and by others.
2. Form a hypothesis about the mechanism, in one or two sentences, naming the axis it
   should move and the axis it risks. Example: "A cap keeps the participation gain of
   proportional pay but invites the largest DReps to split; adding a floor of 50
   delegators per DRep should make splitting costly without losing participation."
3. Write up to five designs in `candidates.yaml` (format below).
4. Run `rss-gov static --schemes candidates.yaml`. It is instant and exact: look at
   `split_gain` and who gets paid before spending simulation time.
5. Run `rss-gov try candidates.yaml`.
6. Record the hypothesis and the outcome in `notes/` (one short file per round). A
   rejected proposal that kills a hypothesis is a useful result.

The five axes are in `config.yaml` under `axes`: participation, decentralisation, skin in
the game, cost and Sybil resistance. A proposal is accepted only when
it widens the front: it raises the holdout hypervolume by an amount whose 95% interval
excludes zero. Most proposals will be rejected. That is expected. An accepted proposal is
not a recommendation: the report's shortlist also applies the guardrails.

## Proposal format

```yaml
- name: capped_floor_25          # unique, descriptive
  alpha: 1.0                     # weight = counted stake ** alpha
  cap_ada: 10000000              # counted stake is at most this
  min_delegators: 25
  budget_ada: 2500000            # optional; default is the programme budget
- preset: sqrt                   # or start from a named scheme and override
  name: sqrt_gate
  activity_gate: 0.5
```

Fields: `budget_ada`, `alpha`, `cap_ada`, `k_exclude`, `n_pay`, `min_stake_ada`,
`min_delegators`, `activity_gate`, `rationale_bonus`, `delegator_share`, `delegator_mode`
(`passthrough` or `flat`), `pledge_leverage`, `hard_cap`. See `src/rss_gov/mechanisms.py`.
Every scheme pays only for explicit votes; that is not a parameter.

## What you may change

- `candidates.yaml` and `notes/`: freely.
- `src/rss_gov/mechanisms.py`: you may add a new field to the family when a hypothesis
  cannot be expressed with the existing ones. It must read only what `Round` provides,
  default to "off", pay nothing to a DRep that has not voted, come with a test in
  `tests/test_mechanisms.py`, and state what it needs on chain in `feasibility()`.

## What you may not change

- `model.py`, `calibrate.py`, `experiment.py`, `search.py`, `metrics.py`, `static.py`,
  the axes, guardrails, scenarios, assumptions or tolerances in `config.yaml`, or anything
  under `results/` by hand. If you believe the evaluator is wrong, write the argument in
  `notes/` and stop; a human decides.

## Standards

- Do not claim an effect that is smaller than its interval, or smaller than the axis's
  `meaningful` difference.
- Report every axis a design moves, including the ones it makes worse.
- Do not propose a design only because it scores well. Say what behaviour it relies on,
  and check that behaviour is one the model actually has (`METHODS.md`, "What is
  assumed"). A design that wins by exploiting a gap in the model is a bug report, not a
  result.
- Say whether a design needs anything not on chain today.
- The holdout seeds are reused by every `try`. After about thirty proposals, ask for the
  holdout seeds to be changed and the search rerun.
