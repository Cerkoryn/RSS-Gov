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
| pledge_soft_cap | +2.7 ± 0.1 ▲ | -1.2 ± 0.3 ▽ | -0.00 ± 0.00 | 10.1M | 0% |
| pledge_hard_cap | -19.3 ± 0.2 ▼ | -11.9 ± 0.3 ▼ | +2.52 ± 0.05 ▲ | 10.1M | 0% |
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
| pledge_soft_cap_skip20 | +0.6 ± 0.1 | +1.6 ± 0.2 △ | +0.45 ± 0.01 △ | 10.1M | 3% |
| pledge_soft_cap_skip10 | +0.7 ± 0.1 △ | +1.3 ± 0.2 △ | +0.32 ± 0.01 △ | 10.1M | 3% |
| pledge_soft_cap_capped | +1.6 ± 0.1 △ | +0.1 ± 0.3 | +0.31 ± 0.00 △ | 10.1M | 0% |
| pledge_backed_delegators | +2.2 ± 0.1 △ | +3.9 ± 0.3 ▲ | +0.30 ± 0.01 △ | 10.1M | 0% |
| skip_top20_delegators | +3.6 ± 0.2 ▲ | +5.4 ± 0.3 ▲ | +0.08 ± 0.01 △ | 10.1M | 34% |
| haircut_top20_delegators | +2.1 ± 0.1 ▲ | -0.1 ± 0.3 | +0.15 ± 0.01 △ | 10.1M | 0% |
| small_drep_delegators | +2.7 ± 0.1 ▲ | +3.8 ± 0.3 ▲ | +0.13 ± 0.01 △ | 10.1M | 9% |
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
| pledge_soft_cap | +2.1 | +0.0 | -0.0 | +0.0 | +2.7 |
| pledge_hard_cap | -20.3 | -21.6 | -21.1 | -21.1 | -19.3 |
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
| pledge_soft_cap_skip20 | +0.4 | +0.0 | -0.0 | +0.0 | +0.6 |
| pledge_soft_cap_skip10 | +0.5 | +0.0 | -0.0 | +0.0 | +0.7 |
| pledge_soft_cap_capped | +1.2 | +0.0 | -0.0 | +0.0 | +1.6 |
| pledge_backed_delegators | +0.8 | +0.7 | -0.1 | +0.0 | +2.2 |
| skip_top20_delegators | +0.3 | +3.3 | +0.0 | +0.0 | +3.6 |
| haircut_top20_delegators | +0.7 | +1.3 | -0.0 | +0.0 | +2.1 |
| small_drep_delegators | +1.3 | +0.9 | -0.0 | +0.0 | +2.7 |
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
| pledge_soft_cap | +0.0 | +0.0 | -0.8 | -0.0 | -1.2 |
| pledge_hard_cap | -13.0 | -12.9 | -14.1 | -10.0 | -11.9 |
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
| pledge_soft_cap_skip20 | +0.2 | +0.0 | +0.8 | +0.2 | +1.6 |
| pledge_soft_cap_skip10 | +0.3 | +0.0 | +0.7 | +0.1 | +1.3 |
| pledge_soft_cap_capped | +0.0 | +0.0 | -0.2 | +0.2 | +0.1 |
| pledge_backed_delegators | +0.1 | +3.3 | -0.0 | +0.1 | +3.9 |
| skip_top20_delegators | +0.2 | +4.2 | +0.4 | +0.0 | +5.4 |
| haircut_top20_delegators | +0.1 | -0.5 | +0.3 | +0.0 | -0.1 |
| small_drep_delegators | +0.0 | +3.2 | -0.1 | +0.1 | +3.8 |
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
| pledge_soft_cap | +0.00 | +0.00 | -0.00 | +0.00 | -0.00 |
| pledge_hard_cap | +3.44 | +3.51 | +2.93 | +2.95 | +2.52 |
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
| pledge_soft_cap_skip20 | +0.00 | +0.00 | +0.00 | +0.38 | +0.45 |
| pledge_soft_cap_skip10 | +0.00 | +0.00 | +0.01 | +0.24 | +0.32 |
| pledge_soft_cap_capped | +0.00 | +0.00 | +0.00 | +0.27 | +0.31 |
| pledge_backed_delegators | +0.00 | +0.02 | +0.00 | +0.20 | +0.30 |
| skip_top20_delegators | +0.00 | -0.13 | -0.00 | +0.13 | +0.08 |
| haircut_top20_delegators | +0.00 | -0.05 | +0.00 | +0.17 | +0.15 |
| small_drep_delegators | +0.00 | -0.03 | -0.00 | +0.15 | +0.13 |
| delegators_not_top20 | -0.00 | -0.05 | -0.01 | +0.00 | -0.06 |
| top100_delegators_not_top20 | -0.00 | -0.06 | -0.01 | +0.00 | -0.06 |

