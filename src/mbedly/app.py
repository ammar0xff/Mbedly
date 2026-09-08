"""Mbedly dashboard - a full-screen TUI in btop/opencode style (textual)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
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
GREY = "#1F1F1F"


def _clip(text: str, width: int = 70) -> str:
    text = str(text).replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


# --------------------------------------------------------------------------
# Modal screens
# --------------------------------------------------------------------------

class HelpScreen(ModalScreen[None]):
    """Shortcut cheatsheet overlay."""

    BINDINGS = [Binding("escape", "dismiss_popup", "close")]

    def action_dismiss_popup(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        rows = [
            ("enter", "on URL: analyse the page for embedded videos"),
            ("↑ / ↓", "select a media result"),
            ("d", "download the selected video"),
            ("a", "download every video found"),
            ("/", "focus the URL box"),
            ("g", "focus the downloads panel"),
            ("r", "show download history"),
            ("esc", "close this / history window"),
            ("q / ctrl+q", "quit"),
        ]
        yield Container(
            Static("mbedly - shortcuts", classes="modal-title"),
            *[
                Static(f"  {k:<10} {v}", classes="modal-row")
                for k, v in rows
            ],
            id="help-modal",
        )


class HistoryScreen(ModalScreen[None]):
    """Last downloads, newest first."""

    BINDINGS = [Binding("escape", "dismiss_popup", "close")]

    def action_dismiss_popup(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        entries: list = []
        try:
            path = engine.history_path()
            if path.exists():
                entries = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            entries = []

        if not entries:
            yield Container(
                Static("download history", classes="modal-title"),
                Static("  nothing downloaded yet", classes="modal-row dim"),
                Static("esc to close", classes="modal-foot"),
                id="history-modal",
            )
            return

        rows: list = []
        for e in reversed(entries[-(40):]):
            title = _clip(e.get("title") or e.get("url") or "?")
            kval = e.get("quality", "")
            at = (e.get("at") or "").replace("T", " ")
            dest = _clip(e.get("destination") or "", 130)
            rows.append(Static(
                f"  [{kval:>5}] {at[5:16]}  {title}",
                classes="modal-row",
            ))
            rows.append(Static(f"      ↳ {dest}", classes="modal-row dim"))
        yield VerticalScroll(
            Static("download history", classes="modal-title"),
            *rows,
            Static("esc to close", classes="modal-foot"),
            id="history-modal",
        )


# --------------------------------------------------------------------------
# Main app
# --------------------------------------------------------------------------

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
    Button.success {{
        background: {GREEN};
        color: #000000;
        text-style: bold;
    }}
    Button.variant-warning {{
        border: round {YELLOW};
        color: {YELLOW};
    }}
    #actions {{
        height: 4;
    }}
    #actions Button {{
        width: 18;
        min-width: 18;
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
        border: solid {GREY};
        background: #0A0A0A;
    }}
    .dl-title {{
        color: {GREEN};
        text-style: bold;
    }}
    .dl-sub {{
        color: {DIM};
    }}
    .dl-status {{
        width: 1fr;
        color: {DIM};
        text-align: right;
    }}
    .dl-status.ok {{
        color: {GREEN};
    }}
    .dl-status.err {{
        color: {RED};
    }}
    .dl-status.busy {{
        color: {YELLOW};
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

    HelpScreen {{
        align: center middle;
    }}
    #help-modal {{
        width: 72;
        height: auto;
        border: round {YELLOW};
        background: #050505;
        padding: 1 2;
    }}
    #history-modal {{
        width: 90;
        height: 70%;
        border: round {YELLOW};
        background: #050505;
        padding: 1 2;
    }}
    .modal-title {{
        color: {YELLOW};
        text-style: bold;
        margin-bottom: 1;
    }}
    .modal-row {{
        color: #E0E0E0;
        margin: 0 0 1 0;
    }}
    .modal-row.dim {{
        color: {DIM};
    }}
    .modal-foot {{
        color: {DIM};
        margin-top: 1;
    }}
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "quit"),
        Binding("q", "quit", "quit"),
        Binding("/", "focus_url", "url"),
        Binding("d", "download_selected", "dl sel"),
        Binding("a", "download_all", "dl all"),
        Binding("g", "focus_downloads", "downloads"),
        Binding("r", "history", "history"),
        Binding("?", "help", "help"),
    ]

    def __init__(self, output: Path | None = None, start_url: str | None = None) -> None:
        super().__init__()
        self.title = "mbedly"
        self.outdir: Path = output or default_output_dir()
        self.quality: str = "1080p"
        self.start_url: str | None = start_url
        self._items: list[engine.MediaItem] = []
        self._row_keys: list = []
        self._col_keys: dict[int, object] = {}
        self._downloading = False
        self._tasks: dict[str, tuple[ProgressBar, Static]] = {}
        self.sub_title = f"quality: {self.quality} · output: {self.outdir}"

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
            VerticalScroll(
                Static(
                    "no downloads yet - analyse a page, pick a quality, then\n"
                    "hit download selected or download all",
                    classes="empty",
                ),
                id="downloads",
            ),
            id="body",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#downloads").border_title = "downloads"
        self.query_one("#left").border_title = "media"
        table = self.query_one("#results")
        for i, name in enumerate(("#", "kind", "title", "channel / source")):
            self._col_keys[i] = table.add_column(name)
        self._highlight_quality()
        self.query_one("#url").focus()
        if self.start_url:
            url_input = self.query_one("#url")
            url_input.value = self.start_url
            url_input.action_submit()

    # ------------------------------------------------------------------
    # Actions / key bindings
    # ------------------------------------------------------------------

    def action_quit(self) -> None:
        self.exit(0)

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_history(self) -> None:
        self.push_screen(HistoryScreen())

    def action_focus_url(self) -> None:
        self.query_one("#url").focus()

    def action_focus_downloads(self) -> None:
        self.query_one("#downloads").focus()

    def action_download_selected(self) -> None:
        self._start_downloads(selected=True)

    def action_download_all(self) -> None:
        self._start_downloads(selected=False)

    # ------------------------------------------------------------------
    # URL scraping + metadata resolution
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
        self.query_one("#hint").update(f"analysing {_clip(url, 60)}…")
        self.notify(f"analysing {url[:60]}...", timeout=6)

    def _scrape_failed(self, error: str) -> None:
        self.query_one("#hint").update(f"analysis failed: {error}")
        self.notify(f"scrape failed: {error}", severity="error", timeout=8)

    def _scrape_done(self, items: list[engine.MediaItem]) -> None:
        table = self.query_one("#results")
        table.clear()
        self._items = items
        self._row_keys = []
        for item in items:
            row_key = table.add_row(
                str(len(self._row_keys) + 1),
                item.kind,
                item.title or "fetching title…",
                item.channel or "",
            )
            self._row_keys.append(row_key)
        hint = self.query_one("#hint")
        if not items:
            hint.update("no supported media found on that page")
            self.notify("no media found", severity="warning", timeout=3)
            return
        hint.update(f"{len(items)} video(s) found - resolving titles…")
        self.sub_title = (
            f"quality: {self.quality} · {len(items)} media · output: {self.outdir}"
        )
        if items:
            table.focus()
        self.meta_worker()

    @work(thread=True, group="scrape")
    def meta_worker(self) -> None:
        """Resolve human-readable titles/channels for items missing them."""
        for idx, item in enumerate(self._items):
            if item.title:
                continue
            try:
                title, channel = engine.resolve_meta(item)
            except Exception:
                title, channel = "", item.channel
            item.title, item.channel = title or item.url, channel or item.channel
            self.call_from_thread(self._meta_updated, idx, item.title, item.channel)
        self.call_from_thread(self._meta_done)

    def _meta_updated(self, idx: int, title: str, channel: str) -> None:
        table = self.query_one("#results")
        if idx < len(self._row_keys):
            table.update_cell(self._row_keys[idx], self._col_keys[2], _clip(title))
            table.update_cell(self._row_keys[idx], self._col_keys[3], _clip(channel, 40))

    def _meta_done(self) -> None:
        self.query_one("#hint").update(
            f"{len(self._items)} video(s) - ↑/↓ select, then d to download one or a for all"
        )
        self.notify("titles resolved", timeout=2)

    # ------------------------------------------------------------------
    # Quality + downloads
    # ------------------------------------------------------------------

    def _highlight_quality(self) -> None:
        for q in engine.QUALITIES:
            btn = self.query_one(f"#q-{q}")
            btn.variant = "success" if q == self.quality else "default"

    @on(Button.Pressed)
    def _on_button(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("q-"):
            self.quality = bid[2:]
            self._highlight_quality()
            self.sub_title = (
                f"quality: {self.quality} · {len(self._items)} media · output: {self.outdir}"
            )
            self.notify(f"quality: {self.quality}")
        elif bid == "dl-sel":
            self._start_downloads(selected=True)
        elif bid == "dl-all":
            self._start_downloads(selected=False)

    def _set_download_buttons(self, disabled: bool) -> None:
        self.query_one("#dl-sel").disabled = disabled
        self.query_one("#dl-all").disabled = disabled

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
                self.notify("select a result first (↑/↓)", severity="warning")
                return
            targets = [self._items[index]]
        else:
            targets = list(self._items)

        self._downloading = True
        self._set_download_buttons(True)
        self.notify(f"downloading {len(targets)} video(s) at {self.quality}", timeout=3)
        self.download_worker(targets, self.quality)

    @work(thread=True, group="downloads")
    def download_worker(self, targets: list[engine.MediaItem], quality: str) -> None:
        self.call_from_thread(self._panel_clear)
        for raw in targets:
            if not raw.title:
                try:
                    raw.title = engine.resolve_title(raw)
                except Exception:
                    pass
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
                try:
                    engine.record_history(
                        {
                            "url": raw.url,
                            "kind": raw.kind,
                            "title": raw.title or "",
                            "quality": quality,
                            "destination": dest,
                        }
                    )
                except Exception:
                    pass
                self.call_from_thread(self._dl_done, bar, status, dest)
            except Exception as exc:
                self.call_from_thread(self._dl_error, bar, status, str(exc))
        self.call_from_thread(self._downloading_done)

    def _panel_clear(self) -> None:
        self.query_one("#downloads").remove_children()

    def _dl_start(self, raw: engine.MediaItem) -> None:
        bar = ProgressBar(show_eta=True, show_percentage=True)
        status = Static("queued…", classes="dl-status")
        row = Container(
            Static(_clip(raw.title or raw.url, 60), classes="dl-title"),
            Label(f"{raw.kind or 'unknown'} · {_clip(raw.url, 46)}", classes="dl-sub"),
            bar,
            status,
            classes="dl-row",
        )
        panel = self.query_one("#downloads")
        panel.mount(row)
        panel.scroll_end(animate=False)
        self._tasks[raw.url] = (bar, status)
        self.notify(f"downloading: {_clip(raw.title or raw.url, 40)}", timeout=2)

    def _dl_tick(self, bar: ProgressBar, status: Static, info: dict) -> None:
        if info.get("status") != "downloading":
            return
        total = info.get("total_bytes") or info.get("total_bytes_estimate")
        done = info.get("downloaded_bytes", 0)
        if total:
            bar.update(total=total, progress=done)
            speed = info.get("speed")
            if speed:
                status.update(f"{done / total * 100:5.1f}% · {format_bytes(speed)}/s")
            else:
                status.update(f"{done / total * 100:5.1f}%")

    def _dl_done(self, bar: ProgressBar, status: Static, dest: str) -> None:
        bar.update(total=100, progress=100)
        status.add_class("ok")
        status.update(f"saved: {Path(dest).name}")

    def _dl_error(self, bar: ProgressBar, status: Static, error: str) -> None:
        status.add_class("err")
        status.update(f"failed: {_clip(error, 50)}")

    def _downloading_done(self) -> None:
        self._downloading = False
        self._tasks.clear()
        self._set_download_buttons(False)
        self.query_one("#url").focus()
        self.notify("all downloads finished", timeout=4)


def format_bytes(n: float | int) -> str:
    """Turn a byte count into a compact human string."""
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} GB"


def launch(output: Path | None = None, start_url: str | None = None) -> None:
    MbedlyApp(output=output, start_url=start_url).run()