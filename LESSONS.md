# Lessons

Trends found across reward designs, and where they break. A working log for us and for the
research agent (`program.md`); it is not published on the site.

## How to keep it

- **One trend per lesson**, stated as a claim across designs, not about one design.
- **Evidence**: the designs compared (names as in `config.yaml` or the report), the
  scenario (`central`, or a single-reaction scenario such as `yield_only` to show which
  reaction drives it) and the size of the effect, with the run it comes from. Numbers are
  from that run and drift when the data or the model changes; the direction should not.
  If a number changes sign or falls inside its interval, the lesson needs checking.
- **Only meaningful effects count.** Effects are paired differences from unpaid. One whose
  95% interval includes zero, or that is smaller than the axis's `meaningful` difference
  in `config.yaml` (1 point of participation, 1 DRep, 0.2 points of backing, 2 points of
  Sybil gain), is not a trend.
- **Why**: the mechanism in the model behind it (a `METHODS.md` section). A lesson that
  rests on an assumed reaction says so.
- **Numbers are names**: a new lesson takes the next free number wherever it is filed, so
  references to it stay valid.
- **Status**: *holds*, *holds with exceptions* or *contradicted*. When a design breaks a
  lesson, list it under the lesson as a counter-example instead of deleting the lesson;
  when the exceptions show where the trend really stops, rewrite the claim.

