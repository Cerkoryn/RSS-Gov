// The exact checks of a rule on today's DReps, run in the browser: a line-by-line port of
// weights/allocate in mechanisms.py and analyse in static.py. No simulation and no
// assumptions about behaviour. tests/test_checks.py runs both on the same world and
// requires the same answers, so change the two together.
const Checks = (() => {
  const NEWCOMER_SPLITS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000];
  const INCUMBENT_SPLITS = [2, 5, 10, 20];
  const INCUMBENT_RANKS = [...Array(20).keys(), 49, 99, 199];
  const sum = (a) => { let t = 0; for (const v of a) t += v; return t; };
  // largest stake first; equal stakes keep their order, as numpy's stable argsort
  const byStake = (stake) => [...stake.keys()].sort((i, j) => stake[j] - stake[i] || i - j);

  function weights(s, r) {
    const n = r.stake.length;
    const ok = new Array(n);
    for (let i = 0; i < n; i++) {
      ok[i] = r.activity[i] > 0 && r.activity[i] >= s.activity_gate && r.stake[i] >= s.min_stake_ada && r.delegators[i] >= s.min_delegators;
    }
    if (s.k_exclude || s.n_pay) {
      const candidates = byStake(r.stake).slice(s.k_exclude).filter((i) => ok[i]);
      const ranked = new Set(s.n_pay ? candidates.slice(0, s.n_pay) : candidates);
      for (let i = 0; i < n; i++) ok[i] = ok[i] && ranked.has(i);
    }
    const cap = s.cap_ada === null || s.cap_ada === undefined ? Infinity : s.cap_ada;
    const w = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      if (!ok[i]) continue;
      let counted = Math.min(r.stake[i], cap);
      if (s.pledge_leverage > 0) counted = Math.min(counted, s.pledge_leverage * r.pledge[i]);
      const base = s.alpha === 0 ? 1 : Math.pow(counted, s.alpha);
      w[i] = base * r.activity[i] * (1 + s.rationale_bonus * r.rationale[i]);
    }
    return w;
  }

  // One round's pot: [DRep awards, delegator yield per ADA delegated].
  function allocate(s, r, pot) {
    const n = r.stake.length;
    const award = new Float64Array(n), yields = new Float64Array(n);
    if (pot <= 0) return [award, yields];
    const w = weights(s, r), total = sum(w);
    if (total <= 0) return [award, yields];
    for (let i = 0; i < n; i++) award[i] = pot * (1 - s.delegator_share) * (w[i] / total);
    const delegatorPot = pot * s.delegator_share;
    if (delegatorPot > 0) {
      const paid = [...w.keys()].filter((i) => w[i] > 0 && r.stake[i] > 0);
      if (s.delegator_mode === "flat") {
        const base = sum(paid.map((i) => r.stake[i] * r.activity[i]));
        if (base > 0) for (const i of paid) yields[i] = (delegatorPot * r.activity[i]) / base;
      } else {
        for (const i of paid) yields[i] = (delegatorPot * (w[i] / total)) / r.stake[i];
      }
    }
    return [award, yields];
  }

  // Share of the pot going to the DReps `rows` and their delegators.
  function take(s, r, pot, rows) {
    const [award, yields] = allocate(s, r, pot);
    return (sum(rows.map((i) => award[i])) + sum(rows.map((i) => yields[i] * r.stake[i]))) / pot;
  }
  const range = (from, to) => Array.from({ length: to - from }, (_, k) => from + k);

  // The round with DRep `drop` removed (or nobody) and `copies` identical DReps added.
  function withCopies(r, drop, add, copies) {
    const out = {};
    for (const k of ["stake", "activity", "rationale", "delegators", "pledge"]) {
      const kept = drop === null ? [...r[k]] : r[k].filter((_, i) => i !== drop);
      for (let c = 0; c < copies; c++) kept.push(add[k]);
      out[k] = kept;
    }
    return out;
  }

  function newcomerSplit(s, r, pot, t) {
    let best = 0, bestM = 1, single = 0;
    for (const m of NEWCOMER_SPLITS) {
      const each = t.capital / m - t.deposit;
      if (each < Math.max(s.min_stake_ada, s.min_delegators * t.delegator_min, 1)) break;
      const plus = withCopies(r, null, { stake: each, activity: 1, rationale: 1, delegators: Math.floor(each / t.delegator_min), pledge: each }, m);
      const share = take(s, plus, pot, range(r.stake.length, r.stake.length + m));
      if (m === 1) single = share;
      if (share > best) { best = share; bestM = m; }
    }
    return [best, bestM, single];
  }

  function incumbentSplit(s, r, pot) {
    const order = byStake(r.stake);
    let best = [0, null, 1];
    for (const rank of INCUMBENT_RANKS) {
      if (rank >= order.length) break;
      const i = order[rank];
      const whole = take(s, r, pot, [i]);
      for (const m of INCUMBENT_SPLITS) {
        const parts = withCopies(r, i, { stake: r.stake[i] / m, activity: r.activity[i], rationale: r.rationale[i], delegators: r.delegators[i] / m, pledge: r.pledge[i] / m }, m);
        const n = r.stake.length - 1;
        const extra = take(s, parts, pot, range(n, n + m)) - whole;
        if (extra > best[0]) best = [extra, rank + 1, m];
      }
    }
    return best;
  }

  // Delegating accounts that would have a claim, and the share of them under the minimum payout.
  function claims(yields, t, accounts) {
    let claimants = 0, dust = 0, k = 0;
    accounts.per_drep.forEach((rows, d) => {
      for (let j = 0; j < rows; j++, k++) {
        const claim = yields[d] * accounts.unit[k] * t.epochs;
        if (claim > 0) {
          const holders = accounts.palette[accounts.count[k]];
          claimants += holders;
          if (claim < t.min_payout) dust += holders;
        }
      }
    });
    return [claimants, claimants ? dust / claimants : null];
  }

  // What it would take to run the rule on Cardano: Scheme.feasibility() in mechanisms.py.
  function notes(s) {
    if (!(s.budget_ada > 0)) return [];
    const out = [];
    if (s.rationale_bonus > 0) out.push("An anchor proves a rationale exists, not that it is good.");
    if (s.delegator_share > 0) out.push("Many small delegator claims: needs a claim contract or minimum payout.");
    if (s.pledge_leverage > 0) out.push("Own stake is not a ledger concept: DReps must declare their accounts.");
    if (s.hard_cap) out.push("Capping voting power changes ratification rules: needs a hard fork.");
    return out;
  }

  // The facts static.analyse gives for one rule. `accounts` is needed only when the rule
  // pays delegators; without it the delegator facts are null.
  function analyse(s, t, accounts) {
    const r = t;
    const power = s.hard_cap ? r.stake.map((v, i) => Math.min(v, s.pledge_leverage * r.pledge[i])) : r.stake;
    const row = {
      paid_dreps: 0, max_award: null, top10_award_share: null, power_kept: sum(power) / sum(r.stake),
      newcomer_capture: 0, newcomer_extra: 0, newcomer_identities: null, incumbent_extra: 0, incumbent_rank: null,
      incumbent_parts: null, split_gain: 0, delegator_claimants: null, delegator_dust_share: null,
    };
    if (!(s.budget_ada > 0)) return row;
    const pot = s.budget_ada / t.epochs;
    const [award, yields] = allocate(s, r, pot);
    const paid = [...award].filter((v) => v > 0);
    const [best, identities, single] = newcomerSplit(s, r, pot, t);
    const [extra, rank, parts] = incumbentSplit(s, r, pot);
    Object.assign(row, {
      paid_dreps: paid.length,
      max_award: paid.length ? Math.max(...paid) : 0,
      top10_award_share: sum(t.top10.map((i) => award[i])) / Math.max(sum(award), 1e-9),
      newcomer_capture: best, newcomer_identities: identities, newcomer_extra: best - single,
      incumbent_extra: extra, incumbent_rank: rank, incumbent_parts: parts,
      split_gain: Math.max(best - single, extra),
    });
    if (s.delegator_share > 0 && accounts) [row.delegator_claimants, row.delegator_dust_share] = claims(yields, t, accounts);
    else if (!(s.delegator_share > 0)) row.delegator_claimants = 0;
    return row;
  }

  return { weights, allocate, analyse, notes };
})();
if (typeof module !== "undefined") module.exports = Checks;
