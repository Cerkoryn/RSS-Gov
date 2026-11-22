# RSS-Gov results

Chain data to epoch 666. Default programme: 5,000,000 ADA over 36 epochs. Regenerate with `rss-gov all`; method in `METHODS.md`. Interactive charts: `site/index.html` in this folder.

## The chain today

- 848 DReps hold voting power; 20 of them hold two thirds of it (effective number 30.0).
- 5.42B ADA is delegated to DReps, 10.49B to always-abstain and 0.13B to always-no-confidence.
- 158 governance actions have closed; 30,299 DRep ballots.
- Accounts that funded a DRep's registration or that it declares as its payment address hold 46.3M ADA in total, for 748 of 848 DReps. That backs **0.85%** of DRep voting power: the average vote is cast with about 117 times the voter's pledge.

## How schemes are compared

Every scheme starts from the same chain snapshot, runs on the same random seeds, and pays only for explicit votes (Yes, No and Abstain count alike). Named schemes get the same budget. Each is then measured on one axis per objective family; nothing is folded into a single score.

| family | measure | better | meaningful change | what the number rests on | how a real programme would show it |
|---|---|---|---|---|---|
| Participation | Delegated ADA casting an explicit vote | higher | 1 points | simulated; rests on the voting and yield responses | on chain: votes and delegation each epoch |
| Decentralisation | DReps needed for 2/3 of voting power | higher | 1 | simulated; rests on the yield and reinvestment responses | on chain: DRep voting power each epoch |
| Skin in the game | Voting power backed by the DRep's pledge | higher | 0.2 points | starts from accounts linked on chain; changes rest on the pledge response | needs DReps to declare their accounts and sign for them |
| Reward sustainability | Cost per year (ADA), from a budget or from fees | lower | 0.5 M ADA a year | accounting; exact for a budget, follows the number of actions for a fee | the programme's own books |
| Sybil resistance | Share of the budget gained by splitting one identity | lower | 2 % of budget | exact property of the formula on today's DReps | indirectly: new look-alike DReps and delegation splits |

A change smaller than `meaningful change` counts as no difference even when it is statistically clear. Marks in the tables: ▲ better than unpaid in every response scenario, ▼ worse in every one, △ / ▽ better / worse in some. No mark: no meaningful difference.

## Does the unpaid model reproduce history?

Fitted on epochs 587–626, started from the observed state at epoch 626, and compared with epochs 627–666 (40 runs). **Every gated check passed.**

| metric | observed | simulated | low | high | error | kind | tolerance | result |
|---|---|---|---|---|---|---|---|---|
| tau67 | 22.300 | 22.455 | 21.055 | 23.779 | +0.007 | relative | 0.150 | pass |
| effective_n | 28.317 | 26.061 | 24.086 | 27.991 | -0.080 | relative | 0.150 | pass |
| drep_power (B ADA) | 5.417 | 5.956 | 5.651 | 6.254 | +0.099 | relative | 0.100 | pass |
| abstain (B ADA) | 10.492 | 10.212 | 9.851 | 10.529 | -0.027 | relative | 0.100 | pass |
| dreps | 848.000 | 802.825 | 764.975 | 830.100 | -0.053 | relative | 0.100 | pass |
| turnover | 0.010 | 0.007 | 0.006 | 0.008 | -0.355 | relative | 0.500 | pass |
| turnout | 0.790 | 0.791 | 0.758 | 0.817 | +0.000 | absolute | 0.050 | pass |
| supported_ratified | 0.750 | 0.766 | 0.600 | 1.000 | +0.016 | absolute | 0.150 | pass |
| ratified | 0.500 | 0.696 | 0.532 | 0.850 | +0.196 | absolute |  | context |
| ballots | 172.797 | 197.267 | 183.617 | 207.731 | +0.142 | relative | 0.200 | pass |

`error` is relative unless `kind` says absolute. `context` rows depend on which proposals get submitted, which the model takes from history rather than predicts.

![validation](figures/validation.png)

## What each formula does to today's DReps (no behaviour change)

Exact arithmetic on the current snapshot. `outsider's take` is the share of the budget an outsider gets by bringing 1,000,000 ADA and voting on everything, using as many fake DReps as pays best; the next column is how much of that comes from splitting rather than from simply taking part. `insider split gain` is the most any existing DRep adds by splitting into 2–20 DReps with its delegators following (an upper bound: delegators may not follow). The Sybil axis is the larger of the two splitting gains. `delegators paid` counts the delegating accounts that would be paid anything at all: each gets a CIP-159 direct deposit, however small.

