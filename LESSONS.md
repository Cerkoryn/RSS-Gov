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
rerun, and earlier designs' numbers are unchanged. "DReps" below is the number
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
  more than any other design. All of it comes from `pledge_only` (+0.73).
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

**L22. Capping counted power per DRep, against one large pledge taking the pot, costs a lot
in the model.** *Holds; the model lacks the threat.*
- Evidence (R3): counting at most 1M ADA per DRep −7.4M ± 0.2M ADA a year against the
  uncapped contest (backing +0.21 against +0.75); at most 5M about −4.4M (+0.50).
  Requiring 10 delegators instead costs nothing (+0.04M ± 0.06M).
- Why: a cap removes pay for pledge beyond it, the very thing that buys backing. The
  model has no newcomer who self-delegates a fortune to win the pot, which is what a cap
  or a delegator minimum would guard against; whether either is worth it cannot be
  judged until that is modelled.

## Cost and ranking

**L11. With weak reactions to rewards, no design that costs millions a year is worth its
cost at the starting values.** *Holds with exceptions.*
- Evidence (R1, R2): the leader (`skip_top20_delegators_min_pledge_by_power`) is −1.4M ADA
  a year in `low`, +4.4M in `central`, +19M in `high`; every design costing 1M ADA a year
  or more is negative in `low`.
- Counter-examples: very cheap designs are positive even in `low`: `exclude_k_pay_n`
  (10 ADA a vote, about 0.14M a year) and its proposer-fee versions, and
  `middle_out_fee_10k` (fee-funded, needs a hard fork).
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

**L16. Buying a lot of decentralisation can outweigh a Sybil gain at the starting values,
but only if reactions are not weak.** *Holds (one design).*
- Evidence (R2): `g10_0` (equal DRep pay, cap 2M, skip top 20, 10,000 ADA minimum pledge,
  80% to delegators in square root pots) gains 28.5% by splitting but adds +11.6 DReps in
  `central` (+21.7 in `high`). Its net benefit ties the 1× leader (+0.07M ± 0.25M) and is
  the highest score, but it is −4.0M a year in `low` against −1.4M.
- Why: the Sybil loss is a fixed share of cost; the decentralisation gain scales with the
  reactions. Choosing between them is a question of how sure one is of the reactions.
