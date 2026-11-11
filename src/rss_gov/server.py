"""`rss-gov serve`: the site over HTTP, with instant checks and a queue for proposals.

By default it listens on every interface (0.0.0.0), so other machines on the local network
or a VPN can open it. There is no login: anyone who can reach the port can submit
proposals, and each one costs a few minutes of CPU. Serve it only on networks you trust,
or with --read-only. To publish the results for everyone, host results/site/ as static
files instead; the pages then work without this server.

Endpoints (everything else is a file from results/site/):

    GET  /api/status      is the model loaded, are submissions open, how long is the queue
    GET  /api/proposals   every proposal and its state
    POST /api/preview     exact checks for a rule, without simulating
    POST /api/proposals   queue a proposal; it is simulated with `rss-gov try`
"""

from collections import deque
from functools import partial
import http.server
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
from urllib.parse import urlsplit

import yaml

from rss_gov import experiment, mechanisms, proposals, static, website

MAX_BODY = 20_000  # bytes in one request
PER_CLIENT = 3  # proposals one address may have waiting at once
TIMEOUT = 3 * 3600  # seconds one simulation may take
EPOCHS_A_YEAR = 73


class Refused(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class Service:
    """Holds the loaded model and the proposal queue; one simulation at a time."""

    def __init__(self, config_path, submissions=True, max_queue=20, study=None, log=print):
        self.config_path = str(config_path)
        self.config = experiment.load_config(config_path)
        self.results = Path(self.config["results"])
        self.site = self.results / "site"
        self.submissions = submissions
        self.max_queue = max_queue
        self.log = log
        self.study = study
        self.lock = threading.Lock()  # guards the queue and use of the model
        self.queue = deque()
        self.owner = {}
        self.running = None
        self.wake = threading.Event()
        for row in proposals.listing(self.results):
            if row["state"] == "queued":  # left waiting when the server last stopped
                self.queue.append(row["name"])
        if self.study is None:
            threading.Thread(target=self._load, daemon=True).start()
        threading.Thread(target=self._work, daemon=True).start()
        if self.queue:
            self.wake.set()

    def _load(self):
        try:
            self.study = experiment.open_study(self.config_path)
            self.log("model loaded: instant checks are available")
        except Exception as error:  # the site is still served; checks say why they fail
            self.log(f"could not load the model: {error}")

    # ---------- answers ----------
    def state(self):
        with self.lock:
            return dict(
                ready=self.study is not None,
                submissions=self.submissions,
                queued=len(self.queue),
                running=self.running,
            )

    def listing(self):
        with self.lock:
            status = {name: "queued" for name in self.queue}
            if self.running:
                status[self.running] = "running"
        return proposals.listing(self.results, status)

    def _known(self):
        """Every design name in use, and the parameters of each known design."""
        known = {}
        for row in self.config["experiment"]["schemes"]:
            scheme = mechanisms.from_config(row, float(self.config["programme"]["budget_ada"]))
            known[scheme.name] = scheme
        finalists = self.results / "search_finalists.yaml"
        if finalists.exists():
            for row in yaml.safe_load(finalists.read_text()) or []:
                known[row["name"]] = mechanisms.from_config(row, 0)
        for name, row in proposals.submitted(self.results).items():
            known[name] = mechanisms.from_config(proposals.split(row)[0], 0)
        return known

    def _same(self, scheme):
        mine = {k: v for k, v in scheme.to_dict().items() if k != "name"}
        for name, other in self._known().items():
            if {k: v for k, v in other.to_dict().items() if k != "name"} == mine:
                return name
        return None

    def preview(self, payload):
        if self.study is None:
            raise Refused(503, "the model is still loading; try again in a few seconds")
        scheme, _ = proposals.parse(payload)
        with self.lock:
            row = static.analyse(self.study, [scheme]).iloc[0]
        feasibility = scheme.feasibility()
        keys = [*website.FACTS, "split_gain"]
        return website._plain(
            dict(
                rule=scheme.label(),
                pilot_testable=feasibility["pilot_testable"],
                notes=feasibility["notes"],
                checks={k: row[k] for k in keys},
                annual_cost=scheme.budget_ada * EPOCHS_A_YEAR / self.study.epochs,
                same_as=self._same(scheme),
            )
        )

    def submit(self, payload, client):
        if not self.submissions:
            raise Refused(403, "this server does not accept proposals")
        with self.lock:
            pending = list(self.queue) + ([self.running] if self.running else [])
            if len(pending) >= self.max_queue:
                raise Refused(429, "the queue is full; please try again later")
            if sum(self.owner.get(name) == client for name in pending) >= PER_CLIENT:
                raise Refused(429, f"at most {PER_CLIENT} proposals from one address may wait")
            known = self._known()
            scheme, meta = proposals.parse(payload, set(known) | proposals.taken(self.results))
            if not scheme.paid:
                raise ValueError("a proposal must have a budget")
            if scheme.hard_cap and not self.config["search"].get("allow_hard_fork", False):
                raise ValueError("hard-fork designs are switched off in config.yaml")
            same = self._same(scheme)
            if same:
                raise ValueError(f"this rule is already listed as {same}")
            proposals.submit(self.results, scheme, meta, "web")
            self.queue.append(scheme.name)
            self.owner[scheme.name] = client
        self.log(f"queued {scheme.name} from {client}")
        self.wake.set()
        return dict(name=scheme.name, ahead=len(pending))

    # ---------- the queue ----------
    def _work(self):
        while True:
            self.wake.wait()
            with self.lock:
                if not self.queue:
                    self.wake.clear()
                    continue
                name = self.queue.popleft()
                self.running = name
            try:
                self._simulate(name)
            finally:
                with self.lock:
                    self.running = None

    def _cli(self, *args, log):
        command = [sys.executable, "-m", "rss_gov.cli", "--config", self.config_path, *args]
        return subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=TIMEOUT)

    def _simulate(self, name):
        folder = proposals.folder(self.results)
        self.log(f"simulating {name}")
        with open(folder / f"{name}.log", "w") as log:
            try:
                done = self._cli("try", str(folder / f"{name}.yaml"), log=log).returncode == 0
            except subprocess.TimeoutExpired:
                done = False
            done = done and (folder / f"{name}.json").exists()
            if not done:
                tail = (folder / f"{name}.log").read_text()[-2000:]
                (folder / f"{name}.error").write_text(tail or "the simulation stopped")
                self.log(f"{name} failed; see {folder / (name + '.log')}")
                return
            self._cli("site", log=log)
        self.log(f"{name} simulated; site rebuilt")