| scheme | rule | DReps paid | largest award / epoch | to 10 largest | outsider's take | of which from splitting | insider split gain | voting power kept | delegators paid |
|---|---|---|---|---|---|---|---|---|---|
| proportional | linear; 5M ADA | 193 | 18,907 | 55% | 0% | 0% | 0% | 100% |  |
| equal | equal; 5M ADA | 193 | 1,030 | 5% | 88% | 87% | 12% | 100% |  |
| sqrt | power^0.5; 5M ADA | 193 | 7,445 | 28% | 5% | 5% | 15% | 100% |  |
| capped | linear, cap 20M; 5M ADA | 193 | 3,181 | 16% | 0% | 0% | 30% | 100% |  |
| middle_out | equal, skip top 10, pay 100; 5M ADA | 100 | 1,862 | 0% | 1% | 0% | 24% | 100% |  |
| activity_gate | linear, gate 70%; 5M ADA | 102 | 20,907 | 54% | 0% | 0% | 0% | 100% |  |
| rationale_bonus | power^0.5, rationale +100%; 5M ADA | 193 | 9,327 | 29% | 6% | 6% | 18% | 100% |  |
| small_drep_floor | power^0.5, min 100k, min 10 delegators; 5M ADA | 126 | 7,791 | 29% | 1% | 0% | 15% | 100% |  |
| delegator_flat | linear, 80% to delegators (flat); 5M ADA | 193 | 3,781 | 55% | 0% | 0% | 0% | 100% | 63,839 |
| delegator_passthrough_sqrt | power^0.5, 80% to delegators (passthrough); 5M ADA | 193 | 1,489 | 28% | 5% | 5% | 15% | 100% | 63,839 |
| pledge_soft_cap | linear, pledge soft cap 1000x; 5M ADA | 180 | 34,765 | 49% | 0% | 0% | 0% | 100% |  |
| pledge_hard_cap | linear, pledge hard cap 1000x; 5M ADA | 180 | 34,765 | 49% | 0% | 0% | 0% | 17% |  |
| top_m_equal | equal, pay 100; 5M ADA | 100 | 1,804 | 9% | 0% | 0% | 23% | 100% |  |
| top_m_proportional | linear, pay 100; 5M ADA | 100 | 19,006 | 55% | 0% | 0% | 0% | 100% |  |
| threshold_k | equal, award cap 1%, min 1.00% of power; 5M ADA | 21 | 1,389 | 43% | 0% | 0% | 4% | 100% |  |
| threshold_k_proportional | linear, min 1.00% of power; 5M ADA | 21 | 23,361 | 68% | 0% | 0% | 0% | 100% |  |
| equal_plus_power | linear, 50% equal; 5M ADA | 193 | 9,968 | 30% | 44% | 44% | 6% | 100% |  |
| exclude_k_pay_n | equal, 10 ADA per vote, skip top 10, pay 200 (roll-down); 5M ADA | 184 | 12 | 0% | 1% | 1% | 0% | 100% |  |
| top_haircut | linear, top 20 at 25%, min 10 delegators, gate 70%; 5M ADA | 80 | 12,619 | 33% | 0% | 0% | 19% | 100% |  |
| top_100_gated | equal, pay 100, gate 70%; 5M ADA | 100 | 1,435 | 6% | 8% | 7% | 19% | 100% |  |
| delegators_first | linear, award cap 10%, gate 70%, 90% to delegators (flat); 5M ADA | 102 | 1,389 | 50% | 0% | 0% | 1% | 100% | 47,097 |
| delegator_count_sqrt | delegators^0.5, award cap 5%; 5M ADA | 190 | 6,944 | 27% | 64% | 59% | 22% | 100% |  |
| pledge_soft_cap_skip20 | linear, skip top 20, pledge soft cap 1x; 5M ADA | 164 | 26,294 | 0% | 12% | 0% | 3% | 100% |  |
| pledge_soft_cap_skip10 | linear, skip top 10, pledge soft cap 2x; 5M ADA | 172 | 19,949 | 0% | 8% | 0% | 3% | 100% |  |
| pledge_soft_cap_capped | linear, cap 5M, pledge soft cap 1x; 5M ADA | 180 | 25,292 | 4% | 12% | 0% | 0% | 100% |  |
| pledge_backed_delegators | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 1x; 5M ADA | 180 | 5,058 | 4% | 12% | 0% | 0% | 100% | 60,816 |
| skip_top20_delegators | linear, skip top 20, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | 84 | 4,683 | 0% | 3% | 0% | 34% | 100% | 8,433 |
| haircut_top20_delegators | linear, top 20 at 25%, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | 96 | 4,681 | 0% | 3% | 0% | 0% | 100% | 45,017 |
| small_drep_delegators | power^0.5, min 100k, min 10 delegators, 80% to delegators (passthrough), pledge soft cap 1x; 5M ADA | 115 | 2,016 | 6% | 18% | 9% | 8% | 100% | 60,161 |
| delegators_not_top20 | linear, 50% to delegators (flat), not via top 20; 5M ADA | 193 | 9,453 | 55% | 0% | 0% | 19% | 100% | 12,297 |
| top100_delegators_not_top20 | linear, pay 100, 50% to delegators (flat), not via top 20; 5M ADA | 100 | 9,503 | 55% | 0% | 0% | 20% | 100% | 10,553 |
| capped_1m | linear, cap 20M; 1M ADA | 193 | 636 | 16% | 0% | 0% | 30% | 100% |  |
| capped_2m5 | linear, cap 20M; 2.5M ADA | 193 | 1,591 | 16% | 0% | 0% | 30% | 100% |  |
| capped_10m | linear, cap 20M; 10M ADA | 193 | 6,362 | 16% | 0% | 0% | 30% | 100% |  |
| pledge_backed_delegators_2x | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 2x; 5M ADA | 180 | 3,804 | 5% | 8% | 0% | 0% | 100% | 60,816 |
| pledge_backed_delegators_5x | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 5x; 5M ADA | 180 | 3,098 | 6% | 4% | 0% | 0% | 100% | 60,816 |
| pledge_backed_delegators_uncapped | linear, 80% to delegators (passthrough), pledge soft cap 1x; 5M ADA | 180 | 5,058 | 4% | 12% | 0% | 0% | 100% | 60,816 |
| pledge_backed_delegators_half | linear, cap 5M, 50% to delegators (passthrough), pledge soft cap 1x; 5M ADA | 180 | 12,646 | 4% | 12% | 0% | 0% | 100% | 60,816 |
| skip_top10_delegators | linear, skip top 10, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | 91 | 4,680 | 0% | 3% | 0% | 23% | 100% | 14,134 |
| delegators_not_top10 | linear, 50% to delegators (flat), not via top 10; 5M ADA | 193 | 9,453 | 55% | 0% | 0% | 12% | 100% | 20,013 |
| delegators_not_top20_pledge | linear, 50% to delegators (flat), not via top 20, pledge soft cap 1000x; 5M ADA | 180 | 17,383 | 49% | 0% | 0% | 20% | 100% | 10,984 |
| skip_top20_delegators_min_pledge | linear, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | 22 | 4,748 | 0% | 3% | 0% | 0% | 100% | 1,907 |
| top100_delegators_not_top20_min_pledge | linear, pay 100, min pledge 10k, 50% to delegators (flat), not via top 20; 5M ADA | 57 | 15,576 | 53% | 0% | 0% | 16% | 100% | 2,763 |
| pledge_soft_cap_skip20_min_pledge | linear, skip top 20, min pledge 10k, pledge soft cap 1x; 5M ADA | 54 | 26,554 | 0% | 12% | 0% | 3% | 100% |  |
| equal_plus_power_fee_25k | linear, 50% equal; 25k ADA proposer fee | 193 | 2,082 | 30% | 44% | 44% | 6% | 100% |  |
| proportional_fee_100k | linear; 100k ADA proposer fee | 193 | 15,798 | 55% | 0% | 0% | 0% | 100% |  |
| proportional_fee_50k | linear; 50k ADA proposer fee | 193 | 7,899 | 55% | 0% | 0% | 0% | 100% |  |
| proportional_fee_10k | linear; 10k ADA proposer fee | 193 | 1,580 | 55% | 0% | 0% | 0% | 100% |  |
| equal_fee_100k | equal; 100k ADA proposer fee | 193 | 861 | 5% | 88% | 87% | 12% | 100% |  |
| equal_fee_50k | equal; 50k ADA proposer fee | 193 | 430 | 5% | 88% | 87% | 12% | 100% |  |
| equal_fee_10k | equal; 10k ADA proposer fee | 193 | 86 | 5% | 88% | 87% | 12% | 100% |  |
| sqrt_fee_100k | power^0.5; 100k ADA proposer fee | 193 | 6,221 | 28% | 5% | 5% | 15% | 100% |  |
| sqrt_fee_50k | power^0.5; 50k ADA proposer fee | 193 | 3,110 | 28% | 5% | 5% | 15% | 100% |  |
| sqrt_fee_10k | power^0.5; 10k ADA proposer fee | 193 | 622 | 28% | 5% | 5% | 15% | 100% |  |
| capped_fee_100k | linear, cap 20M; 100k ADA proposer fee | 193 | 2,658 | 16% | 0% | 0% | 30% | 100% |  |
| capped_fee_50k | linear, cap 20M; 50k ADA proposer fee | 193 | 1,329 | 16% | 0% | 0% | 30% | 100% |  |
| capped_fee_10k | linear, cap 20M; 10k ADA proposer fee | 193 | 266 | 16% | 0% | 0% | 30% | 100% |  |
| middle_out_fee_100k | equal, skip top 10, pay 100; 100k ADA proposer fee | 100 | 1,556 | 0% | 1% | 0% | 24% | 100% |  |
| middle_out_fee_50k | equal, skip top 10, pay 100; 50k ADA proposer fee | 100 | 778 | 0% | 1% | 0% | 24% | 100% |  |
| middle_out_fee_10k | equal, skip top 10, pay 100; 10k ADA proposer fee | 100 | 156 | 0% | 1% | 0% | 24% | 100% |  |
| activity_gate_fee_100k | linear, gate 70%; 100k ADA proposer fee | 102 | 17,469 | 54% | 0% | 0% | 0% | 100% |  |
| activity_gate_fee_50k | linear, gate 70%; 50k ADA proposer fee | 102 | 8,735 | 54% | 0% | 0% | 0% | 100% |  |
| activity_gate_fee_10k | linear, gate 70%; 10k ADA proposer fee | 102 | 1,747 | 54% | 0% | 0% | 0% | 100% |  |
| rationale_bonus_fee_100k | power^0.5, rationale +100%; 100k ADA proposer fee | 193 | 7,793 | 29% | 6% | 6% | 18% | 100% |  |
| rationale_bonus_fee_50k | power^0.5, rationale +100%; 50k ADA proposer fee | 193 | 3,897 | 29% | 6% | 6% | 18% | 100% |  |
| rationale_bonus_fee_10k | power^0.5, rationale +100%; 10k ADA proposer fee | 193 | 779 | 29% | 6% | 6% | 18% | 100% |  |
| small_drep_floor_fee_100k | power^0.5, min 100k, min 10 delegators; 100k ADA proposer fee | 126 | 6,510 | 29% | 1% | 0% | 15% | 100% |  |
| small_drep_floor_fee_50k | power^0.5, min 100k, min 10 delegators; 50k ADA proposer fee | 126 | 3,255 | 29% | 1% | 0% | 15% | 100% |  |
| small_drep_floor_fee_10k | power^0.5, min 100k, min 10 delegators; 10k ADA proposer fee | 126 | 651 | 29% | 1% | 0% | 15% | 100% |  |
| delegator_flat_fee_100k | linear, 80% to delegators (flat); 100k ADA proposer fee | 193 | 3,160 | 55% | 0% | 0% | 0% | 100% | 63,839 |
| delegator_flat_fee_50k | linear, 80% to delegators (flat); 50k ADA proposer fee | 193 | 1,580 | 55% | 0% | 0% | 0% | 100% | 63,839 |
| delegator_flat_fee_10k | linear, 80% to delegators (flat); 10k ADA proposer fee | 193 | 316 | 55% | 0% | 0% | 0% | 100% | 63,839 |
| delegator_passthrough_sqrt_fee_100k | power^0.5, 80% to delegators (passthrough); 100k ADA proposer fee | 193 | 1,244 | 28% | 5% | 5% | 15% | 100% | 63,839 |
| delegator_passthrough_sqrt_fee_50k | power^0.5, 80% to delegators (passthrough); 50k ADA proposer fee | 193 | 622 | 28% | 5% | 5% | 15% | 100% | 63,839 |
| delegator_passthrough_sqrt_fee_10k | power^0.5, 80% to delegators (passthrough); 10k ADA proposer fee | 193 | 124 | 28% | 5% | 5% | 15% | 100% | 63,839 |
| pledge_soft_cap_fee_100k | linear, pledge soft cap 1000x; 100k ADA proposer fee | 180 | 29,048 | 49% | 0% | 0% | 0% | 100% |  |
| pledge_soft_cap_fee_50k | linear, pledge soft cap 1000x; 50k ADA proposer fee | 180 | 14,524 | 49% | 0% | 0% | 0% | 100% |  |
| pledge_soft_cap_fee_10k | linear, pledge soft cap 1000x; 10k ADA proposer fee | 180 | 2,905 | 49% | 0% | 0% | 0% | 100% |  |
| pledge_hard_cap_fee_100k | linear, pledge hard cap 1000x; 100k ADA proposer fee | 180 | 29,048 | 49% | 0% | 0% | 0% | 17% |  |
| pledge_hard_cap_fee_50k | linear, pledge hard cap 1000x; 50k ADA proposer fee | 180 | 14,524 | 49% | 0% | 0% | 0% | 17% |  |
| pledge_hard_cap_fee_10k | linear, pledge hard cap 1000x; 10k ADA proposer fee | 180 | 2,905 | 49% | 0% | 0% | 0% | 17% |  |
| top_m_equal_fee_100k | equal, pay 100; 100k ADA proposer fee | 100 | 1,507 | 9% | 0% | 0% | 23% | 100% |  |
| top_m_equal_fee_50k | equal, pay 100; 50k ADA proposer fee | 100 | 754 | 9% | 0% | 0% | 23% | 100% |  |
| top_m_equal_fee_10k | equal, pay 100; 10k ADA proposer fee | 100 | 151 | 9% | 0% | 0% | 23% | 100% |  |
| top_m_proportional_fee_100k | linear, pay 100; 100k ADA proposer fee | 100 | 15,881 | 55% | 0% | 0% | 0% | 100% |  |
| top_m_proportional_fee_50k | linear, pay 100; 50k ADA proposer fee | 100 | 7,940 | 55% | 0% | 0% | 0% | 100% |  |
| top_m_proportional_fee_10k | linear, pay 100; 10k ADA proposer fee | 100 | 1,588 | 55% | 0% | 0% | 0% | 100% |  |
| threshold_k_fee_100k | equal, award cap 1%, min 1.00% of power; 100k ADA proposer fee | 21 | 1,160 | 43% | 0% | 0% | 4% | 100% |  |
| threshold_k_fee_50k | equal, award cap 1%, min 1.00% of power; 50k ADA proposer fee | 21 | 580 | 43% | 0% | 0% | 4% | 100% |  |
| threshold_k_fee_10k | equal, award cap 1%, min 1.00% of power; 10k ADA proposer fee | 21 | 116 | 43% | 0% | 0% | 4% | 100% |  |
| threshold_k_proportional_fee_100k | linear, min 1.00% of power; 100k ADA proposer fee | 21 | 19,519 | 68% | 0% | 0% | 0% | 100% |  |
| threshold_k_proportional_fee_50k | linear, min 1.00% of power; 50k ADA proposer fee | 21 | 9,760 | 68% | 0% | 0% | 0% | 100% |  |
| threshold_k_proportional_fee_10k | linear, min 1.00% of power; 10k ADA proposer fee | 21 | 1,952 | 68% | 0% | 0% | 0% | 100% |  |
| equal_plus_power_fee_100k | linear, 50% equal; 100k ADA proposer fee | 193 | 8,329 | 30% | 44% | 44% | 6% | 100% |  |
| equal_plus_power_fee_50k | linear, 50% equal; 50k ADA proposer fee | 193 | 4,165 | 30% | 44% | 44% | 6% | 100% |  |
| equal_plus_power_fee_10k | linear, 50% equal; 10k ADA proposer fee | 193 | 833 | 30% | 44% | 44% | 6% | 100% |  |
| exclude_k_pay_n_fee_100k | equal, 10 ADA per vote, skip top 10, pay 200 (roll-down); 100k ADA proposer fee | 184 | 12 | 0% | 1% | 1% | 0% | 100% |  |
| exclude_k_pay_n_fee_50k | equal, 10 ADA per vote, skip top 10, pay 200 (roll-down); 50k ADA proposer fee | 184 | 12 | 0% | 2% | 2% | 0% | 100% |  |
| exclude_k_pay_n_fee_10k | equal, 10 ADA per vote, skip top 10, pay 200 (roll-down); 10k ADA proposer fee | 184 | 12 | 0% | 8% | 8% | 2% | 100% |  |
| top_haircut_fee_100k | linear, top 20 at 25%, min 10 delegators, gate 70%; 100k ADA proposer fee | 80 | 10,544 | 33% | 0% | 0% | 19% | 100% |  |
| top_haircut_fee_50k | linear, top 20 at 25%, min 10 delegators, gate 70%; 50k ADA proposer fee | 80 | 5,272 | 33% | 0% | 0% | 19% | 100% |  |
| top_haircut_fee_10k | linear, top 20 at 25%, min 10 delegators, gate 70%; 10k ADA proposer fee | 80 | 1,054 | 33% | 0% | 0% | 19% | 100% |  |
| top_100_gated_fee_100k | equal, pay 100, gate 70%; 100k ADA proposer fee | 100 | 1,199 | 6% | 8% | 7% | 19% | 100% |  |
| top_100_gated_fee_50k | equal, pay 100, gate 70%; 50k ADA proposer fee | 100 | 599 | 6% | 8% | 7% | 19% | 100% |  |
| top_100_gated_fee_10k | equal, pay 100, gate 70%; 10k ADA proposer fee | 100 | 120 | 6% | 8% | 7% | 19% | 100% |  |
| delegators_first_fee_100k | linear, award cap 10%, gate 70%, 90% to delegators (flat); 100k ADA proposer fee | 102 | 1,160 | 50% | 0% | 0% | 1% | 100% | 47,097 |
| delegators_first_fee_50k | linear, award cap 10%, gate 70%, 90% to delegators (flat); 50k ADA proposer fee | 102 | 580 | 50% | 0% | 0% | 1% | 100% | 47,097 |
| delegators_first_fee_10k | linear, award cap 10%, gate 70%, 90% to delegators (flat); 10k ADA proposer fee | 102 | 116 | 50% | 0% | 0% | 1% | 100% | 47,097 |
| delegator_count_sqrt_fee_100k | delegators^0.5, award cap 5%; 100k ADA proposer fee | 190 | 5,802 | 27% | 64% | 59% | 22% | 100% |  |
| delegator_count_sqrt_fee_50k | delegators^0.5, award cap 5%; 50k ADA proposer fee | 190 | 2,901 | 27% | 64% | 59% | 22% | 100% |  |
| delegator_count_sqrt_fee_10k | delegators^0.5, award cap 5%; 10k ADA proposer fee | 190 | 580 | 27% | 64% | 59% | 22% | 100% |  |
| pledge_soft_cap_skip20_fee_100k | linear, skip top 20, pledge soft cap 1x; 100k ADA proposer fee | 164 | 21,970 | 0% | 12% | 0% | 3% | 100% |  |
| pledge_soft_cap_skip20_fee_50k | linear, skip top 20, pledge soft cap 1x; 50k ADA proposer fee | 164 | 10,985 | 0% | 12% | 0% | 3% | 100% |  |
| pledge_soft_cap_skip20_fee_10k | linear, skip top 20, pledge soft cap 1x; 10k ADA proposer fee | 164 | 2,197 | 0% | 12% | 0% | 3% | 100% |  |
| pledge_soft_cap_skip10_fee_100k | linear, skip top 10, pledge soft cap 2x; 100k ADA proposer fee | 172 | 16,668 | 0% | 8% | 0% | 3% | 100% |  |
| pledge_soft_cap_skip10_fee_50k | linear, skip top 10, pledge soft cap 2x; 50k ADA proposer fee | 172 | 8,334 | 0% | 8% | 0% | 3% | 100% |  |
| pledge_soft_cap_skip10_fee_10k | linear, skip top 10, pledge soft cap 2x; 10k ADA proposer fee | 172 | 1,667 | 0% | 8% | 0% | 3% | 100% |  |
| pledge_soft_cap_capped_fee_100k | linear, cap 5M, pledge soft cap 1x; 100k ADA proposer fee | 180 | 21,133 | 4% | 12% | 0% | 0% | 100% |  |
| pledge_soft_cap_capped_fee_50k | linear, cap 5M, pledge soft cap 1x; 50k ADA proposer fee | 180 | 10,567 | 4% | 12% | 0% | 0% | 100% |  |
| pledge_soft_cap_capped_fee_10k | linear, cap 5M, pledge soft cap 1x; 10k ADA proposer fee | 180 | 2,113 | 4% | 12% | 0% | 0% | 100% |  |
| pledge_backed_delegators_fee_100k | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 1x; 100k ADA proposer fee | 180 | 4,227 | 4% | 12% | 0% | 0% | 100% | 60,816 |
| pledge_backed_delegators_fee_50k | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 1x; 50k ADA proposer fee | 180 | 2,113 | 4% | 12% | 0% | 0% | 100% | 60,816 |
| pledge_backed_delegators_fee_10k | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 1x; 10k ADA proposer fee | 180 | 423 | 4% | 12% | 0% | 0% | 100% | 60,816 |
| skip_top20_delegators_fee_100k | linear, skip top 20, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 100k ADA proposer fee | 84 | 3,913 | 0% | 3% | 0% | 34% | 100% | 8,433 |
| skip_top20_delegators_fee_50k | linear, skip top 20, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 50k ADA proposer fee | 84 | 1,956 | 0% | 3% | 0% | 34% | 100% | 8,433 |
| skip_top20_delegators_fee_10k | linear, skip top 20, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 10k ADA proposer fee | 84 | 391 | 0% | 3% | 0% | 34% | 100% | 8,433 |
| haircut_top20_delegators_fee_100k | linear, top 20 at 25%, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 100k ADA proposer fee | 96 | 3,912 | 0% | 3% | 0% | 0% | 100% | 45,017 |
| haircut_top20_delegators_fee_50k | linear, top 20 at 25%, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 50k ADA proposer fee | 96 | 1,956 | 0% | 3% | 0% | 0% | 100% | 45,017 |
| haircut_top20_delegators_fee_10k | linear, top 20 at 25%, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 10k ADA proposer fee | 96 | 391 | 0% | 3% | 0% | 0% | 100% | 45,017 |
| small_drep_delegators_fee_100k | power^0.5, min 100k, min 10 delegators, 80% to delegators (passthrough), pledge soft cap 1x; 100k ADA proposer fee | 115 | 1,685 | 6% | 18% | 9% | 8% | 100% | 60,161 |
| small_drep_delegators_fee_50k | power^0.5, min 100k, min 10 delegators, 80% to delegators (passthrough), pledge soft cap 1x; 50k ADA proposer fee | 115 | 842 | 6% | 18% | 9% | 8% | 100% | 60,161 |
| small_drep_delegators_fee_10k | power^0.5, min 100k, min 10 delegators, 80% to delegators (passthrough), pledge soft cap 1x; 10k ADA proposer fee | 115 | 168 | 6% | 18% | 9% | 8% | 100% | 60,161 |
| delegators_not_top20_fee_100k | linear, 50% to delegators (flat), not via top 20; 100k ADA proposer fee | 193 | 7,899 | 55% | 0% | 0% | 19% | 100% | 12,297 |
| delegators_not_top20_fee_50k | linear, 50% to delegators (flat), not via top 20; 50k ADA proposer fee | 193 | 3,949 | 55% | 0% | 0% | 19% | 100% | 12,297 |
| delegators_not_top20_fee_10k | linear, 50% to delegators (flat), not via top 20; 10k ADA proposer fee | 193 | 790 | 55% | 0% | 0% | 19% | 100% | 12,297 |
| top100_delegators_not_top20_fee_100k | linear, pay 100, 50% to delegators (flat), not via top 20; 100k ADA proposer fee | 100 | 7,940 | 55% | 0% | 0% | 20% | 100% | 10,553 |
| top100_delegators_not_top20_fee_50k | linear, pay 100, 50% to delegators (flat), not via top 20; 50k ADA proposer fee | 100 | 3,970 | 55% | 0% | 0% | 20% | 100% | 10,553 |
| top100_delegators_not_top20_fee_10k | linear, pay 100, 50% to delegators (flat), not via top 20; 10k ADA proposer fee | 100 | 794 | 55% | 0% | 0% | 20% | 100% | 10,553 |