Runs cited: **R1** = 2026-11-22, data to epoch 666, 100 seeds per design, budget 5M ADA
over the six-month programme (about 10M a year) unless stated. **R2** = the same day and
data, with `per_drep` delegator pots added to the search and eleven variations around the
leading design; numbers for designs in both runs are the same. **R3** = the same day and
data, with 51 pledge contest designs (`pledge_contest*`, L17 to L22); the search was not
rerun, and earlier designs' numbers are unchanged. **R4** = 2026-11-23, the same data, with
a wealthy newcomer in the model (`central_whale`), two wealth stress tests (`central_poor`,
`central_rich`), pots that grow with pledge (`pledge_rate`) and combinations of the R3
contest winners (L23 to L28); the search was rerun with `pledge_rate` and leverages of 1×
and 2× among its choices, so its finalists are new (R2's `g10_0` is gone). Designs in
earlier runs keep their numbers. **R5** = the same day and data, with DReps taking back
added pledge that stops paying (all scenarios), and two more newcomer tests: wanting only
1% a year (`central_whale_idle`) and also splitting over up to 20 DReps
(`central_whale_split`), whose DReps count as one actor in the concentration measures
(L29 to L31). The search was rerun; designs' numbers moved by at most a few hundredths of
a point in `central` (L29). **R6** = the same day and data, with a cap on any DRep's
delegator yield as a multiple of the flat yield (`*_ycap*`, L32), the leading design
skipping 30 to 100 of the largest DReps (`skip_top{30,50,70,100}_*`, L33) and the share of
voting power the newcomer's DReps hold (`whale_power`, L34); the search was rerun with both
among its choices. Designs in R5 have the same numbers. Checks outside the pipeline say
"ad hoc" and give their seeds. "DReps" below is the number
of DReps holding two thirds of the voting power: more is more decentralised.

## DRep pay

**L1. Proportional pay buys participation, and concentrates power through the reach that
awards buy.** *Holds.*
- Evidence (R1, `central`): `proportional` +4.4 points of participation and −2.1 DReps;
  `sqrt` +4.6 and −1.2; `equal` +3.5 and +0.2. The concentration comes from
  `reinvest_only` (`proportional` −2.2), none from `voting_only` (−0.0).
- Why: awards buy reach (`reinvest_response`), and proportional pay gives the largest
  awards to the largest DReps. Assumed reaction.

**L2. The flatter the DRep rule, the more splitting into many DReps pays.** *Holds.*
- Evidence (R1, exact): share of the budget gained by splitting, `proportional` 0%,
  `sqrt` 15%, `equal` 87%; caps and skip-the-largest designs in between (`capped` 30%,
  `middle_out` 24%, `top_m_equal` 23%). R3: the pledge contest by counted power gains 1%,
  by its square root 12% (`pledge_contest_sqrt`).
- Why: an exact property of the rule on today's DReps (`static.py`); no reaction assumed.

**L3. Requiring pledge removes the Sybil gain of skip-the-largest designs, as long as pay
per DRep grows with the pledge behind it.** *Holds with exceptions; claim narrowed in R2.*
- Evidence (R1): `skip_top20_delegators` gains 34% by splitting;
  `skip_top20_delegators_min_pledge` (10,000 ADA per DRep) 0%, and also does better on
  participation (+5.2 against +3.9 points). Limiting delegator pay by pledge does the
  same without a minimum: `skip_top20_delegators_by_power` 0% (L9).
- Counter-examples (R2): with the same 10,000 ADA minimum, a delegator pot per DRep by the
  square root of counted power gains 26% (`skip_top20_min_pledge_delegators_sqrt`), an
  equal pot 52% (`skip_top20_min_pledge_delegators_equal`), and the search's `g10_0`
  (equal DRep pay, square root pots) 28.5%.
- Why: each fake DRep then needs its owner's own ADA; without pledge it earns its
  delegators nothing. But a fixed minimum is cheap next to an equal or square root pot:
  splitting still pays once the minimum is met.

## Delegator pay

**L4. Delegators move on differences in yield between DReps, not on the amount.** *Holds.*
- Evidence (R1, half the budget to delegators, `yield_only`): an equal pot per DRep
  (`*_delegators_equal`) adds +2.2 DReps under every DRep rule; a pot by counted power
  (`*_delegators_by_power`, the same yield per ADA everywhere, about 0.1% a year) adds
  +0.6 points of participation and no meaningful change in DReps (−0.5); the square root
  is in between (+0.05). In `high`, `equal_delegators_equal` reaches +5.1 DReps.
- Why: delegators react per point of annual yield (`delegator_response`), and 5M ADA a
  year over 5.4B delegated ADA is a tenth of a point unless it is concentrated. An equal
  pot per DRep gives the delegators of small DReps a few percent a year. Assumed reaction.

**L5. The DRep rule and the delegator rule work through different reactions, so they can
be chosen separately.** *Holds.*
- Evidence (R1): in `yield_only` the 12 designs of the DRep rule × delegator rule grid give
  the same numbers for every DRep rule; in `voting_only` and `reinvest_only`, the same for
  every delegator rule. So proportional DReps with an equal delegator pot per DRep
  (`proportional_delegators_equal`) keep proportional pay's participation (+4.4 points)
  and lose most of its concentration (−0.6 DReps against −2.1), where equal DReps with
  equal pots (`equal_delegators_equal`) spread power more (+2.4) but buy a point less
  participation (+3.3).
- Why: in the model DReps react to their own award (voting, reach) and delegators to
  their yield; neither reacts to the other's pay. The effects do not simply add up in
  `central`, because a DRep that gains delegation also votes with more ADA.

**L6. Moving money from DReps to delegators trades DReps voting more for delegators
moving.** *Holds with exceptions; rests on a model assumption.*
- Evidence (R1, proportional DReps, delegator pot by counted power, 0 / 20 / 50 / 80% to
  delegators): `voting_only` participation +4.3 / +4.2 / +3.8 / +3.1 points;
  `yield_only` 0 / +0.3 / +0.6 / +0.9; `central` +4.4 / +4.6 / +4.6 / +4.3. With an equal
  pot per DRep, decentralisation rises with the share: −1.6 / −0.6 / +0.7 DReps at
  20 / 50 / 80%.
- Counter-example (R2): where DRep pay buys little voting, more to delegators is better.
  `skip_top20_delegators_min_pledge_by_power` (80%) against `_half` (50%): participation
  +4.2 against +3.2 points, DReps +7.2 against +6.0, net benefit +1.3M ± 0.2M ADA a year.
  Its DRep pay adds only +0.3 points in `voting_only`: the 20 largest are skipped and
  the rest must vote on 70% of actions.
- Evidence (R3, pledge contest with 0 / 20 / 50 / 80% to delegators): net benefit +1.6 /
  +2.2 / +0.4 / −3.3M ADA a year; a fifth to delegators beats none by +0.6M ± 0.15M.
- Why: a DRep weighs only its own award when deciding to vote, not that its delegators
  are paid only when it votes (`METHODS.md`, "How DReps behave"). If real DReps do care,
  paying delegators costs less participation than this. The trade only matters where the
  DRep part buys voting.

**L7. A design's Sybil gain mixes its DRep and delegator parts, weighted by their
shares.** *Holds.*
- Evidence (R1, exact): an equal delegator pot per DRep carries equal pay's 87% into
  proportional pay: 17%, 44% and 70% with a fifth, half and four fifths to delegators.
  A delegator pot by counted power, or a flat yield, adds none (`equal_delegators_by_power`
  44%, half of `equal`'s 87%). Pass-through keeps the DRep rule's gain on both parts.
  R2: the same with a minimum pledge, 0% / 26% / 52% for pots by power, square root
  and equal (L3).
- Why: splitting multiplies whatever is paid per DRep rather than per ADA.

**L33. The more of the largest DReps are skipped, the more delegator pay buys; beyond
about 50, the pay goes to the delegators of a handful of DReps.** *Holds in the model;
rests on delegators chasing yields far above any seen, and on DReps voting more to pass
the gate.*
- Evidence (R6, the leader's settings — 10,000 ADA minimum pledge, a 70% vote gate, 80% to
  delegators, L = 1 — skipping 20 / 30 / 50 / 70 / 100, with a flat yield): net benefit
  +7.1 / +13.5 / +24.8 / +32.9 / +34.0M ADA a year, in `low` −1.5 / +2.9 / +14.0 / +8.9 /
  +4.3M. With pots by counted power +7.5 / +12.6 / +20.3 / +28.4 / +37.1M, and
  `skip_top100_min_pledge_by_power_1x` is first of all designs. Paired: skipping 30 with a
  flat yield against the leader +5.92M ± 0.19M, 50 against 30 +11.32M ± 0.31M. Given 30 to
  100 among its choices, the search puts two designs skipping 70 at #4 and #6 (`g9_4`,
  `g6_0`).
- Evidence (R6, flat yield): the delegator yield at the start, a year, weighted by ADA, is
  4.3% / 8.6% / 20% / 25% / 57%. Late in a run (ad hoc, 3 seeds) it falls to 0.5% / 0.6% /
  0.9% / 1.3% / 24% in `central` as delegators arrive; in `low` it is 1.6% / 2.5% / 5.1%,
  then hundreds to thousands of percent. Skipping 70 or 100, the pay goes to 5 and 3 DReps a
  round in `low` (29 skipping 20; in `central` 28 and 10), and DReps holding two thirds fall
  below unpaid (−3.6 and −4.1). With pots by counted power they stay above it (+12.7 and
  +11.2, 13 and 4 DReps a round). In `yield_only`, a flat yield skipping 50 or 100
  concentrates power (−6.2 and −6.9 DReps): the spread in `central` needs the other
  reactions too.
- Why: skipping more leaves fewer, smaller DReps whose delegators are paid, so the same
  pot is a higher yield. Movers weigh a paid DRep by exp(`delegator_response` × points of
  yield) up to 50 points (`max_yield_pp`), so a few percent draws most of them. How many are
  left to pay depends on how many DReps outside the K largest vote on 70% of actions with
  10,000 ADA pledged: when DReps hardly react (`low`), few do. Arriving delegators lift a
  DRep into the K largest, where its delegators stop being paid; the model's delegators do
  not learn this. Whether real delegators would chase such yields is untested.
- Not pursued (ad hoc, 20 seeds): a fixed ceiling on any delegator's yield, the rest left
  unspent. At 10% a year it lifts the flat designs skipping 70 and 100 in `low` (+7.8 →
  +22.9M and +4.3 → +19.6M) but lowers the one by counted power skipping 100 (+38.2 →
  +32.2M over the three scenarios), and in `low` the 10 best-paid DReps still take 98% to
  100% of the pay. It bounds the yield, not how few are paid.

## Pledge

**L8. Under a `flat` delegator yield, pledge decides whether delegators are paid, not how
much.** *Holds (structural).*
- Evidence (R1, exact): `skip_top20_delegators_min_pledge` pays delegators through 22
  DReps holding 0.19B ADA, while their pledge, counted twice, supports about 0.01B.
- Why: `flat` pays per delegated ADA through every paid DRep. `per_drep` limits delegator
  pay by the pledge soft cap instead (L9).

**L9. Limiting delegator pay by pledge spreads power and removes Sybil gain, and costs
participation where pay was concentrated on a few pledged DReps.** *Holds; confirmed in
other designs in R2.*
- Evidence (R1, `central`, by counted power against flat, paired net benefit):
  `skip_top20_delegators`: +1.6 DReps, Sybil 0% against 34%, participation −0.2 points
  (not meaningful), net benefit +5.3M ± 0.2M ADA a year. With a 10,000 ADA minimum
  pledge: +1.1 DReps, participation −0.95 points, net benefit +0.3M ± 0.2M; it became the
  top design. A plain 2× pledge soft cap with half to delegators: +1.5 DReps,
  +1.7M ± 0.2M. Backing rises in each, by less than the meaningful 0.2 points.
- Evidence (R2, the same comparison in two more designs): `haircut_top20_delegators`
  +2.8 DReps, +4.5M ± 0.2M; `delegators_not_top20` with a 2× pledge soft cap +1.0 DReps,
  Sybil 2% against 20%, +2.9M ± 0.2M. When the search may choose (R2), 10 of its 14 new
  finalists use pots by counted power or its square root. R3: in the pledge contest
  with half to delegators, a flat yield instead of pots −2.1M ± 0.15M.
- Why: an ADA delegated to a DRep with more pledge per ADA then earns more, so delegators
  move to pledge-backed DReps, which are mostly not the largest. Under a flat yield all
  pledged DReps pay the same, and the minimum-pledge design drew more delegation to its
  22 DReps (`yield_only` +7.9 points of participation against +5.3).

**L10. Tying pay to pledge raises pledge backing only by tenths of a point, unless DReps
can afford more.** *Holds in `central`; contradicted in `high` (R3).*
- Evidence (R1, `central`): `pledge_soft_cap_2x_delegators_by_power` +0.8 points,
  `pledge_soft_cap_skip20` +0.6, the skip-the-largest delegator designs +0.2 to +0.4;
  designs without a pledge soft cap about 0. R3: the pledge contests reach +1.2 in
  `central` but about +6 in `high` (L17).
- Why: little pledge stands behind votes today; DReps add only part of what is missing,
  and only while it pays (`pledge_response`, `pledge_min_return`). Assumed reaction.

**L14. The tighter the pledge limit on pay, the better, down to 1×.** *Holds; widened from
delegator pay to all pay in R3.*
- Evidence (R2, `skip_top20_delegators_min_pledge_by_power` at 1× / 2× / 5× / 10× pledge
  leverage, `central`): backing +0.45 / +0.35 / +0.21 / +0.10 points; DReps and
  participation about the same. Net benefit against 2×: +0.35M ± 0.18M, 0, −0.39M ± 0.17M,
  −1.41M ± 0.20M ADA a year. 1× also has the smallest shortfall in any scenario.
- Evidence (R3, `pledge_contest`, the top 100 at 1× / 2× / 5× / 10× / 100× / no pledge
  limit): backing +0.75 / +0.63 / +0.54 / +0.49 / +0.17 / 0 points; net benefit +1.6 /
  +1.3 / +0.8 / −2.5 / −8.0 / −8.6M ADA a year (2× against 1×: −0.34M ± 0.08M). The same
  order with 50, 200 or all DReps competing, and with delegators.
- Why: the looser the limit, the less an extra pledged ADA adds to the DRep's share (and
  its delegators' pot), so the less pledge pays (`pledge_response`). Below 1× the split is
  the same as at 1×: pledge is part of voting power, so at L = 1 every DRep is already
  paid by its pledge alone.

## The pledge contest

The paid DReps share the whole pot by voting power counted up to their pledge (L = 1: by
pledge), so they compete for it with their own ADA. `pledge_contest` pays the 100 largest;
`pledge_contest_delegators` gives half to their delegators in pots by the same counted
power.

**L17. Paying by pledge buys skin in the game more cheaply than any other rule tried, and
the cheapest contest buys the most per ADA.** *Holds; the size rests on wealth assumptions.*
- Evidence (R3, `central`): `pledge_contest` doubles backing, 0.71% to 1.46% of voting
  power (+0.75 points, about 40M ADA more pledge behind votes), for 10.1M ADA a year; the
  R2 leader `skip_top20_min_pledge_by_power_1x` adds +0.45. Of the 25 budget-funded designs
  that buy the most backing per ADA, 22 are contests (the other 3 pay delegators by pledge). Backing
  stops growing with money: 1M / 2.5M / 5M / 10M budgets add +0.50 / +0.73 / +0.75 /
  +0.75 points, so 2.5 / 1.4 / 0.7 / 0.4 points per 10M ADA a year; paid by a 10,000 ADA
  proposer fee (0.9M a year, hard fork), 4.2. In `high` the contests add about 6 points,
  more than any other design. All of it comes from `pledge_only` (+0.73). R4: a pot that
  grows with pledge buys more per ADA still (`pledge_contest_rate5`, 2.8 per 10M; L24), and
  the size does rest on wealth: `central_poor` +0.18, `central_rich` +3.53 (L28).
- Why: the pot is shared, so a pledged ADA earns the pot over all pledge, a very high
  return today (12M ADA of traced pledge). DReps add pledge until what they can afford
  stops them (`pledge_wealth_multiple`, `untraced_wealth_share`), and more money cannot
  buy past that. The order of designs should survive other wealth assumptions; the
  points will not.

**L18. In a pledge contest, limiting who may compete saves nothing and shuts out small
pledged DReps.** *Holds.*
- Evidence (R3, L = 1, the 25 / 50 / 100 / 200 / 400 largest / all): net benefit −2.9 /
  +0.4 / +1.6 / +2.1 / +2.1 / +2.2M ADA a year; backing +0.41 / +0.61 / +0.75 / +0.82 /
  +0.83 / +0.83 points; DReps −3.1 / −2.0 / −1.6 / −1.4 / −1.4 / −1.4. The cost is the
  whole pot in every case, and the Sybil gain at most 1% (0% with everyone). The same
  order at 2× and 10×. Other limits: 0.5% of all power to compete −0.7M; a 70% vote-rate
  gate −1.1M ± 0.2M; roll-down within the top 100, which reaches further down, +0.4M ± 0.1M.
- Why: pay by pledge is already Sybil-proof (pledge split across DReps adds to no more),
  so a limit buys no protection. The 100th DRep holds about 1M ADA, which leaves out
  small self-funded DReps whose pledge is a large part of their power.

**L19. Pledge works as a share of the pot, not as an entry ticket.** *Holds; partly by
model assumption.*
- Evidence (R3): `pledge_contest` against the same top 100 paid by voting power
  (`top_m_proportional`) +10.2M ± 0.15M ADA a year: backing +0.75 against 0, DReps −1.6
  against −2.1. Against the top 100 with a 10,000 ADA minimum pledge (`top100_min_pledge`)
  +12.0M ± 0.2M; the minimum adds no backing and only +1.7 points of participation, as
  most of the top 100 are left out.
- Why: under a share every extra pledged ADA earns more; under a ticket nothing past the
  minimum does. The model also takes a DRep below a minimum to stay below it (`METHODS.md`,
  "Topping up pledge"), so a ticket buys no new pledge by assumption.

**L20. Paying by pledge buys little voting from the largest DReps.** *Holds; rests on traced
pledge.*
- Evidence (R3, `voting_only`): `pledge_contest` +1.2 points of participation,
  `top_m_proportional` +4.3. In `central` +4.0 against +4.4: the rest comes from DReps
  that add pledge and then earn.
- Why: the largest DReps have almost no traced pledge (among the top 20, a median under a
  millionth of their voting power), so they earn nothing for voting, and they hold most
  of the ADA. If they declared their own ADA in a pilot this would change (`METHODS.md`,
  "What the chain cannot show").

**L21. Skipping the largest DReps pays only together with delegator pay.** *Holds.*
- Evidence (R3): skipping the 20 largest in the contest without delegators −1.4M ± 0.2M
  ADA a year (DReps +2.4 against −1.6, participation +1.5 against +4.0 points); with half
  to delegators +5.5M ± 0.2M (DReps +5.5, the best contest design,
  `pledge_contest_delegators_skip20`). Leaving out only the delegators of the 20 largest,
  who are still paid themselves, +2.2M ± 0.15M. Every R1/R2 leader skips the top 20 and
  pays delegators; `pledge_soft_cap_skip20`, without delegators, +0.7M.
- Why: a skipped DRep loses its pay and votes less, but only delegators react to yield.
  With delegator pay, the delegators of the largest move to paid DReps (`yield_only`).
- R6: the more are skipped, the more it buys, up to 100 (L33).

**L22. Capping counted power per DRep, against one large pledge taking the pot, costs a lot
in the model.** *Holds; R4 models the threat (L23): the cap stops it, but the score does not
count the harm.*
- Evidence (R3): counting at most 1M ADA per DRep −7.4M ± 0.2M ADA a year against the
  uncapped contest (backing +0.21 against +0.75); at most 5M about −4.4M (+0.50).
  Requiring 10 delegators instead costs nothing (+0.04M ± 0.06M).
- Why: a cap removes pay for pledge beyond it, the very thing that buys backing. The
  model has no newcomer who self-delegates a fortune to win the pot, which is what a cap
  or a delegator minimum would guard against; whether either is worth it cannot be
  judged until that is modelled.
- R4 (`central_whale`): counting at most 1M ADA per DRep holds a newcomer with 100M ADA to
  7% of the pay (51% uncapped), and 7% again with a 1% hurdle; 5M to 15%. Requiring 10
  delegators stops nothing (51%): the newcomer holds its ADA in as many accounts as it
  needs. By the ranking values its ADA is backing like any other, so the newcomer raises
  the uncapped contest's `central` score (−4.9M to −0.9M) and the cap still costs.
- R5 (`central_whale_split`): a newcomer that splits over up to 20 DReps gets past both
  caps: 59% of the pay at 1M (19 DReps), 73% at 5M (L30).

## A wealthy newcomer, and a pot that grows with pledge

`central_whale` adds a newcomer with 100M ADA that each epoch self-delegates whatever part
of it earns most over 5% a year and the cost of voting (`METHODS.md`, "What is assumed").
`pledge_rate` caps each round's pot at a yearly rate on the pledge behind paid votes, up to
the budget. An ad hoc check (30 seeds) put every hurdle, DReps' and the newcomer's, at 1%.

**L23. A wealthy newcomer takes about half of a pot paid by pledge, more when the pot is
large against the pledge already there.** *Holds; the harm is not on the axes.*
- Evidence (R4, `central_whale`): `pledge_contest` 51% of the pay for 50M ADA
  self-delegated (0.9% of voting power). The 25 / 50 / 100 / 200 largest / all competing:
  67 / 57 / 51 / 48 / 46%. Budgets of 1M / 2.5M / 5M / 10M: 8 / 36 / 51 / 65% (all 100M
  at 10M). Leverage 1× / 2× / 5× / 10×: 51 / 40 / 12 / 4%. Without any pledge rule at most
  5% (mean 0.2% over 41 designs). DReps' own pledge hardly changes (+0.71 points against
  +0.75 without it). With a 1% hurdle: `pledge_contest` 66% for all 100M, the 1M contest
  52%.
