"""The HTTP layer, without a model: files, refusals and request checks."""

from functools import partial
import http.server
import json
import threading
import urllib.error
import urllib.request

import pytest

from rss_gov import server


class FakeService:
    def __init__(self, results):
        self.results = results
        self.submitted = []

    def state(self):
        return dict(submissions=False, queued=0, running=None)

    def listing(self):
        return []

    def submit(self, payload, client):
        raise server.Refused(403, "this server does not accept proposals")


@pytest.fixture
def site(tmp_path):
    folder = tmp_path / "site"
    folder.mkdir()
    (folder / "index.html").write_text("<p>results</p>")
    (tmp_path / "secret.txt").write_text("not for the web")
    handler = partial(server.make_handler(FakeService(tmp_path)), directory=str(folder))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def get(url):
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def post(url, body):
    data = body if isinstance(body, bytes) else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    return get(request)


def test_files_come_from_the_site_folder_only(site):
    assert get(site + "/") == (200, "<p>results</p>")
    assert get(site + "/../secret.txt")[0] == 404
    assert get(site + "/%2e%2e/secret.txt")[0] == 404


def test_api_answers_in_json(site):
    status, body = get(site + "/api/status")
    assert status == 200 and json.loads(body)["submissions"] is False
    assert get(site + "/api/nothing")[0] == 404


def test_submissions_are_refused_when_closed(site):
    status, body = post(site + "/api/proposals", {"budget_ada": 1e6})
    assert status == 403 and "does not accept" in json.loads(body)["error"]


def test_bad_requests_are_refused(site):
    assert post(site + "/api/proposals", b"{not json")[0] == 400
    assert post(site + "/api/proposals", b"x" * (server.MAX_BODY + 1))[0] == 413
    assert post(site + "/api/preview", {"budget_ada": 1e6})[0] == 404  # checks run in the page
