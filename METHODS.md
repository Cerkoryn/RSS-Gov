# Methods

What RSS-Gov claims, what it does not, and how each number is produced. The first section
is a plain-language summary; the rest is the detail behind it.

## In short

**The question.** DReps, and the people who delegate to them, could be paid for taking
part in governance: from Cardano's treasury, or by a *proposer fee*: part of each governance action's deposit
kept instead of returned. There
are many ways to do that, and each one buys something
and risks something. RSS-Gov does not pick a winner. It measures what each way of paying
does, on five things that matter, so that the choice between them can be made in the open.

**The five things measured.** For every reward rule:

1. *Participation*: how much of all delegated ADA ends up casting a vote.
2. *Decentralisation*: how many DReps it takes to hold two thirds of the voting power. More
   is better: power is spread wider.
3. *Skin in the game*: how much of the voting power is backed by the DRep's own ADA, its *pledge*, so
   that those who decide also bear the consequences.
4. *Cost*: how much ADA a year the rewards cost, whoever pays it.
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
  DReps add pledge when a rule rewards it. Each is tried at a low, a central and
  a high strength. A result that only appears at high strength is a hope, not a finding.
- It runs every rule many times from the same starting point with the same luck, and
  reports each result as a difference from paying nothing, with its uncertainty.

*How a simulation works*, below, explains each step in plain terms, with diagrams.

**What comes out.** No rule wins on every count. Paying in proportion to voting power
draws more votes but, if awards help DReps attract delegation, concentrates power. Paying
everyone the same invites fake DReps. Caps and "skip the largest" invite large DReps to
split themselves. Paying delegators moves some delegation but costs many tiny payments. Tying
pay to pledge shows how little pledge stands behind today's votes. The results
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
Paying in proportion to voting power rewards the DReps who already hold the power. Paying
everyone the same invites fake DReps. Paying delegators can move idle ADA but spreads
the money thin. Ignoring a DRep's pledge rewards power exercised with nothing at risk.
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

## How a simulation works

This section explains in plain terms what happens inside one simulated programme. The
sections after it give the formulas and where each number comes from.

### One run

A run is one possible six months of Cardano governance (36 epochs of five days) under one
reward rule. It starts from the chain as it is today: every DRep with voting power, its
voting record and pledge, and the accounts delegating to it. Large accounts are copied
one by one and small ones as weighted samples, so that a few tens of thousands of rows
stand for every delegating account. The run then plays the epochs forward one at a time,
in six steps:

<!--FIGURE:epoch-->

*The legend shows which parts copy how governance behaved without rewards, which part is
the rule under test, and which parts are the assumed reactions to money. With every
reaction switched off, a paid run is identical to an unpaid one.*

### How DReps behave

**Without rewards**, everything a DRep does copies its own history:

- **Voting.** Each DRep has its own chance of voting on an action, learned from its record.
  Recent votes count more than old ones, and a DRep with a short record is pulled toward
  the typical rate of DReps of its size. Each action is a real past action picked at
  random, and it keeps the attention it drew: on a busy action every DRep is more likely
  to vote. Whether a DRep votes is then a weighted coin toss. Votes split into Yes, No and
  Abstain in the proportions the real action got; the model does not try to predict what
  DReps think of a proposal.
- **Vote rate.** Rules pay by a DRep's *vote rate*: the share of the actions closed in the
  last 12 epochs that it voted on. A DRep that stops voting earns nothing within 12 epochs.
- **Coming and going.** New DReps register at the historical rate. Each starts with a
  delegation, voting habits and pledge drawn from those of real recent newcomers.
  DReps retire at the historical rate; the one that retires is the one closest in size to
  a DRep that really retired. Its delegators are left undelegated until they choose again.

**With rewards**, a DRep can react in the ways below, each only when its response strength
is above zero. Every reaction is worked out afresh each epoch from what the rule pays at
that moment; none builds up on its own.

