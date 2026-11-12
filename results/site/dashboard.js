// The results page. Every number comes from data.js (window.RSS), written by `rss-gov site`.
const hasKind = (k) => D.schemes.some((s) => s.kind === k);
const state = {
  scenario: "central",
  show: { named: true, ladder: false, search: false, proposed: hasKind("proposed") },
  pilot: false, view: "table", selected: null,
  chart: { named: true, search: true, proposed: true, fork: false, sybil: false },
  x: "tau67", y: "participation", lead: D.search && D.search.hypervolume_unpaid ? "combined" : "pair", round: null, allParts: false,
  heat: "participation", focusRow: null,
  cmp: { sort: null, dir: 1, page: 0, per: 25, sig: "" },
  heatv: { sort: null, dir: 1, page: 0, per: 25, sig: "" }, tab: "assumptions",
};
const LIMIT = D.meta.split_limit;
const YEAR = D.meta.epochs_per_year / D.meta.epochs; // programmes per year
// Simulated runs behind a design's numbers: named designs come from the experiment, search
// designs and proposals from the holdout seeds.
const runsOf = (s) => (D.search && (s.kind === "search" || s.kind === "proposed") ? D.search.holdout_seeds : D.meta.seeds);

// ---------- data helpers ----------
function res(s, scen, axis) {
  const r = s.results[scen];
  return r && r[axis] ? r[axis] : null;
}
const val = (s, axis, scen = state.scenario) => (res(s, scen, axis) || [null])[0];
// dir 1 is the natural order: A to Z for names, best first for a measure, fewest given up first.
// Designs with no value sort last either way; ties fall back to the name.
function sortValue(s, key) {
  if (key === "name") return pretty(s.name).toLowerCase();
  if (key === "breaks") return s.breaks === null || s.breaks === undefined ? null : s.breaks ? s.breaks.split(", ").length : 0;
  const v = val(s, key);
  return v === null || v === undefined ? null : AX[key].better === "higher" ? -v : v;
}
function visible() {
  let list = D.schemes.filter((s) => state.show[s.kind]);
  if (state.pilot) list = list.filter((s) => s.pilot);
  if (state.cmp.sort) {
    const key = state.cmp.sort;
    const byName = (p, q) => pretty(p.name).localeCompare(pretty(q.name));
    list = [...list].sort((p, q) => {
      const a = sortValue(p, key), b = sortValue(q, key);
      if (a === null || b === null) return (a === null) - (b === null) || byName(p, q);
      return (a < b ? -1 : a > b ? 1 : 0) * state.cmp.dir || byName(p, q);
    });
  }
  return list;
}
// Long tables show one page at a time. v = { page, per, sig }: a new order or a new set of
// rows goes back to page 1; `focus` names a design whose page to show instead.
function page(list, v, focus) {
  const sig = list.map((s) => s.name).join("|");
  if (sig !== v.sig) { v.sig = sig; v.page = 0; }
  const i = focus ? list.findIndex((s) => s.name === focus) : -1;
  if (i >= 0 && v.per) v.page = Math.floor(i / v.per);
  const pages = v.per ? Math.max(1, Math.ceil(list.length / v.per)) : 1;
  v.page = Math.min(v.page, pages - 1);
  return v.per ? list.slice(v.page * v.per, (v.page + 1) * v.per) : list;
}
const shown = (v, n, total) => (total > n ? `${v.page * v.per + 1}–${v.page * v.per + n} of ${total} designs` : `${total} design${total === 1 ? "" : "s"}`);
// A sortable column heading: the first click gives the natural order, the next reverses it.
function sortHeading(th, label, key, v, onSort, ascending) {
  const on = v.sort === key;
  const b = h("button", { type: "button", className: "th-sort" + (on ? " on" : "") }, th, label);
  h("span", { className: "hint" }, b, on ? sortHint(key, v.dir) : "⇅");
  b.title = on ? `Sorted ${sortHint(key, v.dir)}. Click for ${sortHint(key, -v.dir)}.` : `Sort ${sortHint(key, 1)}`;
  b.addEventListener("click", () => onSort(key, on ? -v.dir : 1));
  if (on) th.setAttribute("aria-sort", (v.dir > 0) === ascending ? "ascending" : "descending");
}
const SORT_LABEL = { name: ["A to Z", "Z to A"], breaks: ["fewest first", "most first"] };
const sortHint = (key, dir = state.cmp.dir) => (SORT_LABEL[key] || ["best first", "worst first"])[dir > 0 ? 0 : 1];
function setSort(key, dir) {
  state.cmp.sort = key || null;
  state.cmp.dir = dir || 1;
  renderAll();
}
// How a design does on one axis: good, good-some, bad, bad-some or flat.
function tone(s, axis) {
  if (axis === "split_gain") return val(s, axis) > LIMIT + 1e-9 ? "bad" : "good";
  if (AX[axis].exact) return "flat";
  return { "▲": "good", "△": "good-some", "▼": "bad", "▽": "bad-some" }[s.marks[axis]] || "flat";
}
const SYM = { good: "▲", "good-some": "△", bad: "▼", "bad-some": "▽", flat: "●" };
function symbol(s, axis, t = tone(s, axis)) {
  if (axis === "split_gain") return t === "good" ? "✓" : "✕";
  if (axis === "annual_cost_ada") return "";
  return SYM[t];
}
function givesUp(breaks) {
  if (breaks === null || breaks === undefined) return null;
  if (breaks === "") return "";
  return breaks.split(", ").map((b) => (b === "sybil resistance" ? "over the Sybil limit" : "worse " + b)).join("; ");
}
const overLimit = (s) => val(s, "split_gain", "central") > LIMIT + 1e-9;

// ---------- opening a design ----------
let lastFocus = null;
function openDesign(name) {
  const s = D.schemes.find((q) => q.name === name);
  if (!s) return;
  state.selected = name;
  if (!state.show[s.kind]) state.show[s.kind] = true;
  if (state.pilot && !s.pilot) state.pilot = false;
  state.chart[s.kind === "ladder" ? "named" : s.kind] = true;
  if (!s.pilot) state.chart.fork = true;
  if (overLimit(s)) state.chart.sybil = true;
  state.focusRow = name;
  try { history.replaceState(null, "", "#design=" + encodeURIComponent(name)); } catch (e) { /* file: URLs */ }
  detail();
  lastFocus = document.activeElement;
  document.body.classList.add("drawer-open");
  $("#drawer").setAttribute("aria-hidden", "false");
  $("#drawer-close").focus({ preventScroll: true });
  $("#detail").scrollTop = 0;
  renderAll();
}
function closeDrawer() {
  document.body.classList.remove("drawer-open");
  $("#drawer").setAttribute("aria-hidden", "true");
  try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* file: URLs */ }
  if (lastFocus && document.contains(lastFocus)) lastFocus.focus({ preventScroll: true });
}

// ---------- hero and the five measures ----------
function hero() {
  const m = D.meta;
  const meta = $("#meta");
  h("span", { className: "badge" }, meta, `Mainnet data to epoch ${m.tip_epoch}`);
  h("span", { className: "badge" }, meta, `${D.schemes.length} designs simulated`);
  const v = h("a", { className: "badge " + (m.validation_passed ? "good" : "bad"), href: "#deeper" }, meta,
    m.validation_passed ? "✓ Model matches mainnet history" : "✕ Model failed a history check");
  v.addEventListener("click", () => setTab("model"));
  if (!m.validation_passed) {
    h("div", { className: "warn" }, $("#banner"), "The model failed at least one check against history. Treat every result as provisional.");
  }
}
function measures() {
  const m = D.meta, t = D.today, b = D.baseline;
  const sim = (v) => `Simulated for the next six months with no rewards: ${v}. Every design is compared with this value.`;
  const cards = {
    participation: ["Mainnet, last " + t.recent_epochs + " epochs", t.participation === null || t.participation === undefined ? "–" : pct(t.participation, 1),
      "of delegated ADA voted on a typical action",
      ["The share of all delegated ADA, always-abstain included, whose DRep voted on a governance action.", `Mainnet average over the ${t.participation_actions} actions that closed in the last ${t.recent_epochs} epochs.`, sim(pct(b.participation, 1))]],
    tau67: ["Mainnet today", num(t.tau67, 0), `DReps hold two thirds of the power`,
      [`The fewer DReps it takes to reach two thirds, the more concentrated power is. There are ${num(t.dreps, 0)} DReps with voting power.`, sim(num(b.tau67, 1) + " DReps")]],
    backing: ["Mainnet today", pct(t.backing, 2), "of voting power is DReps' own ADA",
      ["Skin in the game: DReps who hold their own ADA bear the consequences of what they vote for.", "Own stake is estimated from accounts linked to each DRep on chain, such as the one that funded its registration.", sim(pct(b.backing, 2))]],
    annual_cost_ada: ["Mainnet today", "0 ADA", "paid in governance rewards",
      [m.treasury ? `The treasury holds ${ada(m.treasury)} ADA.` : "", `The named designs pay ${ada(m.budget)} ADA over six months: ${ada(m.budget * YEAR)} ADA a year${m.treasury ? `, ${pct((m.budget * YEAR) / m.treasury, 2)} of the treasury` : ""}.`].filter(Boolean)],
    split_gain: ["Guardrail", `${pct(LIMIT)}`, "of the budget at most",
      ["A Sybil attack is one person posing as many DReps to collect more rewards.", "For each design this is computed exactly on today's DReps: the share of the budget someone gains by splitting into several. Designs above the limit are flagged."]],
  };
  const host = $("#measures");
  for (const a of D.axes) {
    const [when, value, note, more] = cards[a.name] || ["", "", "", []];
    const card = h("div", { className: "measure" }, host);
    const row = h("div", { className: "title-row" }, card);
    h("h3", { className: "m-title" }, row, a.short);
    info(row, [{ value: a.question }, ...more], `About ${a.short}`);
    h("div", { className: "m-when" }, card, when);
    h("div", { className: "m-value" }, card, value);
    h("div", { className: "m-note" }, card, note);
    h("span", { className: "dir" }, card, a.better === "higher" ? "↑ more is better" : "↓ less is better");
  }
}

