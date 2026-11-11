// Helpers shared by every page. Names and text from data are always inserted as text, never as HTML.
const D = window.RSS || {};
const NS = "http://www.w3.org/2000/svg";
const $ = (q) => document.querySelector(q);
const AX = Object.fromEntries((D.axes || []).map((a) => [a.name, a]));
// The three assumptions about how strongly people react to being paid.
const SCEN = { low: "Weak reaction", central: "Medium reaction", high: "Strong reaction" };
const SCEN_SHORT = { low: "Weak", central: "Medium", high: "Strong" };
const KIND = {
  named: { label: "Named scheme", plural: "Named designs", color: "var(--c1)" },
  ladder: { label: "Named scheme at another budget", plural: "Other budgets", color: "var(--c1)" },
  search: { label: "Found by the search", plural: "Found by search", color: "var(--c2)" },
  proposed: { label: "Community proposal", plural: "Community", color: "var(--c3)" },
};

function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function text(parent, x, y, str, attrs = {}) {
  const t = el("text", { x, y, ...attrs }, parent);
  t.textContent = str;
  return t;
}
function h(tag, props = {}, parent, content) {
  const e = document.createElement(tag);
  // aria-*, data-* and role are attributes, not properties
  for (const [k, v] of Object.entries(props)) if (k.includes("-") || k === "role") e.setAttribute(k, v); else e[k] = v;
  if (content !== undefined) e.textContent = content;
  if (parent) parent.appendChild(e);
  return e;
}
const minus = (s) => s.replace(/^-/, "−");
function num(v, digits) {
  if (Number(v.toFixed(digits)) === 0) v = 0;
  return minus(v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits }));
}
function fmt(axis, raw, signed = true) {
  if (raw === null || raw === undefined || Number.isNaN(raw)) return "–";
  const a = AX[axis];
  const v = raw * a.factor;
  if (a.exact) return num(v, a.digits) + a.unit;
  const s = num(v, a.digits);
  return (signed && Number(v.toFixed(a.digits)) > 0 ? "+" : "") + s + a.unit;
}
function ada(v) {
  if (v === null || v === undefined) return "–";
  const a = Math.abs(v);
  if (a >= 1e9) return num(v / 1e9, 2) + "B";
  if (a >= 1e6) return num(v / 1e6, a >= 1e7 || Number.isInteger(v / 1e6) ? 0 : 1) + "M";
  if (a >= 1e4) return num(v / 1e3, 0) + "K";
  return num(v, 0);
}
const pct = (v, d = 0) => (v === null || v === undefined ? "–" : num(v * 100, d) + "%");
function date(iso, withTime = true) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, withTime ? { dateStyle: "medium", timeStyle: "short" } : { dateStyle: "medium" });
}
function ticks(lo, hi, n = 4) {
  const span = hi - lo || Math.abs(hi) || 1;
  const raw = span / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const e = raw / mag;
  const step = (e >= 7.5 ? 10 : e >= 3.5 ? 5 : e >= 1.5 ? 2 : 1) * mag;
  const out = [];
  for (let v = Math.floor(lo / step) * step; v <= hi + step * 0.999; v += step) out.push(+v.toFixed(10) || 0);
  out.step = step;
  return out;
}
function scale(d0, d1, r0, r1) {
  const f = (v) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);
  f.domain = [d0, d1];
  return f;
}
function tickLabel(v, step) {
  const d = step ? Math.max(0, Math.ceil(-Math.log10(step) - 1e-9)) : 0;
  return num(v, Math.min(d, 3));
}
function betterWord(axis) { return AX[axis].better === "higher" ? "higher is better" : "lower is better"; }

// ---------- words for designs ----------
// A design's name as people read it: "middle_out" becomes "Middle out".
const TITLES = Object.fromEntries((D.schemes || []).filter((s) => s.title).map((s) => [s.name, s.title]));
function pretty(name) {
  if (!name) return "";
  if (TITLES[name]) return TITLES[name];
  if (/^g\d+_\d+$/.test(name)) return "Search design " + name;
  const s = name.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}