- Why: a contest pays a pledge W out of others' S a share W/(S+W) of the pot P; the best
  W for a newcomer with hurdle h is √(PS/h) − S, for a share of 1 − √(hS/P). It stays out
  only once others' pledge reaches P/h: about 200M ADA for 10M a year at 5%, against about
  40M in `central`. Self-delegating ADA one already holds locks nothing, so a holder's
  hurdle may be far below 5%.
- Not on the axes: the newcomer's ADA counts as backing and its DRep is one more
  mid-sized one, so by the ranking values it *raises* a contest's score (`pledge_contest`
  −4.9M to −0.9M in `central`). Whether one actor taking half the pay for about 1% of the
  voting power is acceptable is a judgement the score does not make.
- R5 (`central_whale_idle`, hurdle 1%): `pledge_contest` 68% for all 100M, the 1M contest
  61% for 50M, `pledge_contest_5x` 45% for 98M. Over the 136 paid pilot-testable designs
  (fee variants left out) it takes 10% or more under 49 at a 5% hurdle and 70 at 1%.

**L24. A pot that grows with pledge spends only what DReps respond to, which removes the
contest's loss when reactions are weak.** *Holds with an exception; the size rests on the
hurdle.*
- Evidence (R4): `pledge_contest_rate5` against `pledge_contest` +4.46M ± 0.15M ADA a year,
  `rate10` +4.59M ± 0.12M, `pledge_contest_all_rate5` against `pledge_contest_all` +3.95M ±
  0.16M, `pledge_contest_delegators_rate10` against `pledge_contest_delegators` +2.75M ±
  0.20M; `rate5` against the 1M contest +3.33M ± 0.12M. By scenario, `rate5` against the
  plain contest: `low` −0.2M (it spends 0.4M a year and buys nothing) against −8.8M;
  `central` +0.38 points of backing for 1.4M (2.8 points per 10M ADA a year, the most of
  any budget-funded design); `high` the full 10.1M and +5.92 points, as the contest. Of the
  search's 12 new finalists, 5 use a rate (10% or 20%).