// ---------- controls ----------
function controls() {
  const kinds = $("#kinds");
  for (const k of ["named", "ladder", "search", "proposed"]) {
    const n = D.schemes.filter((s) => s.kind === k).length;
    if (!n) continue;
    const b = h("button", { className: "toggle", type: "button" }, kinds);
    b.style.setProperty("--kind", KIND[k].color);
    b.dataset.k = k;
    h("span", { className: "dot" }, b);
    b.appendChild(document.createTextNode(KIND[k].plural + " "));
    h("span", { className: "count" }, b, String(n));
    b.addEventListener("click", () => { state.show[k] = !state.show[k]; renderAll(); });
  }
  $("#pilot-only").addEventListener("click", () => { state.pilot = !state.pilot; renderAll(); });
  for (const seg of document.querySelectorAll(".seg.scenario")) {
    seg.setAttribute("role", "group");
    seg.setAttribute("aria-label", "Reaction to rewards");
    for (const s of D.meta.scenarios) {
      const b = h("button", { type: "button", title: SCEN[s] }, seg, SCEN_SHORT[s] || s);
      b.dataset.s = s;
      b.addEventListener("click", () => { state.scenario = s; renderAll(); if (document.body.classList.contains("drawer-open")) detail(); });
    }
  }
  for (const b of $("#view").children) b.addEventListener("click", () => { state.view = b.dataset.v; renderAll(); });
  // sort bar: the same sort as clicking a column header, and the only way on a phone
  const tools = $("#table-tools");
  const sort = h("label", { className: "control-group" }, tools);
  h("span", { className: "label" }, sort, "Sort by");
  const by = h("select", { id: "sort-by" }, sort);
  h("option", { value: "" }, by, "Default order");
  h("option", { value: "name" }, by, "Design name");
  for (const a of D.axes) h("option", { value: a.name }, by, a.short);
  h("option", { value: "breaks" }, by, "Gives up");
  by.addEventListener("change", () => setSort(by.value, 1));
  const dir = h("button", { className: "toggle sort-dir", id: "sort-dir", type: "button" }, tools);
  dir.addEventListener("click", () => setSort(state.cmp.sort, -state.cmp.dir));
  h("span", { className: "small count-note", id: "row-count" }, tools);
}
function pager(host, total, v, redraw, anchor) {
  host.textContent = "";
  if (!total) return;
  const per = v.per, pages = per ? Math.ceil(total / per) : 1;
  const nav = h("nav", { className: "pages", "aria-label": "Pages of designs" }, host);
  const go = (p) => { v.page = p; redraw(); anchor.scrollIntoView({ behavior: "smooth", block: "start" }); };
  const btn = (label, p, opts = {}) => {
    const b = h("button", { type: "button", className: "pg" + (opts.wide ? " wide" : ""), "aria-label": opts.aria || `Page ${p + 1}` }, nav, label);
    if (opts.current) b.setAttribute("aria-current", "page");
    if (p < 0 || p >= pages || opts.current) b.disabled = true;
    else b.addEventListener("click", () => go(p));
  };
  if (pages > 1) {
    btn("‹ Previous", v.page - 1, { wide: true, aria: "Previous page" });
    // first, last and the pages around the current one
    let prev = -1;
    for (let p = 0; p < pages; p++) {
      if (p !== 0 && p !== pages - 1 && Math.abs(p - v.page) > 1) continue;
      if (p - prev > 1) h("span", { className: "gap", "aria-hidden": "true" }, nav, "…");
      btn(String(p + 1), p, { current: p === v.page });
      prev = p;
    }
    btn("Next ›", v.page + 1, { wide: true, aria: "Next page" });
  }
  const size = h("label", { className: "control-group per" }, host);
  h("span", { className: "label" }, size, "Designs per page");
  const sel = h("select", {}, size);
  for (const n of [10, 25, 50, 0]) {
    const o = h("option", { value: String(n) }, sel, n ? String(n) : "All");
    if (n === per) o.selected = true;
  }
  sel.addEventListener("change", () => {
    const first = v.page * (v.per || 0);
    v.per = Number(sel.value);
    v.page = v.per ? Math.floor(first / v.per) : 0;
    redraw();
  });
}
function syncControls() {
  for (const b of $("#kinds").children) b.setAttribute("aria-pressed", !!state.show[b.dataset.k]);
  $("#pilot-only").setAttribute("aria-pressed", state.pilot);
  for (const b of document.querySelectorAll(".seg.scenario button")) b.setAttribute("aria-pressed", b.dataset.s === state.scenario);
  for (const b of $("#view").children) b.setAttribute("aria-pressed", b.dataset.v === state.view);
  const v = state.cmp;
  $("#sort-by").value = v.sort || "";
  const dir = $("#sort-dir");
  dir.hidden = !v.sort;
  if (v.sort) {
    dir.textContent = "⇅ " + sortHint(v.sort, v.dir).replace(/^./, (c) => c.toUpperCase());
    dir.title = "Reverse to " + sortHint(v.sort, -v.dir);
  }
  for (const b of $("#best-legend").querySelectorAll("button[data-k]")) b.setAttribute("aria-pressed", !!state.chart[b.dataset.k]);
  $("#view-table").hidden = state.view !== "table";
  $("#view-chart").hidden = state.view !== "chart";
}

// ---------- comparison table ----------
function compareTable() {
  const host = $("#view-table");
  host.textContent = "";
  const all = visible(), v = state.cmp;
  const list = page(all, v, state.focusRow);
  state.focusRow = null;
  $("#row-count").textContent = shown(v, list.length, all.length);
  pager($("#pager"), all.length, v, () => { compareTable(); scorecard(); }, $("#compare"));
  if (!all.length) { h("p", { className: "empty" }, host, "Nothing to show: switch on a group of designs above."); return; }
  const table = h("table", { className: "compare" }, host);
  const head = h("tr", {}, h("thead", {}, table));
  const sortable = (th, key, label) => sortHeading(th, label, key, v, setSort, key === "name" || key === "breaks" || AX[key].better !== "higher");
  sortable(h("th", {}, head), "name", "Design");
  for (const a of D.axes) sortable(h("th", { className: "num", title: `${a.question}. ${a.better === "higher" ? "More" : "Less"} is better.` }, head), a.name, a.short);
  sortable(h("th", {}, head), "breaks", "Gives up");
  const body = h("tbody", {}, table);
  for (const s of list) {
    const tr = h("tr", { className: "pick" + (s.name === state.selected ? " sel" : "") }, body);
    tr.tabIndex = 0;
    tr.title = describe(s.scheme);
    tr.addEventListener("click", () => openDesign(s.name));
    tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDesign(s.name); } });
    const td = h("td", { className: "design" }, tr);
    const n = h("div", { className: "dname" }, td);
    h("span", { className: "kind", style: `background:${KIND[s.kind].color}` }, n);
    n.appendChild(document.createTextNode(pretty(s.name)));
    if (!s.pilot) h("span", { className: "tag" }, td, "Needs a hard fork");
    for (const a of D.axes) {
      const c = h("td", { className: "num" }, tr);
      c.dataset.label = a.short;
      const v = val(s, a.name);
      const t = tone(s, a.name);
      const cell = h("span", { className: "cell " + t }, c);
      const sym = symbol(s, a.name, t);
      if (sym) h("span", { className: "sym", "aria-hidden": "true" }, cell, sym);
      cell.appendChild(document.createTextNode(a.name === "annual_cost_ada" ? ada(v) + "/yr" : fmt(a.name, v, !a.exact)));
    }
    const vc = h("td", { className: "vcol" }, tr);
    vc.dataset.label = "Gives up";
    const g = givesUp(s.breaks);
    if (g === null) h("span", { className: "verdict gives" }, vc, "–");
    else if (g === "") h("span", { className: "verdict ok" }, vc, "✓ Nothing");
    else h("span", { className: "verdict gives" }, vc, g.charAt(0).toUpperCase() + g.slice(1));
  }
}