// The rule in plain words, from its parameters. Used for every design and for the proposal form.
function describe(s, always = false) {
  if (!s || !s.budget_ada) return "Pays nothing. This is what every design is compared with.";
  const who = [];
  if (s.activity_gate) who.push(`voted on at least ${pct(s.activity_gate)} of recent actions`);
  if (s.min_delegators) who.push(`have at least ${num(s.min_delegators, 0)} delegators`);
  if (s.min_stake_ada) who.push(`hold at least ${ada(s.min_stake_ada)} ADA of voting power`);
  let first = "Pays DReps for their votes";
  if (who.length) first = `Pays DReps that ${who.join(" and ")}`;
  if (s.k_exclude && s.n_pay) first += `, skipping the ${num(s.k_exclude, 0)} largest and paying only the next ${num(s.n_pay, 0)}`;
  else if (s.k_exclude) first += `, except the ${num(s.k_exclude, 0)} largest`;
  else if (s.n_pay) first += `, only the ${num(s.n_pay, 0)} largest that qualify`;
  const a = s.alpha;
  let split;
  if (a === 0) split = "everyone paid gets the same share";
  else if (a === 1) split = "in proportion to voting power";
  else if (a === 0.5) split = "by the square root of voting power, which tilts pay towards smaller DReps";
  else if (a < 1) split = `by voting power to the power ${num(a, 2)}, between equal and proportional pay`;
  else split = `by voting power to the power ${num(a, 2)}, favouring the largest DReps even more than proportional pay`;
  const out = [`${first}: ${split}.`];
  if (s.cap_ada !== null && s.cap_ada !== undefined && Number.isFinite(s.cap_ada)) out.push(`Voting power above ${ada(s.cap_ada)} ADA earns nothing extra.`);
  if (s.rationale_bonus) out.push(`Votes with a published rationale count ${num(1 + s.rationale_bonus, 2).replace(/\.?0+$/, "")}× as much.`);
  if (s.pledge_leverage) {
    out.push(`Pay counts at most ${num(s.pledge_leverage, 0)}× the DRep's own ADA.`);
    if (s.hard_cap) out.push("Voting power itself is limited the same way, which needs a hard fork.");
  }
  if (s.delegator_share) {
    out.push(s.delegator_mode === "flat"
      ? `${pct(s.delegator_share)} of the budget goes to delegators of DReps that vote, at the same rate per ADA whichever DRep they chose.`
      : `${pct(s.delegator_share)} of the budget goes to delegators, each sharing in their DRep's award.`);
  }
  if (always || !D.meta || s.budget_ada !== D.meta.budget) out.push(`Budget: ${ada(s.budget_ada)} ADA over the programme.`);
  return out.join(" ");
}

// ---------- tooltip ----------
let tip;
function showTip(evt, lines) {
  if (!tip) tip = $("#tip") || h("div", { id: "tip", role: "tooltip" }, document.body);
  tip.textContent = "";
  for (const line of lines) {
    const row = h("div", { className: "row" }, tip);
    if (line.key) h("span", { className: "key" }, row).style.background = line.key;
    if (line.value !== undefined) h("span", { className: "v" }, row, line.value);
    if (line.label !== undefined) h("span", { className: line.value !== undefined ? "l" : "" }, row, line.label);
  }
  tip.style.display = "block";
  const r = tip.getBoundingClientRect();
  let x = evt.clientX + 14, y = evt.clientY + 14;
  if (x + r.width > innerWidth - 8) x = evt.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = evt.clientY - r.height - 14;
  tip.style.left = Math.max(8, x) + "px";
  tip.style.top = Math.max(8, y) + "px";
}
function hideTip() { if (tip) { tip.style.display = "none"; tip.classList.remove("note"); } }