- Exception: on the leader (`skip_top20_min_pledge_by_power_1x`), whose pay goes mostly to
  delegators and DReps with little pledge, a 10% rate −4.18M ± 0.22M.
- Why: below the budget, the pot is the rate times the pledge behind paid votes, so it
  stays small until DReps add pledge. A DRep adds pledge when the return is at least
  `pledge_min_return`, and in the model that test is a threshold: `rate2` buys nothing in
  `central` (hurdle 5%), `rate5` pays exactly the hurdle and buys +0.38. The rate that works
  is the one just above what DReps want, which a pilot would have to find.

**L25. A pot that grows with pledge keeps a wealthy newcomer out only while its rate is
below the newcomer's hurdle.** *Holds.*
- Evidence (R4, `central_whale`, hurdle 5%): `pledge_contest_rate2` and `rate5` 0% of the
  pay; `rate10` 64% (67M self-delegated), `rate20` 55%, `rate50` 52%, against 51% for the
  plain contest. With a 1% hurdle: `rate2` 72% and `rate5` 70%, each with all 100M.
- Why: below the budget every pledged ADA earns the rate, the newcomer's included, and its
  pledge grows the pot. It is a yield, not a prize that shrinks as the newcomer adds more:
  above its hurdle the newcomer adds all it can until the pot reaches the budget, and then
  it is a contest (L23). A rate low enough to keep it out also keeps out DReps with the
  same hurdle, and a holder of idle ADA likely has the lower one.