- **Voting more** (`drep_response`). A DRep looks at what one more vote would earn it: its
  award if it voted on every action, divided by the number of actions. The higher that is
  next to the effort of a vote, put at 50 ADA, the more its chance of voting rises. For
  example, at the central strength a DRep that votes on half of the actions votes on
  about 59% when a vote pays 50 ADA, and about 76% when it pays 450 ADA. Doubling the pay
  does not double the effect. A DRep the rule would not pay, because it is too small or
  among the largest that are skipped, sees no gain and does not change.
- **Writing rationales** (the same strength). The same reaction, for rules that pay extra for a rationale, with
  the effort of a rationale put at 100 ADA.
- **Registering** (the same strength). If a newcomer of typical size would be paid well next to the effort of
  voting on everything, more people register, up to eight times the historical rate.
- **Buying reach** (`reinvest_response`). A DRep can spend its award on promotion, tools or
  staff, which makes it more visible to delegators who are choosing. At the central
  strength, an award equal to the cost of voting on everything makes it 15% more likely to
  be chosen. Under a rule that pays by voting power this helps the largest DReps most,
  which is how a rule can concentrate power.
- **Adding pledge** (`pledge_response`), under rules that count pledge: see below.

### How delegators behave

**Without rewards**:

- **Balances drift.** Each account grows or shrinks a little every epoch, at the pace and
  with the ups and downs seen on chain. Accounts with always-abstain have their own pace.
- **Most accounts never move.** In each epoch an account re-delegates with a small
  probability, learned from how long today's delegations have lasted. Accounts of 100,000
  ADA or more have their own rate.
- **Where movers go.** A mover chooses always-abstain, no-confidence or a DRep, in the
  proportions recent movers chose them. Among DReps it favours large ones and active ones,
  with strengths fitted to history so that the spread of voting power keeps to its real
  path. Because movers favour DReps that vote, a DRep that votes more because it is paid
  also gains delegation. That link is fitted, not assumed.

**With rewards** (`delegator_response`), only when a rule pays delegators, they chase
yield in two ways. An account earning less than a typical paying DRep offers becomes more
likely to move: at the central strength, twice as likely when the gap is one point a year,
and never more than ten times. And a mover favours DReps that pay more: at the central
strength one point of yield a year makes a DRep about 2.7 times as likely to be chosen. When
a DRep shares a fixed award with its delegators, each newcomer lowers the yield for the
next, so movers are taken in small batches and the yields are updated in between.

Delegators do not react to what a DRep itself is paid, except through the reach the DRep
buys with it.

### Pledge

Two words are used throughout. A DRep's *voting power* is all the ADA delegated to it,
its own included. Its *pledge* is the part of that ADA it owns itself. The word is
borrowed from stake pools, where an operator's pledge is the ADA it puts into its own pool;
"stake" is kept for stake pools.

The ledger has no idea of a DRep's pledge, so the simulation uses what can be traced on
chain: the accounts that paid for the DRep's registration and that it names in its
metadata. Of the ADA in those accounts:

- the part **delegated to the DRep itself** is its *pledge*. It stands behind the DRep's
  votes and is part of its voting power like any other delegated ADA;
- the whole balance, wherever it is delegated, is the DRep's *holdings*: a measure of
  what it could afford, used only to limit top-ups;
- ADA that **others** delegate to the DRep is voting power and is never counted as
  pledge.

New DReps get the pledge of a real recent newcomer, no more than their voting power, and
their holdings are taken to be that pledge.

A rule can use pledge in two ways, set by a *leverage* L:

- **A pledge soft cap**, for pay. Only up to L times its pledge counts toward the DRep's
  reward. With L = 2, a DRep with 10M ADA of voting power and 1M of pledge is paid as if
  it had 2M. It still votes with all 10M.
- **A pledge hard cap** on voting power itself: that DRep would vote with 2M. This needs a
  change to the ledger.

