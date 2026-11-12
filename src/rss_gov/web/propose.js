// The proposal form. Fields, limits and help texts come from rss_gov/proposals.py via data.js.
const F = D.form;
const values = { ...F.defaults };
const OPEN = new Set(["Budget", "How the money is split"]); // always shown; the other groups fold away
let previewTimer = null;
const REPO = D.meta.repository ? D.meta.repository.replace(/\/$/, "") : null;
const YEAR = D.meta.epochs_per_year;
const inputs = {};
const groups = {};

const ALPHA_WORDS = [[0, "everyone the same"], [0.5, "square root"], [1, "in proportion"]];

function readout(field, v) {
  if (v === null || v === undefined || v === "") return field.optional ? "no cap" : "–";
  if (field.kind === "ada") return ada(v) + " ADA";
  if (field.kind === "share") return pct(v);
  if (field.name === "alpha") {
    const word = ALPHA_WORDS.find(([a]) => Math.abs(a - v) < 1e-9);
    return num(v, 2) + (word ? ` (${word[1]})` : v > 1 ? " (favours the largest)" : "");
  }
  if (field.name === "pledge_leverage") return v ? `${num(v, 0)}×` : "off";
  return num(v, 0);
}
const isDefault = (f) => {
  const v = values[f.name], d = F.defaults[f.name];
  return v === d || ((v === null || v === "") && (d === null || d === undefined));
};

// ---------- the form ----------
function buildForm() {
  const form = $("#fields");
  for (const group of [...new Set(F.fields.map((f) => f.group))]) {
    const box = h("details", { className: "group", open: OPEN.has(group) }, form);
    const summary = h("summary", {}, box, group);
    const note = h("span", { className: "state-note" }, summary);
    const set = h("fieldset", {}, box);
    groups[group] = { box, note };
    for (const f of F.fields.filter((q) => q.group === group)) {
      const row = h("div", { className: "field" }, set);
      const id = "f-" + f.name;
      const head = h("div", { className: "title-row" }, row);
      h("label", { htmlFor: id }, head, f.label);
      info(head, f.help, "About " + f.label);
      const control = h("div", { className: "control" }, row);
      let input;
      if (f.kind === "bool") {
        input = h("input", { type: "checkbox", id }, control);
        input.addEventListener("change", () => set1(f.name, input.checked));
      } else if (f.kind === "choice") {
        input = h("select", { id }, control);
        for (const [value, label] of f.choices) h("option", { value }, input, label);
        input.addEventListener("change", () => set1(f.name, input.value));
      } else {
        const slider = f.max - f.min <= 10;
        input = h("input", { type: slider ? "range" : "number", id, min: f.min, max: f.max, step: f.step }, control);
        if (f.optional) input.placeholder = "no cap";
        input.addEventListener("input", () => {
          const raw = input.value.trim();
          set1(f.name, raw === "" ? (f.optional ? null : f.min) : Number(raw));
        });
      }
      const out = h("div", { className: "readout" }, control);
      inputs[f.name] = { f, input, out };
    }
  }
  for (const id of ["m-name", "m-hypothesis", "m-author"]) $("#" + id).addEventListener("input", changed);
}
function set1(name, v) {
  values[name] = v;
  changed();
}
function fill(from) {
  Object.assign(values, F.defaults, from);
  for (const { f, input } of Object.values(inputs)) {
    const v = values[f.name];
    if (f.kind === "bool") input.checked = !!v;
    else input.value = v === null || v === undefined ? "" : v;
  }
  for (const [group, { box }] of Object.entries(groups)) {
    if (!OPEN.has(group) && F.fields.some((f) => f.group === group && !isDefault(f))) box.open = true;
  }
  changed();
}
function presets() {
  const sel = $("#preset");
  const named = h("optgroup", { label: "Named schemes" }, sel);
  for (const name of Object.keys(F.presets)) h("option", { value: "preset:" + name }, named, pretty(name));
  const others = D.schemes.filter((s) => s.kind === "search" || s.kind === "proposed");
  if (others.length) {
    const group = h("optgroup", { label: "Found by search, or proposed" }, sel);
    for (const s of others) h("option", { value: "design:" + s.name }, group, pretty(s.name) + (s.breaks === "" ? " (inside every guardrail)" : ""));
  }
  sel.addEventListener("change", () => {
    const [kind, name] = sel.value.split(/:(.*)/s);
    fill(kind === "preset" ? F.presets[name] : D.schemes.find((s) => s.name === name).scheme);
  });
  const m = /from=([^&]+)/.exec(location.hash);
  const start = m && D.schemes.find((s) => s.name === decodeURIComponent(m[1]));
  if (start) {
    const key = F.presets[start.name] ? "preset:" + start.name : "design:" + start.name;
    if ([...sel.options].some((o) => o.value === key)) sel.value = key;
    $("#m-name").value = start.name + "_variant";
    fill(start.scheme);
  } else {
    sel.value = "preset:proportional";
    fill(F.presets.proportional);
  }
}