## Scorecard: named schemes at the same budget

100 seeds per scheme and scenario. Unpaid baseline: Delegated ADA casting an explicit vote 25.3 points; DReps needed for 2/3 of voting power 19.6; Voting power backed by the DRep's pledge 0.71 points. Cells are the change against unpaid in the `central` scenario ± 95%; the marks use all of `low`, `central`, `high`.

| scheme | Participation (points) | Decentralisation (DReps) | Skin in the game (points) | Reward sustainability (M ADA a year) | Sybil resistance (% of budget) |
|---|---|---|---|---|---|
| proportional | +4.4 ± 0.1 ▲ | -2.1 ± 0.2 ▼ | -0.01 ± 0.00 | 10.1M | 0% |
| equal | +3.5 ± 0.1 ▲ | +0.2 ± 0.2 | +0.01 ± 0.00 | 10.1M | 87% |
| sqrt | +4.6 ± 0.1 ▲ | -1.2 ± 0.2 ▽ | -0.00 ± 0.00 | 10.1M | 15% |
| capped | +4.5 ± 0.1 ▲ | -0.5 ± 0.2 | -0.00 ± 0.00 | 10.1M | 30% |
| middle_out | +2.6 ± 0.1 ▲ | +1.8 ± 0.3 △ | -0.00 ± 0.00 | 10.1M | 24% |
| activity_gate | +4.5 ± 0.1 ▲ | -2.2 ± 0.2 ▼ | -0.01 ± 0.00 | 10.1M | 0% |
| rationale_bonus | +4.5 ± 0.1 ▲ | -1.3 ± 0.2 ▽ | -0.00 ± 0.00 | 10.1M | 18% |
| small_drep_floor | +4.5 ± 0.1 ▲ | -1.3 ± 0.2 ▽ | -0.01 ± 0.00 | 10.1M | 15% |
| delegator_flat | +4.4 ± 0.1 ▲ | -2.5 ± 0.3 ▼ | -0.05 ± 0.00 | 10.1M | 0% |
| delegator_passthrough_sqrt | +4.1 ± 0.1 ▲ | -0.9 ± 0.3 ▽ | -0.02 ± 0.01 | 10.1M | 15% |
| pledge_soft_cap | +4.0 ± 0.1 ▲ | -1.8 ± 0.2 ▽ | +0.01 ± 0.00 | 10.1M | 0% |
| pledge_hard_cap | -17.1 ± 0.2 ▼ | -1.8 ± 0.2 ▼ | +1.47 ± 0.02 ▲ | 10.1M | 0% |
| top_m_equal | +4.3 ± 0.1 ▲ | -0.3 ± 0.1 | -0.00 ± 0.00 | 10.1M | 23% |
| top_m_proportional | +4.4 ± 0.1 ▲ | -2.1 ± 0.2 ▼ | -0.01 ± 0.00 | 10.1M | 0% |
| threshold_k | +3.5 ± 0.1 ▲ | -2.8 ± 0.2 ▼ | -0.01 ± 0.00 | 9.2M | 4% |
| threshold_k_proportional | +3.5 ± 0.1 ▲ | -3.3 ± 0.2 ▼ | -0.01 ± 0.00 | 10.1M | 0% |
| equal_plus_power | +4.3 ± 0.1 ▲ | -1.5 ± 0.2 ▽ | +0.00 ± 0.00 | 10.1M | 44% |
| exclude_k_pay_n | +0.2 ± 0.0 | +0.2 ± 0.1 | +0.00 ± 0.00 | 0.1M | 1% |
| top_haircut | +4.6 ± 0.1 ▲ | -1.3 ± 0.2 ▽ | -0.00 ± 0.00 | 10.1M | 19% |
| top_100_gated | +4.3 ± 0.1 ▲ | -0.4 ± 0.2 | -0.00 ± 0.00 | 10.1M | 19% |
| delegators_first | +4.2 ± 0.1 ▲ | -2.4 ± 0.3 ▼ | -0.06 ± 0.00 | 10.1M | 1% |
| delegator_count_sqrt | +4.2 ± 0.1 ▲ | -1.1 ± 0.2 ▽ | -0.00 ± 0.00 | 10.1M | 59% |
| pledge_soft_cap_skip20 | +1.4 ± 0.0 △ | +2.3 ± 0.2 △ | +0.56 ± 0.01 △ | 10.1M | 3% |
| pledge_soft_cap_skip10 | +2.2 ± 0.1 △ | +1.2 ± 0.2 △ | +0.50 ± 0.01 △ | 10.1M | 3% |
| pledge_soft_cap_capped | +3.7 ± 0.1 △ | -0.7 ± 0.2 | +0.60 ± 0.01 △ | 10.1M | 0% |
| pledge_backed_delegators | +2.9 ± 0.1 △ | +2.2 ± 0.3 ▲ | +0.41 ± 0.01 △ | 10.1M | 0% |
| skip_top20_delegators | +3.9 ± 0.2 ▲ | +5.4 ± 0.3 ▲ | +0.19 ± 0.01 △ | 10.1M | 34% |
| haircut_top20_delegators | +3.0 ± 0.1 ▲ | -1.1 ± 0.3 ▽ | +0.40 ± 0.01 △ | 10.1M | 0% |
| small_drep_delegators | +3.4 ± 0.1 ▲ | +0.6 ± 0.2 △ | +0.36 ± 0.01 △ | 10.1M | 9% |
| delegators_not_top20 | +5.1 ± 0.1 ▲ | -0.6 ± 0.3 | -0.06 ± 0.00 | 10.1M | 19% |
| top100_delegators_not_top20 | +5.2 ± 0.1 ▲ | -0.8 ± 0.3 | -0.06 ± 0.01 | 10.1M | 20% |