// ---------- detail drawer ----------
function sentence(s, axis) {
  const v = val(s, axis);
  const a = AX[axis], base = D.baseline[axis];
  const small = Math.abs(v * a.factor) < a.threshold;
  switch (axis) {
    case "participation":
      return small ? `No clear change: about ${pct(base, 1)} of delegated ADA votes.` : `${pct(base, 1)} → ${pct(base + v, 1)} of delegated ADA votes on a typical action.`;
    case "tau67":
      return small ? `About the same: ${num(base, 0)} DReps hold two thirds of the power.`
        : `${num(base, 1)} → ${num(base + v, 1)} DReps hold two thirds of the power: power is ${v > 0 ? "more spread out" : "more concentrated"}.`;
    case "backing":
      return small ? `No clear change: ${pct(base, 2)} of voting power is the DReps' own ADA.` : `${pct(base, 2)} → ${pct(base + v, 2)} of voting power is the DReps' own ADA.`;
    case "annual_cost_ada":
      return `${ada(v)} ADA a year from the treasury` + (D.meta.treasury ? `, ${pct(v / D.meta.treasury, 2)} of what it holds.` : ".");
    case "split_gain":
      return `One actor posing as many DReps would gain ${pct(v)} of the budget, ${v > LIMIT + 1e-9 ? "over" : "within"} the ${pct(LIMIT)} limit.`;
    default:
      return fmt(axis, v);
  }
}
function detail() {
  const host = $("#detail");
  host.textContent = "";
  const s = D.schemes.find((q) => q.name === state.selected);
  if (!s) return;
  const kind = $("#drawer-kind");
  kind.textContent = "";
  h("span", { className: "dot", style: `display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;background:${KIND[s.kind].color}` }, kind);
  kind.appendChild(document.createTextNode(KIND[s.kind].label));
  h("h2", { id: "detail-title" }, host, pretty(s.name));
  h("p", { className: "desc" }, host, describe(s.scheme));
  const badges = h("div", { className: "meta", style: "margin:10px 0 0" }, host);
  h("span", { className: "badge" }, badges, s.pilot ? "Works on today's Cardano" : "Needs a hard fork");
  const g = givesUp(s.breaks);
  if (g === "") h("span", { className: "badge good" }, badges, "✓ Inside every guardrail");
  else if (g) h("span", { className: "badge bad" }, badges, g.charAt(0).toUpperCase() + g.slice(1));
  if (s.proposal) {
    const p = s.proposal;
    const box = h("div", { style: "margin-top:16px" }, host);
    h("div", { className: "small" }, box, (p.author ? `Proposed by ${p.author}` : "Proposed anonymously") + (p.evaluated ? `, simulated ${date(p.evaluated, false)}` : ""));
    if (p.hypothesis) h("div", { className: "quote" }, box, p.hypothesis);
    h("div", { className: "small" }, box, (p.accepted ? "Offers a trade-off no other design did. " : "Did not add a new trade-off: ") + (p.reason || ""));
  }
  h("h3", { style: "margin-top:22px" }, host, "What it changes");
  h("p", { className: "small", style: "margin:0" }, host, `Compared with paying nothing, ${SCEN[state.scenario].toLowerCase()}.`);
  const ul = h("ul", { className: "effects" }, host);
  for (const a of D.axes) {
    const t = tone(s, a.name);
    const li = h("li", { className: t.startsWith("good") ? "good" : t.startsWith("bad") ? "bad" : "" }, ul);
    h("span", { className: "ico", "aria-hidden": "true" }, li, symbol(s, a.name, t) || "₳");
    const box = h("div", {}, li);
    h("div", { className: "what" }, box, a.short);
    h("div", { className: "say" }, box, sentence(s, a.name));
    if (!a.exact) {
      const r = D.meta.scenarios.map((sc) => `${SCEN_SHORT[sc]} ${fmt(a.name, val(s, a.name, sc))}`).join(" · ");
      h("div", { className: "range" }, box, r + (t.endsWith("some") ? " · depends on the reaction" : ""));
    }
  }

  const more1 = h("details", { className: "more" }, host);
  h("summary", {}, more1, "Numbers for each reaction strength");
  const table = h("table", {}, more1);
  const head = h("tr", {}, h("thead", {}, table));
  h("th", {}, head, "Change from paying nothing");
  for (const sc of D.meta.scenarios) h("th", { className: "num" }, head, SCEN_SHORT[sc]);
  const body = h("tbody", {}, table);
  for (const a of D.axes) {
    const tr = h("tr", {}, body);
    h("td", {}, tr, a.short);
    for (const sc of D.meta.scenarios) {
      const q = res(s, sc, a.name);
      const ci = q && q[1] !== null && !a.exact ? ` ± ${num(q[1] * a.factor, a.digits)}` : "";
      h("td", { className: "num" }, tr, q ? fmt(a.name, q[0], !a.exact) + ci : "–");
    }
  }
  h("p", { className: "small" }, more1, `± is the 95% interval over ${num(runsOf(s), 0)} simulated runs with different random luck.`);

  const f = s.facts;
  const more2 = h("details", { className: "more" }, host);
  h("summary", {}, more2, "Who gets paid, and how easy it is to cheat");
  const dl = h("dl", { className: "facts" }, more2);
  const row = (k, v) => { h("dt", {}, dl, k); h("dd", {}, dl, v); };
  row("DReps paid today", num(f.paid_dreps, 0));
  if (f.max_award !== null) row("Largest award per epoch", ada(f.max_award) + " ADA");
  if (f.top10_award_share !== null) row("Share paid to the 10 largest", pct(f.top10_award_share));
  row(`An outsider with ${ada(D.meta.capital)} ADA could take`, `${pct(f.newcomer_capture)} (as ${num(f.newcomer_identities || 0, 0)} DRep${f.newcomer_identities === 1 ? "" : "s"})`);
  row("…of which from splitting", pct(f.newcomer_extra));
  row("Most an existing DRep gains by splitting", f.incumbent_extra >= 0.005 ? `${pct(f.incumbent_extra)} (rank ${f.incumbent_rank}, into ${f.incumbent_parts})` : "0%");
  row("Voting power kept", pct(f.power_kept));
  if (f.delegator_claimants) row(`Delegator payments under ${D.meta.min_payout} ADA`, pct(f.delegator_dust_share));
  const pay = s.results[state.scenario] && s.results[state.scenario].payments;
  if (pay) row("Payments a year", num(pay * YEAR, 0));

  const more3 = h("details", { className: "more" }, host);
  h("summary", {}, more3, "What it would take to run");
  h("p", { className: "small" }, more3, s.pilot
    ? "It works on today's Cardano: everything it reads is on chain."
    : "It changes how voting power counts, which needs a hard fork.");
  if (s.notes && s.notes.length) { const ul2 = h("ul", { className: "notes" }, more3); for (const n of s.notes) h("li", {}, ul2, n); }
  h("p", { className: "rule" }, more3, "Rule in short: " + s.rule);

  const act = h("div", { className: "actions", style: "margin-top:20px" }, host);
  h("a", { className: "primary", href: "propose.html#from=" + encodeURIComponent(s.name) }, act, "Propose a variation");
  const see = h("button", { className: "ghost", type: "button" }, act, "Show on the chart");
  see.addEventListener("click", () => { closeDrawer(); if (state.lead !== "pair") { state.lead = "pair"; lead(); } $("#best").scrollIntoView({ behavior: "smooth" }); });
}

// ---------- scorecard (chart view) ----------
function markShape(g, x, y, mark, size = 5) {
  const up = mark === "▲" || mark === "△";
  const down = mark === "▼" || mark === "▽";
  const hollow = mark === "△" || mark === "▽";
  const colour = up ? "var(--good)" : down ? "var(--bad)" : "var(--neutral)";
  let shape;
  if (up || down) {
    const s = size * 1.25, d = up ? 1 : -1;
    shape = el("path", { d: `M${x},${y - d * s} L${x + s},${y + d * s * 0.75} L${x - s},${y + d * s * 0.75} Z` }, g);
  } else {
    shape = el("circle", { cx: x, cy: y, r: size - 0.5 }, g);
  }
  shape.setAttribute("stroke-linejoin", "round");
  if (hollow) {
    shape.setAttribute("fill", "var(--surface)");
    shape.setAttribute("stroke", colour);
    shape.setAttribute("stroke-width", 1.75);
  } else {
    shape.setAttribute("fill", colour);
    shape.setAttribute("stroke", "var(--surface)");
    shape.setAttribute("stroke-width", 2);
  }
  return shape;
}
function scoreLegend() {
  const host = $("#score-legend");
  for (const [mark, label] of [["▲", "better under every reaction"], ["△", "better under some"], ["", "no clear difference"], ["▽", "worse under some"], ["▼", "worse under every reaction"]]) {
    const span = h("span", {}, host);
    const svg = el("svg", { width: 14, height: 14 }, span);
    markShape(svg, 7, 7.5, mark, 4.6);
    span.appendChild(document.createTextNode(label));
  }
}
function hbar(x0, x1, y, hgt, r = 4) {
  const dir = x1 >= x0 ? 1 : -1, len = Math.abs(x1 - x0);
  r = Math.min(r, len, hgt / 2);
  const top = y - hgt / 2, bot = y + hgt / 2, end = x1 - dir * r;
  if (len < 0.5) return "";
  return `M${x0},${top} H${end} Q${x1},${top} ${x1},${top + r} V${bot - r} Q${x1},${bot} ${end},${bot} H${x0} Z`;
}
function domainFor(axis, list) {
  const a = AX[axis];
  const vals = [0];
  for (const s of list) {
    const r = res(s, state.scenario, axis);
    if (!r) continue;
    vals.push(r[0]);
    if (!a.exact) {
      if (r[1] !== null) vals.push(r[0] - r[1], r[0] + r[1]);
      for (const sc of D.meta.scenarios) { const q = res(s, sc, axis); if (q) vals.push(q[0]); }
    }
  }
  if (axis === "split_gain") vals.push(LIMIT);
  const scaled = vals.map((v) => v * a.factor);
  let lo = Math.min(...scaled), hi = Math.max(...scaled);
  const pad = (hi - lo) * 0.04 || 1;
  if (lo < 0) lo -= pad;
  if (hi > 0) hi += pad;
  const t = ticks(lo, hi, 3);
  return { lo: Math.min(lo, t[0]), hi: Math.max(hi, t[t.length - 1]), t };
}
function scorecard() {
  const host = $("#scorecard");
  host.textContent = "";
  if (state.view !== "chart") return;
  const all = visible();
  if (!all.length) { h("p", { className: "empty" }, host, "Nothing to show: switch on a group of designs above."); return; }
  const list = page(all, state.cmp);
  const W = host.clientWidth;
  const wide = W >= 940;
  const rowH = 28, top = 46, bottom = 30, gap = 30;
  const labelW = wide ? Math.min(210, W * 0.19) : Math.min(165, W * 0.42);
  const maxChars = Math.floor(labelW / 6.8);
  const height = top + rowH * list.length + bottom;
  const panels = D.axes.map((a) => a.name);
  let svg;
  const pw = wide ? (W - labelW - gap * (panels.length - 1)) / panels.length : W - labelW - 8;
  panels.forEach((axis, i) => {
    if (wide && i === 0) svg = el("svg", { width: W, height, role: "img", "aria-label": "Chart of every design on every measure; the table view has the same numbers" }, host);
    if (!wide) svg = el("svg", { width: W, height, role: "img", "aria-label": `Chart, ${AX[axis].short}`, style: "margin-bottom:18px" }, host);
    const x0 = wide ? labelW + i * (pw + gap) : labelW + 4;
    const showLabels = !wide || i === 0;
    const a = AX[axis];
    const dom = domainFor(axis, all); // one scale across every page
    const x = scale(dom.lo, dom.hi, x0, x0 + pw);
    const g = el("g", {}, svg);
    text(g, x0, 14, a.short, { class: "ink", "font-weight": 650, "font-size": 13 });
    text(g, x0, 30, `${a.change} · ${a.better === "higher" ? "more" : "less"} is better`, { "font-size": 11 });
    list.forEach((s, r) => {
      if (s.name === state.selected) {
        el("rect", { x: showLabels ? 0 : x0 - 6, y: top + r * rowH, width: showLabels ? x0 + pw + 6 : pw + 12, height: rowH, rx: 5, class: "rowsel" }, g);
      }
    });
    for (const t of dom.t) {
      if (t < dom.lo - 1e-9 || t > dom.hi + 1e-9) continue;
      el("line", { x1: x(t), x2: x(t), y1: top - 4, y2: top + rowH * list.length, class: "grid" }, g);
      text(g, x(t), height - 10, tickLabel(t, dom.t.step), { "text-anchor": "middle" });
    }
    el("line", { x1: x(0), x2: x(0), y1: top - 4, y2: top + rowH * list.length, class: "base", "stroke-width": 1.5 }, g);
    if (axis === "split_gain") {
      const lx = x(LIMIT * a.factor);
      el("line", { x1: lx, x2: lx, y1: top - 6, y2: top + rowH * list.length, stroke: "var(--ink-2)", "stroke-width": 1, "stroke-dasharray": "3 3" }, g);
      text(g, lx + 3, top - 8, "limit", { "font-size": 10.5 });
    }
    list.forEach((s, r) => {
      const y = top + r * rowH + rowH / 2;
      if (showLabels) {
        const nm = pretty(s.name);
        const name = nm.length > maxChars ? nm.slice(0, maxChars - 1) + "…" : nm;
        el("circle", { cx: 4, cy: y, r: 3.5, fill: KIND[s.kind].color }, g);
        text(g, 13, y + 4, name, { class: s.name === state.selected ? "ink" : "ink2", "font-size": 12.5, "font-weight": s.name === state.selected ? 650 : 400 });
      }
      const q = res(s, state.scenario, axis);
      if (!q) return;
      const v = q[0] * a.factor;
      if (a.exact) {
        const over = axis === "split_gain" && q[0] > LIMIT + 1e-9;
        el("path", { d: hbar(x(0), x(v), y, 10), fill: over ? "var(--bad)" : "var(--neutral)", opacity: over ? 0.75 : 1 }, g);
      } else {
        const lo = res(s, "low", axis), hi = res(s, "high", axis);
        const mark = s.marks[axis];
        if (lo && hi) {
          const xs = [lo[0], hi[0], q[0]].map((w) => x(w * a.factor));
          const colour = mark === "▲" || mark === "△" ? "var(--good)" : mark ? "var(--bad)" : "var(--neutral)";
          const band = el("line", { x1: Math.min(...xs), x2: Math.max(...xs), y1: y, y2: y, stroke: colour, "stroke-width": 8, "stroke-linecap": "round" }, g);
          band.style.opacity = "var(--band)";
        }
        if (q[1] !== null) el("line", { x1: x(v - q[1] * a.factor), x2: x(v + q[1] * a.factor), y1: y, y2: y, stroke: "var(--ink-2)", "stroke-width": 1.25 }, g);
        markShape(g, x(v), y, mark, 5);
      }
      const hit = el("rect", { x: showLabels ? 0 : x0 - gap / 2, y: y - rowH / 2, width: showLabels ? x0 + pw : pw + gap, height: rowH, class: "hit" }, g);
      hit.addEventListener("pointermove", (e) => showTip(e, [{ value: pretty(s.name) }, { label: `${a.short}: ${sentence(s, axis)}` }]));
      hit.addEventListener("pointerleave", hideTip);
      hit.addEventListener("click", () => openDesign(s.name));
    });
  });
}

