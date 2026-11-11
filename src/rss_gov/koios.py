"""Download Cardano governance history from the public Koios API into parquet tables.

Every request is a read. Raw pages are cached on disk, so an interrupted pull resumes
and a finished pull can be rebuilt offline. Nothing here is modelled or estimated.
"""

import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://api.koios.rest/api/v1"
PAGE = 1000
SHELLEY_START, SHELLEY_EPOCH, EPOCH_SECONDS = 1596059091, 208, 432000
SPECIAL = ("drep_always_abstain", "drep_always_no_confidence")
FIRST_GOVERNANCE_EPOCH = 507


def epoch_of(block_time):
    return SHELLEY_EPOCH + (int(block_time) - SHELLEY_START) // EPOCH_SECONDS


def api_key():
    """KOIOS_API_KEY from the environment, else from ./.env or ../.env. Optional."""
    if os.environ.get("KOIOS_API_KEY"):
        return os.environ["KOIOS_API_KEY"]
    for folder in (Path.cwd(), Path.cwd().parent):
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                name, _, value = line.partition("=")
                if name.strip() == "KOIOS_API_KEY" and value.strip():
                    return value.strip().strip("\"'")
    return None


class Koios:
    def __init__(self, cache, key=None, pause=0.15, log=print):
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.key, self.pause, self.log, self.requests = key, pause, log, 0

    def page(self, endpoint, params=None, body=None):
        params = dict(params or {})
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{BASE}/{endpoint}" + (f"?{query}" if query else "")
        name = hashlib.sha256((url + json.dumps(body, sort_keys=True)).encode()).hexdigest()
        path = self.cache / f"{name}.json.gz"
        if path.exists():
            return json.loads(gzip.decompress(path.read_bytes()))
        headers = {"accept": "application/json", "user-agent": "governance-research-client"}
        if self.key:
            headers["authorization"] = f"Bearer {self.key}"
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["content-type"] = "application/json"
        for attempt in range(8):
            try:
                request = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(request, timeout=120) as response:
                    rows = json.loads(response.read())
                break
            except urllib.error.HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504) or attempt == 7:
                    raise RuntimeError(f"Koios {error.code} for {endpoint}") from None
                wait = float(error.headers.get("retry-after") or 2 ** (attempt + 1))
                self.log(f"  Koios {error.code} on {endpoint}; retrying in {min(wait, 120):.0f}s")
            except (urllib.error.URLError, TimeoutError):
                if attempt == 7:
                    raise RuntimeError(f"Koios unreachable for {endpoint}") from None
                wait = 2 ** (attempt + 1)
                self.log(f"  Koios timeout on {endpoint}; retrying in {wait}s")
            time.sleep(min(wait, 120))
        if not isinstance(rows, list):
            raise RuntimeError(f"Koios returned a non-list for {endpoint}")
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(gzip.compress(json.dumps(rows).encode()))
        tmp.replace(path)
        self.requests += 1
        time.sleep(self.pause)
        return rows

    def count(self, endpoint, params):
        """Exact row count from the Content-Range header, without downloading the rows."""
        query = "&".join(f"{k}={v}" for k, v in params.items())
        headers = {
            "accept": "application/json",
            "user-agent": "governance-research-client",
            "Prefer": "count=exact",
            "Range": "0-0",
        }
        if self.key:
            headers["authorization"] = f"Bearer {self.key}"
        request = urllib.request.Request(f"{BASE}/{endpoint}?{query}", headers=headers)
        with urllib.request.urlopen(request, timeout=180) as response:
            return int(response.headers["content-range"].rsplit("/", 1)[1])

    def all(self, endpoint, params=None, body=None, order=None):
        """Offset pagination with a stable order; stops at the first short page."""
        rows, offset = [], 0
        while True:
            p = dict(params or {}, limit=PAGE, offset=offset)
            if order:
                p["order"] = order
            chunk = self.page(endpoint, p, body)
            rows += chunk
            if len(chunk) < PAGE:
                return rows
            offset += PAGE


