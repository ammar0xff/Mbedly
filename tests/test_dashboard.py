"""Tests for the Mbedly dashboard TUI - engine is mocked, no network."""

import asyncio

import pytest

from mbedly import engine
from mbedly.app import MbedlyApp


def fake_scrape(url, cookie=None):
    return [
        engine.MediaItem(
            url="https://youtu.be/dQw4w9WgXcQ",
            kind="youtube",
            title="Never Gonna Give You Up",
            channel="A Test Channel",
        ),
        engine.MediaItem(url="https://cdn.example/x.mp4", kind="mp4"),
    ]


def run(scenario):
    asyncio.run(scenario())


def test_dashboard_scrapes_into_table(monkeypatch):
    monkeypatch.setattr(engine, "scrape", fake_scrape)

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.query_one("#url").value = "https://example.com"
            await pilot.press("enter")
            await pilot.pause()
            for _ in range(10):
                await pilot.pause(0.05)
            table = app.query_one("#results")
            assert table.row_count == 2
            hint = str(app.query_one("#hint").render())
            assert "2 media item(s)" in hint

    run(scenario)


def test_quality_button_sets_quality(monkeypatch):
    monkeypatch.setattr(engine, "scrape", fake_scrape)

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.click("#q-720p")
            assert app.quality == "720p"
            await pilot.click("#q-mp3")
            assert app.quality == "mp3"

    run(scenario)


def test_download_all_flow(monkeypatch):
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(engine, "scrape", fake_scrape)

    def fake_download(url, quality="1080p", output_dir=".", progress_cb=None):
        calls.append((url, quality))
        return "/tmp/fake.mp4"

    monkeypatch.setattr(engine, "download", fake_download)

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.query_one("#url").value = "https://example.com"
            await pilot.press("enter")
            for _ in range(10):
                await pilot.pause(0.05)

            await pilot.click("#q-360p")
            await pilot.click("#dl-all")
            for _ in range(10):
                await pilot.pause(0.05)

            assert len(calls) == 2
            assert all(q == "360p" for _, q in calls)
            assert not app._downloading

    run(scenario)


def test_download_requires_media(monkeypatch):
    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.click("#dl-all")
            # Should just notify a warning, not crash or download anything.
            assert app._items == []

    run(scenario)