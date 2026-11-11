"""Proposals from people outside the code: what they may set, checking it, and storage.

A proposal is a point in the reward family of `mechanisms.py`, plus a name, the idea
behind it and, optionally, who proposed it. `FIELDS` is the single description of what a
proposal may set: the web form is generated from it and every submission is checked
against it. Each proposal is kept in `results/proposals/` as three files:

    <name>.yaml      the submission; also a valid input for `rss-gov try`
    <name>.json      the verdict of `rss-gov try`, written when it has been simulated
    <name>.parquet   its runs on the holdout seeds, comparable with the search finalists
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

import yaml

from rss_gov import mechanisms

GENERATED = re.compile(r"g\d+_\d+")  # names the search gives its own designs
META = {"hypothesis": 2000, "author": 80}  # free text a proposal may carry, with length limits
EXTRA = {"submitted", "source"}  # bookkeeping kept with a submission
RESERVED = set(mechanisms.PRESETS)

FIELDS = [
    dict(
        name="budget_ada",
        group="Budget",
        kind="ada",
        min=100_000,
        max=100_000_000,
        step=100_000,
        label="Budget over the whole programme",
        help="Total ADA paid over the programme (36 epochs, about six months). The cost a "
        "year is about twice this, plus a small fee per payment.",
    ),
    dict(
        name="activity_gate",
        group="Who qualifies",
        kind="share",
        min=0,
        max=1,
        step=0.05,
        label="Minimum recent vote rate",
        help="Only DReps that voted on at least this share of the actions closed in the last "
        "12 epochs are paid. Pay always grows with the vote rate; this adds a floor.",
    ),
    dict(
        name="min_stake_ada",
        group="Who qualifies",
        kind="ada",
        min=0,
        max=1_000_000_000,
        step=10_000,
        label="Minimum voting power",
        help="DReps with less delegated voting power than this are not paid.",
    ),
    dict(
        name="min_delegators",
        group="Who qualifies",
        kind="int",
        min=0,
        max=10_000,
        step=1,
        label="Minimum number of delegators",
        help="Delegating accounts of at least 100 ADA. Makes every extra (fake) DRep more "
        "expensive to set up.",
    ),
    dict(
        name="k_exclude",
        group="Who qualifies",
        kind="int",
        min=0,
        max=500,
        step=1,
        label="Skip the largest DReps",
        help="The DReps with the most voting power, this many of them, are not paid.",
    ),
    dict(
        name="n_pay",
        group="Who qualifies",
        kind="int",
        min=0,
        max=5_000,
        step=10,
        label="Pay at most this many DReps (0: no limit)",
        help="After skipping the largest, only the next this-many qualifying DReps by voting "
        "power are paid.",
    ),
    dict(
        name="alpha",
        group="How the money is split",
        kind="number",
        min=0,
        max=1.5,
        step=0.05,
        label="How pay grows with voting power",
        help="0: every paid DRep gets the same. 1: in proportion to voting power. 0.5: square "
        "root, in between. Above 1 favours large DReps even more.",
    ),
    dict(
        name="cap_ada",
        group="How the money is split",
        kind="ada",
        optional=True,
        min=0,
        max=10_000_000_000,
        step=1_000_000,
        label="Count at most this much voting power (empty: no cap)",
        help="Voting power above this counts for nothing when the money is split. Voting power "
        "itself is not changed.",
    ),
    dict(
        name="rationale_bonus",
        group="How the money is split",
        kind="share",
        min=0,
        max=5,
        step=0.25,
        label="Extra weight for votes with a published rationale",
        help="100% means a DRep whose votes all carry a rationale counts double. The chain shows "
        "that a rationale exists, not whether it is any good.",
    ),
    dict(
        name="pledge_leverage",
        group="Own stake",
        kind="number",
        min=0,
        max=1_000_000,
        step=10,
        label="Count at most this many times the DRep's own stake (0: off)",
        help="Ties pay to stake the DRep holds itself: with 100, a DRep with 1,000 ADA of its "
        "own counts at most 100,000 ADA of voting power. Needs DReps to declare their accounts.",
    ),
    dict(
        name="hard_cap",
        group="Own stake",
        kind="bool",
        label="Also limit voting power itself (needs a hard fork)",
        help="Applies the own-stake limit to voting power, not only to pay. This changes how "
        "actions are ratified, so it needs a hard fork.",
    ),
    dict(
        name="delegator_share",
        group="Delegators",
        kind="share",
        min=0,
        max=1,
        step=0.05,
        label="Share of the budget paid to delegators",
        help="Paid only through DReps that voted. Delegating to always-abstain or to a DRep "
        "that does not vote earns nothing.",
    ),
    dict(
        name="delegator_mode",
        group="Delegators",
        kind="choice",
        choices=[
            ["passthrough", "Share the DRep's award"],
            ["flat", "Same yield per ADA"],
        ],
        label="How delegators are paid",
        help="Passthrough follows the DRep rule. Flat pays delegators of small and large DReps "
        "alike, per ADA and per unit of the DRep's vote rate.",
    ),
]
BY_NAME = {f["name"]: f for f in FIELDS}


def _number(field, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field['name']} must be a number")
    value = float(value)
    if not math.isfinite(value) or not field["min"] <= value <= field["max"]:
        low, high = (f"{v:,.0f}" if v >= 1000 else f"{v:g}" for v in (field["min"], field["max"]))
        raise ValueError(f"{field['name']} must be between {low} and {high}")
    return value


def _value(field, value):
    kind = field["kind"]
    if field.get("optional") and value in (None, ""):
        return None
    if kind == "bool":
        if not isinstance(value, bool):
            raise ValueError(f"{field['name']} must be true or false")
        return value
    if kind == "choice":
        if value not in [c[0] for c in field["choices"]]:
            raise ValueError(f"{field['name']} must be one of {[c[0] for c in field['choices']]}")
        return value
    number = _number(field, value)
    if kind == "int":
        if number != int(number):
            raise ValueError(f"{field['name']} must be a whole number")
        return int(number)
    return number


def _text(key, value):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{key} must be text")
    value = "".join(c for c in value if c in "\n\t" or c.isprintable()).strip()
    if len(value) > META[key]:
        raise ValueError(f"{key} is longer than {META[key]} characters")
    return value


def slug(text):
    """A safe design name: lower case letters, digits and underscores, starting with a letter."""
    name = re.sub(r"[^a-z0-9]+", "_", str(text or "").lower()).strip("_")[:40].strip("_")
    if not name:
        return "proposal"
    if not name[0].isalpha() or GENERATED.fullmatch(name) or name in RESERVED:
        name = f"p_{name}"
    return name


def unique(name, taken):
    if name not in taken:
        return name
    n = 2
    while f"{name}_{n}" in taken:
        n += 1
    return f"{name}_{n}"


def parse(payload, taken=()):
    """Check a submission. Returns (Scheme, meta) or raises ValueError with a readable reason."""
    if not isinstance(payload, dict):
        raise ValueError("expected an object with the proposal's fields")
    unknown = set(payload) - set(BY_NAME) - set(META) - {"name"}
    if unknown:
        raise ValueError(f"unknown fields: {', '.join(sorted(map(str, unknown)))}")
    values = {name: _value(BY_NAME[name], payload[name]) for name in BY_NAME if name in payload}
    if "budget_ada" not in values:
        raise ValueError("budget_ada is required")
    meta = {key: _text(key, payload.get(key)) for key in META}
    name = unique(slug(payload.get("name")), set(taken))
    scheme = mechanisms.scheme(name=name, **values)  # raises on inconsistent values
    return scheme, meta


def known(config):
    """Every design in use: the config's schemes, the search finalists and stored proposals."""
    results = Path(config["results"])
    out = {}
    for row in config["experiment"]["schemes"]:
        scheme = mechanisms.from_config(row, float(config["programme"]["budget_ada"]))
        out[scheme.name] = scheme
    finalists = results / "search_finalists.yaml"
    if finalists.exists():
        for row in yaml.safe_load(finalists.read_text()) or []:
            out[row["name"]] = mechanisms.from_config(row, 0)
    for name, row in submitted(results).items():
        out[name] = mechanisms.from_config(split(row)[0], 0)
    return out