### Variations of named designs

Named designs with a setting changed, `central` scenario; compare each with its named design in the scorecard. The response to a reward is assumed to grow with its logarithm, so a bigger budget buys less than proportionally more.

| scheme | varies | cost a year | cost ÷ treasury | Participation | Decentralisation | ADA a year per point of participation |
|---|---|---|---|---|---|---|
| capped_1m | `capped`: 1M ADA | 2.0M | 0.15% | +3.1 ± 0.1 | -0.5 ± 0.1 | 644,895 |
| capped_2m5 | `capped`: 2.5M ADA | 5.1M | 0.36% | +4.0 ± 0.1 | -0.5 ± 0.1 | 1,278,335 |
| capped_10m | `capped`: 10M ADA | 20.3M | 1.45% | +5.0 ± 0.1 | -0.5 ± 0.2 | 4,047,060 |
| pledge_backed_delegators_2x | `pledge_backed_delegators`: pledge soft cap 2× | 10.1M | 0.73% | +2.1 ± 0.1 | +4.4 ± 0.3 | 4,721,071 |
| pledge_backed_delegators_5x | `pledge_backed_delegators`: pledge soft cap 5× | 10.1M | 0.73% | +2.3 ± 0.1 | +4.5 ± 0.3 | 4,469,568 |
| pledge_backed_delegators_uncapped | `pledge_backed_delegators`: no cap | 10.1M | 0.73% | +2.3 ± 0.1 | +3.3 ± 0.3 | 4,398,134 |
| pledge_backed_delegators_half | `pledge_backed_delegators`: 50% to delegators | 10.1M | 0.73% | +2.1 ± 0.1 | +3.0 ± 0.3 | 4,792,074 |
| skip_top10_delegators | `skip_top20_delegators`: skip 10 | 10.1M | 0.73% | +2.7 ± 0.1 | +1.9 ± 0.3 | 3,745,662 |
| delegators_not_top10 | `delegators_not_top20`: delegators not via top 10 | 10.1M | 0.73% | +4.9 ± 0.1 | -1.6 ± 0.2 | 2,088,185 |
| delegators_not_top20_pledge | `delegators_not_top20`: pledge soft cap 1000× | 10.1M | 0.73% | +3.6 ± 0.1 | +0.8 ± 0.3 | 2,838,508 |
| skip_top20_delegators_min_pledge | `skip_top20_delegators`: ≥10k ADA pledge | 10.1M | 0.73% | +7.4 ± 0.2 | +6.6 ± 0.3 | 1,368,041 |
| top100_delegators_not_top20_min_pledge | `top100_delegators_not_top20`: ≥10k ADA pledge | 10.1M | 0.73% | +6.2 ± 0.2 | +2.3 ± 0.2 | 1,627,879 |
| pledge_soft_cap_skip20_min_pledge | `pledge_soft_cap_skip20`: ≥10k ADA pledge | 10.1M | 0.73% | +0.5 ± 0.1 | +1.5 ± 0.2 | 20,241,118 |
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
| pledge_soft_cap | +2.7 | +2.6 | +2.3 | +1.5 |
| pledge_hard_cap | -19.3 | -19.3 | -19.5 | -19.9 |
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
| pledge_soft_cap_skip20 | +0.6 | +0.5 | +0.4 | +0.2 |
| pledge_soft_cap_skip10 | +0.7 | +0.7 | +0.5 | +0.3 |
| pledge_soft_cap_capped | +1.6 | +1.6 | +1.3 | +0.6 |
| pledge_backed_delegators | +2.2 | +1.9 | +1.1 | +0.3 |
| skip_top20_delegators | +3.6 | +3.0 | +1.6 | +0.4 |
| haircut_top20_delegators | +2.1 | +1.8 | +1.1 | +0.3 |
| small_drep_delegators | +2.7 | +2.4 | +1.4 | +0.5 |
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
| pledge_soft_cap | -1.2 | -1.1 | -1.0 | -1.0 |
| pledge_hard_cap | -11.9 | -11.8 | -11.7 | -11.3 |
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
| pledge_soft_cap_skip20 | +1.6 | +1.4 | +1.1 | +0.5 |
| pledge_soft_cap_skip10 | +1.3 | +1.0 | +0.9 | +0.5 |
| pledge_soft_cap_capped | +0.1 | +0.1 | -0.2 | +0.2 |
| pledge_backed_delegators | +3.9 | +3.3 | +1.7 | +0.2 |
| skip_top20_delegators | +5.4 | +4.4 | +2.2 | +0.5 |
| haircut_top20_delegators | -0.1 | +0.2 | +0.0 | +0.2 |
| small_drep_delegators | +3.8 | +3.2 | +1.3 | +0.2 |
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
| pledge_soft_cap | -0.00 | +0.00 | +0.00 | +0.00 |
| pledge_hard_cap | +2.52 | +2.51 | +2.58 | +2.69 |
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
| pledge_soft_cap_skip20 | +0.45 | +0.44 | +0.39 | +0.07 |
| pledge_soft_cap_skip10 | +0.32 | +0.31 | +0.28 | +0.07 |
| pledge_soft_cap_capped | +0.31 | +0.30 | +0.27 | +0.04 |
| pledge_backed_delegators | +0.30 | +0.25 | +0.08 | +0.03 |
| skip_top20_delegators | +0.08 | +0.09 | +0.06 | -0.01 |
| haircut_top20_delegators | +0.15 | +0.14 | +0.09 | -0.00 |
| small_drep_delegators | +0.13 | +0.11 | +0.04 | +0.01 |
| delegators_not_top20 | -0.06 | -0.05 | -0.03 | -0.01 |
| top100_delegators_not_top20 | -0.06 | -0.05 | -0.03 | -0.01 |