// ---------- what is sent ----------
function payload() {
  const out = { name: $("#m-name").value.trim(), hypothesis: $("#m-hypothesis").value.trim(), author: $("#m-author").value.trim() };
  for (const f of F.fields) {
    let v = values[f.name];
    if (f.kind === "int" && v !== null) v = Math.round(v);
    if (f.optional && (v === "" || v === undefined)) v = null;
    out[f.name] = v;
  }
  if (!out.pledge_leverage) out.hard_cap = false;
  return out;
}
function yaml(p, withIdea = true) {
  const q = (v) => (v === null || v === undefined ? "null" : typeof v === "string" ? JSON.stringify(v) : String(v));
  const lines = [`- name: ${q(p.name || "my_proposal")}`];
  if (p.hypothesis && withIdea) lines.push(`  hypothesis: ${q(p.hypothesis)}`);
  if (p.author) lines.push(`  author: ${q(p.author)}`);
  for (const f of F.fields) lines.push(`  ${f.name}: ${q(p[f.name])}`);
  return lines.join("\n") + "\n";
}

function changed() {
  for (const { f, input, out } of Object.values(inputs)) {
    out.textContent = f.kind === "bool" || f.kind === "choice" ? "" : readout(f, values[f.name]);
    if (f.name === "hard_cap") input.disabled = !values.pledge_leverage;
  }
  for (const [group, { note }] of Object.entries(groups)) {
    const changedHere = F.fields.filter((f) => f.group === group && !isDefault(f)).length;
    note.textContent = OPEN.has(group) ? "" : changedHere ? `${changedHere} set` : "off";
  }
  const p = payload();
  $("#plain").textContent = describe(p, true);
  $("#yaml").textContent = yaml(p);
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => renderChecks(check(p)), 150);
}

