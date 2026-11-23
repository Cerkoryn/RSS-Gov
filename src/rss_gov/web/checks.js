// The exact checks of a rule on today's DReps, run in the browser: a line-by-line port of
// weights/allocate in mechanisms.py and analyse in static.py. No simulation and no
// assumptions about behaviour. tests/test_checks.py runs both on the same world and
// requires the same answers, so change the two together.
const Checks = (() => {
  const NEWCOMER_SPLITS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000];
  const INCUMBENT_SPLITS = [2, 5, 10, 20];
  const INCUMBENT_RANKS = [...Array(20).keys(), 49, 99, 199];
  const sum = (a) => { let t = 0; for (const v of a) t += v; return t; };
  // largest voting power first; equal powers keep their order, as numpy's stable argsort
  const byPower = (power) => [...power.keys()].sort((i, j) => power[j] - power[i] || i - j);

  function eligible(s, r) {
    const n = r.power.length, ok = new Array(n);
    const floor = s.min_share ? s.min_share * sum(r.power) : 0;
    for (let i = 0; i < n; i++) {
      ok[i] = r.activity[i] > 0 && r.activity[i] >= s.activity_gate && r.power[i] >= s.min_power_ada && r.delegators[i] >= s.min_delegators && r.pledge[i] >= (s.min_pledge_ada || 0);
      if (s.min_share && !(r.power[i] >= floor)) ok[i] = false;
    }
    return ok;
  }

  // What a DRep's rank lets it keep: top_weight for the K largest, 1 for the next N; with
  // roll-down, the share of a slot left after the DReps above are expected to vote.
  function ranked(s, r, ok, expected) {
    const keep = ok.map((v) => (v ? 1 : 0));
    if (!(s.k_exclude || s.n_pay)) return keep;
    const order = byPower(r.power);
    for (const i of order.slice(0, s.k_exclude)) keep[i] *= s.top_weight || 0;
    const rest = order.slice(s.k_exclude).filter((i) => ok[i]);
    if (s.roll_down) {
      let above = 0;
      for (const i of rest) { keep[i] = Math.min(Math.max(s.n_pay - above, 0), 1); above += expected[i]; }
    } else if (s.n_pay) {
      for (const i of rest.slice(s.n_pay)) keep[i] = 0;
    }
    return keep;
  }

  // Voting power counted for rewards: at most the cap, and at most leverage x pledge.
  function counted(s, r, i) {
    const cap = s.cap_ada === null || s.cap_ada === undefined ? Infinity : s.cap_ada;
    let size = Math.min(r.power[i], cap);
    if (s.pledge_leverage > 0) size = Math.min(size, s.pledge_leverage * r.pledge[i]);
    return size;
  }

  // With pledge_rate, the round pays at most that yearly rate on the pledge behind paid
  // votes (pledge at most voting power, times vote rate and rank keep); mechanisms.spendable.
  const ROUNDS_PER_YEAR = 73;
  function spendable(s, r, pot) {
    if (!(s.pledge_rate > 0)) return pot;
    const ok = eligible(s, r);
    const keep = ranked(s, r, ok, r.activity.map((a, i) => (ok[i] ? a : 0)));
    let behind = 0;
    for (let i = 0; i < r.power.length; i++) behind += keep[i] * r.activity[i] * Math.min(r.pledge[i], r.power[i]);
    return Math.min(pot, (s.pledge_rate * behind) / ROUNDS_PER_YEAR);
  }

  // Reward weights as [fraction of the DReps' pot, weights]; zero means not paid.
  function parts(s, r, expected) {
    const n = r.power.length, ok = eligible(s, r);
    if (!expected) expected = r.activity.map((a, i) => (ok[i] ? a : 0));
    const keep = ranked(s, r, ok, expected);
    const votes = new Float64Array(n), w = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      votes[i] = keep[i] * r.activity[i] * (1 + s.rationale_bonus * r.rationale[i]);
      const size = s.basis === "delegators" ? r.delegators[i] : counted(s, r, i);
      w[i] = votes[i] * (s.alpha === 0 ? 1 : Math.pow(size, s.alpha));
    }
    return s.equal_share ? [[s.equal_share, votes], [1 - s.equal_share, w]] : [[1, w]];
  }

  function weights(s, r) { const p = parts(s, r); return p[p.length - 1][1]; }

  // Each part splits its fraction of `reps` by weight over its total (one per DRep, or one
  // for all); pay per vote sets the rate unless the pot cannot cover it; caps are not passed on.
  function awards(s, ps, totals, reps, actions) {
    const n = ps[0][1].length, award = new Float64Array(n);
    ps.forEach(([fraction, w], p) => {
      for (let i = 0; i < n; i++) {
        const total = typeof totals[p] === "number" ? totals[p] : totals[p][i];
        let rate = total > 0 ? (fraction * reps) / total : 0;
        if (s.per_vote_ada) rate = Math.min(rate, s.per_vote_ada * actions);
        award[i] += w[i] * rate;
      }
    });
    if (s.max_award_share) for (let i = 0; i < n; i++) award[i] = Math.min(award[i], s.max_award_share * reps);
    return award;
  }

  // One round's pot: [DRep awards, delegator yield per ADA delegated].
  function allocate(s, r, pot) {
    const n = r.power.length;
    const zero = [new Float64Array(n), new Float64Array(n)];
    pot = spendable(s, r, pot);
    if (pot <= 0) return zero;
    const ps = parts(s, r);
    const award = awards(s, ps, ps.map(([, w]) => sum(w)), pot * (1 - s.delegator_share), r.actions ?? 1);
    const total = sum(award);
    if (total <= 0) return zero;
    const yields = new Float64Array(n);
    const delegatorPot = pot * s.delegator_share;
    if (delegatorPot > 0) {
      // not through the K largest DReps (delegator_k_exclude): their part goes to the others
      const skipped = new Set(byPower(r.power).slice(0, s.delegator_k_exclude || 0));
      const paid = [...award.keys()].filter((i) => award[i] > 0 && r.power[i] > 0 && !skipped.has(i));
      if (s.delegator_mode === "flat") {
        const base = sum(paid.map((i) => r.power[i] * r.activity[i]));
        if (base > 0) for (const i of paid) yields[i] = (delegatorPot * r.activity[i]) / base;
      } else if (s.delegator_mode === "per_drep") {
        // a pot per DRep by counted power ** delegator_alpha and vote rate, shared per ADA
        const b = s.delegator_alpha ?? 1;
        const w = paid.map((i) => (b ? Math.pow(counted(s, r, i), b) : counted(s, r, i) > 0 ? 1 : 0) * r.activity[i]);
        const total = sum(w);
        if (total > 0) paid.forEach((i, j) => { yields[i] = (delegatorPot * w[j]) / total / r.power[i]; });
      } else {
        const shared = sum(paid.map((i) => award[i]));
        if (shared > 0) for (const i of paid) yields[i] = (delegatorPot * award[i]) / shared / r.power[i];
      }
    }
    return [award, yields];
  }

  // Share of the pot going to the DReps `rows` and their delegators.
  function take(s, r, pot, rows) {
    const [award, yields] = allocate(s, r, pot);
    return (sum(rows.map((i) => award[i])) + sum(rows.map((i) => yields[i] * r.power[i]))) / pot;
  }
  const range = (from, to) => Array.from({ length: to - from }, (_, k) => from + k);

  // The round with DRep `drop` removed (or nobody) and `copies` identical DReps added.
  function withCopies(r, drop, add, copies) {
    const out = {};
    for (const k of ["power", "activity", "rationale", "delegators", "pledge"]) {
      const kept = drop === null ? [...r[k]] : r[k].filter((_, i) => i !== drop);
      for (let c = 0; c < copies; c++) kept.push(add[k]);
      out[k] = kept;
    }
    out.actions = r.actions;
    return out;
  }

  function newcomerSplit(s, r, pot, t) {
    let best = 0, bestM = 1, single = 0;
    for (const m of NEWCOMER_SPLITS) {
      const each = t.capital / m - t.deposit;
      if (each < Math.max(s.min_power_ada, s.min_delegators * t.delegator_min, s.min_pledge_ada || 0, 1)) break;
      const plus = withCopies(r, null, { power: each, activity: 1, rationale: 1, delegators: Math.floor(each / t.delegator_min), pledge: each }, m);
      const share = take(s, plus, pot, range(r.power.length, r.power.length + m));
      if (m === 1) single = share;
      if (share > best + 1e-12) { best = share; bestM = m; } // in a tie, the fewest identities
    }
    return [best, bestM, single];
  }

  function incumbentSplit(s, r, pot) {
    const order = byPower(r.power);
    let best = [0, null, 1];
    for (const rank of INCUMBENT_RANKS) {
      if (rank >= order.length) break;
      const i = order[rank];
      const whole = take(s, r, pot, [i]);
      for (const m of INCUMBENT_SPLITS) {
        const parts = withCopies(r, i, { power: r.power[i] / m, activity: r.activity[i], rationale: r.rationale[i], delegators: r.delegators[i] / m, pledge: r.pledge[i] / m }, m);
        const n = r.power.length - 1;
        const extra = take(s, parts, pot, range(n, n + m)) - whole;
        if (extra > best[0]) best = [extra, rank + 1, m];
      }
    }
    return best;
  }

  // Delegating accounts that would be paid anything at all.
  function paidDelegators(yields, accounts) {
    let paid = 0, k = 0;
    accounts.per_drep.forEach((rows, d) => {
      for (let j = 0; j < rows; j++, k++) if (yields[d] * accounts.unit[k] > 0) paid += accounts.palette[accounts.count[k]];
    });
    return paid;
  }

  const isPaid = (s) => s.budget_ada > 0 || s.fee_ada > 0; // Scheme.paid

  // What it would take to run the rule on Cardano: Scheme.feasibility() in mechanisms.py.
  function notes(s) {
    if (!isPaid(s)) return [];
    const out = [];
    if (s.rationale_bonus > 0) out.push("An anchor proves a rationale exists, not that it is good.");
    if (s.basis === "delegators") out.push("Accounts are cheap to create: paying by their number invites fake ones.");
    if (s.delegator_share > 0) out.push("Pays every delegating account, however little: one CIP-159 direct deposit each.");
    if (s.pledge_leverage > 0 || s.min_pledge_ada > 0 || s.pledge_rate > 0) out.push("Pledge is not a ledger concept: DReps must declare their accounts.");
    if (s.hard_cap) out.push("Capping voting power changes ratification rules: needs a hard fork.");
    if (s.fee_ada > 0) out.push("Today every governance action deposit is returned: keeping part of it as a fee changes the ledger's rules and needs a hard fork.");
    return out;
  }

  // The facts static.analyse gives for one rule. `accounts` is needed only when the rule
  // pays delegators; without it the delegator facts are null.
  function analyse(s, t, accounts) {
    const r = t;
    const power = s.hard_cap ? r.power.map((v, i) => Math.min(v, s.pledge_leverage * r.pledge[i])) : r.power;
    const row = {
      paid_dreps: 0, max_award: null, top10_award_share: null, power_kept: sum(power) / sum(r.power),
      newcomer_capture: 0, newcomer_extra: 0, newcomer_identities: null, incumbent_extra: 0, incumbent_rank: null,
      incumbent_parts: null, split_gain: 0, paid_delegators: null, fee_share: 0,
    };
    if (!isPaid(s)) return row;
    // Scheme.income: a fee per action is counted at the average pace of closing actions.
    const pot = s.budget_ada / t.epochs + (s.fee_ada || 0) * r.actions;
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
      fee_share: (s.fee_ada || 0) * r.actions / pot,
    });
    if (s.delegator_share > 0 && accounts) row.paid_delegators = paidDelegators(yields, accounts);
    else if (!(s.delegator_share > 0)) row.paid_delegators = 0;
    return row;
  }

  return { weights, allocate, analyse, notes };
})();
if (typeof module !== "undefined") module.exports = Checks;