![scorecard](figures/scorecard.png)

### Which assumption each result rests on

Each column switches on one response channel at its central strength and leaves the others off. A scheme whose result comes from one channel stands or falls with that assumption. With every channel off, paying changes nothing (a hard cap on voting power excepted).

Participation: change in Delegated ADA casting an explicit vote (points)

| scheme | voting only | yield only | reinvest only | pledge only | central |
|---|---|---|---|---|---|
| proportional | +4.3 | +0.0 | +0.2 | +0.0 | +4.4 |
| equal | +3.4 | +0.0 | +0.2 | +0.0 | +3.5 |
| sqrt | +4.4 | +0.0 | +0.2 | +0.0 | +4.6 |
| capped | +4.4 | +0.0 | +0.2 | +0.0 | +4.5 |
| middle_out | +2.5 | +0.0 | +0.1 | +0.0 | +2.6 |
| activity_gate | +4.3 | +0.0 | +0.4 | +0.0 | +4.5 |
| rationale_bonus | +4.4 | +0.0 | +0.2 | +0.0 | +4.5 |
| small_drep_floor | +4.4 | +0.0 | +0.2 | +0.0 | +4.5 |
| delegator_flat | +3.1 | +1.0 | +0.2 | +0.0 | +4.4 |
| delegator_passthrough_sqrt | +3.1 | +0.8 | +0.2 | +0.0 | +4.1 |
| pledge_soft_cap | +2.1 | +0.0 | -0.0 | +0.0 | +4.0 |
| pledge_hard_cap | -20.3 | -21.6 | -21.1 | -18.8 | -17.1 |
| top_m_equal | +4.2 | +0.0 | +0.2 | +0.0 | +4.3 |
| top_m_proportional | +4.3 | +0.0 | +0.2 | +0.0 | +4.4 |
| threshold_k | +3.3 | +0.0 | +0.2 | +0.0 | +3.5 |
| threshold_k_proportional | +3.3 | +0.0 | +0.3 | +0.0 | +3.5 |
| equal_plus_power | +4.2 | +0.0 | +0.2 | +0.0 | +4.3 |
| exclude_k_pay_n | +0.2 | +0.0 | +0.0 | +0.0 | +0.2 |
| top_haircut | +4.5 | +0.0 | +0.3 | +0.0 | +4.6 |
| top_100_gated | +4.1 | +0.0 | +0.3 | +0.0 | +4.3 |
| delegators_first | +2.7 | +1.4 | +0.2 | +0.0 | +4.2 |
| delegator_count_sqrt | +4.1 | +0.0 | +0.2 | +0.0 | +4.2 |
| pledge_soft_cap_skip20 | +0.4 | +0.0 | -0.0 | +0.1 | +1.4 |
| pledge_soft_cap_skip10 | +0.5 | +0.0 | -0.0 | +0.1 | +2.2 |
| pledge_soft_cap_capped | +1.2 | +0.0 | -0.0 | +0.1 | +3.7 |
| pledge_backed_delegators | +0.8 | +0.7 | -0.1 | +0.1 | +2.9 |
| skip_top20_delegators | +0.3 | +3.3 | +0.0 | +0.0 | +3.9 |
| haircut_top20_delegators | +0.7 | +1.3 | -0.0 | +0.1 | +3.0 |
| small_drep_delegators | +1.3 | +0.9 | -0.0 | +0.1 | +3.4 |
| delegators_not_top20 | +3.8 | +1.1 | +0.2 | +0.0 | +5.1 |
| top100_delegators_not_top20 | +3.8 | +1.2 | +0.2 | +0.0 | +5.2 |