// ---------- instant checks: the rule applied to today's DReps, in this browser ----------
// The same limits proposals.py applies, so a rule that passes here is accepted there.
function invalid(p) {
  for (const f of F.fields) {
    const v = p[f.name];
    if (f.kind === "bool" || f.kind === "choice" || (f.optional && v === null)) continue;
    if (typeof v !== "number" || !Number.isFinite(v) || v < f.min || v > f.max) return `${f.label}: between ${readout(f, f.min)} and ${readout(f, f.max)}.`;
    if (f.kind === "int" && v !== Math.round(v)) return `${f.label}: a whole number.`;
  }
  return null;
}
function sameAs(p) {
  const keys = F.fields.map((f) => f.name);
  const same = D.schemes.find((s) => keys.every((k) => (s.scheme[k] ?? null) === (p[k] ?? null)));
  return same ? same.name : null;
}
let accountsLoading = false;
function check(p) {
  const today = window.RSS_TODAY;
  if (!today) return { error: "The instant checks need today.js, which this copy of the site lacks." };
  const bad = invalid(p);
  if (bad) return { error: bad };
  if (p.delegator_share > 0 && !window.RSS_ACCOUNTS) {
    if (!accountsLoading) { // about 1 MB, so it is fetched only for rules that pay delegators
      accountsLoading = true;
      const s = h("script", { src: today.accounts }, document.body);
      s.addEventListener("load", changed);
      s.addEventListener("error", () => { accountsLoading = false; renderChecks({ error: "Could not load the delegator accounts." }); });
    }
    return { loading: true };
  }
  return {
    pilot_testable: !p.hard_cap,
    notes: Checks.notes(p),
    checks: Checks.analyse(p, today, window.RSS_ACCOUNTS),
    annual_cost: (p.budget_ada * YEAR) / today.epochs,
    same_as: sameAs(p),
  };
}
function renderChecks(r) {
  const host = $("#checks"), badges = $("#badges");
  host.textContent = "";
  badges.textContent = "";
  if (r.loading) {
    h("p", { className: "small" }, host, "Loading today's delegators for the delegator checks…");
    return;
  }
  if (r.error) {
    h("p", { className: "status err" }, host, r.error);
    return;
  }
  h("span", { className: "badge" }, badges, r.pilot_testable ? "Works on today's Cardano" : "Needs a hard fork");
  if (r.same_as) h("span", { className: "badge bad" }, badges, "Same rule as " + pretty(r.same_as));
  const c = r.checks;
  const limit = D.meta.split_limit;
  const ok = c.split_gain <= limit + 1e-9;
  const kpis = h("div", { className: "kpis" }, host);
  const kpi = (label, value, cls = "") => { const k = h("div", { className: "kpi " + cls }, kpis); h("div", { className: "k" }, k, label); h("div", { className: "v" }, k, value); };
  kpi("DReps paid today", num(c.paid_dreps, 0));
  kpi("Cost a year, about", ada(r.annual_cost) + " ADA");
  kpi("Largest award per epoch", c.max_award === null ? "–" : ada(c.max_award) + " ADA");
  kpi(`Sybil risk (limit ${pct(limit)})`, (ok ? "✓ " : "✕ ") + pct(c.split_gain), ok ? "good" : "bad");
  h("p", { className: "small" }, host, ok
    ? "Posing as several DReps would not pay: this rule stays within the Sybil limit."
    : `Posing as several DReps would gain ${pct(c.split_gain)} of the budget, over the ${pct(limit)} limit. It will be simulated anyway, and flagged.`);
  const more = h("details", { className: "more" }, host);
  h("summary", {}, more, "More exact checks");
  const dl = h("dl", { className: "facts" }, more);
  const row = (k, v) => { h("dt", {}, dl, k); h("dd", {}, dl, v); };
  if (c.top10_award_share !== null) row("Share paid to the 10 largest", pct(c.top10_award_share));
  row(`An outsider with ${ada(D.meta.capital)} ADA could take`, pct(c.newcomer_capture));
  row("…of which from splitting", pct(c.newcomer_extra));
  row("Most an existing DRep gains by splitting", pct(c.incumbent_extra));
  row("Voting power kept", pct(c.power_kept));
  if (c.delegator_dust_share !== null) row(`Delegator payments under ${D.meta.min_payout} ADA`, pct(c.delegator_dust_share));
  if (r.notes && r.notes.length) {
    const ul = h("ul", { className: "notes" }, more);
    for (const n of r.notes) h("li", {}, ul, n);
  }
}

// ---------- actions ----------
function actions() {
  const host = $("#actions");
  host.textContent = "";
  if (REPO) {
    // GitHub's issue form for proposals, filled in: the proposer only has to press Submit.
    const b = h("a", { className: "button primary", target: "_blank", rel: "noopener" }, host, "Submit on GitHub");
    b.title = "Opens a filled-in proposal on GitHub. Needs a GitHub account.";
    b.addEventListener("click", (e) => {
      const p = payload();
      const bad = p.name ? invalid(p) : "Give the proposal a short name first (step 3).";
      if (bad) { e.preventDefault(); say(bad, "err"); return; }
      const q = new URLSearchParams({ template: "proposal.yml", title: "Scheme proposal: " + p.name, hypothesis: p.hypothesis, rule: yaml(p, false) });
      b.href = `${REPO}/issues/new?${q}`;
      say("Opened on GitHub: press “Create” there to send it. A maintainer then starts the simulation.", "ok");
    });
  }
  const dl = h("button", { className: "ghost", type: "button" }, host, "Download");
  dl.title = "Download the proposal as a YAML file, for rss-gov try";
  dl.addEventListener("click", () => {
    const p = payload();
    const blob = new Blob([yaml(p)], { type: "text/yaml" });
    const a = h("a", { href: URL.createObjectURL(blob), download: (p.name || "proposal").replace(/[^a-z0-9_]+/gi, "_") + ".yaml" }, document.body);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  });
  const cp = h("button", { className: "ghost", type: "button" }, host, "Copy");
  cp.title = "Copy the proposal as YAML";
  cp.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(yaml(payload())); say("Copied.", "ok"); } catch (e) { say("Copying is blocked here; use the YAML below.", "err"); }
  });
}
function say(message, kind = "") {
  const s = $("#status");
  s.className = "status " + kind;
  s.textContent = message;
}