- R5 (`central_whale_idle`): `rate2` 91% and `rate5` 78% of the pay, each for all 100M.

**L26. Skipping the largest DReps holds a single wealthy newcomer to a few percent, when
delegators follow pay.** *Holds for one identity; a newcomer that splits gets past it (L30).*
- Evidence (R4, `central_whale`): with delegator pay, `skip_top20_min_pledge_by_power_1x`
  2.2%, `pledge_contest_delegators_skip20` 3.3%, the search's `g10_5` 6% (50 seeds); with a
  1% hurdle 2.6%, 4.0% and 7.0%. Without delegator pay, `pledge_contest_skip20` 41% and
  `pledge_soft_cap_skip20` 37%; skipping 10, `pledge_contest_skip10` 53%.
- Why: its pay draws delegation, 76M to 120M ADA in a traced run under the skip-20 designs
  (28M under the plain contest), and more of its own ADA would put it among the 20 largest,
  who are not paid. A DRep cannot refuse delegation. Several DReps, each below the line,
  would escape it: splitting is measured on the Sybil axis, not here.

**L27. The best contest settings do not add up.** *Holds.*
- Evidence (R4): everyone competing with a fifth to delegators against
  `pledge_contest_delegators` +2.13M ± 0.19M, as R3's parts suggest. But with the 20
  largest skipped, a fifth to delegators −2.55M ± 0.18M (`pledge_contest_delegators_skip20_20`
  against `pledge_contest_delegators_skip20`), −2.19M ± 0.16M with everyone competing too;
  everyone competing +0.31M ± 0.17M; 2.5M instead of 5M −0.30M ± 0.18M. The best combination
  (`pledge_contest_delegators_all_skip20`, +6.1M) is still −1.56M ± 0.25M behind the
  leader. The search's `g10_5` (the top 100 after skipping 20, half to delegators, a 20%
  rate) ties the leader (−0.31M ± 0.24M) and beats `pledge_contest_delegators_skip20` by
  +1.56M ± 0.19M.
