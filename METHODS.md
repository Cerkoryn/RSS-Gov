# Methods

What RSS-Gov claims, what it does not, and how each number is produced. The first section
is a plain-language summary; the rest is the detail behind it.

## In short

**The question.** Cardano's treasury could pay DReps, and the people who delegate to them,
for taking part in governance. There are many ways to do that, and each one buys something
and risks something. RSS-Gov does not pick a winner. It measures what each way of paying
does, on five things that matter, so that the choice between them can be made in the open.

**The five things measured.** For every reward rule:

1. *Participation*: how much of all delegated ADA ends up casting a vote.
2. *Decentralisation*: how many DReps it takes to hold two thirds of the voting power. More
   is better: power is spread wider.
3. *Skin in the game*: how much of the voting power is backed by the DRep's own ADA, so
   that those who decide also bear the consequences.
4. *Cost*: how much ADA a year leaves the treasury.
5. *Sybil risk*: how much of the budget someone gains by pretending to be several DReps
   (a Sybil attack). Lower is better.

**Only votes are paid.** Every rule pays for explicit votes (Yes, No and Abstain alike).
Nothing is paid for just being registered or holding delegation.

**What is known and what is assumed.** Some things can be computed exactly from the chain
today: who a rule would pay, what it costs, and how much splitting into several DReps
would gain. How people *react* to being paid cannot be known before anyone has been paid.
So RSS-Gov does three things:

- It builds a model of governance *without* rewards from the chain's history: how often
  each DRep votes, how delegators move, how DReps come and go. It then checks that model
  by starting it 40 epochs in the past and seeing whether it reproduces what actually
  happened. It does.
- It adds four reactions to money, each switched on and off separately: DReps vote more,
  delegators move towards paying DReps, DReps spend awards on attracting delegation, and
  DReps add their own stake when a rule rewards it. Each is tried at a low, a central and
  a high strength. A result that only appears at high strength is a hope, not a finding.
- It runs every rule many times from the same starting point with the same luck, and
  reports each result as a difference from paying nothing, with its uncertainty.

**What comes out.** No rule wins on every count. Paying in proportion to voting power
draws more votes but, if awards help DReps attract delegation, concentrates power. Paying
everyone the same invites fake DReps. Caps and "skip the largest" invite large DReps to
split themselves. Paying delegators moves some stake but costs many tiny payments. Tying
pay to own stake shows how little own stake stands behind today's votes. The results
page shows these trade-offs side by side, and which designs are not beaten on all five at
once.

**What would settle it.** Only a real programme can measure how strongly people react. The
last section describes how a programme could be set up to measure it.

**How to take part.** Anyone can propose a reward rule on the "Propose a scheme" page; it
is simulated exactly like the others and listed with its results. The method itself is
open too: this page is generated from `METHODS.md`, and `CONTRIBUTING.md` explains how to
suggest a change.

## The question

Every way of paying for governance participation buys something and risks something.
Paying in proportion to stake rewards the DReps who already hold the power. Paying
everyone the same invites fake DReps. Paying delegators can move idle stake but spreads
the money thin. Ignoring a DRep's own stake rewards power exercised with nothing at risk.
The question is therefore not "which rule is best" but: **for each rule, what does it do
on each of these dimensions, how sure are we, and which rules are not beaten on all of
them at once?**

Nobody has been paid yet, so history cannot say how people react to money. RSS-Gov
separates three kinds of evidence and never mixes them:

| Tier | Question | Depends on |
|---|---|---|
| A. Static | Who would this rule pay today, what does it cost, how gameable is it? | Chain data only |
| B. Model | What happens if people react with a given strength? | Chain data + assumed reaction strengths |
| C. Real world | How strongly do people actually react? | A real programme set up as an experiment |

Tier A results are facts about a formula. Tier B results are conditional forecasts. Only
tier C can turn them into findings.

## The axes

One measure per objective family. Decision quality (and "harmful proposals") is left out:
it cannot be observed on chain, and any label for it would be invented. Proposal
completion is left out as an axis too: too few actions close during one programme to tell
schemes apart on it. The model still simulates ratification, which is checked against
history and reported as `supported_ratified` in the run tables.