Decentralisation: change in DReps needed for 2/3 of voting power (DReps)

| scheme | voting only | yield only | reinvest only | pledge only | central |
|---|---|---|---|---|---|
| proportional | -0.0 | +0.0 | -2.2 | +0.0 | -2.1 |
| equal | +0.3 | +0.0 | -0.3 | +0.0 | +0.2 |
| sqrt | +0.2 | +0.0 | -1.4 | +0.0 | -1.2 |
| capped | +0.2 | +0.0 | -0.8 | +0.0 | -0.5 |
| middle_out | +0.5 | +0.0 | +1.2 | +0.0 | +1.8 |
| activity_gate | +0.0 | +0.0 | -2.3 | +0.0 | -2.2 |
| rationale_bonus | +0.1 | +0.0 | -1.4 | +0.0 | -1.3 |
| small_drep_floor | +0.1 | +0.0 | -1.5 | +0.0 | -1.3 |
| delegator_flat | -0.1 | -0.7 | -1.9 | +0.0 | -2.5 |
| delegator_passthrough_sqrt | +0.1 | +0.3 | -1.2 | +0.0 | -0.9 |
| pledge_soft_cap | +0.0 | +0.0 | -0.8 | -0.0 | -1.8 |
| pledge_hard_cap | -13.0 | -12.9 | -14.1 | +0.0 | -1.8 |
| top_m_equal | +0.1 | +0.0 | -0.6 | +0.0 | -0.3 |
| top_m_proportional | -0.0 | +0.0 | -2.3 | +0.0 | -2.1 |
| threshold_k | -0.3 | +0.0 | -2.6 | +0.0 | -2.8 |
| threshold_k_proportional | -0.4 | +0.0 | -3.2 | +0.0 | -3.3 |
| equal_plus_power | +0.2 | +0.0 | -1.7 | +0.0 | -1.5 |
| exclude_k_pay_n | +0.1 | +0.0 | +0.1 | +0.0 | +0.2 |
| top_haircut | +0.0 | +0.0 | -1.6 | +0.0 | -1.3 |
| top_100_gated | +0.2 | +0.0 | -0.8 | +0.0 | -0.4 |
| delegators_first | -0.1 | -0.7 | -1.5 | +0.0 | -2.4 |
| delegator_count_sqrt | +0.1 | +0.0 | -1.4 | +0.0 | -1.1 |
| pledge_soft_cap_skip20 | +0.2 | +0.0 | +0.8 | +0.2 | +2.3 |
| pledge_soft_cap_skip10 | +0.3 | +0.0 | +0.7 | +0.2 | +1.2 |
| pledge_soft_cap_capped | +0.0 | +0.0 | -0.2 | +0.2 | -0.7 |
| pledge_backed_delegators | +0.1 | +3.3 | -0.0 | +0.1 | +2.2 |
| skip_top20_delegators | +0.2 | +4.2 | +0.4 | +0.1 | +5.4 |
| haircut_top20_delegators | +0.1 | -0.5 | +0.3 | +0.1 | -1.1 |
| small_drep_delegators | +0.0 | +3.2 | -0.1 | +0.0 | +0.6 |
| delegators_not_top20 | -0.1 | +2.0 | -2.2 | +0.0 | -0.6 |
| top100_delegators_not_top20 | -0.0 | +1.9 | -2.2 | +0.0 | -0.8 |

Skin in the game: change in Voting power backed by the DRep's pledge (points)

| scheme | voting only | yield only | reinvest only | pledge only | central |
|---|---|---|---|---|---|
| proportional | -0.00 | +0.00 | -0.01 | +0.00 | -0.01 |
| equal | +0.01 | +0.00 | -0.00 | +0.00 | +0.01 |
| sqrt | +0.00 | +0.00 | -0.00 | +0.00 | -0.00 |
| capped | -0.00 | +0.00 | -0.00 | +0.00 | -0.00 |
| middle_out | +0.00 | +0.00 | -0.00 | +0.00 | -0.00 |
| activity_gate | -0.00 | +0.00 | -0.01 | +0.00 | -0.01 |
| rationale_bonus | -0.00 | +0.00 | -0.00 | +0.00 | -0.00 |
| small_drep_floor | -0.00 | +0.00 | -0.01 | +0.00 | -0.01 |
| delegator_flat | -0.00 | -0.04 | -0.00 | +0.00 | -0.05 |
| delegator_passthrough_sqrt | -0.00 | -0.02 | -0.00 | +0.00 | -0.02 |
| pledge_soft_cap | +0.00 | +0.00 | -0.00 | +0.02 | +0.01 |
| pledge_hard_cap | +3.44 | +3.51 | +2.93 | +1.52 | +1.47 |
| top_m_equal | +0.00 | +0.00 | -0.00 | +0.00 | -0.00 |
| top_m_proportional | -0.00 | +0.00 | -0.01 | +0.00 | -0.01 |
| threshold_k | -0.00 | +0.00 | -0.01 | +0.00 | -0.01 |
| threshold_k_proportional | -0.00 | +0.00 | -0.01 | +0.00 | -0.01 |
| equal_plus_power | +0.01 | +0.00 | -0.00 | +0.00 | +0.00 |
| exclude_k_pay_n | -0.00 | +0.00 | +0.00 | +0.00 | +0.00 |
| top_haircut | -0.00 | +0.00 | -0.01 | +0.00 | -0.00 |
| top_100_gated | +0.00 | +0.00 | -0.00 | +0.00 | -0.00 |
| delegators_first | -0.00 | -0.06 | -0.00 | +0.00 | -0.06 |
| delegator_count_sqrt | +0.00 | +0.00 | -0.01 | +0.00 | -0.00 |
| pledge_soft_cap_skip20 | +0.00 | +0.00 | +0.00 | +0.50 | +0.56 |
| pledge_soft_cap_skip10 | +0.00 | +0.00 | +0.01 | +0.45 | +0.50 |
| pledge_soft_cap_capped | +0.00 | +0.00 | +0.00 | +0.58 | +0.60 |
| pledge_backed_delegators | +0.00 | +0.02 | +0.00 | +0.43 | +0.41 |
| skip_top20_delegators | +0.00 | -0.13 | -0.00 | +0.22 | +0.19 |
| haircut_top20_delegators | +0.00 | -0.05 | +0.00 | +0.43 | +0.40 |
| small_drep_delegators | +0.00 | -0.03 | -0.00 | +0.41 | +0.36 |
| delegators_not_top20 | -0.00 | -0.05 | -0.01 | +0.00 | -0.06 |
| top100_delegators_not_top20 | -0.00 | -0.06 | -0.01 | +0.00 | -0.06 |

### Variations of named designs

Named designs with a setting changed, `central` scenario; compare each with its named design in the scorecard. The response to a reward is assumed to grow with its logarithm, so a bigger budget buys less than proportionally more.

| scheme | varies | cost a year | cost ÷ treasury | Participation | Decentralisation | ADA a year per point of participation |
|---|---|---|---|---|---|---|
| capped_1m | `capped`: 1M ADA | 2.0M | 0.15% | +3.1 ± 0.1 | -0.5 ± 0.1 | 644,895 |
| capped_2m5 | `capped`: 2.5M ADA | 5.1M | 0.36% | +4.0 ± 0.1 | -0.5 ± 0.1 | 1,278,335 |
| capped_10m | `capped`: 10M ADA | 20.3M | 1.45% | +5.0 ± 0.1 | -0.5 ± 0.2 | 4,047,060 |
| pledge_backed_delegators_2x | `pledge_backed_delegators`: pledge soft cap 2× | 10.1M | 0.73% | +3.0 ± 0.1 | +2.7 ± 0.3 | 3,351,456 |
| pledge_backed_delegators_5x | `pledge_backed_delegators`: pledge soft cap 5× | 10.1M | 0.73% | +3.1 ± 0.1 | +3.1 ± 0.3 | 3,232,370 |
| pledge_backed_delegators_uncapped | `pledge_backed_delegators`: no cap | 10.1M | 0.73% | +3.2 ± 0.1 | +0.2 ± 0.2 | 3,129,522 |
| pledge_backed_delegators_half | `pledge_backed_delegators`: 50% to delegators | 10.1M | 0.73% | +3.7 ± 0.1 | +1.1 ± 0.2 | 2,758,912 |
| skip_top10_delegators | `skip_top20_delegators`: skip 10 | 10.1M | 0.73% | +3.3 ± 0.1 | +1.2 ± 0.3 | 3,050,155 |
| delegators_not_top10 | `delegators_not_top20`: delegators not via top 10 | 10.1M | 0.73% | +4.9 ± 0.1 | -1.6 ± 0.2 | 2,088,185 |
| delegators_not_top20_pledge | `delegators_not_top20`: pledge soft cap 1000× | 10.1M | 0.73% | +4.7 ± 0.1 | -0.0 ± 0.2 | 2,162,135 |
| skip_top20_delegators_min_pledge | `skip_top20_delegators`: ≥10k ADA pledge | 10.1M | 0.73% | +5.2 ± 0.2 | +6.1 ± 0.3 | 1,956,459 |
| top100_delegators_not_top20_min_pledge | `top100_delegators_not_top20`: ≥10k ADA pledge | 10.1M | 0.73% | +6.2 ± 0.2 | +2.3 ± 0.2 | 1,627,879 |
| pledge_soft_cap_skip20_min_pledge | `pledge_soft_cap_skip20`: ≥10k ADA pledge | 10.1M | 0.73% | +1.4 ± 0.1 | +2.2 ± 0.2 | 7,345,822 |
| equal_plus_power_fee_25k | `equal_plus_power`: no budget, 25k ADA proposer fee | 2.2M | 0.16% | +3.1 ± 0.1 | -1.3 ± 0.2 | 704,272 |