### Topping up pledge

Under such a rule a DRep may add pledge, when `pledge_response` is above zero. It decides
once an epoch:

<!--FIGURE:top-up-->

1. **What is missing.** The pledge it needs so that all of its voting power counts, or
   under a cap on counted power all of the capped amount, minus what it has. If nothing is missing,
   it adds nothing.
2. **This epoch's step.** A small share of the gap, sized so that if nothing else changed
   the DRep would close `pledge_response` of it over the programme: a quarter at the
   central strength.
3. **What it can afford.** Its pledge can grow to at most `pledge_wealth_multiple` times
   its holdings. Surveys of crypto owners find crypto is on average about a fifth of their
   financial wealth, more than half of it for about a fifth of owners, and under 15% for
   most; hence 5 times at the central strength, 2 at low and 7 at high. A DRep with no
   linked accounts adds nothing: nothing is known about what it owns.
4. **Whether it pays.** The extra reward a year the step would bring, with everyone else as
   they are, must be at least `pledge_min_return` of the ADA added: 5% at the central
   strength. Under a rule that pays everyone the same, pledge earns nothing and nobody
   adds any. Under a hard cap the test is skipped: the DRep adds pledge to keep its voting
   power, whatever it earns.

ADA a DRep adds counts as its pledge from then on and joins its voting power, so it
votes. The model treats it as new ADA brought into governance, not taken from another
DRep, and it leaves with the DRep if the DRep retires.

### How the five measures are taken

Four of the five measures come out of each run. The fifth, Sybil risk, is exact and needs
no simulation.

1. **Participation.** On every action that closes during the run: the voting power of the
   DReps who voted on it (Yes, No or Abstain alike), divided by all delegated ADA: to DReps
   (including pledge they added), to always-abstain or to no-confidence, or left behind
   by a DRep that retired. It is averaged over all the actions in the run. Because
   always-abstain is in the denominator, moving ADA from it to a DRep that votes raises
   participation, while a DRep that already votes always cannot.
2. **Decentralisation.** At the end of each epoch, DReps are lined up from the largest
   down, and the measure is how many it takes to pass two thirds of all DRep voting power
   (after any hard cap). It is averaged over the second half of the programme, when
   rewards have had time to move delegation.
3. **Skin in the game.** At the end of each epoch: for each DRep, the part of its voting
   power covered by its pledge, including any top-ups; summed over DReps and divided
   by all DRep voting power. A DRep with more pledge than voting power does not make up
   for another's shortfall. It is averaged over the second half of the programme.
4. **Cost.** All ADA paid out during the run, to DReps and to delegators, plus 0.3 ADA for
   each payment, turned into ADA a year. Each recipient gets one payment for the whole
   programme, and totals under 5 ADA are not sent. Money a rule does not pay out is not a
   cost.