// ---------- the list of proposals ----------
const STATE = {
  queued: ["var(--neutral)", "Waiting"],
  done: ["var(--good)", "Simulated"],
  stale: ["var(--neutral)", "Needs re-running"],
};
function renderList(rows) {
  const host = $("#list");
  host.textContent = "";
  if (!rows.length) { h("p", { className: "empty" }, host, "No proposals yet. Be the first."); return; }
  const table = h("table", {}, host);
  const head = h("tr", {}, h("thead", {}, table));
  const shown = ["participation", "tau67", "split_gain"].filter((a) => AX[a]);
  for (const c of ["Proposal", "State"]) h("th", {}, head, c);
  for (const a of shown) { const th = h("th", { className: "num" }, head, AX[a].short); h("br", {}, th); h("span", { style: "font-weight:400; color:var(--muted)" }, th, AX[a].change); }
  h("th", {}, head, "Adds a trade-off?");
  const body = h("tbody", {}, table);
  for (const p of rows) {
    const tr = h("tr", {}, body);
    const td = h("td", { style: "min-width:260px" }, tr);
    const title = h("div", { className: "dname" }, td);
    if (p.state === "done") h("a", { href: "index.html#design=" + encodeURIComponent(p.name) }, title, pretty(p.name));
    else title.textContent = pretty(p.name);
    h("div", { className: "small" }, td, `${p.author || "Anonymous"} · ${date(p.submitted, false)}`);
    if (p.hypothesis) { const q = h("div", { className: "small", style: "max-width:460px; margin-top:4px; font-style:italic" }, td, "“" + (p.hypothesis.length > 220 ? p.hypothesis.slice(0, 219) + "…" : p.hypothesis) + "”"); q.title = p.hypothesis; }
    const [colour, label] = STATE[p.state] || ["var(--neutral)", p.state];
    const st = h("td", {}, tr);
    const span = h("span", { className: "state" }, st);
    h("span", { className: "dot", style: `background:${colour}` }, span);
    span.appendChild(document.createTextNode(label));
    if (p.state === "done" && !D.schemes.some((s) => s.name === p.name)) h("div", { className: "small" }, st, "reload the results page to see it");
    for (const a of shown) {
      const v = p.change ? p.change[a] : null;
      h("td", { className: "num" }, tr, v === null || v === undefined ? "–" : fmt(a, v, !AX[a].exact));
    }
    h("td", { className: "small" }, tr, p.accepted === true ? "Yes" : p.accepted === false ? "No: " + (p.reason || "") : "–");
  }
}
function showList() {
  renderList(D.proposals || []);
  if (REPO) {
    const note = h("p", { className: "small", style: "margin:12px 0 0" }, $("#list"), "Proposals still waiting for review or simulation are ");
    h("a", { href: `${REPO}/issues?q=${encodeURIComponent("is:issue is:open label:proposal")}`, target: "_blank", rel: "noopener" }, note, "open on GitHub");
    note.appendChild(document.createTextNode("."));
  }
}

function start() {
  buildForm();
  presets();
  if (D.search) $("#runs").textContent = num(D.search.holdout_seeds, 0); // proposals run on the holdout seeds
  const mode = $("#mode");
  const badge = (text, cls = "") => h("span", { className: "badge " + cls }, mode, text);
  if (REPO) {
    badge("✓ Submissions open: through GitHub, simulated on GitHub's servers", "good");
  } else {
    badge("Offline copy: download your proposal");
  }
  actions();
  changed();
  showList();
}
start();