// ---------- the lead chart: every design, and the line of best trade-offs ----------
// One range per measure: everything shown, under every reaction strength. Picking measures
// and the reaction switch never rescale; only switching groups of designs on or off can.
function domains(list) {
  const out = {};
  for (const a of D.axes) {
    const vals = [0];
    for (const s of list) for (const sc of D.meta.scenarios) { const q = res(s, sc, a.name); if (q) vals.push(q[0] * a.factor); }
    if (a.name === "split_gain") vals.push(LIMIT * a.factor);
    let lo = Math.min(...vals), hi = Math.max(...vals);
    const pad = (hi - lo) * 0.08 || 1;
    lo -= pad; hi += pad;
    out[a.name] = { lo, hi, t: ticks(lo, hi, 5) };
  }
  return out;
}
function scatterControls() {
  const chips = $("#presets");
  const tab = (key, label) => {
    const b = h("button", { type: "button" }, chips, label);
    b.dataset.lead = key;
    b.addEventListener("click", () => { state.lead = key; lead(); });
  };
  if (D.search && D.search.hypervolume_unpaid) tab("combined", "Combined trade-offs");
  tab("pair", "Comparison");
  // two measures, any pair; picking the one already on the other axis swaps them
  const pick = $("#axis-pick");
  const select = (axis, label) => {
    const s = h("select", { "aria-label": label }, pick);
    for (const a of D.axes) h("option", { value: a.name }, s, a.short);
    s.dataset.axis = axis;
    s.addEventListener("change", () => {
      const other = axis === "x" ? "y" : "x";
      if (s.value === state[other]) state[other] = state[axis];
      state[axis] = s.value;
      lead();
    });
    return s;
  };
  select("y", "Vertical axis");
  h("span", { className: "label" }, pick, "against");
  select("x", "Horizontal axis");
  const swap = h("button", { className: "icon-btn swap", type: "button", "aria-label": "Swap the axes", title: "Swap the axes" }, pick, "⇄");
  swap.addEventListener("click", () => { [state.x, state.y] = [state.y, state.x]; lead(); });
  const legend = $("#best-legend");
  const toggle = (key, label, color, hollow) => {
    const b = h("button", { className: "toggle", type: "button" }, legend);
    b.dataset.k = key;
    b.style.setProperty("--kind", color);
    const dot = h("span", { className: "dot" }, b);
    if (hollow) dot.style.borderRadius = "2px";
    b.appendChild(document.createTextNode(label));
    b.addEventListener("click", () => { state.chart[key] = !state.chart[key]; syncControls(); lead(); });
  };
  toggle("named", "Named designs", KIND.named.color);
  if (hasKind("search")) toggle("search", "Found by search", KIND.search.color);
  if (hasKind("proposed")) toggle("proposed", "Community", KIND.proposed.color);
  if (D.schemes.some(overLimit)) toggle("sybil", "Over the Sybil limit", "var(--bad)");
  if (D.schemes.some((s) => !s.pilot)) toggle("fork", "Needs a hard fork", "var(--ink-2)", true);
  const key = $("#pair-key");
  let span = h("span", {}, key);
  let svg = el("svg", { width: 20, height: 12 }, span);
  el("rect", { x: 0, y: 0, width: 20, height: 12, rx: 2, fill: "var(--front-fill)" }, svg);
  el("path", { d: "M0,2 H10 V10 H20", fill: "none", stroke: "var(--ink)", "stroke-width": 2 }, svg);
  span.appendChild(document.createTextNode("best trade-offs, and the area they cover"));
  span = h("span", {}, key);
  svg = el("svg", { width: 12, height: 12 }, span);
  el("circle", { cx: 6, cy: 6, r: 4, fill: "var(--surface)", stroke: "var(--ink)", "stroke-width": 2 }, svg);
  span.appendChild(document.createTextNode("paying nothing"));
}
function chartVisible() {
  return D.schemes.filter((s) => state.chart[s.kind === "ladder" ? "named" : s.kind] && (s.pilot || state.chart.fork) && (state.chart.sybil || !overLimit(s)));
}
// Designs no other shown design beats on both measures, ordered along the line.
function frontier(pts, ax, ay) {
  const sx = ax.better === "higher" ? 1 : -1, sy = ay.better === "higher" ? 1 : -1;
  const beats = (p, q) => sx * p.vx >= sx * q.vx && sy * p.vy >= sy * q.vy && (sx * p.vx > sx * q.vx || sy * p.vy > sy * q.vy);
  return pts.filter((p) => !pts.some((q) => beats(q, p))).sort((p, q) => sx * (p.vx - q.vx) || sy * (q.vy - p.vy));
}
function scatter() {
  const host = $("#scatter");
  host.textContent = "";
  const ax = AX[state.x], ay = AX[state.y];
  const W = host.clientWidth, H = Math.max(320, Math.min(500, W * 0.62));
  const m = { l: 46, r: 18, t: 30, b: 46 };
  const svg = el("svg", { width: W, height: H, role: "img", "aria-label": `${ax.short} against ${ay.short}, with the line of best trade-offs` }, host);
  const pts = chartVisible().map((s) => {
    const qx = res(s, state.scenario, state.x), qy = res(s, state.scenario, state.y);
    return qx && qy ? { s, vx: qx[0] * ax.factor, vy: qy[0] * ay.factor } : null;
  }).filter(Boolean);
  pts.unshift({ s: { name: "paying nothing", kind: "unpaid", pilot: true }, vx: 0, vy: 0 });
  const dom = domains(chartVisible());
  const dx = dom[state.x], dy = dom[state.y];
  const x = scale(dx.lo, dx.hi, m.l, W - m.r), y = scale(dy.lo, dy.hi, H - m.b, m.t);
  for (const p of pts) { p.px = x(p.vx); p.py = y(p.vy); }
  const right = ax.better === "higher", upward = ay.better === "higher";

  // the area the best designs cover, and the line along its edge
  const front = frontier(pts, ax, ay);
  const rx = right ? m.l : W - m.r, ry = upward ? H - m.b : m.t;
  let line = null;
  if (front.length) {
    const edge = [[rx, front[0].py]];
    front.forEach((p, i) => { edge.push([p.px, p.py]); if (i + 1 < front.length) edge.push([p.px, front[i + 1].py]); });
    edge.push([front[front.length - 1].px, ry]);
    const path = edge.map(([a, b], i) => `${i ? "L" : "M"}${a},${b}`).join(" ");
    el("path", { d: `${path} L${rx},${ry} Z`, fill: "var(--front-fill)" }, svg);
    line = path;
  }
  for (const t of dx.t) if (t >= dx.lo && t <= dx.hi) {
    el("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b, class: "grid" }, svg);
    text(svg, x(t), H - m.b + 16, tickLabel(t, dx.t.step), { "text-anchor": "middle" });
  }
  for (const t of dy.t) if (t >= dy.lo && t <= dy.hi) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(t), y2: y(t), class: "grid" }, svg);
    text(svg, m.l - 6, y(t) + 4, tickLabel(t, dy.t.step), { "text-anchor": "end" });
  }
  el("line", { x1: x(0), x2: x(0), y1: m.t, y2: H - m.b, class: "base", "stroke-width": 1.5 }, svg);
  el("line", { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: "base", "stroke-width": 1.5 }, svg);
  if (line) el("path", { d: line, fill: "none", stroke: "var(--ink)", "stroke-width": 2, "stroke-linejoin": "round" }, svg);
  text(svg, (m.l + W - m.r) / 2, H - 8, `${ax.short} (${ax.change})  ${right ? "→" : "←"} better`, { "text-anchor": "middle", class: "ink2" });
  text(svg, 0, 12, `${ay.short} (${ay.change})  ${upward ? "↑" : "↓"} better`, { class: "ink2" });
  if (state.x === "split_gain" || state.y === "split_gain") {
    const v = LIMIT * AX.split_gain.factor;
    const attrs = { stroke: "var(--ink-2)", "stroke-width": 1, "stroke-dasharray": "4 3" };
    if (state.x === "split_gain") {
      el("line", { x1: x(v), x2: x(v), y1: m.t, y2: H - m.b, ...attrs }, svg);
      text(svg, x(v) + 4, H - m.b - 6, `Sybil limit`, { "font-size": 10.5 });
    } else {
      el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), ...attrs }, svg);
      text(svg, W - m.r - 2, y(v) - 4, `Sybil limit`, { "text-anchor": "end", "font-size": 10.5 });
    }
  }
  const cx = right ? W - m.r - 4 : m.l + 4, cy = upward ? m.t + 14 : H - m.b - 8;
  const better = text(svg, cx, cy, `better ${upward ? (right ? "↗" : "↖") : right ? "↘" : "↙"}`, { "text-anchor": right ? "end" : "start", class: "ink", "font-weight": 650, "font-size": 12.5 });
  better.setAttribute("paint-order", "stroke");
  better.setAttribute("stroke", "var(--surface)");
  better.setAttribute("stroke-width", 4);

  const onFront = new Set(front.map((p) => p.s.name));
  const order = [...pts].sort((p, q) => (onFront.has(p.s.name) - onFront.has(q.s.name)) || ((p.s.name === state.selected) - (q.s.name === state.selected)));
  for (const p of order) {
    const sel = p.s.name === state.selected;
    if (p.s.kind === "unpaid") {
      el("circle", { cx: p.px, cy: p.py, r: 5.5, fill: "var(--surface)", stroke: "var(--ink)", "stroke-width": 2 }, svg);
      continue;
    }
    const c = KIND[p.s.kind].color, r = sel ? 6.5 : onFront.has(p.s.name) ? 5.5 : 4.5;
    const faded = !onFront.has(p.s.name) && !sel;
    if (sel) el("circle", { cx: p.px, cy: p.py, r: r + 5, fill: "none", stroke: "var(--ink)", "stroke-width": 1.5 }, svg);
    let mark;
    if (p.s.pilot) mark = el("circle", { cx: p.px, cy: p.py, r, fill: c, stroke: "var(--surface)", "stroke-width": 2 }, svg);
    else mark = el("path", { d: `M${p.px},${p.py - r - 1} L${p.px + r + 1},${p.py} L${p.px},${p.py + r + 1} L${p.px - r - 1},${p.py} Z`, fill: "var(--surface)", stroke: c, "stroke-width": 2 }, svg);
    if (faded) mark.setAttribute("opacity", 0.55);
  }
  // labels only for the designs on the line and the selection; skip any that collide
  const boxes = pts.map((p) => ({ x0: p.px - 6, x1: p.px + 6, y0: p.py - 6, y1: p.py + 6 }));
  const want = pts.filter((p) => p.s.name === state.selected || onFront.has(p.s.name))
    .sort((p, q) => (q.s.name === state.selected) - (p.s.name === state.selected));
  for (const p of want) {
    const label = p.s.kind === "unpaid" ? "paying nothing" : pretty(p.s.name);
    const t = text(svg, 0, 0, label, { class: "ink", "font-size": 11.5, "font-weight": p.s.name === state.selected ? 700 : 560 });
    t.setAttribute("paint-order", "stroke");
    t.setAttribute("stroke", "var(--surface)");
    t.setAttribute("stroke-width", 3);
    const w = t.getComputedTextLength();
    let placed = false;
    // up and to the side first: the line runs level into each point and drops away from it
    const spots = right ? [[7, -9, "start"], [-7, -9, "end"], [9, 14, "start"], [-9, 14, "end"]] : [[-7, -9, "end"], [7, -9, "start"], [-9, 14, "end"], [9, 14, "start"]];
    for (const [ox, oy, anchor] of upward ? spots : spots.map(([a, b, c]) => [a, b < 0 ? 16 : -9, c])) {
      const bx0 = anchor === "start" ? p.px + ox : anchor === "end" ? p.px + ox - w : p.px - w / 2;
      const box = { x0: bx0, x1: bx0 + w, y0: p.py + oy - 12, y1: p.py + oy + 2 };
      if (box.x0 < m.l || box.x1 > W - m.r || box.y0 < m.t - 4 || box.y1 > H - m.b) continue;
      if (boxes.some((b, i) => pts[i] !== p && b.x0 < box.x1 && box.x0 < b.x1 && b.y0 < box.y1 && box.y0 < b.y1)) continue;
      t.setAttribute("x", p.px + ox); t.setAttribute("y", p.py + oy); t.setAttribute("text-anchor", anchor);
      boxes.push(box); placed = true; break;
    }
    if (!placed) t.remove();
  }
  const layer = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, class: "hit" }, svg);
  const ring = el("circle", { r: 9, fill: "none", stroke: "var(--ink-2)", "stroke-width": 1.5, visibility: "hidden", "pointer-events": "none" }, svg);
  const nearest = (e) => {
    const b = svg.getBoundingClientRect(), mx = e.clientX - b.left, my = e.clientY - b.top;
    let best = null, bd = 24 * 24;
    for (const p of pts) { const d = (p.px - mx) ** 2 + (p.py - my) ** 2; if (d < bd) { bd = d; best = p; } }
    return best;
  };
  layer.addEventListener("pointermove", (e) => {
    const p = nearest(e);
    if (!p) { hideTip(); ring.setAttribute("visibility", "hidden"); layer.style.cursor = "default"; return; }
    layer.style.cursor = p.s.kind === "unpaid" ? "default" : "pointer";
    ring.setAttribute("cx", p.px); ring.setAttribute("cy", p.py); ring.setAttribute("visibility", "visible");
    if (p.s.kind === "unpaid") { showTip(e, [{ value: "Paying nothing" }, { label: "Every other point is a change from here." }]); return; }
    const lines = [{ value: pretty(p.s.name) }, { label: KIND[p.s.kind].label + (p.s.pilot ? "" : "; needs a hard fork") + (onFront.has(p.s.name) ? "; on the line" : "") }];
    for (const axis of [state.x, state.y]) lines.push({ value: AX[axis].short + ":", label: sentence(p.s, axis) });
    lines.push({ label: "Click for details" });
    showTip(e, lines);
  });
  layer.addEventListener("pointerleave", () => { hideTip(); ring.setAttribute("visibility", "hidden"); });
  layer.addEventListener("click", (e) => { const p = nearest(e); if (p && p.s.kind !== "unpaid") openDesign(p.s.name); });
  frontierList(front);
}
function frontierList(front) {
  const host = $("#frontier-list");
  host.textContent = "";
  const row = h("div", { className: "title-row" }, host);
  h("h3", {}, row, "On the line");
  info(row, ["These designs are not beaten on both measures shown by any other design in the chart.", "Each makes a different trade-off: moving along the line, one measure gets better as the other gets worse."]);
  const ol = h("ol", { className: "front-list" }, host);
  for (const p of front) {
    const li = h("li", {}, ol);
    const name = p.s.kind === "unpaid" ? "Paying nothing" : pretty(p.s.name);
    const b = h(p.s.kind === "unpaid" ? "span" : "button", { className: "front-item", type: "button" }, li);
    const dot = h("span", { className: "dot" }, b);
    dot.style.background = p.s.kind === "unpaid" ? "var(--surface)" : KIND[p.s.kind].color;
    if (p.s.kind === "unpaid") dot.style.boxShadow = "inset 0 0 0 2px var(--ink)";
    h("span", { className: "nm" }, b, name);
    if (p.s.kind !== "unpaid") {
      h("span", { className: "vals" }, b, `${fmt(state.x, val(p.s, state.x))} · ${fmt(state.y, val(p.s, state.y))}`);
      b.addEventListener("click", () => openDesign(p.s.name));
    }
  }
}
// ---------- combined trade-offs: the hypervolume, as a multiple of what paying nothing covers ----------
function lead() {
  const combined = state.lead === "combined";
  for (const b of $("#presets").children) b.setAttribute("aria-pressed", b.dataset.lead === state.lead);
  for (const s of $("#axis-pick").querySelectorAll("select")) s.value = state[s.dataset.axis];
  $("#pair").hidden = combined;
  $("#combined").hidden = !combined;
  $("#axis-pick").hidden = combined;
  $("#best-scenario").hidden = combined;
  if (combined) coverage(); else scatter();
}
// Exact hypervolume above the origin, every score maximised (the same recursion as metrics.py).
function hvol(points) {
  const prod = (p) => p.reduce((a, b) => a * b, 1);
  const nondom = (ps) => {
    const uniq = [...new Map(ps.map((p) => [p.join(","), p])).values()];
    return uniq.filter((p, i) => !uniq.some((q, j) => j !== i && q.every((v, d) => v >= p[d])));
  };
  const wfg = (ps) => {
    if (!ps.length) return 0;
    if (ps.length === 1) return prod(ps[0]);
    const n = ps[0].length;
    if (n === 1) return Math.max(...ps.map((p) => p[0]));
    ps = [...ps].sort((a, b) => a[n - 1] - b[n - 1]);
    let total = 0;
    for (let k = 0; k < ps.length; k++) {
      const overlap = ps.slice(k + 1).map((q) => q.map((v, d) => Math.min(v, ps[k][d])));
      total += prod(ps[k]) - wfg(nondom(overlap));
    }
    return total;
  };
  return wfg(nondom(points.filter((p) => p.every((v) => v > 0))));
}
// The shown designs, each adding the most coverage it can on top of those already chosen.
const rankCache = new Map();
function ranked(names) {
  const keyName = names.join("|");
  if (rankCache.has(keyName)) return rankCache.get(keyName);
  const S = D.search.scores, base = S[D.search.baseline];
  const vol = (members) => hvol([base, ...members.map((n) => S[n])]);
  const out = [];
  let chosen = [], before = vol([]), rest = names.filter((n) => S[n]);
  while (rest.length) {
    let best = null, bestSize = -1;
    for (const n of rest) { const size = vol([...chosen, n]); if (size > bestSize) { bestSize = size; best = n; } }
    if (bestSize - before < 1e-12) { for (const n of rest) out.push({ name: n, adds: 0 }); break; }
    out.push({ name: best, adds: bestSize - before });
    chosen.push(best); rest = rest.filter((n) => n !== best); before = bestSize;
  }
  const result = { parts: out, total: before };
  rankCache.set(keyName, result);
  return result;
}
// Which search round first tried a design: generated names carry it, named designs start in round 0.
const roundOf = (name) => { const m = GENERATED.exec(name); return m ? +m[1] : 0; };
const fromRound = (s, round) => s.kind !== "proposed" && roundOf(s.name) === round;
function coverage() {
  const s = D.search, side = $("#coverage"), host = $("#coverage-chart");
  side.textContent = ""; host.textContent = "";
  const base = s.hypervolume_unpaid;
  const guarded = s.hypervolume_guarded ? s.hypervolume_guarded / base : null;
  const all = s.hypervolume / base;
  const lead = guarded ?? all; // the prominent line and number
  const ci = (guarded ? s.hypervolume_guarded_ci : s.hypervolume_ci)?.map((v) => v / base);
  const namedAlone = guarded
    ? (s.hypervolume_named_guarded ? s.hypervolume_named_guarded / base : null)
    : s.search_gain !== null && s.search_gain !== undefined ? (s.hypervolume - s.search_gain) / base : null;
  const hist = (s.history || []).map((r, i) => ({
    n: r.evaluated, round: r.generation ?? i,
    v: (guarded && r.hypervolume_guarded ? r.hypervolume_guarded : r.hypervolume) / base, all: r.hypervolume / base,
  }));
  const shown = chartVisible().filter((q) => s.scores && s.scores[q.name]);
  const SAFE = "var(--c2)", MUTED = "var(--muted)";

  const row = h("div", { className: "title-row" }, side);
  h("h3", {}, row, "Trade-off coverage");
  info(row, [
    "How much ground the best designs cover on all five measures at once. It is the five-measure version of the shaded area in the other charts; researchers call it the hypervolume.",
    "Paying nothing on its own counts as 1×. Higher means a wider choice of good trade-offs. It does not mean any single design got better.",
    guarded ? `The solid line counts only designs within the Sybil limit (at most ${pct(LIMIT)} of the budget to gain by posing as several DReps). The dotted line also counts designs over it, which reach further but are easy to game.` : "",
    `The search scored designs on its own random runs, then re-checked the final set on ${num(s.holdout_seeds, 0)} fresh runs it never saw${ci ? ` (95% range ${num(ci[0], 1)}–${num(ci[1], 1)}×)` : ""}.`,
  ].filter(Boolean));
  const big = h("div", { className: "cov-big" }, side);
  h("span", { className: "v" }, big, num(lead, 1) + "×");
  h("span", { className: "small" }, big, guarded ? "what paying nothing covers, within the Sybil limit" : "what paying nothing covers");
  const keys = h("div", { className: "cov-keys" }, side);
  const key = (draw, label, value) => {
    const r = h("div", {}, keys);
    const svg = el("svg", { width: 22, height: 12 }, r);
    draw(svg);
    h("span", {}, r, label);
    h("b", {}, r, value);
  };
  key((g) => el("line", { x1: 1, x2: 21, y1: 6, y2: 6, stroke: "var(--ink-2)", "stroke-width": 1.5, "stroke-dasharray": "4 3" }, g), "Paying nothing", "1×");
  if (namedAlone) key((g) => el("line", { x1: 1, x2: 21, y1: 6, y2: 6, stroke: "var(--c1)", "stroke-width": 2, "stroke-dasharray": "1 3", "stroke-linecap": "round" }, g), "Named designs alone", num(namedAlone, 1) + "×");
  key((g) => { el("line", { x1: 1, x2: 21, y1: 6, y2: 6, stroke: SAFE, "stroke-width": 2 }, g); el("circle", { cx: 11, cy: 6, r: 3, fill: SAFE }, g); }, guarded ? "Within the Sybil limit" : "With the search's designs", num(lead, 1) + "×");
  if (guarded) key((g) => { el("line", { x1: 1, x2: 21, y1: 6, y2: 6, stroke: MUTED, "stroke-width": 1.5, "stroke-dasharray": "2 3" }, g); el("circle", { cx: 11, cy: 6, r: 2.5, fill: "var(--surface)", stroke: MUTED, "stroke-width": 1.5 }, g); }, "Including designs over the limit", num(all, 1) + "×");
  key((g) => el("path", { d: "M11,1 L16,6 L11,11 L6,6 Z", fill: "var(--surface)", stroke: "var(--ink)", "stroke-width": 1.5 }, g), `Re-checked on ${num(s.holdout_seeds, 0)} fresh runs`, "");
  h("p", { className: "small", style: "margin:12px 0 0" }, side, "Hover or click a round to see which designs it found.");

  contributions(shown);
  if (hist.length < 2) return;
  const W = host.clientWidth, H = Math.max(300, Math.min(440, W * 0.55));
  const m = { l: 46, r: 26, t: 30, b: 46 };
  const svg = el("svg", { width: W, height: H, role: "img", "aria-label": "Trade-off coverage as the search tried more designs" }, host);
  const top = Math.max(lead, all, ci ? ci[1] : 0, ...hist.map((r) => Math.max(r.v, r.all))) * 1.1;
  const x = scale(hist[0].n, hist[hist.length - 1].n, m.l, W - m.r), y = scale(0, top, H - m.b, m.t);
  const xt = ticks(hist[0].n, hist[hist.length - 1].n, 5), yt = ticks(0, top, 5);
  for (const v of xt) if (v >= hist[0].n && v <= hist[hist.length - 1].n) {
    el("line", { x1: x(v), x2: x(v), y1: m.t, y2: H - m.b, class: "grid" }, svg);
    text(svg, x(v), H - m.b + 16, num(v, 0), { "text-anchor": "middle" });
  }
  for (const v of yt) if (v <= top) {
    el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: v === 0 ? "base" : "grid" }, svg);
    text(svg, m.l - 6, y(v) + 4, num(v, yt.step < 1 ? 1 : 0) + "×", { "text-anchor": "end" });
  }
  text(svg, (m.l + W - m.r) / 2, H - 8, "Designs the search has tried", { "text-anchor": "middle", class: "ink2" });
  text(svg, 0, 12, "Coverage (× paying nothing)  ↑ better", { class: "ink2" });
  const halo = (t) => { t.setAttribute("paint-order", "stroke"); t.setAttribute("stroke", "var(--surface)"); t.setAttribute("stroke-width", 3); return t; };
  const ref = (v, label, attrs) => {
    el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), ...attrs }, svg);
    halo(text(svg, W - m.r - 4, y(v) - 6, label, { "text-anchor": "end", "font-size": 11.5, class: "ink2" }));
  };
  ref(1, "paying nothing", { stroke: "var(--ink-2)", "stroke-width": 1.5, "stroke-dasharray": "4 3" });
  if (namedAlone) ref(namedAlone, guarded && W > 520 ? "named designs alone, within the limit" : "named designs alone", { stroke: "var(--c1)", "stroke-width": 2, "stroke-dasharray": "1 4", "stroke-linecap": "round" });
  const path = (key) => hist.map((r, i) => `${i ? "L" : "M"}${x(r.n)},${y(r[key])}`).join(" ");
  const fx = x(hist[hist.length - 1].n);
  if (guarded) {
    el("path", { d: path("all"), fill: "none", stroke: MUTED, "stroke-width": 1.5, "stroke-dasharray": "2 4", "stroke-linecap": "round" }, svg);
    for (const r of hist) el("circle", { cx: x(r.n), cy: y(r.all), r: 2.5, fill: "var(--surface)", stroke: MUTED, "stroke-width": 1.5 }, svg);
    el("circle", { cx: fx, cy: y(all), r: 4.5, fill: "var(--surface)", stroke: MUTED, "stroke-width": 1.5 }, svg);
    halo(text(svg, fx - 10, y(all) - 9, `including designs over the Sybil limit: ${num(all, 1)}×`, { "text-anchor": "end", "font-size": 11.5, fill: MUTED }));
  }
  el("path", { d: path("v"), fill: "none", stroke: SAFE, "stroke-width": 2.5, "stroke-linejoin": "round" }, svg);
  for (const r of hist) {
    const found = shown.some((q) => fromRound(q, r.round));
    if (state.round === r.round) el("circle", { cx: x(r.n), cy: y(r.v), r: 10, fill: "none", stroke: "var(--ink)", "stroke-width": 1.5 }, svg);
    el("circle", { cx: x(r.n), cy: y(r.v), r: found ? 5.5 : 3.5, fill: found ? SAFE : "var(--surface)", stroke: found ? "var(--surface)" : SAFE, "stroke-width": 2 }, svg);
  }
  // the final set, re-checked on fresh runs
  if (ci) {
    el("line", { x1: fx, x2: fx, y1: y(ci[0]), y2: y(ci[1]), stroke: "var(--ink)", "stroke-width": 1.5 }, svg);
    for (const v of ci) el("line", { x1: fx - 4, x2: fx + 4, y1: y(v), y2: y(v), stroke: "var(--ink)", "stroke-width": 1.5 }, svg);
  }
  el("path", { d: `M${fx},${y(lead) - 6} L${fx + 6},${y(lead)} L${fx},${y(lead) + 6} L${fx - 6},${y(lead)} Z`, fill: "var(--surface)", stroke: "var(--ink)", "stroke-width": 2 }, svg);

  const pts = hist.map((r) => {
    const mine = shown.filter((q) => fromRound(q, r.round));
    const lines = [
      { value: r.round ? `Round ${r.round}: ${num(r.v, 1)}×` : `Starting set: ${num(r.v, 1)}×` },
      { label: r.round ? `After ${num(r.n, 0)} designs tried` : `The first ${num(r.n, 0)} designs, named ones included` },
    ];
    if (guarded) lines.push({ label: `${num(r.all, 1)}× including designs over the Sybil limit` });
    if (mine.length) {
      lines.push({ label: "In the final set from this round:" });
      for (const q of mine.slice(0, 4)) lines.push({ value: "· " + pretty(q.name) });
      if (mine.length > 4) lines.push({ label: `and ${mine.length - 4} more` });
      lines.push({ label: "Click to highlight them below" });
    } else lines.push({ label: "None of the designs switched on came from this round." });
    return { px: x(r.n), py: y(r.v), round: r.round, lines };
  });
  pts.push({ px: fx, py: y(lead), round: null, lines: [{ value: `Final set: ${num(lead, 1)}×` }, { label: `Re-checked on ${num(s.holdout_seeds, 0)} fresh runs` }, ...(ci ? [{ label: `95% range ${num(ci[0], 2)}–${num(ci[1], 2)}×` }] : []), { label: "Click to show every design" }] });
  const layer = el("rect", { x: m.l - 8, y: m.t, width: W - m.l - m.r + 16, height: H - m.t - m.b, class: "hit" }, svg);
  const ring = el("circle", { r: 9, fill: "none", stroke: "var(--ink-2)", "stroke-width": 1.5, visibility: "hidden", "pointer-events": "none" }, svg);
  const nearest = (e) => {
    const b = svg.getBoundingClientRect(), mx = e.clientX - b.left, my = e.clientY - b.top;
    let best = null, bd = 30 * 30;
    for (const p of pts) { const dd = (p.px - mx) ** 2 + (p.py - my) ** 2; if (dd < bd) { bd = dd; best = p; } }
    return best;
  };
  layer.addEventListener("pointermove", (e) => {
    const p = nearest(e);
    if (!p) { hideTip(); ring.setAttribute("visibility", "hidden"); layer.style.cursor = "default"; return; }
    layer.style.cursor = "pointer";
    ring.setAttribute("cx", p.px); ring.setAttribute("cy", p.py); ring.setAttribute("visibility", "visible");
    showTip(e, p.lines);
  });
  layer.addEventListener("pointerleave", () => { hideTip(); ring.setAttribute("visibility", "hidden"); });
  layer.addEventListener("click", (e) => {
    const p = nearest(e);
    if (!p) return;
    state.round = p.round === null || state.round === p.round ? null : p.round;
    hideTip();
    coverage();
    $("#contrib").scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
}
// The designs switched on, ranked by how much coverage each adds on top of the ones above it.
function contributions(shown) {
  const host = $("#contrib");
  host.textContent = "";
  const base = D.search.hypervolume_unpaid;
  const { parts, total } = ranked(shown.map((q) => q.name));
  const head = h("div", { className: "contrib-head" }, host);
  const row = h("div", { className: "title-row" }, head);
  h("h3", {}, row, parts.length ? `What makes up the ${num(total / base, 1)}×` : "Nothing to rank");
  info(row, [
    "The designs switched on above the chart, ranked by how much coverage each adds on top of the designs above it. The bars add up to the total.",
    "A design high on the list reaches a corner of the five measures that nothing above it reaches. A design near the bottom does something the others already do; it is not necessarily worse.",
    "Switch groups on or off to re-rank: for example, switch on “Over the Sybil limit” to see what those designs add.",
  ]);
  if (state.round !== null) {
    const chip = h("button", { className: "toggle", type: "button", title: "Show every design" }, head);
    chip.setAttribute("aria-pressed", "true");
    chip.style.setProperty("--kind", "var(--c2)");
    h("span", { className: "dot" }, chip);
    chip.appendChild(document.createTextNode((state.round ? `Found in round ${state.round}` : "In the starting set") + "  ✕"));
    chip.addEventListener("click", () => { state.round = null; coverage(); });
  }
  if (!parts.length) { h("p", { className: "empty" }, host, "Switch on a group of designs above the chart."); return; }
  const TOP = 8;
  const max = Math.max(...parts.map((p) => p.adds), 1e-12);
  const list = h("ol", { className: "contrib" }, host);
  let rank = 0, hidden = 0;
  for (const p of parts) {
    rank++;
    const s = D.schemes.find((q) => q.name === p.name);
    const inRound = state.round !== null && s && fromRound(s, state.round);
    if (rank > TOP && !state.allParts && !inRound) { hidden++; continue; }
    const li = h("li", { className: state.round !== null && !inRound ? "dim" : "" }, list);
    const b = h("button", { className: "contrib-row", type: "button" }, li);
    h("span", { className: "rank" }, b, String(rank));
    const nm = h("span", { className: "nm" }, b);
    const dot = h("span", { className: "dot" }, nm);
    dot.style.background = KIND[s.kind].color;
    nm.appendChild(document.createTextNode(pretty(p.name)));
    if (overLimit(s)) h("span", { className: "tag bad" }, nm, "Over the Sybil limit");
    if (!s.pilot) h("span", { className: "tag" }, nm, "Needs a hard fork");
    const bar = h("span", { className: "bar" }, b);
    h("span", { style: `width:${(p.adds / max) * 100}%` }, bar);
    h("span", { className: "val" }, b, p.adds / base < 0.005 ? "≈0" : "+" + num(p.adds / base, 2) + "×");
    b.title = describe(s.scheme, true);
    b.addEventListener("click", () => openDesign(p.name));
  }
  if (hidden || state.allParts) {
    const more = h("button", { className: "ghost", type: "button", style: "margin-top:8px" }, host,
      state.allParts ? "Show the top " + TOP : `Show all ${parts.length}`);
    more.addEventListener("click", () => { state.allParts = !state.allParts; contributions(shown); });
  }
}

// ---------- dig deeper: tabs ----------
function setTab(tab) {
  state.tab = tab;
  for (const b of $("#tabs").children) {
    const on = b.dataset.tab === tab;
    b.setAttribute("aria-selected", on);
    b.tabIndex = on ? 0 : -1;
  }
  for (const p of document.querySelectorAll(".tabpanel")) p.hidden = p.dataset.panel !== tab;
  renderTab();
}
function renderTab() {
  ({ assumptions: heat, budget: ladder, model: validation, glossary: () => {} })[state.tab]();
}
function tabs() {
  const list = $("#tabs");
  for (const b of list.children) {
    b.id = "tab-" + b.dataset.tab;
    b.addEventListener("click", () => setTab(b.dataset.tab));
  }
  list.addEventListener("keydown", (e) => {
    const all = [...list.children], i = all.findIndex((b) => b.dataset.tab === state.tab);
    const j = e.key === "ArrowRight" ? (i + 1) % all.length : e.key === "ArrowLeft" ? (i - 1 + all.length) % all.length : -1;
    if (j >= 0) { setTab(all[j].dataset.tab); all[j].focus(); }
  });
  wireInfo($("#ladder-info"), () => [
    `Same rule, different budgets, ${SCEN[state.scenario].toLowerCase()}, with 95% intervals.`,
    "The model assumes each extra ADA buys a little less than the one before, so doubling the budget does not double the effect.",
  ]);
  wireInfo($("#valid-info"), () => validInfo);
  const heatAxis = $("#heat-axis");
  for (const a of D.axes.filter((q) => !q.exact)) {
    const b = h("button", { type: "button" }, heatAxis, a.short);
    b.dataset.a = a.name;
    b.addEventListener("click", () => { state.heat = a.name; state.heatv.page = 0; heat(); });
  }
  const legend = $("#heat-legend");
  for (const [c, label] of [["var(--div-worse)", "worse than paying nothing"], ["var(--div-mid)", "no clear change"], ["var(--div-better)", "better than paying nothing"]]) {
    const span = h("span", {}, legend);
    const svg = el("svg", { width: 14, height: 12 }, span);
    el("rect", { x: 0, y: 0, width: 14, height: 12, rx: 3, fill: c, stroke: "var(--ring)" }, svg);
    span.appendChild(document.createTextNode(label));
  }
  h("span", {}, legend, "darker: a larger change");
}

// ---------- which assumption each result rests on ----------
function heat() {
  for (const b of $("#heat-axis").children) b.setAttribute("aria-pressed", b.dataset.a === state.heat);
  const host = $("#heat");
  host.textContent = "";
  const a = AX[state.heat];
  const cols = [...D.meta.channels, { name: "central", label: "All four together" }];
  const v = state.heatv;
  const sign = a.better === "higher" ? 1 : -1;
  let all = D.schemes.filter((s) => cols.every((c) => s.results[c.name]));
  const values = all.flatMap((s) => cols.map((c) => res(s, c.name, a.name)[0]));
  const max = Math.max(...values.map(Math.abs), 1e-12);
  if (v.sort) {
    const key = (s) => (v.sort === "name" ? pretty(s.name).toLowerCase() : -sign * res(s, v.sort, a.name)[0]);
    all = [...all].sort((p, q) => { const x = key(p), y = key(q); return (x < y ? -1 : x > y ? 1 : 0) * v.dir || pretty(p.name).localeCompare(pretty(q.name)); });
  }
  const rows = page(all, v);
  $("#heat-count").textContent = shown(v, rows.length, all.length);
  pager($("#heat-pager"), all.length, v, heat, $("#deeper"));
  const onSort = (key, dir) => { v.sort = key; v.dir = dir; heat(); };
  const table = h("table", { className: "heat", style: "min-width:640px" }, host);
  const head = h("tr", {}, h("thead", {}, table));
  sortHeading(h("th", {}, head), `${a.short} (${a.change})`, "name", v, onSort, true);
  for (const c of cols) sortHeading(h("th", { className: "num" }, head), c.label, c.name, v, onSort, sign < 0);
  const body = h("tbody", {}, table);
  for (const s of rows) {
    const tr = h("tr", { className: "pick" + (s.name === state.selected ? " sel" : "") }, body);
    tr.addEventListener("click", () => openDesign(s.name));
    h("td", {}, tr, pretty(s.name));
    for (const c of cols) {
      const v = res(s, c.name, a.name)[0];
      const meaningful = Math.abs(v * a.factor) >= a.threshold;
      const t = meaningful ? Math.min(1, Math.abs(v) / max) : 0;
      const share = Math.round(20 + 70 * t);
      const pole = sign * v > 0 ? "var(--div-better)" : "var(--div-worse)";
      const td = h("td", { className: "num" }, tr, fmt(a.name, v));
      td.style.background = meaningful ? `color-mix(in oklab, ${pole} ${share}%, var(--div-mid))` : "var(--div-mid)";
      td.style.color = meaningful && share > 58 ? "#ffffff" : "var(--ink)";
      td.style.borderBottom = "2px solid var(--surface)";
      td.style.borderLeft = "2px solid var(--surface)";
    }
  }
}

// ---------- what more money buys ----------
function ladder() {
  const host = $("#ladder");
  host.textContent = "";
  const parent = D.meta.ladder_parent;
  const steps = D.schemes.filter((s) => s.kind === "ladder" || s.name === parent).sort((p, q) => p.budget - q.budget);
  if (steps.length < 2) { $("#ladder-note").textContent = "No budget comparison in this run."; return; }
  $("#ladder-note").textContent = `The ${pretty(parent).toLowerCase()} design at ${steps.length} budgets.`;
  const shown = ["participation", "tau67", "backing"].filter((n) => AX[n]);
  const boxes = shown.map(() => h("div", {}, host));
  for (const [n, axis] of shown.entries()) {
    const a = AX[axis];
    const box = boxes[n];
    const W = box.clientWidth || 320, H = 220, m = { l: 46, r: 14, t: 28, b: 40 };
    const svg = el("svg", { width: W, height: H, role: "img", "aria-label": `${a.short} by budget` }, box);
    const title = text(svg, 0, 13, a.short, { class: "ink", "font-weight": 650, "font-size": 13 });
    text(svg, title.getComputedTextLength() + 6, 13, `(${a.change})`, { "font-size": 11 });
    const pts = steps.map((s) => { const q = res(s, state.scenario, axis); return { s, b: s.budget / 1e6, v: q[0] * a.factor, ci: (q[1] || 0) * a.factor }; });
    const lo = Math.min(0, ...pts.map((p) => p.v - p.ci)), hi = Math.max(0, ...pts.map((p) => p.v + p.ci));
    const t = ticks(lo, hi + (hi - lo) * 0.1, 4);
    const y = scale(Math.min(lo, t[0]), Math.max(hi, t[t.length - 1]), H - m.b, m.t);
    const bx = pts.map((p) => p.b);
    const x = (b) => scale(Math.log(Math.min(...bx)), Math.log(Math.max(...bx)), m.l + 10, W - m.r - 10)(Math.log(b));
    for (const v of t) {
      if (v < y.domain[0] || v > y.domain[1]) continue;
      el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: v === 0 ? "base" : "grid" }, svg);
      text(svg, m.l - 6, y(v) + 4, tickLabel(v, t.step), { "text-anchor": "end" });
    }
    for (const p of pts) text(svg, x(p.b), H - m.b + 16, num(p.b, p.b % 1 ? 1 : 0) + "M", { "text-anchor": "middle" });
    text(svg, (m.l + W - m.r) / 2, H - 6, "budget over the programme, ADA", { "text-anchor": "middle", class: "ink2" });
    el("path", { d: pts.map((p, i) => `${i ? "L" : "M"}${x(p.b)},${y(p.v)}`).join(" "), fill: "none", stroke: "var(--c1)", "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    for (const p of pts) {
      el("line", { x1: x(p.b), x2: x(p.b), y1: y(p.v - p.ci), y2: y(p.v + p.ci), stroke: "var(--ink-2)", "stroke-width": 1.25 }, svg);
      el("circle", { cx: x(p.b), cy: y(p.v), r: 4.5, fill: "var(--c1)", stroke: "var(--surface)", "stroke-width": 2 }, svg);
      const hit = el("circle", { cx: x(p.b), cy: y(p.v), r: 14, class: "hit" }, svg);
      hit.addEventListener("pointermove", (e) => showTip(e, [{ value: fmt(axis, p.v / a.factor) + (p.ci ? ` ± ${num(p.ci, a.digits)}` : ""), label: a.short }, { label: `${pretty(p.s.name)}: ${ada(p.s.budget)} ADA` }]));
      hit.addEventListener("pointerleave", hideTip);
      hit.addEventListener("click", () => openDesign(p.s.name));
    }
    const last = pts[pts.length - 1];
    text(svg, x(last.b) - 8, y(last.v) - 9, fmt(axis, last.v / a.factor), { "text-anchor": "end", class: "ink", "font-size": 11.5 });
  }
  const tbl = $("#ladder-table");
  tbl.textContent = "";
  const table = h("table", {}, tbl);
  const head = h("tr", {}, h("thead", {}, table));
  for (const c of ["Budget", "Cost a year", "Share of the treasury a year", "Participation", "ADA a year per point of participation"]) h("th", { className: c === "Budget" ? "" : "num" }, head, c);
  const body = h("tbody", {}, table);
  for (const s of steps) {
    const tr = h("tr", { className: "pick" + (s.name === state.selected ? " sel" : "") }, body);
    tr.addEventListener("click", () => openDesign(s.name));
    const cost = val(s, "annual_cost_ada");
    const part = val(s, "participation") * 100;
    h("td", {}, tr, `${ada(s.budget)} ADA (${pretty(s.name)})`);
    h("td", { className: "num" }, tr, ada(cost) + " ADA");
    h("td", { className: "num" }, tr, D.meta.treasury ? pct(cost / D.meta.treasury, 2) : "–");
    h("td", { className: "num" }, tr, fmt("participation", part / 100));
    h("td", { className: "num" }, tr, part > 0 ? ada(cost / part) + " ADA" : "–");
  }
}

