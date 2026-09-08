"""Tests for the Mbedly dashboard TUI - engine is mocked, no network."""

import asyncio
from pathlib import Path

from mbedly import engine
from mbedly.app import HelpScreen, HistoryScreen, MbedlyApp


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


def fake_resolve_meta(item):
    return f"Resolved: {item.url}", "Resolver Channel"


def patch_engine(monkeypatch):
    monkeypatch.setattr(engine, "scrape", fake_scrape)
    monkeypatch.setattr(engine, "resolve_meta", fake_resolve_meta)
    monkeypatch.setattr(
        engine, "resolve_title", lambda item: fake_resolve_meta(item)[0]
    )


def run(scenario):
    asyncio.run(scenario())


def test_dashboard_scrapes_into_table(monkeypatch):
    patch_engine(monkeypatch)

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.query_one("#url").value = "https://example.com"
            await pilot.press("enter")
            for _ in range(20):
                await pilot.pause(0.05)

            table = app.query_one("#results")
            assert table.row_count == 2

            # the bare mp4 item should have its title resolved, not left as a URL
            row_title = str(table.get_cell_at((1, 2))).strip()
            assert row_title.startswith("Resolved:")

            hint = str(app.query_one("#hint").render())
            assert "2 video(s)" in hint
            assert "download" in hint

    run(scenario)


def test_download_history_shows_titles(monkeypatch):
    patch_engine(monkeypatch)
    entries = []

    def fake_record(entry):
        entries.append(entry)

    monkeypatch.setattr(engine, "record_history", fake_record)

    def fake_download(url, quality="1080p", output_dir=".", progress_cb=None):
        return "/tmp/fake.mp4"

    monkeypatch.setattr(engine, "download", fake_download)

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.query_one("#url").value = "https://example.com"
            await pilot.press("enter")
            for _ in range(20):
                await pilot.pause(0.05)

            await pilot.click("#q-360p")
            await pilot.click("#dl-all")
            for _ in range(20):
                await pilot.pause(0.05)

            panel = app.query_one("#downloads")
            assert len(panel.query(".dl-row")) == 2

            titles = [str(w.render()).strip() for w in panel.query(".dl-title")]
            assert any(t.startswith("Resolved:") for t in titles)

            assert len(entries) == 2
            assert all(e["quality"] == "360p" for e in entries)
            assert not app._downloading

    run(scenario)


def test_quality_button_sets_quality_and_highlight(monkeypatch):
    patch_engine(monkeypatch)

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.click("#q-720p")
            assert app.quality == "720p"
            assert app.query_one("#q-720p").variant == "success"
            assert app.query_one("#q-1080p").variant != "success"

            await pilot.click("#q-mp3")
            assert app.quality == "mp3"
            assert app.query_one("#q-mp3").variant == "success"

    run(scenario)


def test_download_requires_media(monkeypatch):
    patch_engine(monkeypatch)

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.click("#dl-all")
            assert app._items == []

    run(scenario)


def test_help_and_history_screens_open(monkeypatch):
    patch_engine(monkeypatch)
    monkeypatch.setattr(
        engine,
        "history_path",
        lambda: Path("/dev/null/nope-history.json"),
    )

    async def scenario():
        app = MbedlyApp()
        async with app.run_test(size=(120, 40)) as pilot:
            app.action_help()
            await pilot.pause(0.1)
            assert isinstance(app.screen, HelpScreen)
            assert "shortcuts" in str(app.screen.query_one(".modal-title").render())
            await pilot.press("escape")
            await pilot.pause(0.1)
            assert not isinstance(app.screen, HelpScreen)

            app.action_history()
            await pilot.pause(0.1)
            assert isinstance(app.screen, HistoryScreen)
            assert "nothing downloaded yet" in str(app.screen.query_one(".modal-row").render())
            await pilot.press("escape")
            await pilot.pause(0.1)
            assert not isinstance(app.screen, HistoryScreen)

    run(scenario)