### Paid from a budget or by a proposer fee

Each named design with its budget, and the same rule with no budget, paid instead by a proposer fee kept from every governance action that closes; `central` scenario, change against unpaid. Simulated DReps react to the fee's average flow, so a fee differs from a budget by how much money it brings, how its cost varies with the number of actions, and the hard fork it needs. Median cost a year: 5M budget 10.1M, 100k proposer fee 8.7M, 50k proposer fee 4.3M, 10k proposer fee 0.9M.

Participation: change in Delegated ADA casting an explicit vote (points)

| scheme | 5M budget | 100k proposer fee | 50k proposer fee | 10k proposer fee |
|---|---|---|---|---|
| proportional | +4.4 | +4.3 | +3.9 | +2.6 |
| equal | +3.5 | +3.3 | +2.7 | +1.3 |
| sqrt | +4.6 | +4.4 | +3.9 | +2.4 |
| capped | +4.5 | +4.4 | +3.8 | +2.3 |
| middle_out | +2.6 | +2.5 | +2.1 | +1.2 |
| activity_gate | +4.5 | +4.4 | +3.9 | +2.7 |
| rationale_bonus | +4.5 | +4.4 | +3.8 | +2.4 |
| small_drep_floor | +4.5 | +4.4 | +3.9 | +2.5 |
| delegator_flat | +4.4 | +4.0 | +3.0 | +1.4 |
| delegator_passthrough_sqrt | +4.1 | +3.8 | +2.8 | +1.1 |
| pledge_soft_cap | +4.0 | +3.9 | +3.4 | +2.2 |
| pledge_hard_cap | -17.1 | -17.1 | -17.3 | -17.7 |
| top_m_equal | +4.3 | +4.2 | +3.6 | +2.1 |
| top_m_proportional | +4.4 | +4.3 | +3.8 | +2.6 |
| threshold_k | +3.5 | +3.4 | +3.1 | +2.1 |
| threshold_k_proportional | +3.5 | +3.5 | +3.2 | +2.4 |
| equal_plus_power | +4.3 | +4.2 | +3.7 | +2.2 |
| exclude_k_pay_n | +0.2 | +0.2 | +0.2 | +0.2 |
| top_haircut | +4.6 | +4.5 | +4.0 | +2.7 |
| top_100_gated | +4.3 | +4.1 | +3.5 | +1.9 |
| delegators_first | +4.2 | +3.8 | +2.7 | +1.1 |
| delegator_count_sqrt | +4.2 | +4.1 | +3.5 | +2.1 |
| pledge_soft_cap_skip20 | +1.4 | +1.3 | +1.0 | +0.4 |
| pledge_soft_cap_skip10 | +2.2 | +2.1 | +1.6 | +0.7 |
| pledge_soft_cap_capped | +3.7 | +3.6 | +2.9 | +1.0 |
| pledge_backed_delegators | +2.9 | +2.5 | +1.4 | +0.3 |
| skip_top20_delegators | +3.9 | +3.3 | +1.7 | +0.4 |
| haircut_top20_delegators | +3.0 | +2.7 | +1.8 | +0.3 |
| small_drep_delegators | +3.4 | +3.0 | +1.9 | +0.4 |
| delegators_not_top20 | +5.1 | +4.8 | +3.8 | +2.1 |
| top100_delegators_not_top20 | +5.2 | +4.9 | +3.8 | +2.1 |

Decentralisation: change in DReps needed for 2/3 of voting power (DReps)

| scheme | 5M budget | 100k proposer fee | 50k proposer fee | 10k proposer fee |
|---|---|---|---|---|
| proportional | -2.1 | -2.1 | -2.1 | -1.7 |
| equal | +0.2 | +0.0 | -0.0 | -0.0 |
| sqrt | -1.2 | -1.2 | -1.2 | -0.9 |
| capped | -0.5 | -0.4 | -0.5 | -0.4 |
| middle_out | +1.8 | +1.7 | +1.4 | +0.6 |
| activity_gate | -2.2 | -2.2 | -2.1 | -1.8 |
| rationale_bonus | -1.3 | -1.3 | -1.2 | -1.1 |
| small_drep_floor | -1.3 | -1.2 | -1.2 | -0.9 |
| delegator_flat | -2.5 | -2.3 | -1.8 | -0.9 |
| delegator_passthrough_sqrt | -0.9 | -1.0 | -0.8 | -0.5 |
| pledge_soft_cap | -1.8 | -1.9 | -1.9 | -1.5 |
| pledge_hard_cap | -1.8 | -1.9 | -1.8 | -1.4 |
| top_m_equal | -0.3 | -0.3 | -0.4 | -0.3 |
| top_m_proportional | -2.1 | -2.1 | -2.2 | -1.7 |
| threshold_k | -2.8 | -2.6 | -2.5 | -1.6 |
| threshold_k_proportional | -3.3 | -3.3 | -3.0 | -2.2 |
| equal_plus_power | -1.5 | -1.4 | -1.5 | -1.1 |
| exclude_k_pay_n | +0.2 | +0.2 | +0.2 | +0.2 |
| top_haircut | -1.3 | -1.3 | -1.2 | -0.9 |
| top_100_gated | -0.4 | -0.4 | -0.4 | -0.3 |
| delegators_first | -2.4 | -2.4 | -1.8 | -0.6 |
| delegator_count_sqrt | -1.1 | -1.1 | -1.1 | -0.8 |
| pledge_soft_cap_skip20 | +2.3 | +2.0 | +1.7 | +0.7 |
| pledge_soft_cap_skip10 | +1.2 | +1.1 | +0.8 | +0.2 |
| pledge_soft_cap_capped | -0.7 | -0.7 | -0.7 | -0.0 |
| pledge_backed_delegators | +2.2 | +1.9 | +1.4 | +0.2 |
| skip_top20_delegators | +5.4 | +4.7 | +2.5 | +0.5 |
| haircut_top20_delegators | -1.1 | -0.9 | -0.8 | +0.1 |
| small_drep_delegators | +0.6 | +0.4 | -0.2 | +0.2 |
| delegators_not_top20 | -0.6 | -0.9 | -1.3 | -1.4 |
| top100_delegators_not_top20 | -0.8 | -1.0 | -1.4 | -1.4 |

Skin in the game: change in Voting power backed by the DRep's pledge (points)

| scheme | 5M budget | 100k proposer fee | 50k proposer fee | 10k proposer fee |
|---|---|---|---|---|
| proportional | -0.01 | -0.01 | -0.00 | -0.00 |
| equal | +0.01 | +0.01 | +0.01 | +0.00 |
| sqrt | -0.00 | -0.00 | -0.00 | -0.00 |
| capped | -0.00 | -0.00 | -0.00 | -0.00 |
| middle_out | -0.00 | -0.00 | -0.00 | +0.00 |
| activity_gate | -0.01 | -0.00 | -0.00 | -0.01 |
| rationale_bonus | -0.00 | -0.00 | -0.00 | -0.00 |
| small_drep_floor | -0.01 | -0.00 | -0.00 | -0.00 |
| delegator_flat | -0.05 | -0.04 | -0.02 | -0.00 |
| delegator_passthrough_sqrt | -0.02 | -0.01 | -0.01 | -0.00 |
| pledge_soft_cap | +0.01 | +0.01 | +0.01 | +0.02 |
| pledge_hard_cap | +1.47 | +1.46 | +1.46 | +1.48 |
| top_m_equal | -0.00 | -0.00 | -0.00 | -0.00 |
| top_m_proportional | -0.01 | -0.01 | -0.00 | -0.00 |
| threshold_k | -0.01 | -0.01 | -0.00 | -0.00 |
| threshold_k_proportional | -0.01 | -0.01 | -0.01 | -0.00 |
| equal_plus_power | +0.00 | +0.00 | +0.00 | -0.00 |
| exclude_k_pay_n | +0.00 | +0.00 | +0.00 | +0.00 |
| top_haircut | -0.00 | -0.00 | -0.00 | -0.00 |
| top_100_gated | -0.00 | -0.00 | -0.00 | -0.00 |
| delegators_first | -0.06 | -0.05 | -0.03 | -0.00 |
| delegator_count_sqrt | -0.00 | -0.00 | -0.00 | -0.00 |
| pledge_soft_cap_skip20 | +0.56 | +0.56 | +0.51 | +0.11 |
| pledge_soft_cap_skip10 | +0.50 | +0.49 | +0.45 | +0.16 |
| pledge_soft_cap_capped | +0.60 | +0.59 | +0.54 | +0.10 |
| pledge_backed_delegators | +0.41 | +0.31 | +0.13 | +0.03 |
| skip_top20_delegators | +0.19 | +0.19 | +0.11 | -0.00 |
| haircut_top20_delegators | +0.40 | +0.36 | +0.27 | +0.00 |
| small_drep_delegators | +0.36 | +0.34 | +0.27 | +0.02 |
| delegators_not_top20 | -0.06 | -0.05 | -0.03 | -0.01 |
| top100_delegators_not_top20 | -0.06 | -0.05 | -0.03 | -0.01 |

## Search over the scheme family

231 designs simulated over 10 generations, with the budget as one of the searched parameters. The finalists were re-run on 100 seeds the search never saw; all numbers here are from those seeds, averaged over `low`, `central`, `high`. Marks: ▲ better than unpaid in every scenario, ▼ worse in at least one.

- 24 of 62 finalists are unbeaten: no other design is at least as good on all 5 axes.
- Guardrail: no axis other than cost and Sybil resistance may be worse than unpaid in any scenario; those two are exact trade-offs, weighed on the front like the others. **36 of 62 finalists stay inside it.**
- Hypervolume of the front (progress measure, in the units of `axes.scale`): **0.07173** (95% 0.07051–0.07311); unpaid alone 0.00455. The search adds **0.02747** over the named schemes (95% 0.02687–0.02815).