// ---------- does the model match history? ----------
let validInfo = [];
function validation() {
  const v = D.meta.validation;
  const fitStart = v.start - (v.end - v.start) + 1;
  $("#valid-note").textContent = `Predicting epochs ${v.start + 1}–${v.end} without having seen them: ${v.passed ? "every check passed" : "at least one check failed"}.`;
  validInfo = [
    "Before trusting the model with rewards, it is tested without them.",
    `It is fitted on epochs ${fitStart}–${v.start}, started from mainnet as it was at epoch ${v.start}, and asked to predict epochs ${v.start + 1}–${v.end}, which it never saw (${v.seeds} runs).`,
    "The charts compare its predictions with what actually happened on mainnet.",
  ];
  const host = $("#bands");
  host.textContent = "";
  if (D.bands) {
    const ep = D.bands.epochs;
    const boxes = D.bands.panels.map(() => h("div", {}, host));
    for (const [n, p] of D.bands.panels.entries()) {
      const box = boxes[n];
      const W = box.clientWidth || 280, H = 190, m = { l: 44, r: 10, t: 24, b: 26 };
      const svg = el("svg", { width: W, height: H, role: "img", "aria-label": p.label }, box);
      text(svg, 0, 13, p.label, { class: "ink", "font-weight": 650, "font-size": 13 });
      const all = [...p.low, ...p.high, ...p.observed];
      let lo = Math.min(...all), hi = Math.max(...all);
      const pad = (hi - lo) * 0.15 || 1;
      lo -= pad; hi += pad;
      const t = ticks(lo, hi, 3);
      const x = scale(ep[0], ep[ep.length - 1], m.l, W - m.r), y = scale(lo, hi, H - m.b, m.t);
      for (const v2 of t) if (v2 >= lo && v2 <= hi) {
        el("line", { x1: m.l, x2: W - m.r, y1: y(v2), y2: y(v2), class: "grid" }, svg);
        text(svg, m.l - 6, y(v2) + 4, tickLabel(v2, t.step), { "text-anchor": "end" });
      }
      for (const e of [ep[0], ep[Math.floor(ep.length / 2)], ep[ep.length - 1]]) text(svg, x(e), H - 8, String(e), { "text-anchor": "middle" });
      const area = ep.map((e, i) => `${i ? "L" : "M"}${x(e)},${y(p.high[i])}`).join(" ") + " " +
        ep.map((e, i) => `L${x(ep[ep.length - 1 - i])},${y(p.low[ep.length - 1 - i])}`).join(" ") + " Z";
      el("path", { d: area, fill: "var(--c1)", opacity: 0.12 }, svg);
      const line = (vals, c) => el("path", { d: ep.map((e, i) => `${i ? "L" : "M"}${x(e)},${y(vals[i])}`).join(" "), fill: "none", stroke: c, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
      line(p.mean, "var(--c1)");
      line(p.observed, "var(--ink)");
      const cross = el("line", { y1: m.t, y2: H - m.b, stroke: "var(--ink-2)", "stroke-width": 1, visibility: "hidden" }, svg);
      const layer = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, class: "hit" }, svg);
      layer.style.cursor = "crosshair";
      layer.addEventListener("pointermove", (e) => {
        const b = svg.getBoundingClientRect();
        const ex = ep[0] + ((e.clientX - b.left - m.l) / (W - m.l - m.r)) * (ep[ep.length - 1] - ep[0]);
        let i = 0;
        for (let k = 0; k < ep.length; k++) if (Math.abs(ep[k] - ex) < Math.abs(ep[i] - ex)) i = k;
        cross.setAttribute("x1", x(ep[i])); cross.setAttribute("x2", x(ep[i])); cross.setAttribute("visibility", "visible");
        const d = Math.abs(p.observed[i]) < 100 ? 1 : 0;
        showTip(e, [
          { label: `epoch ${ep[i]}` },
          { key: "var(--ink)", value: num(p.observed[i], d), label: "what happened" },
          { key: "var(--c1)", value: num(p.mean[i], d), label: `model average (${num(p.low[i], d)}–${num(p.high[i], d)})` },
        ]);
      });
      layer.addEventListener("pointerleave", () => { hideTip(); cross.setAttribute("visibility", "hidden"); });
    }
  }
  const tbl = $("#checks");
  tbl.textContent = "";
  const table = h("table", {}, tbl);
  const head = h("tr", {}, h("thead", {}, table));
  for (const c of ["Check", "What happened", "Model", "95% of runs", "Error", "Allowed", "Result"]) h("th", { className: c === "Check" || c === "Result" ? "" : "num" }, head, c);
  const body = h("tbody", {}, table);
  for (const c of D.checks) {
    const tr = h("tr", {}, body);
    const d = Math.abs(c.observed) < 10 ? 3 : 2;
    h("td", {}, tr, c.metric);
    h("td", { className: "num" }, tr, num(c.observed, d));
    h("td", { className: "num" }, tr, num(c.simulated, d));
    h("td", { className: "num" }, tr, `${num(c.low, d)}–${num(c.high, d)}`);
    h("td", { className: "num" }, tr, (c.error > 0 ? "+" : "") + num(c.error * (c.kind === "relative" ? 100 : 1), c.kind === "relative" ? 1 : 3) + (c.kind === "relative" ? "%" : ""));
    h("td", { className: "num" }, tr, c.tolerance === null || c.tolerance === undefined ? "–" : c.kind === "relative" ? pct(c.tolerance) : num(c.tolerance, 2));
    const td = h("td", {}, tr);
    if (!c.gated) td.textContent = "for context";
    else h("span", { className: c.passed ? "mark-good" : "mark-bad" }, td, c.passed ? "✓ pass" : "✕ FAIL");
  }
}

