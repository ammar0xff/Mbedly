"""Tests for the Mbedly JSON API - mocked engine, no network."""

import json
import threading
import time
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from mbedly import api, engine
from mbedly.engine import MediaItem

SERVER_PORT = 19876  # arbitrary; tests never run in parallel so this is safe
BASE = f"http://127.0.0.1:{SERVER_PORT}"


def _start_server():
    s = api.start(SERVER_PORT, "127.0.0.1")
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    return s


def _post(route: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = Request(
        f"{BASE}{route}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urlopen(req, timeout=10).read())


def _get(route: str) -> dict:
    return json.loads(urlopen(f"{BASE}{route}", timeout=10).read())


@pytest.fixture(scope="module", autouse=True)
def _server():
    api.JOBS.clear()
    s = _start_server()
    yield s
    s.shutdown()


# -- engine stubs ----------------------------------------------------------


def _patch(monkeypatch):
    def fake_scrape(url, cookie=None):
        if "youtube.com/playlist" in url:
            return [
                MediaItem(url=f"https://www.youtube.com/watch?v=aa{i}", kind="youtube", title=f"ep {i+1}", channel="mychan")
                for i in range(3)
            ]
        return [
            MediaItem(url="https://example.com/v1.mp4", kind="mp4", title="", channel="")
        ]

    def fake_resolve_meta(item):
        if not item.title:
            return ("Resolved Title", "Some Channel")
        return (item.title, item.channel)

    def fake_download(url, quality="1080p", output_dir="downloads", progress_cb=None):
        if progress_cb:
            progress_cb({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100, "speed": 1.0})
            progress_cb({"status": "finished", "downloaded_bytes": 100, "total_bytes": 100})
        return str(api.outdir() / "test.mp4")

    def fake_record_history(entry):
        return None

    monkeypatch.setattr(engine, "scrape", fake_scrape)
    monkeypatch.setattr(engine, "resolve_meta", fake_resolve_meta)
    monkeypatch.setattr(engine, "download", fake_download)
    monkeypatch.setattr(engine, "record_history", fake_record_history)


# -- tests ------------------------------------------------------------------


def test_health():
    res = _get("/health")
    assert res["ok"] is True
    assert res["service"] == "mbedly-api"


def test_qualities():
    res = _get("/qualities")
    assert "144p" in res["qualities"]
    assert "mp3" in res["qualities"]


def test_scrape_single(monkeypatch):
    _patch(monkeypatch)
    res = _post("/scrape", {"url": "https://example.com/v1.mp4"})
    assert len(res["items"]) == 1
    item = res["items"][0]
    assert item["kind"] == "mp4"
    assert item["title"] == "Resolved Title"
    assert item["channel"] == "Some Channel"


def test_scrape_playlist(monkeypatch):
    _patch(monkeypatch)
    res = _post("/scrape", {"url": "https://www.youtube.com/playlist?list=PLabc"})
    assert len(res["items"]) == 3
    assert [it["title"] for it in res["items"]] == ["ep 1", "ep 2", "ep 3"]


def test_scrape_requires_url():
    try:
        _post("/scrape", {})
        assert False, "expected 400"
    except HTTPError as e:
        assert e.code == 400


def test_download_single(monkeypatch):
    _patch(monkeypatch)
    res = _post("/download", {"url": "https://example.com/v.mp4", "quality": "480p"})
    assert "job_ids" in res
    assert len(res["job_ids"]) == 1
    # job was started in a background thread - wait a tick
    time.sleep(0.05)
    job_id = res["job_ids"][0]
    jobs = _get("/jobs")["jobs"]
    assert any(j["id"] == job_id for j in jobs)
    matching = next(j for j in jobs if j["id"] == job_id)
    assert matching["quality"] == "480p"
    assert matching["status"] in ("working", "done")


def test_download_batch(monkeypatch):
    _patch(monkeypatch)
    res = _post(
        "/download",
        {
            "urls": [
                "https://example.com/a.mp4",
                "https://example.com/b.mp4",
            ],
            "quality": "720p",
        },
    )
    assert len(res["job_ids"]) == 2
    time.sleep(0.1)
    jobs = _get("/jobs")["jobs"]
    assert len(jobs) >= 2


def test_download_requires_url():
    try:
        _post("/download", {})
        assert False, "expected 400"
    except HTTPError as e:
        assert e.code == 400


def test_history_empty(monkeypatch):
    _patch(monkeypatch)
    res = _get("/history")
    assert "entries" in res


def test_unknown_route():
    req = Request(f"{BASE}/nonexistent", method="GET")
    with pytest.raises(Exception):
        urlopen(req, timeout=5)