5. **Sybil risk.** The largest share of the budget someone could gain by splitting one
   identity into several DReps, computed from the rule and today's chain without a
   simulation: see [Tier A](#tier-a-static-analysis-staticpy).

### From runs to results

Each rule is run many times. Run number 1 of every rule, and of paying nothing, sees the
same luck: the same actions closing in the same epochs, the same would-be newcomers, the
same coin tosses for who moves and who votes. Any difference between a rule's run and the
unpaid run with the same luck is therefore mostly the rule's doing. A result is the average
of those differences over all runs, with a 95% interval, and it is computed three times:
with weak, central and strong reactions. A result that holds at all three is one the
assumptions do not decide.

## The axes

One measure per objective family. Decision quality (and "harmful proposals") is left out:
it cannot be observed on chain, and any label for it would be invented. Proposal
completion is left out as an axis too: too few actions close during one programme to tell
schemes apart on it. The model still simulates ratification, which is checked against
history and reported as `supported_ratified` in the run tables.

| Family | Measure (`config.yaml` name) | Better | Tier |
|---|---|---|---|
| Participation | Share of all delegated ADA, including always-abstain and no-confidence, that casts an explicit vote on an action (`participation`) | higher | B |
| Decentralisation | DReps needed to exceed two thirds of DRep voting power (`tau67`) | higher | B |
| Skin in the game | Share of DRep voting power backed by the DRep's pledge: Σ min(power, pledge) / Σ power (`backing`) | higher | B, from an on-chain start |
| Reward sustainability | Cost a year: what is paid out, from a budget or from fees, plus one transaction fee per payment (`annual_cost_ada`) | lower | A |
| Sybil resistance | Largest share of the budget gained by splitting one identity into several (`split_gain`) | lower | A |

Notes on the choices:

- **Participation** is measured against all delegated ADA, not only ADA already with
  DReps. A scheme that moves ADA out of always-abstain into a voting DRep therefore
  scores, and one that only makes existing DReps vote more scores less than its turnout
  suggests. Turnout among DReps is still reported.
- **Skin in the game** is the reciprocal of leverage. One DRep's surplus cannot cover
  another's shortfall. Today it is under 1%: see the data section for why that number is a
  proxy.
- **Cost** is an axis because the budget is a design choice. Named schemes are compared
  at one budget; the search varies it, and variations of named designs at other budgets
  show what more money buys; each named design is also run paid by fees alone. It counts
  every ADA paid out, whether it comes from a budget or from a proposer fee, and does
  not say who bears it in the end.
- **Sybil resistance** is a measured quantity, not a pass/fail gate. Like cost, it is an
  exact property of a rule and is traded off against the other axes with no limit of its
  own. Its `scale` in `config.yaml` sets how fast it counts against a design in the
  hypervolume: a rule that lets splitting gain half the budget or more covers nothing on it.

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
of at least 100,000 ADA hold about 90% of delegated ADA.

**A DRep's pledge** is not a ledger concept. Two clues are on chain and both are
downloaded: the account that funded the DRep's registration transaction, and the
payment address the DRep declares in its metadata. The current balance of those accounts,
each counted once, is what the DRep is known to hold. Only the part delegated to the DRep
itself counts as its pledge: own ADA delegated elsewhere is not behind its votes, and
ADA others delegate to it is never counted as pledge. This is a proxy with errors in both
directions: a DRep can hold ADA in
accounts never linked to it, a registration can be paid for by someone else, and a
declared address proves nothing about control. It is good enough to show the order of
magnitude (most large DReps vote with thousands of times their pledge) and not good
enough to pay on. A programme that rewards pledge needs accounts declared and signed
for by the DRep key.

Raw pages are cached, so a pull can be rebuilt offline; `manifest.json` records a hash per
table and `calibration.json` copies those hashes.

## The reward family (`mechanisms.py`)

**Only explicit votes are paid.** Yes, No and Abstain count alike; not voting earns
nothing; nothing is paid for merely being registered or holding delegation. Each epoch a
DRep's weight is

    eligible × rank × size^alpha × vote rate × (1 + bonus × rationale share)

where `vote rate` is the share of actions closed in the last 12 epochs that the DRep voted
on, and `size` is its voting power, limited by `cap` and by `leverage × pledge`, or,
with `basis: delegators`, its number of delegating accounts. Weight is linear in the vote
rate, so every vote earns the same increment.

- `eligible` applies a minimum voting power in ADA, a minimum share of all DRep voting
  power (`min_share`), a minimum number of delegators and a minimum vote rate.
- `rank` handles "skip the K largest, pay the next N". The K largest are weighted by
  `top_weight` (0 skips them; 0.25 pays them a quarter). With `roll_down`, a place among
  the N passes down when a DRep above does not vote: a DRep keeps the part of a place left
  after the DReps ranked above it are expected to vote (their vote rates), which is the
  expected value of paying the first N voters on each action.

The weights split the DReps' pot. `equal_share` splits that fraction of it by vote rate
alone, and the rest by the full weight. Two settings stop the pot being spent in full;
the unspent ADA stays in the budget:

- `per_vote_ada` pays a fixed amount per vote instead of a share. Votes are the vote rate
  times the actions closing per epoch on average. If the votes would cost more than the
  pot, every payment is scaled down. It needs `alpha` 0 and no delegator share.
- `max_award_share` limits any one DRep to that share of the DReps' pot. The excess is not
  handed to the others.

A share of the pot can go to delegators, always through a DRep that voted: `passthrough`
shares each DRep's own award with its delegators, `flat` pays one yield per ADA and per
unit of the DRep's vote rate. Delegating to always-abstain or to a DRep that does not vote
earns nothing.

`leverage` ties the voting power that counts for rewards to the DRep's pledge: a pledge soft
cap. With `hard_cap` it limits *voting power* itself: a pledge hard cap. That changes ratification
and needs a hard fork; such schemes are simulated and flagged `pilot_testable: false`.

### Paying from a proposer fee

`fee_ada`, the *proposer fee*, funds the pot from governance actions instead of, or as
well as, a budget: each action that closes adds that much, as if that part of its
proposer's deposit were kept as a fee rather than returned ([CIP PR #1117](https://github.com/cardano-foundation/CIPs/pull/1117)
proposes this). Today every deposit is returned, so a fee needs a ledger change and such
designs are flagged `pilot_testable: false`. With `budget_ada: 0` a design is paid by fees
alone.