### Shortlist: inside every guardrail and unbeaten

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| pledge_backed_delegators_half | linear, cap 5M, 50% to delegators (passthrough), pledge soft cap 1x; 5M ADA | +3.7 ± 0.1 ▲ | +2.1 ± 0.2 ▲ | +1.10 ± 0.01 | 10.1M | 0% |
| skip_top20_delegators_min_pledge | linear, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | +6.4 ± 0.2 ▲ | +6.5 ± 0.3 ▲ | +0.57 ± 0.01 | 10.1M | 0% |
| g5_22 | linear, skip top 20, min pledge 10k, 80% to delegators (passthrough), pledge soft cap 1x; 10M ADA | +6.5 ± 0.2 ▲ | +10.9 ± 0.3 ▲ | +1.28 ± 0.01 | 20.3M | 3% |
| g2_22 | linear, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 10M ADA | +10.6 ± 0.2 ▲ | +9.0 ± 0.3 ▲ | +0.71 ± 0.01 | 20.3M | 0% |
| g1_12 | power^0.75, cap 200M, award cap 2%, skip top 20, min 1M, min 10 delegators, min pledge 10k, gate 25%, 80% to delegators (flat), pledge soft cap 100x; 2.5M ADA | +4.0 ± 0.1 ▲ | +3.9 ± 0.3 ▲ | -0.13 ± 0.01 | 5.1M | 31% |
| g7_2 | equal, cap 2M, award cap 5%, min 100k, min pledge 10k, 50% to delegators (passthrough), not via top 10; 10M ADA | +5.6 ± 0.2 ▲ | +12.2 ± 0.3 ▲ | -0.06 ± 0.01 | 20.3M | 19% |
| g8_6 | power^0.75, cap 200M, award cap 2%, skip top 20, min 1M, min 5 delegators, min pledge 10k, gate 25%, 80% to delegators (passthrough), pledge soft cap 100x; 2.5M ADA | +3.0 ± 0.1 ▲ | +4.6 ± 0.3 ▲ | -0.09 ± 0.01 | 5.1M | 35% |
| g9_13 | linear, award cap 1%, skip top 20, min pledge 10k, gate 25%, 80% to delegators (flat), pledge soft cap 2x; 10M ADA | +9.7 ± 0.2 ▲ | +10.3 ± 0.3 ▲ | +0.13 ± 0.01 | 20.2M | 27% |
| capped_1m | linear, cap 20M; 1M ADA | +3.3 ± 0.1 ▲ | -0.4 ± 0.2 | -0.00 ± 0.00 | 2.0M | 30% |
| capped_2m5 | linear, cap 20M; 2.5M ADA | +4.0 ± 0.1 ▲ | -0.4 ± 0.2 | -0.00 ± 0.00 | 5.1M | 30% |
| g7_12 | power^0.75, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 1M ADA | +1.5 ± 0.1 ▲ | +1.9 ± 0.2 | +0.07 ± 0.01 | 2.0M | 3% |
| g0_18 | linear, 25% equal, cap 50M, pay 100 (roll-down), min 5 delegators, pledge soft cap 10000x; 1M ADA | +3.0 ± 0.1 ▲ | -0.5 ± 0.2 | -0.00 ± 0.00 | 2.0M | 12% |
| g7_6 | linear, pay 100, min pledge 10k, 50% to delegators (flat), not via top 20; 2.5M ADA | +4.2 ± 0.2 ▲ | +0.0 ± 0.2 | -0.11 ± 0.01 | 5.1M | 16% |
| pledge_soft_cap_skip20 | linear, skip top 20, pledge soft cap 1x; 5M ADA | +1.6 ± 0.0 | +3.1 ± 0.2 | +1.27 ± 0.01 | 10.1M | 3% |
| pledge_soft_cap_skip10 | linear, skip top 10, pledge soft cap 2x; 5M ADA | +2.2 ± 0.1 | +1.2 ± 0.2 | +1.41 ± 0.01 | 10.1M | 3% |
| g5_16 | linear, skip top 20, min pledge 10k, pledge soft cap 1x; 2.5M ADA | +1.2 ± 0.0 | +2.6 ± 0.2 | +1.12 ± 0.01 | 5.1M | 3% |
| g10_7 | linear, cap 5M, min 10k, 50% to delegators (passthrough), not via top 10, pledge soft cap 1x; 1M ADA | +1.5 ± 0.1 | +0.3 ± 0.2 | +0.27 ± 0.01 | 2.0M | 1% |
| g7_7 | linear, skip top 10, gate 50%, pledge soft cap 2x; 5M ADA | +1.9 ± 0.1 | +1.0 ± 0.2 | +1.31 ± 0.01 | 10.1M | 0% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| pledge_backed_delegators_half | +1.0 | +3.7 | +6.3 | +1.4 | +1.2 | +3.6 |
| skip_top20_delegators_min_pledge | +4.1 | +5.1 | +10.1 | +3.9 | +6.2 | +9.4 |
| g5_22 | +3.5 | +5.2 | +10.8 | +6.9 | +11.6 | +14.3 |
| g2_22 | +7.5 | +9.3 | +15.0 | +6.5 | +8.8 | +11.8 |
| g1_12 | +2.0 | +4.0 | +6.0 | +1.8 | +4.1 | +5.7 |
| g7_2 | +3.0 | +5.1 | +8.7 | +4.4 | +10.7 | +21.6 |
| g8_6 | +1.6 | +2.8 | +4.5 | +1.4 | +4.2 | +8.1 |
| g9_13 | +6.5 | +8.5 | +14.2 | +6.8 | +9.4 | +14.7 |
| capped_1m | +1.8 | +3.1 | +4.8 | -0.3 | -0.3 | -0.5 |
| capped_2m5 | +2.4 | +3.9 | +5.7 | -0.2 | -0.4 | -0.5 |
| g7_12 | +1.0 | +1.2 | +2.4 | +0.6 | +1.5 | +3.8 |
| g0_18 | +1.5 | +2.9 | +4.6 | -0.3 | -0.4 | -0.8 |
| g7_6 | +1.9 | +3.5 | +7.4 | +0.2 | +0.4 | -0.4 |
| pledge_soft_cap_skip20 | +0.3 | +1.4 | +3.0 | +0.7 | +2.5 | +6.0 |
| pledge_soft_cap_skip10 | +0.4 | +2.2 | +4.1 | +0.6 | +1.1 | +2.0 |
| g5_16 | +0.2 | +1.1 | +2.4 | +0.5 | +1.9 | +5.3 |
| g10_7 | +0.5 | +1.4 | +2.8 | +0.1 | +0.2 | +0.5 |
| g7_7 | +0.4 | +1.9 | +3.5 | +0.5 | +1.2 | +1.5 |

### Accepting a cost in decentralisation

8 unbeaten among the finalists that give up exactly this.

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| proportional | linear; 5M ADA | +4.4 ± 0.1 ▲ | -2.2 ± 0.2 ▼ | -0.01 ± 0.00 | 10.1M | 0% |
| proportional_gate_half_budget | linear, gate 50%; 2.5M ADA | +4.0 ± 0.1 ▲ | -2.1 ± 0.2 ▼ | -0.01 ± 0.00 | 5.1M | 0% |
| pledge_backed_delegators_uncapped | linear, 80% to delegators (passthrough), pledge soft cap 1x; 5M ADA | +3.4 ± 0.1 ▲ | -0.3 ± 0.2 ▼ | +0.88 ± 0.02 | 10.1M | 0% |
| g1_20 | linear, top 20 at 50%, min pledge 10k, pledge soft cap 1x; 5M ADA | +3.5 ± 0.1 | -1.0 ± 0.2 ▼ | +2.31 ± 0.02 | 10.1M | 1% |
| delegators_not_top10 | linear, 50% to delegators (flat), not via top 10; 5M ADA | +5.0 ± 0.1 ▲ | -1.6 ± 0.2 ▼ | -0.05 ± 0.00 | 10.1M | 12% |
| delegator_passthrough_sqrt | power^0.5, 80% to delegators (passthrough); 5M ADA | +4.3 ± 0.1 ▲ | -0.7 ± 0.2 ▼ | -0.03 ± 0.00 | 10.1M | 15% |
| sqrt_floor_25_gate_half | power^0.5, min 25 delegators, gate 50%; 2.5M ADA | +3.9 ± 0.1 ▲ | -1.4 ± 0.2 ▼ | -0.01 ± 0.00 | 5.1M | 17% |
| delegators_not_top20 | linear, 50% to delegators (flat), not via top 20; 5M ADA | +5.4 ± 0.1 ▲ | -0.6 ± 0.2 ▼ | -0.07 ± 0.01 | 10.1M | 19% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| proportional | +2.8 | +4.4 | +5.9 | -1.1 | -2.1 | -3.3 |
| proportional_gate_half_budget | +2.5 | +4.0 | +5.4 | -1.1 | -2.0 | -3.4 |
| pledge_backed_delegators_uncapped | +1.0 | +3.3 | +6.0 | +1.9 | +0.1 | -3.0 |
| g1_20 | +0.7 | +3.7 | +6.0 | +0.1 | -0.9 | -2.0 |
| delegators_not_top10 | +3.0 | +4.9 | +7.3 | -0.8 | -1.4 | -2.5 |
| delegator_passthrough_sqrt | +2.3 | +4.0 | +6.6 | -0.4 | -0.6 | -1.1 |
| sqrt_floor_25_gate_half | +2.4 | +3.9 | +5.3 | -0.7 | -1.2 | -2.1 |
| delegators_not_top20 | +3.1 | +5.2 | +7.9 | -0.3 | -0.6 | -1.0 |