def make_handler(service):
    class Handler(http.server.SimpleHTTPRequestHandler):
        server_version = "rss-gov"
        sys_version = ""

        def end_headers(self):
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            super().end_headers()

        def log_message(self, format, *args):  # keep the console for what matters
            pass

        def list_directory(self, path):
            self.send_error(404)
            return None

        def _json(self, code, body):
            data = json.dumps(body, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/status":
                return self._json(200, service.state())
            if path == "/api/proposals":
                return self._json(200, dict(proposals=service.listing()))
            if path.startswith("/api/"):
                return self._json(404, dict(error="not found"))
            return super().do_GET()

        def do_POST(self):
            path = urlsplit(self.path).path
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if not 0 < length <= MAX_BODY:
                return self._json(413, dict(error="the request is empty or too large"))
            try:
                payload = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                return self._json(400, dict(error="the request is not valid JSON"))
            try:
                if path == "/api/preview":
                    return self._json(200, service.preview(payload))
                if path == "/api/proposals":
                    return self._json(202, service.submit(payload, self.client_address[0]))
            except Refused as refused:
                return self._json(refused.code, dict(error=str(refused)))
            except ValueError as error:
                return self._json(400, dict(error=str(error)))
            return self._json(404, dict(error="not found"))

    return Handler


def addresses():
    """IPv4 addresses of this machine other than loopback, with their interface names."""
    found = []
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show"], capture_output=True, text=True)
        for line in out.stdout.splitlines():
            match = re.search(r"^\d+:\s+(\S+)\s+inet\s+([\d.]+)/", line)
            if match and not match.group(2).startswith("127."):
                found.append((match.group(2), match.group(1)))
    except OSError:
        pass
    if not found:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.connect(("10.255.255.255", 1))  # chooses a route; sends nothing
                found.append((probe.getsockname()[0], ""))
        except OSError:
            pass
    return found


def serve(config_path, host, port, submissions, max_queue, log=print):
    config = experiment.load_config(config_path)
    site = Path(config["results"]) / "site"
    study = None
    if not (site / "data.js").exists():
        log("building the site first (rss-gov site)...")
        study = experiment.open_study(config_path)
        website.write(study)
    service = Service(config_path, submissions, max_queue, study, log)
    handler = partial(make_handler(service), directory=str(site))
    httpd = http.server.ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    log(f"serving {site} on {host}:{port}")
    log(f"  this machine: http://localhost:{port}/")
    if host in ("0.0.0.0", ""):
        for address, interface in addresses():
            log(
                f"  network:      http://{address}:{port}/"
                + (f"  ({interface})" if interface else "")
            )
    log(
        "proposal submissions are "
        + ("OPEN: anyone who can reach this port can queue simulations" if submissions else "off")
    )
    log("press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("stopped")
    finally:
        httpd.server_close()
