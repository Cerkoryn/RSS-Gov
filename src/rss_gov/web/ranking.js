// Net benefit in ADA a year, recomputed in the browser when a visitor changes what an
// improvement is worth: a line-by-line port of ranking.py. tests/test_ranking.py runs both
// on the same numbers and requires the same answers, so change the two together.
// A design d is { m: mean change per scenario [gains..., cost], c: covariance of those
// means (upper triangle, row by row), s: share of the budget one actor gains by splitting }.
const Ranking = (() => {
  // what one unit of each column is worth: the gains at k times their value, then cost
  const weights = (d, value, loss, k = 1) => [...value.map((v) => k * v), -(1 + loss * d.s)];

  function score(d, value, loss, k = 1) {
    const g = weights(d, value, loss, k), S = d.m.length;
    const by = d.m.map((row) => row.reduce((t, x, j) => t + x * g[j], 0));
    const flat = [];
    for (let s = 0; s < S; s++) for (const x of g) flat.push(x / S);
    let v = 0, at = 0;
    for (let i = 0; i < flat.length; i++) {
      for (let j = i; j < flat.length; j++) v += (i === j ? 1 : 2) * flat[i] * flat[j] * d.c[at++];
    }
    return { by, score: by.reduce((a, b) => a + b, 0) / S, ci: 1.96 * Math.sqrt(Math.max(v, 0)) };
  }

  // the same random draws every time, so the shares do not flicker as the page redraws
  function draws(n, shake, seed = 1) {
    let a = seed >>> 0;
    const next = () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    return Array.from({ length: n }, () => [0, 0, 0, 0].map(() => 1 - shake + 2 * shake * next()));
  }

  // Every design ranked by net benefit, paying nothing (name null) as a row at zero.
  // behind: the most it falls short of the best design in any one scenario.
  // worthFrom: the share of the stated values at which its gains pay for its cost.
  // first: how often it ranks first when every value moves by up to `shake` either way.
  function table(designs, value, loss, shake, n = 2000) {
    const names = Object.keys(designs);
    const rows = names.map((name) => ({ name, ...score(designs[name], value, loss) }));
    const S = rows.length ? rows[0].by.length : 3;
    rows.push({ name: null, by: new Array(S).fill(0), score: 0, ci: 0 });
    const best = [...Array(S).keys()].map((s) => Math.max(...rows.map((r) => r.by[s])));
    const avg = [...names.map((nm) => designs[nm].m[0].map((_, j) => designs[nm].m.reduce((t, row) => t + row[j], 0) / S)), [0, 0, 0, 0]];
    const split = [...names.map((nm) => designs[nm].s), 0];
    const first = new Array(rows.length).fill(0);
    for (const f of draws(n, shake)) {
      let top = 0, topScore = -Infinity;
      avg.forEach((a, i) => {
        const v = a[0] * value[0] * f[0] + a[1] * value[1] * f[1] + a[2] * value[2] * f[2] - a[3] * (1 + loss * split[i] * f[3]);
        if (v > topScore) { topScore = v; top = i; }
      });
      first[top]++;
    }
    rows.forEach((r, i) => {
      const a = avg[i], gains = a[0] * value[0] + a[1] * value[1] + a[2] * value[2];
      r.behind = Math.max(...r.by.map((v, s) => best[s] - v));
      r.worthFrom = r.name === null ? null : gains > 0 ? (a[3] * (1 + loss * split[i])) / gains : Infinity;
      r.first = first[i] / n;
    });
    return rows.sort((p, q) => q.score - p.score);
  }

  return { score, table };
})();
if (typeof module !== "undefined") module.exports = Ranking;