The money arrives in lumps: many epochs close no action, and a busy one closes many at once.
Payments follow the lumps, so the cost follows the number of actions in each run.
Behaviour follows the steady flow, the fee times the average number of actions closing
per epoch, because that is what a DRep or delegator can count on; reacting to each lump
would make a fee look worse only because the model's actors look one epoch ahead. At the
same expected money a fee therefore buys the same reactions as a budget, at a cost that
moves with the number of actions.

Not modelled: proposers proposing less when part of the deposit is kept (the deposit has
not changed since governance began, so there is no data on how they would react), fees
added to treasury requests, and fewer actions easing the load on DReps (a DRep's chance
of voting does not depend on how many actions are open). The number of actions in a run
is drawn from history whatever the fee.

To compare the two sources, every named design is also simulated with no budget, paid by
each proposer fee in `experiment.fees_ada` in `config.yaml` (named like `capped_fee_50k`,
labelled "50k ADA proposer fee"). The
report sets each beside its budget version. The search varies budgets, not fees, and does
not start from these.

### Named designs

Besides the generic shapes (`proportional`, `equal`, `sqrt`, `capped`, gates, floors,
rationale bonus, delegator designs and pledge caps), the named designs come from published
proposals. Each is the closest point in the family, not an exact copy. The `pledge_soft_cap_*`
designs were found by hand: they have only two settings each, so they are easy to explain
and to implement.