### Accepting a cost in skin in the game

2 unbeaten among the finalists that give up exactly this.

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| g5_23 | linear, skip top 20, min 1M, min 50 delegators, min pledge 10k, gate 50%, rationale +200%, 80% to delegators (passthrough), not via top 20, pledge soft cap 100x; 10M ADA | +12.7 ± 0.3 ▲ | +3.3 ± 0.3 ▲ | -0.31 ± 0.01 ▼ | 20.3M | 0% |
| top100_delegators_not_top20_min_pledge | linear, pay 100, min pledge 10k, 50% to delegators (flat), not via top 20; 5M ADA | +7.3 ± 0.2 ▲ | +1.5 ± 0.2 ▲ | -0.17 ± 0.01 ▼ | 10.1M | 16% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| g5_23 | +7.5 | +13.8 | +16.8 | +3.7 | +1.4 | +4.9 |
| top100_delegators_not_top20_min_pledge | +3.0 | +6.1 | +12.7 | +1.1 | +2.2 | +1.3 |

### Accepting a cost in participation, decentralisation (needs another hard fork)

1 unbeaten among the finalists that give up exactly this.

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| pledge_hard_cap | linear, pledge hard cap 1000x; 5M ADA | -16.7 ± 0.2 ▼ | -5.4 ± 0.3 ▼ | +1.78 ± 0.03 ▲ | 10.1M | 0% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| pledge_hard_cap | -20.3 | -17.0 | -12.8 | -12.8 | -1.8 | -1.5 |

### Where the named schemes end up

| scheme | gives up | unbeaten among designs giving up the same |
|---|---|---|
| pledge_backed_delegators_half | nothing | yes |
| skip_top20_delegators_min_pledge | nothing | yes |
| capped_1m | nothing | yes |
| capped_2m5 | nothing | yes |
| pledge_soft_cap_skip20 | nothing | yes |
| pledge_soft_cap_skip10 | nothing | yes |
| top100_delegators_not_top20_min_pledge | skin in the game | yes |
| pledge_hard_cap | participation, decentralisation | yes |
| skip_top20_delegators | nothing | no |
| pledge_backed_delegators_2x | nothing | no |
| pledge_backed_delegators_5x | nothing | no |
| skip_top10_delegators | nothing | no |
| proportional | decentralisation | yes |
| equal | nothing | no |
| sqrt | decentralisation | no |
| capped | nothing | no |
| middle_out | nothing | no |
| activity_gate | decentralisation | no |
| rationale_bonus | decentralisation | no |
| small_drep_floor | decentralisation | no |
| delegator_flat | decentralisation | no |
| delegator_passthrough_sqrt | decentralisation | yes |
| pledge_soft_cap | decentralisation | no |
| top_m_equal | nothing | no |
| top_m_proportional | decentralisation | no |
| threshold_k | decentralisation | no |
| threshold_k_proportional | decentralisation | no |
| equal_plus_power | decentralisation | no |
| top_haircut | decentralisation | no |
| top_100_gated | nothing | no |
| delegators_first | decentralisation | no |
| delegator_count_sqrt | decentralisation | no |
| pledge_backed_delegators | nothing | no |
| haircut_top20_delegators | decentralisation | no |
| small_drep_delegators | nothing | no |
| delegators_not_top20 | decentralisation | yes |
| top100_delegators_not_top20 | decentralisation | no |
| capped_10m | nothing | no |
| pledge_backed_delegators_uncapped | decentralisation | yes |
| delegators_not_top10 | decentralisation | yes |
| delegators_not_top20_pledge | nothing | no |
| exclude_k_pay_n | nothing | yes |
| pledge_soft_cap_capped | nothing | no |
| pledge_soft_cap_skip20_min_pledge | nothing | no |

The guardrails are judgement calls in `config.yaml`. Moving one and running `rss-gov report` regroups these tables without simulating anything.

![front](figures/front.png)

## Ranking by net benefit

One score per design: what its gains are worth at the values in `config.yaml` (`ranking`), minus its cost and what one actor could take by splitting into many DReps, in ADA a year, averaged over `low`, `central`, `high`. The values are judgements, not measurements: 1M ADA a year for 1 point of participation, 1.25M for 1 more DRep holding two thirds of the power, 4.5M for 1 point of pledge backing; ADA lost to splitting counts 1× on top of the cost. Paying nothing scores 0. Every design is scored on the same holdout seeds; ± is the 95% interval.

*Behind the best*: the most it falls short of the best design in any one scenario. *Pays off from*: the share of these values at which its gains cover its cost. *First*: how often it ranks first when every value moves by up to 50% either way. *Gives up*: the guardrail it crosses.

Designs that need only CIP-159 (61 designs: the experiment's and the search's finalists), the top 15:

| rank | scheme | rule | net benefit | low | central | high | behind the best | pays off from | first, values ±50% | gives up |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | skip_top20_delegators_min_pledge | linear, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | +7.0M ± 0.3M | -1.6M | +3.6M | +19.0M | 2.2M | 0.59× | 66% |  |
| 2 | g5_22 | linear, skip top 20, min pledge 10k, 80% to delegators (passthrough), pledge soft cap 1x; 10M ADA | +5.1M ± 0.3M | -8.1M | +2.3M | +21.2M | 8.2M | 0.80× | 14% |  |
| 3 | g2_22 | linear, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 10M ADA | +4.8M ± 0.3M | -5.4M | +0.8M | +18.8M | 5.5M | 0.81× | 4% |  |
| 4 | g5_16 | linear, skip top 20, min pledge 10k, pledge soft cap 1x; 2.5M ADA | +4.3M ± 0.2M | -3.9M | +0.5M | +16.2M | 5.0M | 0.55× | 6% |  |
| 5 | g6_5 | power^0.5, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 10M ADA | +2.8M ± 0.3M | -6.4M | +0.0M | +14.7M | 6.5M | 0.89× | 0% |  |
| 6 | g1_20 | linear, top 20 at 50%, min pledge 10k, pledge soft cap 1x; 5M ADA | +2.4M ± 0.2M | -8.9M | -4.0M | +20.0M | 8.9M | 0.81× | 10% | decentralisation |
| 7 | g7_12 | power^0.75, skip top 20, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 1M ADA | +2.2M ± 0.2M | -0.5M | +1.1M | +6.0M | 15.3M | 0.49× | 0% |  |
| 8 | g5_6 | linear, cap 5M, 50% to delegators (passthrough), not via top 10, pledge soft cap 1x; 5M ADA | +1.8M ± 0.3M | -6.5M | -1.4M | +13.4M | 7.8M | 0.85× | 0% |  |
| 9 | g1_12 | power^0.75, cap 200M, award cap 2%, skip top 20, min 1M, min 10 delegators, min pledge 10k, gate 25%, 80% to delegators (flat), pledge soft cap 100x; 2.5M ADA | +1.6M ± 0.3M | -2.9M | +1.8M | +5.8M | 15.4M | 0.81× | 0% |  |
| 10 | g8_6 | power^0.75, cap 200M, award cap 2%, skip top 20, min 1M, min 5 delegators, min pledge 10k, gate 25%, 80% to delegators (passthrough), pledge soft cap 100x; 2.5M ADA | +1.4M ± 0.3M | -3.7M | +0.7M | +7.3M | 13.9M | 0.83× | 0% |  |
| 11 | pledge_backed_delegators_half | linear, cap 5M, 50% to delegators (passthrough), pledge soft cap 1x; 5M ADA | +1.1M ± 0.2M | -6.7M | -2.0M | +11.9M | 9.3M | 0.90× | 0% |  |
| 12 | skip_top20_delegators | linear, skip top 20, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | +1.1M ± 0.3M | -8.7M | -1.7M | +13.6M | 8.8M | 0.93× | 0% |  |
| 13 | g10_7 | linear, cap 5M, min 10k, 50% to delegators (passthrough), not via top 10, pledge soft cap 1x; 1M ADA | +1.0M ± 0.2M | -1.3M | +0.2M | +4.3M | 16.9M | 0.67× | 0% |  |
| 14 | pledge_soft_cap_skip20 | linear, skip top 20, pledge soft cap 1x; 5M ADA | +0.7M ± 0.2M | -8.8M | -3.3M | +14.1M | 8.9M | 0.94× | 0% |  |
| 15 | pledge_soft_cap_skip20_min_pledge | linear, skip top 20, min pledge 10k, pledge soft cap 1x; 5M ADA | +0.5M ± 0.2M | -8.9M | -3.5M | +13.9M | 9.0M | 0.95× | 0% |  |
| 20 | paying nothing |  | +0.0M ± 0.0M | +0.0M | +0.0M | +0.0M | 21.2M |  | 0% |  |

- Smallest shortfall in any scenario: `skip_top20_delegators_min_pledge`, never more than 2.2M ADA a year behind the best.
- Best design that needs another hard fork: `pledge_soft_cap_skip20_fee_50k`, +4.8M ADA a year.

## How to read this

- The unpaid world is fitted to chain history and tested on held-out epochs. How people react to money is **assumed**: four response channels, each at low, central and high strength. A result that holds only in `high` is a hope, not a finding.
- Cost and the gain from splitting are exact for a given formula. The other axes are conditional on the response assumptions.
- Pledge comes from accounts linked to a DRep on chain (the funder of its registration, its declared payment address). That misses ADA the DRep holds elsewhere and can count ADA that is not the DRep's. A real programme needs signed declarations.
- A hard cap on voting power is simulated mechanically: delegators of a capped DRep are not modelled as moving away, so its cost in participation is an upper bound.
- Differences smaller than their ± are not differences.
- Only real-world data can measure the responses. `METHODS.md` describes how a programme could be set up to measure them.