## Search over the scheme family

250 designs simulated over 10 generations, with the budget as one of the searched parameters. The finalists were re-run on 100 seeds the search never saw; all numbers here are from those seeds, averaged over `low`, `central`, `high`. Marks: ▲ better than unpaid in every scenario, ▼ worse in at least one.

- 25 of 64 finalists are unbeaten: no other design is at least as good on all 5 axes.
- Guardrail: no axis other than cost and Sybil resistance may be worse than unpaid in any scenario; those two are exact trade-offs, weighed on the front like the others. **35 of 64 finalists stay inside it.**
- Hypervolume of the front (progress measure, in the units of `axes.scale`): **0.03429** (95% 0.03363–0.03506); unpaid alone 0.00455. The search adds **0.00611** over the named schemes (95% 0.00590–0.00639).

### Shortlist: inside every guardrail and unbeaten

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| skip_top20_delegators | linear, skip top 20, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | +4.1 ± 0.1 ▲ | +6.1 ± 0.2 ▲ | +0.13 ± 0.01 | 10.1M | 34% |
| small_drep_delegators | power^0.5, min 100k, min 10 delegators, 80% to delegators (passthrough), pledge soft cap 1x; 5M ADA | +3.0 ± 0.1 ▲ | +4.5 ± 0.2 ▲ | +0.18 ± 0.01 | 10.1M | 9% |
| pledge_backed_delegators_5x | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 5x; 5M ADA | +2.6 ± 0.1 ▲ | +5.2 ± 0.2 ▲ | +0.11 ± 0.01 | 10.1M | 0% |
| pledge_backed_delegators_half | linear, cap 5M, 50% to delegators (passthrough), pledge soft cap 1x; 5M ADA | +2.4 ± 0.1 ▲ | +3.7 ± 0.2 ▲ | +0.55 ± 0.01 | 10.1M | 0% |
| g3_19 | linear, skip top 20, min 100k, min pledge 10k, gate 70%, 80% to delegators (flat), pledge soft cap 2x; 5M ADA | +7.9 ± 0.2 ▲ | +6.3 ± 0.3 ▲ | +0.10 ± 0.01 | 10.1M | 0% |
| g6_19 | linear, cap 5M, 80% to delegators (passthrough), not via top 20, pledge soft cap 5x; 10M ADA | +5.6 ± 0.1 ▲ | +12.4 ± 0.3 ▲ | +0.08 ± 0.01 | 20.3M | 3% |
| g7_7 | linear, cap 5M, gate 50%, 80% to delegators (passthrough), pledge soft cap 1x; 5M ADA | +2.9 ± 0.1 ▲ | +4.8 ± 0.3 ▲ | +0.36 ± 0.01 | 10.1M | 0% |
| g7_8 | linear, cap 5M, award cap 2%, 50% to delegators (passthrough), pledge soft cap 1x; 5M ADA | +2.3 ± 0.1 ▲ | +4.7 ± 0.2 ▲ | +0.57 ± 0.01 | 10.1M | 13% |
| g2_22 | linear, cap 5M, 80% to delegators (passthrough), pledge soft cap 5x; 10M ADA | +4.1 ± 0.1 ▲ | +8.6 ± 0.3 ▲ | +0.11 ± 0.01 | 20.3M | 0% |
| g10_4 | power^0.5, award cap 1%, skip top 20, pay 400 (roll-down), min 0.20% of power, min 25 delegators, gate 75%, rationale +100%, 25% to delegators (passthrough); 2.5M ADA | +2.5 ± 0.1 ▲ | +3.6 ± 0.2 ▲ | -0.06 ± 0.01 | 4.9M | 27% |
| capped_1m | linear, cap 20M; 1M ADA | +3.3 ± 0.1 ▲ | -0.4 ± 0.2 | -0.00 ± 0.00 | 2.0M | 30% |
| capped_2m5 | linear, cap 20M; 2.5M ADA | +4.0 ± 0.1 ▲ | -0.4 ± 0.2 | -0.00 ± 0.00 | 5.1M | 30% |
| g8_0 | linear, 80% to delegators (passthrough), pledge soft cap 5x; 10M ADA | +4.7 ± 0.1 ▲ | +1.4 ± 0.3 | +0.65 ± 0.01 | 20.3M | 0% |
| g4_20 | linear, cap 200M, min 1M, min 50 delegators, min pledge 10k, rationale +200%, 80% to delegators (passthrough), not via top 20, pledge soft cap 100x; 2.5M ADA | +5.7 ± 0.2 ▲ | +0.6 ± 0.3 | -0.14 ± 0.01 | 5.1M | 18% |
| g8_16 | linear, 25% equal, award cap 2%, skip top 10, min 1M, 25% to delegators (flat), pledge soft cap 10000x; 1M ADA | +1.6 ± 0.1 | +1.2 ± 0.2 | -0.01 ± 0.00 | 2.0M | 15% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| skip_top20_delegators | +1.8 | +3.6 | +6.9 | +2.5 | +5.6 | +10.0 |
| small_drep_delegators | +1.3 | +2.7 | +5.1 | +1.7 | +4.0 | +7.7 |
| pledge_backed_delegators_5x | +1.1 | +2.3 | +4.4 | +2.1 | +4.4 | +9.2 |
| pledge_backed_delegators_half | +1.0 | +2.1 | +4.1 | +1.4 | +3.3 | +6.3 |
| g3_19 | +4.0 | +7.4 | +12.3 | +4.1 | +6.7 | +8.0 |
| g6_19 | +2.6 | +4.9 | +9.4 | +5.6 | +11.3 | +20.3 |
| g7_7 | +1.3 | +2.6 | +4.9 | +2.3 | +4.4 | +7.9 |
| g7_8 | +1.0 | +2.0 | +3.8 | +1.6 | +3.8 | +8.8 |
| g2_22 | +1.8 | +3.6 | +6.9 | +4.1 | +7.9 | +13.9 |
| g10_4 | +1.3 | +2.3 | +3.9 | +1.2 | +3.2 | +6.6 |
| capped_1m | +1.8 | +3.1 | +4.8 | -0.3 | -0.3 | -0.5 |
| capped_2m5 | +2.4 | +3.9 | +5.7 | -0.2 | -0.4 | -0.5 |
| g8_0 | +1.9 | +4.1 | +8.1 | +2.4 | +2.4 | -0.5 |
| g4_20 | +2.6 | +5.2 | +9.4 | +0.6 | +1.2 | +0.1 |
| g8_16 | +0.7 | +1.5 | +2.6 | +0.7 | +1.0 | +2.0 |