def accept(config, payload):
    """Check a submission against the rules and every known design: (Scheme, meta)."""
    designs = known(config)
    scheme, meta = parse(payload, set(designs) | taken(config["results"]))
    if not scheme.paid:
        raise ValueError("a proposal must have a budget")
    if scheme.hard_cap and not config["search"].get("allow_hard_fork", False):
        raise ValueError("hard-fork designs are switched off in config.yaml")
    mine = {k: v for k, v in scheme.to_dict().items() if k != "name"}
    for name, other in designs.items():
        if {k: v for k, v in other.to_dict().items() if k != "name"} == mine:
            raise ValueError(f"this rule is already listed as {name}")
    return scheme, meta


FENCE = re.compile(r"```ya?ml[ \t]*\n(.*?)```", re.S)
SECTION = re.compile(r"^###[ \t]*Hypothesis[ \t]*\n(.*?)(?=^###[ \t]|\Z)", re.S | re.M)


def from_text(text):
    """A submission from text: a YAML proposal, or a GitHub issue that contains one.

    The issue form puts the rule in a ```yaml block under its own heading, and the idea
    behind it under "### Hypothesis". Everything read here is checked by `parse` after.
    """
    block = FENCE.search(text)
    rows = yaml.safe_load(block.group(1) if block else text)
    if isinstance(rows, list) and len(rows) == 1:
        rows = rows[0]
    if not isinstance(rows, dict):
        raise ValueError("expected one proposal: a YAML mapping of its fields")
    section = SECTION.search(text) if block else None
    idea = section.group(1).strip() if section else ""
    if idea and idea != "_No response_" and not rows.get("hypothesis"):
        rows["hypothesis"] = idea
    return rows