| Family | Measure (`config.yaml` name) | Better | Tier |
|---|---|---|---|
| Participation | Share of all delegated stake, including always-abstain and no-confidence, that casts an explicit vote on an action (`participation`) | higher | B |
| Decentralisation | DReps needed to exceed two thirds of DRep voting power (`tau67`) | higher | B |
| Skin in the game | Share of DRep voting power backed by the DRep's own stake: Σ min(power, own stake) / Σ power (`backing`) | higher | B, from an on-chain start |
| Reward sustainability | Treasury cost a year: what is paid out plus one transaction fee per payment (`annual_cost_ada`) | lower | A |
| Sybil resistance | Largest share of the budget gained by splitting one identity into several (`split_gain`) | lower | A |

Notes on the choices:

- **Participation** is measured against all delegated stake, not only stake already with
  DReps. A scheme that moves stake out of always-abstain into a voting DRep therefore
  scores, and one that only makes existing DReps vote more scores less than its turnout
  suggests. Turnout among DReps is still reported.
- **Skin in the game** is the reciprocal of leverage. One DRep's surplus cannot cover
  another's shortfall. Today it is under 1%: see the data section for why that number is a
  proxy.
- **Cost** is an axis because the budget is a design choice. Named schemes are compared
  at one budget; the search varies it, and a budget ladder shows what more money buys.
- **Sybil resistance** is a measured quantity, not a pass/fail gate. Where to draw the
  line is a separate, explicit guardrail (below).

Each axis has a `meaningful` difference in `config.yaml`: the smallest change worth acting
on. A change smaller than that counts as "same as unpaid" even if it is statistically
clear, and a change larger than that counts only if its 95% interval excludes zero.

## Data

`rss-gov data pull` reads the public Koios API and stores parquet tables under `data/`:
governance actions and their official tallies, every vote, each DRep's voting power in
every epoch since epoch 508, DRep certificates, protocol parameters, treasury totals, and
the accounts currently delegating to each DRep and to the two predefined options.

Two delegator lists are too long to page through (always-abstain has about 200,000
accounts). For lists over 5,000 accounts, every account of at least 100,000 ADA is fetched
exactly and the rest are represented by evenly spaced sample pages with a weight. Accounts
of at least 100,000 ADA hold about 90% of delegated stake.

**A DRep's own stake** is not a ledger concept. Two clues are on chain and both are
downloaded: the stake account that funded the DRep's registration transaction, and the
payment address the DRep declares in its metadata. The current balance of those accounts,
each counted once, is used as the DRep's own stake. For 828 of the 848 DReps with voting
power the linked accounts hold a balance. This is a proxy with errors in both directions: a DRep can hold stake in
accounts never linked to it, a registration can be paid for by someone else, and a
declared address proves nothing about control. It is good enough to show the order of
magnitude (most large DReps vote with thousands of times their linked stake) and not good
enough to pay on. A programme that rewards own stake needs accounts declared and signed
for by the DRep key.

Raw pages are cached, so a pull can be rebuilt offline; `manifest.json` records a hash per
table and `calibration.json` copies those hashes.

## The reward family (`mechanisms.py`)

**Only explicit votes are paid.** Yes, No and Abstain count alike; not voting earns
nothing; nothing is paid for merely being registered or holding delegation. Each epoch a
DRep's weight is

    eligible × min(stake, cap, leverage × own stake)^alpha × vote rate × (1 + bonus × rationale share)

where `vote rate` is the share of actions closed in the last 12 epochs that the DRep voted
on, and `eligible` applies a minimum stake, a minimum number of delegators, a minimum vote
rate, and an optional "skip the K largest, pay the next N". Weight is linear in the vote
rate, so every vote earns the same increment.

A share of the pot can go to delegators, always through a DRep that voted: `passthrough`
shares each DRep's own award with its delegators, `flat` pays one yield per ADA and per
unit of the DRep's vote rate. Delegating to always-abstain or to a DRep that does not vote
earns nothing.

