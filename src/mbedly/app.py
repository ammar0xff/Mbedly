"""Mbedly dashboard - a full-screen TUI in btop/opencode style (textual)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    Static,
)

from mbedly import engine
from mbedly.tui import default_output_dir

GREEN = "#00FF41"
YELLOW = "#FFC300"
RED = "#FF3333"
DIM = "#94A3B8"


class MbedlyApp(App):
    """Full-screen Mbedly downloader dashboard."""

    CSS = f"""
    Screen {{
        background: #000000;
        color: #E0E0E0;
    }}

    #inputs {{
        height: 3;
        padding: 0 1;
        background: #050505;
    }}
    #url {{
        width: 3fr;
        border: round {GREEN};
    }}
    #cookies {{
        width: 1fr;
        border: round {DIM};
    }}
    Input:focus {{
        border: round {GREEN};
    }}

    #body {{
        height: 1fr;
    }}

    #left {{
        width: 3fr;
        height: 1fr;
    }}
    #results {{
        height: 1fr;
    }}
    #downloads {{
        width: 2fr;
        height: 1fr;
    }}

    #results {{
        border: round {GREEN};
        background: #030303;
    }}
    DataTable > .datatable--header {{
        background: #001a06;
        color: {GREEN};
    }}
    DataTable > .datatable--cursor {{
        background: #00330c;
    }}

    #hint {{
        padding: 0 1;
        color: {DIM};
    }}

    #qualities {{
        height: 4;
        margin: 0 1 1 1;
    }}
    .quality {{
        width: 9;
        min-width: 9;
        max-width: 9;
    }}
    Button {{
        width: auto;
        padding: 0 1;
        border: round {GREEN};
        color: {GREEN};
        background: #001206;
    }}
    Button.focus {{
        background: {GREEN};
        color: #000000;
    }}
    Button.primary {{
        background: {GREEN};
        color: #000000;
    }}
    Button.variant-warning {{
        border: round {YELLOW};
        color: {YELLOW};
    }}

    #downloads {{
        border: round {YELLOW};
        background: #060500;
        padding: 0 1;
    }}
    .dl-row {{
        height: auto;
        margin: 1 0;
        padding: 0 1;
        border: solid #1F1F1F;
        background: #0A0A0A;
    }}
    .dl-title {{
        color: {GREEN};
        text-style: bold;
    }}
    .dl-status {{
        width: 1fr;
        color: {DIM};
        text-align: right;
    }}
    ProgressBar > .bar--bar {{
        background: {GREEN};
    }}
    .empty {{
        color: {DIM};
        padding: 1 2;
    }}

    Header {{
        background: #001206;
        color: {GREEN};
    }}
    Footer {{
        background: #001206;
        color: {GREEN};
    }}
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "quit"),
        Binding("/", "focus_url", "url"),
        Binding("g", "focus_downloads", "downloads"),
        Binding("r", "recent", "history"),
    ]

    def __init__(self, output: Path | None = None, start_url: str | None = None) -> None:
        super().__init__()
        self.outdir: Path = output or default_output_dir()
        self.quality: str = "1080p"
        self.start_url: str | None = start_url
        self._items: list[engine.MediaItem] = []
        self._downloading = False
        self._tasks: dict[str, tuple[ProgressBar, Static]] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Input(
                placeholder="page or direct video URL - Enter to analyse (finds every embedded video)",
                id="url",
            ),
            Input(
                placeholder="cookies header (optional - mahara-tech courses)",
                id="cookies",
            ),
            id="inputs",
        )
        yield Horizontal(
            Vertical(
                DataTable(id="results", cursor_type="row"),
                Label(
                    "no media yet - enter a URL above and hit Enter",
                    id="hint",
                ),
                Horizontal(
                    *[
                        Button(q, id=f"q-{q}", classes="quality")
                        for q in engine.QUALITIES
                    ],
                    id="qualities",
                ),
                Horizontal(
                    Button("download selected", id="dl-sel", variant="primary"),
                    Button("download all", id="dl-all"),
                    id="actions",
                ),
                id="left",
            ),
            VerticalScroll(id="downloads"),
            id="body",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#downloads").border_title = "downloads"
        self.query_one("#left").border_title = "media"
        table = self.query_one("#results")
        table.add_columns("#", "kind", "title", "channel / source")
        if self.start_url:
            url_input = self.query_one("#url")
            url_input.value = self.start_url
            url_input.action_submit()

    # ------------------------------------------------------------------
    # Actions / key bindings
    # ------------------------------------------------------------------

    def action_quit(self) -> None:
        self.exit(0)

    def action_focus_url(self) -> None:
        self.query_one("#url").focus()

    def action_focus_downloads(self) -> None:
        self.query_one("#downloads").focus()

    def action_recent(self) -> None:
        path = engine.history_path()
        if not path.exists():
            self.notify("no download history yet")
            return
        rows = engine.history_path().read_text(encoding="utf-8")
        self.query_one("#downloads").remove_children()
        self.query_one("#downloads").mount(
            Static(rows, classes="dl-history")
        )

    # ------------------------------------------------------------------
    # URL scraping
    # ------------------------------------------------------------------

    @on(Input.Submitted, "#url")
    def _on_url_submitted(self, event: Input.Submitted) -> None:
        url = event.value.strip()
        if not url:
            return
        cookies = self.query_one("#cookies").value.strip() or None
        self.scrape_worker(url, cookies)

    @work(thread=True, exclusive=True, group="scrape")
    def scrape_worker(self, url: str, cookies: Optional[str]) -> None:
        self.call_from_thread(self._scrape_started, url)
        try:
            items = engine.scrape(url, cookies)
        except Exception as exc:
            self.call_from_thread(self._scrape_failed, str(exc))
            return
        self.call_from_thread(self._scrape_done, items)

    def _scrape_started(self, url: str) -> None:
        self.set_focus(self.query_one("#url"))
        self.notify(f"analysing {url[:60]}...", timeout=6)

    def _scrape_failed(self, error: str) -> None:
        self.notify(f"scrape failed: {error}", severity="error", timeout=8)

    def _scrape_done(self, items: list[engine.MediaItem]) -> None:
        table = self.query_one("#results")
        table.clear()
        self._items = items
        for i, item in enumerate(items, start=1):
            table.add_row(
                str(i),
                item.kind,
                item.title or item.url,
                item.channel or ("" if item.title else item.url),
            )
        hint = self.query_one("#hint")
        if not items:
            hint.update("no supported media found on that page")
        else:
            hint.update(f"{len(items)} media item(s) found - select with ↑/↓, then download")
        if items:
            table.focus()
        self.notify(f"{len(items)} media item(s) found", timeout=3)

    # ------------------------------------------------------------------
    # Quality + downloads
    # ------------------------------------------------------------------

    @on(Button.Pressed)
    def _on_button(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("q-"):
            self.quality = bid[2:]
            self.notify(f"quality: {self.quality}")
        elif bid == "dl-sel":
            self._start_downloads(selected=True)
        elif bid == "dl-all":
            self._start_downloads(selected=False)

    def _start_downloads(self, selected: bool) -> None:
        if self._downloading:
            self.notify("downloads already running", severity="warning")
            return
        if not self._items:
            self.notify("no media - scrape a page first", severity="warning")
            return

        table = self.query_one("#results")
        if selected:
            index = table.cursor_coordinate.row
            if index >= len(self._items):
                self.notify("select a row first", severity="warning")
                return
            targets = [self._items[index]]
        else:
            targets = list(self._items)

        self._downloading = True
        self.notify(f"downloading {len(targets)} video(s) at {self.quality}", timeout=3)
        self.download_worker(targets, self.quality)

    @work(thread=True, group="downloads")
    def download_worker(self, targets: list[engine.MediaItem], quality: str) -> None:
        for raw in targets:
            self.call_from_thread(self._dl_start, raw)
            task = self._tasks.get(raw.url)
            if task is None:
                continue
            bar, status = task
            hook = lambda s, b=bar, st=status: self.call_from_thread(
                self._dl_tick, b, st, s
            )
            try:
                dest = engine.download(
                    raw.url, quality=quality, output_dir=self.outdir, progress_cb=hook
                )
                self.call_from_thread(self._dl_done, bar, status, dest)
            except Exception as exc:
                self.call_from_thread(self._dl_error, bar, status, str(exc))
        self.call_from_thread(self._downloading_done)

    def _dl_start(self, raw: engine.MediaItem) -> None:
        bar = ProgressBar(show_eta=False, show_percentage=False)
        status = Static("queued", classes="dl-status")
        row = Container(
            Static(raw.title or raw.url, classes="dl-title"),
            Horizontal(Label(raw.url, classes="dl-status"), classes="dl-sub"),
            bar,
            status,
            classes="dl-row",
        )
        panel = self.query_one("#downloads")
        if panel.query(".empty"):
            panel.remove_children()
        panel.mount(row, before=None)
        panel.scroll_end(animate=False)
        self._tasks[raw.url] = (bar, status)

    def _dl_tick(self, bar: ProgressBar, status: Static, info: dict) -> None:
        if info.get("status") != "downloading":
            return
        total = info.get("total_bytes") or info.get("total_bytes_estimate")
        done = info.get("downloaded_bytes", 0)
        if total:
            bar.update(total=total, progress=done)
            status.update(f"{done / total * 100:5.1f}%")

    def _dl_done(self, bar: ProgressBar, status: Static, dest: str) -> None:
        bar.update(total=100, progress=100)
        status.update(f"saved: {Path(dest).name}")

    def _dl_error(self, bar: ProgressBar, status: Static, error: str) -> None:
        status.update(f"failed: {error[:60]}")

    def _downloading_done(self) -> None:
        self._downloading = False
        self._tasks.clear()
        self.query_one("#url").focus()
        self.notify("all downloads finished", timeout=4)


def launch(output: Path | None = None, start_url: str | None = None) -> None:
    MbedlyApp(output=output, start_url=start_url).run()