// ---------- glossary and notes ----------
function glossary() {
  const s = D.search;
  const runs = s && s.holdout_seeds !== D.meta.seeds
    ? `${num(D.meta.seeds, 0)} times (named designs) or ${num(s.holdout_seeds, 0)} times (search designs and proposals)`
    : `${num(D.meta.seeds, 0)} times`;
  const terms = [
    ["Paying nothing", "Governance as it would run over the next six months with no rewards, simulated from chain history. Every number on this page is a change from it."],
    ["Reaction to rewards", "How strongly DReps and delegators change what they do when paid is not known yet. Every design is simulated with a weak, a medium and a strong reaction. A result that only shows up with a strong reaction is a hope, not a finding."],
    ["Guardrails", `Limits a design should respect: no more than ${pct(LIMIT)} of the budget to gain by posing as several DReps, and never worse than paying nothing on participation, decentralisation or skin in the game.`],
    ["Sybil attack", "One person posing as many independent DReps to collect more rewards. Rules that favour small DReps, or cap large ones, invite it."],
    ["Found by search", s ? `An automated search tried ${num(s.evaluated, 0)} variations of the rules and kept the best trade-offs, then re-checked them on ${num(s.holdout_seeds, 0)} fresh random runs it never saw.` : "Designs found by an automated search over the rules."],
    ["Community proposal", "Submitted by anyone on the Propose page and simulated in exactly the same way."],
    ["± and intervals", `Each design is simulated ${runs} with different random luck. The ± is the 95% range of the average; differences smaller than it are not differences.`],
    ["Exact versus assumed", "Cost and Sybil risk are exact properties of a rule applied to today's DReps. The other three measures depend on the assumed reactions; the first tab shows which one."],
    ["Sybil tests", `Sybil risk is the larger of two tests: an outsider bringing ${ada(D.meta.capital)} ADA as many look-alike DReps, and an existing DRep splitting into 2–20 with its delegators following. The second is an upper bound.`],
    ["Own stake", "Estimated from accounts linked to a DRep on chain (the funder of its registration, its declared payment address). It misses stake held elsewhere; a real programme would need signed declarations."],
    ["Hard fork", "Limiting voting power itself changes how votes are counted, which needs a hard fork. Such designs are simulated mechanically: delegators of a capped DRep are not modelled as moving away."],
  ];
  const dl = $("#glossary");
  for (const [k, v] of terms) { h("dt", {}, dl, k); h("dd", {}, dl, v); }
}

// ---------- everything ----------
function renderAll() {
  syncControls();
  compareTable();
  scorecard();
  lead();
  renderTab();
}
function fromHash() {
  const m = /design=([^&]+)/.exec(location.hash);
  const name = m && decodeURIComponent(m[1]);
  if (name && D.schemes.some((q) => q.name === name)) { openDesign(name); return true; }
  return false;
}

hero();
measures();
controls();
scoreLegend();
scatterControls();
tabs();
glossary();
setTab("assumptions");
renderAll();
fromHash();
$("#drawer-close").addEventListener("click", closeDrawer);
$("#backdrop").addEventListener("click", closeDrawer);
addEventListener("keydown", (e) => { if (e.key === "Escape" && document.body.classList.contains("drawer-open")) closeDrawer(); });
addEventListener("hashchange", fromHash);
let pending = null, lastWidth = innerWidth;
addEventListener("resize", () => {
  if (innerWidth === lastWidth) return;
  lastWidth = innerWidth;
  cancelAnimationFrame(pending);
  pending = requestAnimationFrame(renderAll);
});