- Why: skipping the largest pays only through delegators moving (L21), so a smaller
  delegator share undoes it; a fifth is best only when nobody is skipped.

**L29. Letting DReps take back pledge that stops paying changes results only where pledge
outgrows what the pot pays.** *Holds.*
- Evidence (R5 against R4, the 128 designs with a pledge rule): backing in `central`
  −0.009 points on average (at most −0.07, `pledge_contest_fee_10k`); in `low` nothing; in
  `high` −0.15 on average and up to −0.81 (`pledge_contest_1m`, −3.5M ADA a year of net
  benefit); `central_rich` −0.08, up to −0.59 (`pledge_contest_rate10`). With the newcomer
  in the contest, DReps' own backing is +0.71 points in both runs (+0.75 without it).
- Why: a DRep takes pledge back only once its part earns less than its hurdle. In `central`
  the contest still pays well above 5% on DReps' pledge even with a newcomer taking half;
  only when strong reactions or rich DReps pile in does the return fall below it, most in
  the 1M contest and the pots that grow with pledge.

**L30. A newcomer that can run many DReps gets past every per-DRep limit tried; only rules
that pay nothing for pledge or for being one more DRep keep it out.** *Holds; rests on
cheap identities (a DRep deposit is refundable).*
- Evidence (R5, wanting 1% a year, one DRep → up to 20): the leader
  `skip_top20_min_pledge_by_power_1x` 3% → 26% of the pay (95M ADA over 13 DReps);
  `pledge_contest_delegators_skip20` 4% → 46%; `pledge_contest_skip20` 40% → 77%;
  `pledge_contest_cap1m` 7% → 59%; `pledge_contest_cap5m` 14% → 73%; `pledge_contest_sqrt`
  15% → 48%; `middle_out` 1% → 21% (all 20 DReps); `top_m_equal` 1% → 17%. 0% under
  `proportional`, `capped`, `threshold_k`, `exclude_k_pay_n`, `delegator_flat`,
  `delegators_not_top20`. Mean share over 136 paid pilot-testable designs: 14% (5%, one
  DRep), 25% (1%, one DRep), 35% (1%, split). Among designs worth their cost, the least
  exposed are `exclude_k_pay_n` and `capped_1m` (0%, +0.3M and +0.2M) and the
  `skip_top20_*` family (17% to 36%).