// ---------- info bubbles: the explanation behind a heading or number, on hover, focus or tap ----------
let openInfo = null;
function info(parent, content, label = "More about this") {
  const b = h("button", { className: "info", type: "button" }, parent, "i");
  b.setAttribute("aria-label", label);
  wireInfo(b, content);
  return b;
}
function wireInfo(b, content) {
  const lines = () => {
    const c = typeof content === "function" ? content() : content;
    return (Array.isArray(c) ? c : [c]).map((x) => (typeof x === "string" ? { label: x } : x));
  };
  const show = () => {
    const r = b.getBoundingClientRect();
    showTip({ clientX: r.left - 4, clientY: r.bottom - 6 }, lines());
    tip.classList.add("note");
    openInfo = b;
  };
  const hide = () => { if (openInfo === b) { hideTip(); openInfo = null; } };
  b.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") show(); });
  b.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") hide(); });
  b.addEventListener("focus", show);
  b.addEventListener("blur", hide);
  b.addEventListener("click", (e) => { e.stopPropagation(); if (openInfo === b && tip.style.display === "block") hide(); else show(); });
}
addEventListener("click", () => { if (openInfo) { hideTip(); openInfo = null; } });
addEventListener("scroll", () => { if (openInfo) { hideTip(); openInfo = null; } }, { passive: true });
function setupInfo() {
  for (const b of document.querySelectorAll("button.info")) if (!b.textContent) b.textContent = "i";
  for (const b of document.querySelectorAll("button.info[data-info]")) wireInfo(b, b.dataset.info.split("||").map((s) => s.trim()));
}

// ---------- theme ----------
const ICONS = {
  moon: "M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z",
  sun: "M12 7a5 5 0 1 0 0 10a5 5 0 0 0 0-10Zm0-5v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4l1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
};
function icon(name, parent) {
  const svg = el("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 1.8, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" }, parent);
  el("path", { d: ICONS[name] }, svg);
  return svg;
}
function setupTheme() {
  const root = document.documentElement;
  try { const saved = localStorage.getItem("rss-gov-theme"); if (saved) root.dataset.theme = saved; } catch (e) { /* storage unavailable */ }
  const btn = $("#theme");
  if (!btn) return;
  const isDark = () => (root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
  const paint = () => {
    btn.textContent = "";
    icon(isDark() ? "sun" : "moon", btn);
    btn.setAttribute("aria-label", isDark() ? "Switch to the light theme" : "Switch to the dark theme");
    btn.title = btn.getAttribute("aria-label");
  };
  paint();
  btn.addEventListener("click", () => {
    root.dataset.theme = isDark() ? "light" : "dark";
    try { localStorage.setItem("rss-gov-theme", root.dataset.theme); } catch (e) { /* storage unavailable */ }
    paint();
    window.dispatchEvent(new Event("themechange"));
  });
}

// ---------- the optional local server ----------
// `rss-gov serve` answers /api/*; a static copy of the site does not, and the pages then
// fall back to what the data file holds.
async function api(path, body) {
  const options = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch("api/" + path, { cache: "no-store", ...options });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `server answered ${res.status}`);
  return data;
}
async function serverStatus() {
  if (location.protocol === "file:") return null;
  try { return await api("status"); } catch (e) { return null; }
}

function footer() {
  const f = $("footer.site .inner");
  if (!f || !D.meta) return;
  h("span", {}, f, `Chain data to epoch ${D.meta.tip_epoch}`);
  if (D.meta.built) h("span", {}, f, `Built ${date(D.meta.built, false)}`);
  for (const [href, label] of [["index.html", "Results"], ["methods.html", "How it works"], ["propose.html", "Propose a scheme"]]) h("a", { href }, f, label);
  if (D.meta.repository) h("a", { href: D.meta.repository }, f, "Source code");
}

setupTheme();
setupInfo();
footer();