### Accepting a cost in decentralisation

8 unbeaten among the finalists that give up exactly this.

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| g5_11 | power^0.5, 50% equal, cap 2M, award cap 5%, top 20 at 50%, min 10k, min 0.20% of power, min 25 delegators, min pledge 100k, gate 75%, rationale +200%, 80% to delegators (passthrough), pledge soft cap 10000x; 2.5M ADA | +4.7 ± 0.2 ▲ | -2.4 ± 0.3 ▼ | -0.14 ± 0.01 | 5.0M | 0% |
| proportional | linear; 5M ADA | +4.4 ± 0.1 ▲ | -2.2 ± 0.2 ▼ | -0.01 ± 0.00 | 10.1M | 0% |
| proportional_gate_half_budget | linear, gate 50%; 2.5M ADA | +4.0 ± 0.1 ▲ | -2.1 ± 0.2 ▼ | -0.01 ± 0.00 | 5.1M | 0% |
| pledge_soft_cap | linear, pledge soft cap 1000x; 5M ADA | +2.7 ± 0.1 ▲ | -1.3 ± 0.2 ▼ | -0.00 ± 0.00 | 10.1M | 0% |
| g9_22 | linear, cap 200M, award cap 1%, top 20 at 50%, min 1M, min 0.50% of power, rationale +200%; 1M ADA | +3.1 ± 0.1 ▲ | -1.2 ± 0.2 ▼ | -0.00 ± 0.00 | 1.9M | 9% |
| delegators_not_top10 | linear, 50% to delegators (flat), not via top 10; 5M ADA | +5.0 ± 0.1 ▲ | -1.6 ± 0.2 ▼ | -0.05 ± 0.00 | 10.1M | 12% |
| delegator_passthrough_sqrt | power^0.5, 80% to delegators (passthrough); 5M ADA | +4.3 ± 0.1 ▲ | -0.7 ± 0.2 ▼ | -0.03 ± 0.00 | 10.1M | 15% |
| delegators_not_top20 | linear, 50% to delegators (flat), not via top 20; 5M ADA | +5.4 ± 0.1 ▲ | -0.6 ± 0.2 ▼ | -0.07 ± 0.01 | 10.1M | 19% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| g5_11 | +2.8 | +4.3 | +7.1 | -0.5 | -1.7 | -4.9 |
| proportional | +2.8 | +4.4 | +5.9 | -1.1 | -2.1 | -3.3 |
| proportional_gate_half_budget | +2.5 | +4.0 | +5.4 | -1.1 | -2.0 | -3.4 |
| pledge_soft_cap | +1.5 | +2.7 | +3.9 | -0.4 | -1.0 | -2.6 |
| g9_22 | +1.7 | +3.0 | +4.5 | -0.7 | -1.1 | -1.8 |
| delegators_not_top10 | +3.0 | +4.9 | +7.3 | -0.8 | -1.4 | -2.5 |
| delegator_passthrough_sqrt | +2.3 | +4.0 | +6.6 | -0.4 | -0.6 | -1.1 |
| delegators_not_top20 | +3.1 | +5.2 | +7.9 | -0.3 | -0.6 | -1.0 |