def pull(out, key=None, delegators=True, log=print):
    """Fetch everything the study needs. `delegators=False` skips the account cross-section."""
    out = Path(out)
    k = Koios(out / "raw", key, log=log)
    tip = k_tip(out)
    epoch = tip["epoch_no"]
    log(f"tip epoch {epoch}; key {'present' if key else 'absent (public tier)'}")
    tables = {}

    rows = k.all(
        "proposal_list",
        {
            "select": "proposal_id,proposal_type,proposed_epoch,ratified_epoch,enacted_epoch,"
            "dropped_epoch,expired_epoch,expiration,deposit,block_time,withdrawal,meta_url",
            "proposed_epoch": f"lte.{epoch}",
        },
        order="block_time.asc,proposal_id.asc",
    )
    for r in rows:
        r["withdrawal_lovelace"] = sum(int(w.get("amount", 0)) for w in (r.pop("withdrawal") or []))
        r["deposit"] = int(r["deposit"])
        r["has_metadata"] = bool(r.pop("meta_url"))
    tables["proposals"] = pd.DataFrame(rows)
    log(f"proposals {len(rows)}")

    rows = k.all(
        "vote_list",
        {
            "select": "vote_tx_hash,voter_role,voter_id,proposal_id,epoch_no,block_time,vote,meta_url",
            "epoch_no": f"lte.{epoch}",
        },
        order="block_time.asc,vote_tx_hash.asc,proposal_id.asc,voter_id.asc",
    )
    for r in rows:
        r["has_rationale"] = bool(r.pop("meta_url"))
    tables["votes"] = pd.DataFrame(rows).drop_duplicates()
    log(f"votes {len(rows)}")

    rows = []
    for e in range(FIRST_GOVERNANCE_EPOCH, epoch + 1):
        rows += k.all("drep_voting_power_history", {"_epoch_no": e}, order="drep_id.asc")
    power = pd.DataFrame(rows)
    power["amount"] = power["amount"].astype("int64")
    tables["drep_power"] = power
    log(f"drep power rows {len(power)} over epochs {power.epoch_no.min()}..{power.epoch_no.max()}")

    rows = k.all(
        "drep_updates",
        {"select": "drep_id,update_tx_hash,cert_index,block_time,action,meta_url"},
        order="block_time.asc,update_tx_hash.asc,cert_index.asc",
    )
    updates = pd.DataFrame(rows)
    updates["epoch_no"] = updates["block_time"].map(epoch_of)
    updates["has_metadata"] = updates.pop("meta_url").notna()
    tables["drep_updates"] = updates[updates.epoch_no <= epoch]
    log(f"drep updates {len(updates)}")

    ids = sorted(r["drep_id"] for r in k.all("drep_list", order="drep_id.asc"))
    info = []
    for i in range(0, len(ids), 50):
        info += k.page("drep_info", None, {"_drep_ids": ids[i : i + 50]})
    dreps = pd.DataFrame(info)
    dreps["amount"] = dreps["amount"].fillna(0).astype("int64")
    dreps["deposit"] = dreps["deposit"].fillna(0).astype("int64")
    dreps["has_metadata"] = dreps.pop("meta_url").notna()
    tables["dreps"] = dreps.drop(columns=["meta_hash", "hex"], errors="ignore")
    log(f"dreps {len(dreps)}")

    rows = k.page(
        "epoch_params",
        {
            "select": "epoch_no,dvt_motion_no_confidence,dvt_committee_normal,"
            "dvt_committee_no_confidence,dvt_update_to_constitution,dvt_hard_fork_initiation,"
            "dvt_p_p_network_group,dvt_p_p_economic_group,dvt_p_p_technical_group,"
            "dvt_p_p_gov_group,dvt_treasury_withdrawal,gov_action_lifetime,gov_action_deposit,"
            "drep_deposit,drep_activity,min_fee_a,min_fee_b,coins_per_utxo_size",
            "epoch_no": f"gte.{FIRST_GOVERNANCE_EPOCH}",
            "order": "epoch_no.asc",
        },
    )
    tables["params"] = pd.DataFrame(rows)

    rows = []
    for pid in tables["proposals"]["proposal_id"]:
        for r in k.page("proposal_voting_summary", {"_proposal_id": pid}):
            rows.append(r | {"proposal_id": pid})
    tables["voting_summary"] = pd.DataFrame(rows)
    log(f"voting summaries {len(rows)}")

    tables["totals"] = pd.DataFrame(k.page("totals", {"epoch_no": f"gte.{FIRST_GOVERNANCE_EPOCH}"}))

    if delegators:
        counts = dict(zip(dreps.drep_id, dreps.live_delegator_count.fillna(0).astype(int)))
        targets = list(SPECIAL) + sorted(d for d, n in counts.items() if n > 0)
        rows = []
        for n, drep in enumerate(targets):
            rows += delegator_rows(k, drep, counts.get(drep))
            if n % 100 == 0:
                log(f"delegators: {n}/{len(targets)} representatives, {len(rows)} rows")
        tables["delegators"] = pd.DataFrame(
            rows, columns=["drep_id", "stake_address", "delegated_epoch", "amount", "weight"]
        )
        log(f"delegator rows {len(rows)}")

    tables["drep_own"] = own_accounts(k, ids, tables["drep_updates"], log)

    processed = out / "tables"
    processed.mkdir(parents=True, exist_ok=True)
    manifest = dict(tip=tip, requests=k.requests, tables={})
    for name, frame in tables.items():
        path = processed / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        manifest["tables"][name] = dict(
            rows=len(frame), sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log(f"wrote {len(tables)} tables to {processed} ({k.requests} new requests)")
    return manifest


def k_tip(out):
    """The tip pins the pull: it is fetched once and reused when resuming."""
    path = Path(out) / "tip.json"
    if path.exists():
        return json.loads(path.read_text())
    request = urllib.request.Request(
        f"{BASE}/tip",
        headers={"accept": "application/json", "user-agent": "governance-research-client"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        tip = json.loads(response.read())[0]
    tip = {k: tip[k] for k in ("epoch_no", "block_time", "block_height", "hash")}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tip))
    return tip


FULL_LIST_LIMIT = 5000  # accounts; larger delegator lists are fetched as exact tail + sample
TAIL_DIGITS = 12  # lovelace digits: accounts of at least 100,000 ADA are always fetched exactly
SAMPLE_PAGES = 3


def delegator_rows(k, drep, count):
    """Current delegators of one target as (drep, account, delegated_epoch, lovelace, weight).

    The API recomputes the whole list for every page, so very long lists are expensive.
    For those, every account of at least 100,000 ADA is fetched exactly and the remaining
    small accounts are represented by evenly spaced sample pages with a weight. Account
    order is by address hash, so a page is an unbiased sample of the small accounts.
    """
    select = {"_drep_id": drep, "select": "stake_address,epoch_no,amount"}
    order = "stake_address.asc"

    def tidy(chunk, weight=1.0):
        return [(drep, r["stake_address"], r["epoch_no"], int(r["amount"]), weight) for r in chunk]

    first = k.page("drep_delegators", select | {"limit": PAGE, "offset": 0, "order": order})
    if len(first) < PAGE:
        return tidy(first)
    if count is None:
        count = k.count("drep_delegators", select)
    if count <= FULL_LIST_LIMIT:
        return tidy(k.all("drep_delegators", select, order=order))
    tail = k.all(
        "drep_delegators", select | {"amount": "like." + "_" * TAIL_DIGITS + "*"}, order=order
    )
    tail = [r for r in tail if int(r["amount"]) >= 10 ** (TAIL_DIGITS - 1)]
    body = list(first)
    for i in range(1, SAMPLE_PAGES):
        offset = (count * i // SAMPLE_PAGES) // PAGE * PAGE
        body += k.page(
            "drep_delegators", select | {"limit": PAGE, "offset": offset, "order": order}
        )
    body = [r for r in body if int(r["amount"]) < 10 ** (TAIL_DIGITS - 1)]
    weight = max(1.0, (count - len(tail)) / max(1, len(body)))
    return tidy(tail) + tidy(body, weight)


def own_accounts(k, drep_ids, updates, log=print):
    """Accounts that plausibly belong to each DRep, with their current balance.

    A DRep's own stake is not a ledger concept. Two clues are on chain: the account that
    funded the DRep's registration transaction, and the payment address the DRep declares
    in its metadata. Both are proxies: a registration can be paid for by someone else, and
    a declared address proves nothing about who controls it.
    """
    links = set()
    registered = updates[updates.action == "registered"].drop_duplicates("drep_id", keep="last")
    drep_of = dict(zip(registered.update_tx_hash, registered.drep_id))
    hashes = sorted(drep_of)
    for i in range(0, len(hashes), 25):
        body = {"_tx_hashes": hashes[i : i + 25], "_inputs": True}
        for tx in k.page("tx_info", None, body):
            for spent in tx.get("inputs") or []:
                if spent.get("stake_addr"):
                    links.add((drep_of[tx["tx_hash"]], spent["stake_addr"], "funder"))

    declared = {}
    for i in range(0, len(drep_ids), 50):
        for row in k.page("drep_metadata", None, {"_drep_ids": drep_ids[i : i + 50]}):
            meta = row.get("meta_json")
            body = meta.get("body") if isinstance(meta, dict) else None
            address = body.get("paymentAddress") if isinstance(body, dict) else None
            if isinstance(address, dict):
                address = address.get("@value")
            if isinstance(address, str) and address.startswith("addr1"):
                declared[row["drep_id"]] = address.strip()
    addresses = sorted(set(declared.values()))
    stake_of = {}
    for i in range(0, len(addresses), 20):
        for row in k.page("address_info", None, {"_addresses": addresses[i : i + 20]}):
            if row.get("stake_address"):
                stake_of[row["address"]] = row["stake_address"]
    links |= {(d, stake_of[a], "declared") for d, a in declared.items() if a in stake_of}

    accounts = sorted({account for _, account, _ in links})
    info = {}
    for i in range(0, len(accounts), 50):
        for row in k.page("account_info", None, {"_stake_addresses": accounts[i : i + 50]}):
            info[row["stake_address"]] = row
    rows = [
        dict(
            drep_id=drep,
            stake_address=account,
            source=source,
            balance=int(info[account].get("total_balance") or 0),
            delegated_drep=info[account].get("delegated_drep"),
        )
        for drep, account, source in sorted(links)
        if account in info
    ]
    log(f"own-stake links {len(rows)} for {len({r['drep_id'] for r in rows})} DReps")
    return pd.DataFrame(
        rows, columns=["drep_id", "stake_address", "source", "balance", "delegated_drep"]
    )