`leverage` ties the stake that counts for rewards to the DRep's own stake (a soft
requirement). With `hard_cap` it limits *voting power* itself. That changes ratification
and needs a hard fork; such schemes are simulated and flagged `pilot_testable: false`.

## Tier A: static analysis (`static.py`)

The rule is applied to today's real DReps with no behaviour change. Reported: how many
are paid, the size of awards, the share going to the ten largest DReps, the share of
delegator claims too small to be worth a transaction, the voting power a hard cap would
leave, and two splitting measures.

**An outsider splitting.** Someone brings a fixed amount of own stake (default 1M ADA) and
spreads it over m fake DReps, each paying its deposit, voting on everything, attaching a
rationale to every vote, holding its stake in as many minimum-size accounts as the rule
demands, and counting that stake as its own. Reported: the share of the budget at the best
m up to 5,000, and how much of that exceeds what one honest DRep of the same size gets.
Only the excess is a Sybil gain; the rest is the reward for taking part.

**An insider splitting.** For each of the 20 largest DReps and three smaller ones: what it
adds by splitting into 2, 5, 10 or 20 equal DReps with its delegators and own stake
following. The largest gain is reported. Delegators may not follow, so this is an upper
bound. Stake pool operators did split pools in response to a cap, so it is not a
theoretical one.

`split_gain` is the larger of the two. Rules linear in stake give nothing to split for.
Equal splits reward an outsider's fake DReps. Caps, concave rules and "skip the largest"
reward an insider's split, which is the less obvious half of the problem.

## Tier B: the model (`model.py`)

A run is one possible future of the programme (default 36 epochs). State: every DRep with
voting power, and about 64,000 account rows that stand for the 270,000 delegating
accounts. Each epoch:

1. Account balances drift and fluctuate.
2. DReps register and retire at historical rates, with historical sizes.
3. The reward round is computed from what the chain shows.
4. Accounts re-delegate with a small probability. A mover picks always-abstain,
   no-confidence, or a DRep with weight `(stake + floor)^theta × exp(beta × vote rate)`.
5. Governance actions closing this epoch are voted on. Each action is a whole historical
   action resampled (its threshold, the support it had among voters, its abstention share
   and the attention it drew), so the links between those stay as observed. A DRep votes
   with its own fitted probability, shifted by the action's attention.
6. Ratification follows the ledger rule for DReps: yes power over active power, with
   non-voters counted as no, abstain votes and inactive DReps removed, and no-confidence
   stake counted as no. On history this rule alone reproduces 119 of 120 outcomes.

SPOs and the Constitutional Committee are not modelled. The scope is DReps and their
delegators.

### What is fitted, and from what (`calibrate.py`)

| Parameter | Source |
|---|---|
| Each DRep's vote probability | Its own recency-weighted vote history, shrunk toward DReps of similar size. The half-life is chosen by how well votes are predicted 18 epochs ahead. |
| Attention per action | The logit shift that reconciles that forecast with the action's real turnout |
| Re-delegation rate, large and small accounts | Age of current delegations in the account table |
| Share of moves to abstain / no-confidence | Where recent movers went |
| Preference for active DReps (`beta`) | Maximum likelihood on where large recent movers went |
| Preference for large DReps (`theta`) | Simulated moments: the value that keeps the effective number of DReps on its observed path over the fit window |
| Balance drift and volatility | Simulated moments: end totals and the turnover of DRep power shares |
| DRep entry and exit | Counts and sizes over the last 80 epochs |

`theta` deserves a note. Fitting it to individual movers' choices gives 0.45–0.80, and a
model run with that value slowly dissolves concentration, which has not happened on
chain: 20–26 DReps have held two thirds of the power throughout. Real inflows are lumpier
than a size rule (the five most-chosen DReps take 40–60% of moving accounts), so `theta`
is fitted to the concentration path instead and the cross-section value is kept as a
diagnostic.

### Validation gate