- Why: skipping the largest, caps and square roots all act per DRep, and one actor can be
  any number of DReps, each below the line. Pay by voting power earns a newcomer only its
  share of all power (100M is about 2% of the pot), less than it wants.
- Not tried in the pipeline: counting pledge only as far as others' delegation matches it.
  A prototype kept this newcomer out entirely at a cost of up to 0.12 points of backing,
  but only because the model's newcomer does not campaign; delegating half its ADA from
  accounts it does not declare would undo it (by the formula in L23, about 56% of the
  plain contest's pay instead of 68%).

**L31. Under delegator pay by counted power, a splitting newcomer gathers a voting bloc; a
flat delegator yield does not.** *Holds; rests on delegators chasing yield without seeing
that the DReps are one actor.*
- Evidence (R5, `central_whale_split`): under the leader, others delegate about 1.1B ADA
  to the newcomer's DReps, a bloc of 19% of voting power (traced runs, 4 seeds), and DReps
  holding two thirds fall from +7.1 to +1.4 against unpaid. `pledge_contest_delegators_skip20`
  15%, +5.4 to +0.5; the search's `g10_10` (pots by √power) +8.5 to +1.2 (30 seeds). With a
  flat yield (`skip_top20_delegators_min_pledge`): 6%, +6.1 to +5.2; the plain contest 3%.
  Paired over 100 seeds, the flat design trails the leader by −1.39M ± 0.44M ADA a year in
  `central` and leads it by +1.11M ± 0.50M with the splitting newcomer.
- Why: a pot per DRep by counted power pays each DRep's delegators in proportion to its
  pledge, and the newcomer's DReps carry much pledge and few delegators, so they offer the
  highest yields and movers go to them. A flat yield is the same at every paid DRep, so
  nothing draws movers to the newcomer. Under the contest it pays no delegators.
- R6: the leader with a flat yield (`skip_top20_min_pledge_flat_1x`) trails it by −0.49M ±
  0.21M and holds the splitting newcomer to 4.6% of voting power against 14.7%; DReps
  holding two thirds go +6.2 → +5.3 against +7.1 → +1.4. A cap on yields does not get
  there (L32).

**L32. Capping any DRep's delegator yield at a multiple of the flat yield does worse than a
flat yield, with or without a splitting newcomer.** *Holds.*
- Evidence (R6, the leader `skip_top20_min_pledge_by_power_1x` capped at 5× / 3× / 2× /
  1.5× the flat yield): net benefit +6.9 / +6.5 / +5.7 / +5.3M ADA a year, against +7.5M
  uncapped and +7.1M flat; 2× against flat −1.39M ± 0.22M. DReps holding two thirds in
  `central` +6.6 / +6.3 / +5.3 / +5.2, against +7.1 uncapped and +6.2 flat: a cap in
  between is worse than either end. The splitting newcomer's DReps hold 13.4% / 11.1% /
  8.5% / 7.2% of voting power, against 14.7% uncapped and 4.6% flat. On
  `pledge_contest_delegators_skip20`, 2× −3.81M ± 0.18M, with Sybil gain up from 4% to 13%.
  The search, offered 1.5× to 3×, kept no cap among its finalists.
- Why: at the start, a 2× cap binds on 11 of the 22 paid DReps, those with the most pledge
  for their delegation (median 19% of their power, up to 43× the flat yield): the ones pots
  by counted power reward (L9). What it frees goes mostly to the six largest paid DReps,
  with 84% of the paid power and almost no pledge. So it gives up the uncapped design's
  backing (+0.43 → +0.29 points at 2×) and DReps without reaching the flat yield's
  participation (+4.2 against +5.2 points). The newcomer's DReps still offer yields up to
  the line. In the contest, evening out delegator pay per DRep makes splitting pay (L7).

**L34. Net benefit and a splitting newcomer's bloc rise together with how many of the
largest DReps are skipped; at each number, a flat yield gives the smaller bloc.** *Holds;
tracked beside the ranking, not in it.*
- Evidence (R6, the 153 named pilot-testable designs, fee variants left out: holdout net
  benefit against the newcomer's share of voting power in `central_whale_split`): those no
  other design beats on both are, from the top, skipping 100 with pots by counted power
  (+37.1M, 18.1%); with a flat yield skipping 70 (+32.9M, 14.1%), 50 (+24.8M, 9.8%), 30
  (+13.5M, 5.8%) and 20 (+7.1M, 4.6%); `skip_top20_delegators_min_pledge` (+6.9M, 4.4%);
  `pledge_contest_rate10` and `rate20` (+6.1M and +4.5M, 3.2%); `pledge_contest_1m` (+1.5M,
  1.7%); `exclude_k_pay_n` (+0.3M, 0%). With pots by counted power the bloc is 15% to 18%
  whatever is skipped. In 216 variations around the leader (ad hoc, 20 seeds), the 15 best
  under the splitting newcomer all have a flat yield; skipping 30 beats 20 on average by
  +3.5M in `central` and +1.6M with the newcomer.
- Why: the more are skipped, the higher the yield the newcomer's DReps can offer (L33); with
  pots by counted power its pledge buys them the top yields (L31).
- Not in the ranking: the newcomer's ADA counts as backing there, so scoring this scenario
  would reward being exposed to it.

## Cost and ranking

**L11. With weak reactions to rewards, no design that costs millions a year is worth its
cost at the starting values.** *Holds with exceptions; skipping 30 or more of the largest
DReps breaks it (R6, L33).*
- Evidence (R1, R2): the leader (`skip_top20_delegators_min_pledge_by_power`) is −1.4M ADA
  a year in `low`, +4.4M in `central`, +19M in `high`; every design costing 1M ADA a year
  or more is negative in `low`.
- Counter-examples: very cheap designs are positive even in `low`: `exclude_k_pay_n`
  (10 ADA a vote, about 0.14M a year) and its proposer-fee versions, and
  `middle_out_fee_10k` (fee-funded, needs a hard fork).
- Counter-examples (R6): skipping 30, 50 or 100 of the largest with a flat yield, +2.9M,
  +14.0M and +4.3M ADA a year in `low`; skipping 100 with pots by counted power +13.6M.
  Concentrating the delegator pot on fewer DReps makes the yield large enough for weak
  reactions too, though from 70 on the pay goes to a few DReps (L33).
- Why: gains scale with the assumed reactions, cost does not.

**L12. Which design leads depends on what an improvement is worth: cheaper designs lead at
low values, 10M designs at high ones.** *Holds.*
- Evidence (R1): halving every value makes paying nothing first under weak and medium
  reactions; doubling them puts 10M designs first.
- Why: net benefit is a straight line in the value of improvements; bigger budgets have
  steeper lines.

**L13. A 5M design is worth its cost only if pay is tied to pledge: a pledge soft cap or a
minimum pledge.** *Holds with exceptions; claim widened in R2.*
- Evidence (R1): 21 designs that need only CIP-159 rank above paying nothing; 19 have a
  pledge soft cap. The plain DRep × delegator grid scores −8M to −12M ADA a year.
  R2: 33 above paying nothing; 30 have a pledge soft cap, and `g2_4` (square root DReps and
  pots, no soft cap) has a 10,000 ADA minimum pledge. R3: the top 50, 100 or 200, or all
  DReps, paid by voting power score −8.5M to −9.1M; paid by pledge (L = 1), +0.4M to
  +2.2M.
- Counter-examples: `exclude_k_pay_n` (10 ADA a vote, about 0.14M a year) and
  `capped_1m` (1M budget): cheap designs can clear the bar without either.
- Why: at the starting values, Sybil gain counts as lost ADA and concentration as a loss;
  tying pay to pledge removes most of both.

**L15. The middle budget is best.** *Holds (two families).*
- Evidence (R2, `skip_top20_delegators_min_pledge_by_power` at 2.5M / 5M / 10M over the
  programme): participation +2.4 / +4.2 / +7.4 points and DReps +4.2 / +7.2 / +11.3, so
  gains grow, but less than in proportion to money; net benefit against 5M −1.9M ± 0.2M
  and −1.4M ± 0.2M ADA a year. The 10M version found by the search with 1× leverage (`g3_17`)
  is also below the 5M one (−0.7M ± 0.2M).
- Evidence (R3, `pledge_contest` at 1M / 2.5M / 5M / 10M): net benefit +2.7 / +3.6 / +1.6 /
  −7.8M ADA a year; 2.5M beats 1M by +0.9M ± 0.1M and 5M by +2.0M ± 0.1M.
- Why: net benefit peaks where an extra ADA buys gains worth one ADA; from 2.5M to 5M it
  buys more than that, from 5M to 10M less. With weak reactions the cheapest is least bad
  (−0.6M), with strong ones the largest is best (L12).

**L28. The leading design does not depend on what DReps can afford to pledge; the contest
does.** *Holds.*
- Evidence (R4, net benefit from the `central` reactions, with `central_poor` / `central`
  / `central_rich` wealth): `skip_top20_min_pledge_by_power_1x` +6.6 / +5.3 / +5.9M ADA a
  year; `pledge_contest` −8.1 / −4.9 / +6.7M (backing +0.18 / +0.75 / +3.53 points). The
  five best when DReps are poor all skip the top 20 and pay delegators; when they are rich,
  pots that grow with pledge and contests lead (`pledge_contest_rate10` +10.3M). Rank
  correlation of all designs with `central`: 0.96 poor, 0.71 rich.
- Why: the contest buys pledge, which wealth caps (L17); the leader buys DReps and
  participation through delegators moving (L5), which wealth does not touch.

**L16. Buying a lot of decentralisation can outweigh a Sybil gain at the starting values,
but only if reactions are not weak.** *Holds (one design).*
- Evidence (R2): `g10_0` (equal DRep pay, cap 2M, skip top 20, 10,000 ADA minimum pledge,
  80% to delegators in square root pots) gains 28.5% by splitting but adds +11.6 DReps in
  `central` (+21.7 in `high`). Its net benefit ties the 1× leader (+0.07M ± 0.25M) and is
  the highest score, but it is −4.0M a year in `low` against −1.4M.
- Why: the Sybil loss is a fixed share of cost; the decentralisation gain scales with the
  reactions. Choosing between them is a question of how sure one is of the reactions.