### Accepting a cost in skin in the game

5 unbeaten among the finalists that give up exactly this.

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| top100_delegators_not_top20_min_pledge | linear, pay 100, min pledge 10k, 50% to delegators (flat), not via top 20; 5M ADA | +7.3 ± 0.2 ▲ | +1.5 ± 0.2 ▲ | -0.17 ± 0.01 ▼ | 10.1M | 16% |
| g1_12 | linear, skip top 20, min 1M, min 10 delegators, min pledge 10k, rationale +200%, 80% to delegators (passthrough), not via top 20, pledge soft cap 100x; 10M ADA | +9.6 ± 0.2 ▲ | +6.3 ± 0.3 ▲ | -0.25 ± 0.01 ▼ | 20.3M | 20% |
| g9_5 | linear, 25% equal, skip top 20, min 1M, min pledge 10k, rationale +100%, 80% to delegators (passthrough), pledge soft cap 100x; 10M ADA | +8.7 ± 0.2 ▲ | +8.7 ± 0.3 ▲ | -0.20 ± 0.01 ▼ | 20.3M | 24% |
| g0_11 | power^0.75, cap 200M, award cap 2%, skip top 20, min 1M, min 5 delegators, min pledge 10k, gate 25%, 80% to delegators (flat), pledge soft cap 100x; 2.5M ADA | +4.5 ± 0.2 ▲ | +3.9 ± 0.2 ▲ | -0.15 ± 0.01 ▼ | 5.1M | 31% |
| g1_1 | power^0.75, cap 200M, award cap 2%, skip top 20, min 1M, min 50 delegators, min pledge 10k, gate 25%, 80% to delegators (flat), pledge soft cap 100x; 2.5M ADA | +6.8 ± 0.3 ▲ | +1.9 ± 0.3 | -0.23 ± 0.01 ▼ | 5.0M | 36% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| top100_delegators_not_top20_min_pledge | +3.0 | +6.1 | +12.7 | +1.1 | +2.2 | +1.3 |
| g1_12 | +5.3 | +9.0 | +14.3 | +5.6 | +7.4 | +5.9 |
| g9_5 | +4.8 | +8.3 | +12.9 | +6.4 | +9.3 | +10.5 |
| g0_11 | +1.9 | +3.9 | +7.7 | +1.7 | +4.0 | +6.1 |
| g1_1 | +2.5 | +5.2 | +12.7 | +1.8 | +3.6 | +0.2 |

