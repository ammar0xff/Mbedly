"""Mbedly local JSON API - lets any client (e.g. the Flutter app) drive the engine.

Runs with only the standard library (http.server). No framework, no CORS lib.
Start it with:  mbedly-api  (or: python -m mbedly.api --port 8765)
"""

from __future__ import annotations

import argparse
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from mbedly import engine

DEFAULT_PORT = 8765


def outdir() -> Path:
    return Path(os.environ.get("MBEDLY_OUTDIR", "downloads"))


# ---------------------------------------------------------------------------
# Download jobs (background threads)
# ---------------------------------------------------------------------------

JOBS: dict = {}
JOBS_LOCK = threading.Lock()
_JOB_COUNTER = 0
_JOB_COUNTER_LOCK = threading.Lock()


def _next_job_id() -> str:
    global _JOB_COUNTER
    with _JOB_COUNTER_LOCK:
        _JOB_COUNTER += 1
        return f"j{_JOB_COUNTER}"


def _job_state(job_id: str) -> dict:
    with JOBS_LOCK:
        return dict(JOBS[job_id])


def _start_job(url: str, quality: str, kind: str) -> str:
    job_id = _next_job_id()
    with JOBS_LOCK:
        JOBS[job_id] = {
            "id": job_id,
            "url": url,
            "kind": kind,
            "quality": quality,
            "status": "queued",
            "downloaded": 0,
            "total": 0,
            "speed": 0.0,
            "filename": "",
            "error": "",
        }
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, url, quality),
        name=f"mbedly-job-{job_id}",
        daemon=True,
    )
    thread.start()
    return job_id


def _run_job(job_id: str, url: str, quality: str) -> None:
    def progress_cb(hook: dict) -> None:
        status = hook.get("status")
        if status == "downloading":
            total = hook.get("total_bytes") or hook.get("total_bytes_estimate") or 0
            with JOBS_LOCK:
                JOBS[job_id].update(
                    status="working",
                    downloaded=hook.get("downloaded_bytes", 0),
                    total=total,
                    speed=hook.get("speed") or 0.0,
                )
        elif status == "finished":
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "working"

    try:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "working"
        path = engine.download(
            url,
            quality=quality,
            output_dir=str(outdir()),
            progress_cb=progress_cb,
        )
        with JOBS_LOCK:
            JOBS[job_id].update(
                status="done", filename=str(path), downloaded=JOBS[job_id]["total"] or 0
            )
        engine.record_history(
            {
                "url": url,
                "kind": "",
                "quality": quality,
                "title": Path(path).stem,
                "destination": str(path),
            }
        )
    except Exception as exc:  # noqa: BLE001 - surface any download failure
        with JOBS_LOCK:
            JOBS[job_id].update(status="error", error=str(exc)[:500])


# ---------------------------------------------------------------------------
# Scrape + title resolution (off the request thread, quick pool)
# ---------------------------------------------------------------------------

def _scrape_items(url: str, cookies: Optional[str]) -> list[dict]:
    items = engine.scrape(url, cookies)
    _resolve_titles(items)
    return [_item_dict(i) for i in items]


def _resolve_titles(items: list) -> None:
    """Fill empty titles/channels with a small worker pool (best effort)."""
    pending = [it for it in items if not it.title or not it.channel]
    if not pending:
        return
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(engine.resolve_meta, it): it for it in pending}
        for fut in as_completed(futs, timeout=30):
            item = futs[fut]
            try:
                title, channel = fut.result()
            except Exception:
                continue
            item.title = title or item.title
            item.channel = channel or item.channel


def _item_dict(item) -> dict:
    return {
        "url": item.url,
        "kind": item.kind,
        "title": item.title,
        "channel": item.channel,
    }


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def _history() -> list[dict]:
    path = engine.history_path()
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class ApiHandler(BaseHTTPRequestHandler):
    server_version = "mbedly-api"

    # -- helpers ---------------------------------------------------------

    def _send(self, code: int, payload: object, allow: str = "GET, POST, OPTIONS") -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", allow)
        self.send_header(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except Exception:
            return {}

    def log_message(self, fmt: str, *args) -> None:  # quiet, like the engine
        return

    # -- verbs -----------------------------------------------------------

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_GET(self) -> None:
        route = self.path.split("?", 1)[0]
        handlers = {
            "/health": lambda: ({"ok": True, "service": "mbedly-api"}, 200),
            "/qualities": lambda: ({"qualities": list(engine.QUALITIES)}, 200),
            "/settings": lambda: (
                {
                    "qualities": list(engine.QUALITIES),
                    "outdir": str(outdir()),
                },
                200,
            ),
            "/jobs": lambda: (
                {"jobs": [dict(j) for j in JOBS.values()] or []},
                200,
            ),
            "/history": lambda: ({"entries": _history()}, 200),
        }
        if route not in handlers:
            self._send(404, {"error": f"unknown route {route}"})
            return
        payload, code = handlers[route]()
        self._send(code, payload)

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
        data = self._read_json()

        if route == "/scrape":
            url = str(data.get("url") or "").strip()
            if not url:
                self._send(400, {"error": "url is required"})
                return
            try:
                items = _scrape_items(url, data.get("cookies"))
            except Exception as exc:  # noqa: BLE001
                self._send(500, {"error": str(exc)[:500]})
                return
            self._send(200, {"items": items})
            return

        if route == "/download":
            urls = data.get("urls")
            if isinstance(urls, str):
                urls = [urls]
            if not urls:
                url = str(data.get("url") or "").strip()
                urls = [url] if url else []
            if not urls:
                self._send(400, {"error": "url or urls is required"})
                return
            quality = str(data.get("quality") or "1080p")
            job_ids = [
                _start_job(str(u).strip(), quality, str(data.get("kind") or ""))
                for u in urls
                if str(u).strip()
            ]
            if not job_ids:
                self._send(400, {"error": "no usable urls given"})
                return
            self._send(200, {"job_ids": job_ids})
            return

        if route == "/history":
            engine.record_history(data)
            self._send(200, {"ok": True})
            return

        self._send(404, {"error": f"unknown route {route}"})


def start(port: int = DEFAULT_PORT, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), ApiHandler)
    return server


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="mbedly-api", description="Mbedly JSON API")
    parser.add_argument("--port", type=int, default=int(os.environ.get("MBEDLY_PORT", DEFAULT_PORT)))
    parser.add_argument("--host", default=os.environ.get("MBEDLY_HOST", "127.0.0.1"))
    args = parser.parse_args(argv)
    server = start(args.port, args.host)
    print(
        f"mbedly-api listening on http://{args.host}:{args.port} "
        f"(outdir: {outdir()})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())