| Name | Rule | Source |
|---|---|---|
| `middle_out` | equal pay, skip the 10 largest, pay the next 100 | [ExcludeKPayN](https://github.com/Cerkoryn/ExcludeKPayN/blob/main/paper.md) |
| `exclude_k_pay_n` | 10 ADA per vote, skip 10, pay the next 200 with roll-down | ExcludeKPayN, per-proposal form |
| `top_m_equal`, `top_m_proportional` | the 100 largest, equal or by voting power | [IO Research, Reward Schemes for DReps in Voltaire](https://docs.google.com/document/d/1_uadn9Ord3mAYQGWHQySR73CQciVk2YNc5rt8npJ6Aw), variants 1a and 2a |
| `threshold_k` | DReps with at least 1/k of all voting power (k = 100) get 1/k of the pot each; the rest is not spent | [Birmpas et al., FC 2025](https://arxiv.org/abs/2406.10525) Threshold(k); IO Research variant 1b |
| `threshold_k_proportional` | the same DReps, paid by voting power | Birmpas et al. variant 2; IO Research variant 2b |
| `equal_plus_power` | half equal, half by voting power | [CIP PR #1117](https://github.com/cardano-foundation/CIPs/pull/1117) hybrid split |
| `top_haircut` | proportional, 70% vote rate and 10 delegators to qualify, the 20 largest at 25% | [Cardano forum: DAO incentive models](https://forum.cardano.org/t/lessons-in-decentralized-governance-what-cardano-can-learn-from-dao-incentive-models/154264), DRep side of experiment 1 |
| `top_100_gated` | the 100 largest with a 70% vote rate, equal pay | Optimism's top-100 participation rewards ([DAOstar survey](https://forum.scroll.io/t/delegate-incentive-programs-daostar-research/470)) |
| `delegators_first` | 90% to delegators of DReps voting 70%, flat; DReps by voting power, at most 10% of their part each | ENS-style split (same forum post) |
| `delegator_count_sqrt` | square root of the number of delegators, at most 5% each | the same forum post, experiment 4 |
| `pledge_soft_cap_skip20` | by voting power, counting no more than the DRep's pledge, the 20 largest paid nothing | this project: simple pledge soft caps |
| `pledge_soft_cap_skip10` | the same, counting up to twice the pledge, the 10 largest paid nothing | this project |
| `pledge_soft_cap_capped` | by voting power, counting no more than the pledge or 5M ADA | this project |

### What the family cannot express

- **Pay that depends on how a DRep voted**: rewarding the winning side
  ([Beccuti & Schneider](https://arxiv.org/abs/2610.07959)), prediction-market accuracy
  scores, penalties for the losing side. The model draws vote direction from history and
  has no "correct" outcome, so this would reward conformity, not judgement.
- **Judged quality**: peer-review juries, retroactive rewards, rubric scores, delegator
  ratings. None is computable from the chain; a rationale anchor is the closest.
- **Linking DReps run by one operator**: the chain has no identity.
- **Delegator mechanics**: time-weighted balances, one-time bonuses for leaving
  always-abstain, matching new delegation, caps per delegator, and a pool that grows with
  participation. Each needs a response assumption with no data behind it.
- **A base for everyone plus a bonus for the top m** (IO Research variant 3): the family
  applies one eligibility rule to the whole pot.

Pay per action is approximated per epoch: `roll_down` uses expected votes, and
`per_vote_ada` uses the average number of actions per epoch.

## Tier A: static analysis (`static.py`)

The rule is applied to today's real DReps with no behaviour change. Reported: how many
are paid, the size of awards, the share going to the ten largest DReps, the share of
delegator claims too small to be worth a transaction, the voting power a hard cap would
leave, and two splitting measures. A proposer fee is counted at the average pace of
closing actions in history; `fee_share` is the share of the money it brings in.

**An outsider splitting.** Someone brings a fixed amount of its own ADA (default 1M ADA) and
spreads it over m fake DReps, each paying its deposit, voting on everything, attaching a
rationale to every vote, holding its ADA in as many minimum-size accounts as the rule
demands, and counting it as pledge. Reported: the share of the budget at the best
m up to 5,000, and how much of that exceeds what one honest DRep of the same size gets.
Only the excess is a Sybil gain; the rest is the reward for taking part.

**An insider splitting.** For each of the 20 largest DReps and three smaller ones: what it
adds by splitting into 2, 5, 10 or 20 equal DReps with its delegators and pledge
following. The largest gain is reported. Delegators may not follow, so this is an upper
bound. Stake pool operators did split pools in response to a cap, so it is not a
theoretical one.

`split_gain` is the larger of the two. Rules linear in voting power give nothing to split for.
Equal splits reward an outsider's fake DReps. Caps, concave rules and "skip the largest"
reward an insider's split, which is the less obvious half of the problem.

## Tier B: the model (`model.py`)

A run follows the six steps in [How a simulation works](#how-a-simulation-works).
State: every DRep with voting power, and about 64,000 account rows that stand for the
270,000 delegating accounts. Details not given there:

- The reward round uses what the chain shows at the start of the epoch, before that
  epoch's moves and votes. Money a round does not pay out carries over to the next.
- A mover picks always-abstain, no-confidence, or a DRep with weight
  `(voting power + floor)^theta × exp(beta × vote rate)`, times the reactions in the table below.
- Each action is a whole historical action resampled (its threshold, the support it had
  among voters, its abstention share and the attention it drew), so the links between
  those stay as observed. A DRep votes with its own fitted probability, shifted on the
  log-odds scale by the action's attention.
- Ratification follows the ledger rule for DReps: yes power over active power, with
  non-voters counted as no, abstain votes and inactive DReps removed, and no-confidence
  ADA counted as no. On history this rule alone reproduces 119 of 120 outcomes.

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
- Total ADA delegated to DReps passes narrowly. One large account leaving moved it by
  8% inside the window; the model cannot foresee such an event.
- The raw ratification rate is reported but not gated: it depends on which proposals get
  submitted, and recent proposals were more contested than earlier ones.

### What is assumed: four response channels

Each trade-off has its own channel, so a result can be traced to the assumption it rests
on. With every channel at zero, paying changes nothing (the tests check this).

| Channel | What it does | Trade-off it drives |
|---|---|---|
| `drep_response` | A DRep's log-odds of voting rise by `response × log(1 + reward for one more vote / vote cost)`. The same strength scales rationale publishing and new registrations. | Participation |
| `delegator_response` | A mover's log-weight for a DRep rises by `response` per point of annual yield; accounts earning less than a typical paying DRep offers become more likely to move. Yield falls as delegation arrives. | Mobilising idle ADA; where it goes |
| `reinvest_response` | A DRep's pull on movers is multiplied by `(1 + award / upkeep)^response`: awards pay for reach. Under a power-proportional rule this adds about `response` to the exponent with which movers already favour large DReps. | Concentration under proportional pay |
| `pledge_response` | Under a rule that ties rewards or voting power to pledge, a DRep closes this share of its missing pledge over the programme. Under a pledge soft cap, only the pledge that would count for rewards is missing (no more than any cap on counted power allows), and a DRep adds each part only while the extra award it brings is at least `pledge_min_return` a year on that ADA. Under a pledge hard cap a DRep adds it to keep its voting power, whatever it earns. Either way its pledge grows to at most `pledge_wealth_multiple` times the ADA in its linked accounts, a bound on what it could buy, and the ADA it adds joins its voting power. | Skin in the game |

`low`, `central` and `high` move all four together. `voting_only`, `yield_only`,
`reinvest_only` and `pledge_only` switch on one channel at its central value; the report
uses them to show which assumption each result depends on. A scheme's score for ranking is
its mean over `low`, `central` and `high`. The central values are guesses. A design is
credible only if its verdicts hold from `low` to `high`.

Not modelled: delegators leaving a DRep whose voting power is capped, vote buying,
collusion, changes in vote *direction* or quality, and price effects.

A DRep reacts to what one more vote is worth at its current size. It does not campaign
for delegation to reach a threshold. Rules that pay only above a size (`threshold_k`,
top-m) are therefore judged without the climb they are meant to cause, beyond what movers
already give DReps that vote more.

## Comparing schemes fairly (`experiment.py`)

1. **Same start.** Every scheme starts from the same chain snapshot.
2. **Same money.** Named schemes get the same budget and programme length. Where budget
   varies (variations, the search) cost is an axis, so a cheaper design is not penalised
   for buying less.
3. **Same luck.** All schemes share seeds, and every random draw about the outside world
   (which actions arrive, who would register, which accounts move) is common across
   schemes within a seed. Effects are mean paired differences from unpaid with a 95%
   interval across seeds.
4. **Same yardstick.** Each axis gets a verdict against unpaid: better, worse, or no
   meaningful difference. Verdicts are computed per scenario; the report marks a verdict
   as solid only when it holds in `low`, `central` and `high`.
5. **Measurements apart from judgement.** The axes are measured. Where to draw lines is in
   `guardrails`: a design is *acceptable* when no axis other than cost and Sybil
   resistance is worse than unpaid in any scenario. Those two are exact trade-offs every
   paid rule makes to some degree, so they are weighed on the front instead. Changing a
   guardrail re-labels designs without re-running anything.
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

Hypervolume depends on the chosen scales and rewards coverage of every corner, including
corners nobody wants (a very cheap programme that does nothing much). It tracks search
progress. It does not rank designs: read the shortlist.

## Proposed designs: community and agents

Every design is a point in one family, so every setting of every design can be changed.
The site lists the settings each design was simulated with, and gives a design that
differs from a named one in one or two settings a short name of that kind ("Middle out ·
skip 20"). Variations listed in `config.yaml` (a named design with some settings changed)
are simulated like the named designs.

Anyone can propose a design in the same family, through the "Propose a scheme" page or
as a YAML file. A proposal gets the exact static checks at once (the page computes them in
the browser with the same formulas, and a test keeps the two implementations equal) and is
then simulated on the holdout seeds by `rss-gov try`, so its numbers are directly
comparable with the search finalists. A proposal submitted as a GitHub issue is simulated
and published as soon as it arrives, with no human step, up to three a day per person.
Every proposal is kept in `results/proposals/` with its verdict and its runs, and shown on
the results page whether or not it joins the front. The site titles it from its rule and
links to the issue for the idea behind it rather than repeating the issue's text.
Proposals simulated under an older calibration are marked as needing a rerun.

An AI agent can propose designs the same way, following `program.md`. Only `rss-gov
research --rounds N` starts it; nothing else does. Its designs are judged exactly like a
proposal, and those accepted join the search's finalists and are shown as found by
search. Its rejected attempts are kept only in the ledger.
The evaluator is frozen. A proposal is accepted only if it differs from every design on
the front by a meaningful amount without being beaten by one, and raises the holdout
hypervolume by an amount whose 95% interval excludes zero. Every proposal is logged in
`results/ledger.jsonl` with its change on each axis, accepted or not.

Repeated proposals against the same holdout seeds will eventually fit them, and nobody
reviews a proposal before it can join the front. So after `search.tries_per_holdout` new
designs have been simulated on a set of holdout seeds (community or agent; re-running a
stored proposal does not count), the set counts as used. The next `rss-gov try` first
re-runs the search's finalists on a fresh set and judges them again, then tries every
stored proposal again against them (the agent's only if it was accepted). A design that
was accepted on luck then drops out.

## Tier C: measuring real reactions

Only a real programme can measure the responses the model has to assume. Each axis has a
different status there:

| Axis | In a real programme |
|---|---|
| Participation | Directly observable: votes and delegation each epoch. Measures `drep_response` and `delegator_response`. |
| Decentralisation | Observable, but slow: delegation moves by under 1% an epoch. Expect a direction, not a settled level. Measures `reinvest_response`. |
| Skin in the game | Only if the programme collects signed account declarations. A pledge soft cap can be tried; that also measures `pledge_response`. |
| Cost | Known exactly, including the number and size of payments. |
| Sybil resistance | Not directly. Watch for new DReps near the minimum voting power with identical votes, and for large DReps' delegation splitting across new DReps. |

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
  registrations, re-delegation toward paid DReps, ADA leaving always-abstain, and
  declared pledge.

Rules that need a hard fork cannot be tried this way. A soft version of the same rule
(a pledge soft cap instead of a hard one) can, and it measures the response a
hard cap would rely on.