### Accepting a cost in decentralisation, skin in the game

2 unbeaten among the finalists that give up exactly this.

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| g5_18 | linear, min 1M, min 50 delegators, min pledge 10k, rationale +200%, 80% to delegators (passthrough), not via top 20, pledge soft cap 100x; 10M ADA | +19.3 ± 0.4 ▲ | -2.1 ± 0.3 ▼ | -0.36 ± 0.01 ▼ | 20.0M | 18% |
| g9_8 | linear, 25% equal, skip top 20, min 10k, min 50 delegators, min pledge 10k, rationale +200%, 80% to delegators (passthrough), not via top 20, pledge soft cap 100x; 10M ADA | +12.9 ± 0.3 ▲ | +1.8 ± 0.3 ▼ | -0.36 ± 0.01 ▼ | 20.3M | 30% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| g5_18 | +7.5 | +18.2 | +32.2 | +3.1 | -2.9 | -6.4 |
| g9_8 | +5.8 | +11.4 | +21.4 | +5.4 | +2.6 | -2.6 |

### Accepting a cost in participation, decentralisation (needs another hard fork)

1 unbeaten among the finalists that give up exactly this.

| scheme | rule | Participation | Decentralisation | Skin in the game | Reward sustainability | Sybil resistance |
|---|---|---|---|---|---|---|
| pledge_hard_cap | linear, pledge hard cap 1000x; 5M ADA | -19.2 ± 0.1 ▼ | -12.3 ± 0.3 ▼ | +2.56 ± 0.04 ▲ | 10.1M | 0% |

By response scenario:

| scheme | Participation (low) | Participation (central) | Participation (high) | Decentralisation (low) | Decentralisation (central) | Decentralisation (high) |
|---|---|---|---|---|---|---|
| pledge_hard_cap | -20.3 | -19.3 | -17.9 | -12.8 | -11.8 | -12.3 |

### Where the named schemes end up

| scheme | gives up | unbeaten among designs giving up the same |
|---|---|---|
| skip_top20_delegators | nothing | yes |
| small_drep_delegators | nothing | yes |
| pledge_backed_delegators_5x | nothing | yes |
| pledge_backed_delegators_half | nothing | yes |
| capped_1m | nothing | yes |
| capped_2m5 | nothing | yes |
| pledge_hard_cap | participation, decentralisation | yes |
| pledge_backed_delegators_2x | nothing | no |
| pledge_backed_delegators_uncapped | nothing | no |
| skip_top10_delegators | nothing | no |
| skip_top20_delegators_min_pledge | nothing | no |
| top100_delegators_not_top20_min_pledge | skin in the game | yes |
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
| pledge_soft_cap | decentralisation | yes |
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
| haircut_top20_delegators | nothing | no |
| delegators_not_top20 | decentralisation | yes |
| top100_delegators_not_top20 | decentralisation | no |
| capped_10m | nothing | no |
| delegators_not_top10 | decentralisation | yes |
| delegators_not_top20_pledge | nothing | no |
| exclude_k_pay_n | nothing | yes |
| pledge_soft_cap_skip20 | nothing | no |
| pledge_soft_cap_skip10 | nothing | no |
| pledge_soft_cap_capped | nothing | no |
| pledge_soft_cap_skip20_min_pledge | nothing | no |

The guardrails are judgement calls in `config.yaml`. Moving one and running `rss-gov report` regroups these tables without simulating anything.

![front](figures/front.png)

## How to read this

- The unpaid world is fitted to chain history and tested on held-out epochs. How people react to money is **assumed**: four response channels, each at low, central and high strength. A result that holds only in `high` is a hope, not a finding.
- Cost and the gain from splitting are exact for a given formula. The other axes are conditional on the response assumptions.
- Pledge comes from accounts linked to a DRep on chain (the funder of its registration, its declared payment address). That misses ADA the DRep holds elsewhere and can count ADA that is not the DRep's. A real programme needs signed declarations.
- A hard cap on voting power is simulated mechanically: delegators of a capped DRep are not modelled as moving away, so its cost in participation is an upper bound.
- Differences smaller than their ± are not differences.
- Only real-world data can measure the responses. `METHODS.md` describes how a programme could be set up to measure them.