def split(row):
    """A `try` row without the proposal's text: (scheme row, meta)."""
    if not isinstance(row, dict):
        return row, {}
    row = dict(row)
    meta = {k: row.pop(k) for k in list(row) if k in META or k in EXTRA}
    return row, meta


def folder(results):
    path = Path(results) / "proposals"
    path.mkdir(parents=True, exist_ok=True)
    return path


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def submitted(results):
    """Every stored submission by name: scheme fields plus meta."""
    out = {}
    for path in sorted(folder(results).glob("*.yaml")):
        rows = yaml.safe_load(path.read_text()) or []
        if rows and isinstance(rows[0], dict):
            out[path.stem] = rows[0]
    return out


def taken(results):
    path = folder(results)
    return {p.stem for p in path.iterdir() if p.suffix in (".yaml", ".json")}


def submit(results, scheme, meta, source):
    """Store a checked submission; returns its path, a valid `rss-gov try` input."""
    row = {**scheme.to_dict(), **meta, "submitted": now(), "source": source}
    path = folder(results) / f"{scheme.name}.yaml"
    path.write_text(yaml.safe_dump([row], sort_keys=False, allow_unicode=True))
    return path


def fingerprint(results):
    """Identifies the calibration a proposal was simulated against."""
    path = Path(results) / "calibration.json"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.exists() else None


def record(results, scheme, entry, runs, meta):
    """Keep what `rss-gov try` found for one proposal."""
    path = folder(results)
    stored = path / f"{scheme.name}.yaml"
    if not stored.exists():
        submit(results, scheme, {k: meta.get(k) or "" for k in META}, meta.get("source", "cli"))
    else:  # a rerun may bring new text for the same proposal
        row = (yaml.safe_load(stored.read_text()) or [{}])[0]
        fresh = {k: meta[k] for k in META if meta.get(k) and meta[k] != row.get(k)}
        if fresh:
            stored.write_text(
                yaml.safe_dump([{**row, **fresh}], sort_keys=False, allow_unicode=True)
            )
    if runs is not None:
        runs.to_parquet(path / f"{scheme.name}.parquet")
    entry = {**entry, **{k: meta[k] for k in META if k in meta}}
    entry.update(evaluated=now(), calibration=fingerprint(results))
    (path / f"{scheme.name}.json").write_text(json.dumps(entry, indent=1, default=float))


def listing(results):
    """Every proposal with its state: queued (not simulated yet), done or stale."""
    path = folder(results)
    current = fingerprint(results)
    rows = []
    for name, row in submitted(results).items():
        item = dict(
            name=name,
            author=row.get("author", ""),
            hypothesis=row.get("hypothesis", ""),
            submitted=row.get("submitted"),
            source=row.get("source", ""),
        )
        result = path / f"{name}.json"
        if result.exists():
            entry = json.loads(result.read_text())
            item.update(
                state="done" if entry.get("calibration") == current else "stale",
                rule=entry.get("rule"),
                accepted=entry.get("accepted"),
                reason=entry.get("reason"),
                change=entry.get("change_from_unpaid"),
                evaluated=entry.get("evaluated"),
            )
        else:
            item.update(state="queued")
        try:
            scheme_row, _ = split(row)
            item.setdefault("rule", mechanisms.from_config(scheme_row, 0).label())
        except (TypeError, ValueError):
            item.setdefault("rule", "")
        rows.append(item)
    rows.sort(key=lambda r: r.get("submitted") or "", reverse=True)
    return rows