The model is fitted on epochs T-79..T-40 only, started from the observed state at T-40,
and run 40 times without rewards to T. It passes when simulated concentration, totals,
DRep count, share turnover, turnout, ballots per action and the ratification rate of
supported actions are within the tolerances in `config.yaml`. `rss-gov calibrate` prints
each check; every later command warns if the gate failed.

Honest limits of this test:

- The tolerances were set while building the model, not before. The next data pull is the
  first fully out-of-sample check: rerun `rss-gov calibrate` and see whether it still
  passes.
- The account table exists only for today, so the re-delegation rate uses information
  from the validation window. For earlier epochs each DRep's observed total is split into
  accounts the way it is split today.
- Total stake delegated to DReps passes narrowly. One large account leaving moved it by
  8% inside the window; the model cannot foresee such an event.
- The raw ratification rate is reported but not gated: it depends on which proposals get
  submitted, and recent proposals were more contested than earlier ones.

### What is assumed: four response channels

Each trade-off has its own channel, so a result can be traced to the assumption it rests
on. With every channel at zero, paying changes nothing (the tests check this).

| Channel | What it does | Trade-off it drives |
|---|---|---|
| `drep_response` | A DRep's log-odds of voting rise by `response × log(1 + reward for one more vote / vote cost)`. The same strength scales rationale publishing and new registrations. | Participation |
| `delegator_response` | A mover's log-weight for a DRep rises by `response` per point of annual yield; accounts earning less than a typical paying DRep offers become more likely to move. Yield falls as stake arrives. | Mobilising idle stake; where it goes |
| `reinvest_response` | A DRep's pull on movers is multiplied by `(1 + award / upkeep)^response`: awards pay for reach. Under a stake-proportional rule this adds about `response` to the exponent with which movers already favour large DReps. | Concentration under proportional pay |
| `pledge_response` | Under a rule that ties rewards or voting power to own stake, a DRep closes this share of its missing own stake over the programme. | Skin in the game |

`low`, `central` and `high` move all four together. `voting_only`, `yield_only`,
`reinvest_only` and `pledge_only` switch on one channel at its central value; the report
uses them to show which assumption each result depends on. A scheme's score for ranking is
its mean over `low`, `central` and `high`. The central values are guesses. A design is
credible only if its verdicts hold from `low` to `high`.

Not modelled: delegators leaving a DRep whose voting power is capped, vote buying,
collusion, changes in vote *direction* or quality, and price effects.

## Comparing schemes fairly (`experiment.py`)

1. **Same start.** Every scheme starts from the same chain snapshot.
2. **Same money.** Named schemes get the same budget and programme length. Where budget
   varies (the ladder, the search) cost is an axis, so a cheaper design is not penalised
   for buying less.
3. **Same luck.** All schemes share seeds, and every random draw about the outside world
   (which actions arrive, who would register, which accounts move) is common across
   schemes within a seed. Effects are mean paired differences from unpaid with a 95%
   interval across seeds.
4. **Same yardstick.** Each axis gets a verdict against unpaid: better, worse, or no
   meaningful difference. Verdicts are computed per scenario; the report marks a verdict
   as solid only when it holds in `low`, `central` and `high`.
5. **Measurements apart from judgement.** The axes are measured. Where to draw lines is in
   `guardrails`: a design is *acceptable* when splitting gains at most 10% of the budget
   and no axis other than cost is worse than unpaid in any scenario. Changing a guardrail
   re-labels designs without re-running anything.
6. **No single score.** A design is *shortlisted* when no other acceptable design is at
   least as good on every axis and meaningfully better on one. Designs outside a
   guardrail are not discarded: they are grouped by exactly which downside they accept,
   and the unbeaten ones in each group are reported (`best_of_its_kind`). If nothing is
   inside every guardrail, those groups are the result. What remains is a choice between
   trade-offs, which is a governance decision, not a modelling one.

Hard-fork-only designs go through the same comparison and get their own shortlist. They
cannot be tried without a ledger change, so for them tiers A and B are all the evidence
there will be before one.

## Search and hypervolume (`search.py`)

An evolutionary search over the family, budget included, with no language model in the
loop. Each generation mutates designs on the current front and adds random ones.

A search over noisy simulations always finds something. So the finalists are re-run on
100 seeds the search never saw, and only those numbers are reported.

With five axes almost any design is unbeaten on something, so the front is thinned: two
designs that differ by less than the `meaningful` amount on every axis count as one.

Hypervolume is used for one thing: a single number for "how much of the trade-off space
does this set of designs cover". Each axis is rescaled to 0–1 between the `scale` bounds
in `config.yaml`, expressed as a difference from unpaid, and the volume is exact. Unpaid is
always a member, since doing nothing is always available. The 95% interval comes from
resampling seeds. The report also gives what the search adds over the named schemes; if
that interval includes zero, the search found nothing the named schemes did not offer.

Coverage is also tracked using only designs within the Sybil guardrail, every round and on
the holdout seeds, because the widest corners are often reached by designs that are easy
to game. The finalists therefore include the largest contributors to both fronts: with and
without the designs over the limit.

Hypervolume depends on the chosen scales and rewards coverage of every corner, including
corners nobody wants (a very cheap programme that does nothing much). It tracks search
progress. It does not rank designs: read the shortlist.

## Proposed designs: community and agents

Anyone can propose a design in the same family, through the "Propose a scheme" page of
`rss-gov serve` or as a YAML file. A proposal gets the exact static checks at once and is
then simulated on the holdout seeds by `rss-gov try`, so its numbers are directly
comparable with the search finalists. Every proposal is kept in `results/proposals/` with
its text, its verdict and its runs, and shown on the results page whether or not it joins
the front. Proposals simulated under an older calibration are marked as needing a rerun.

The autoresearch loop (`program.md`) works the same way: an agent proposes designs in a
YAML file and runs `rss-gov try`.
The evaluator is frozen. A proposal is accepted only if it differs from every design on
the front by a meaningful amount without being beaten by one, and raises the holdout
hypervolume by an amount whose 95% interval excludes zero. Every proposal is logged in
`results/ledger.jsonl` with its change on each axis, accepted or not.

Repeated proposals against the same holdout seeds will eventually fit them. After a few
dozen proposals, change `HOLDOUT_OFFSET` and rerun the search.

## Tier C: measuring real reactions

Only a real programme can measure the responses the model has to assume. Each axis has a
different status there:

| Axis | In a real programme |
|---|---|
| Participation | Directly observable: votes and delegation each epoch. Measures `drep_response` and `delegator_response`. |
| Decentralisation | Observable, but slow: delegation moves by under 1% an epoch. Expect a direction, not a settled level. Measures `reinvest_response`. |
| Skin in the game | Only if the programme collects signed account declarations. A soft own-stake rule can be tried; that also measures `pledge_response`. |
| Cost | Known exactly, including the number and size of payments. |
| Sybil resistance | Not directly. Watch for new DReps near the minimum stake with identical votes, and for large DReps' delegation splitting across new DReps. |

- **Pre-register.** Before launch, record the rule, the model's predicted change on each
  axis under each scenario (`results/experiment_summary.csv`), and the analysis.
  Afterwards, the scenario closest to the outcome replaces the guess.
- **Randomise.** Before/after comparison of turnout is weak: turnout varied by 9 points
  between actions over the last 80 epochs, so detecting a 5-point change needs about 49
  actions per period, more than a six-month programme sees. Randomising *who is eligible
  first* is far stronger. A DRep's vote rate changed by 0.16 (standard deviation) between
  the last two 36-epoch windows, so two cohorts of about 170 DReps detect a 5-point
  change in vote rate with 80% power, and 45 per cohort detect 10 points.
- **Stagger.** Pay cohort A from the start and cohort B from the midpoint. Everyone is
  paid eventually, and the first half is a clean comparison.
- **Measure what the model predicts.** Vote rate per DRep, rationale rate, new
  registrations, re-delegation toward paid DReps, stake leaving always-abstain, and
  declared own stake.

Rules that need a hard fork cannot be tried this way. A soft version of the same rule
(own stake limiting rewards instead of voting power) can, and it measures the response a
hard cap would rely on.
