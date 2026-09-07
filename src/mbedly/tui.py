"""Mbedly terminal UI built on rich."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.prompt import Prompt
from rich.table import Table

from mbedly import engine

BANNER = r"""
 ██████   ██████ █████                  █████ ████
 ░░██████ ██████ ░░███                  ░░███ ░░███
 ░███░█████░███  ░███████   ██████   ███████  ░███  █████ ████
 ░███░░███ ░███  ░███░░███ ███░░███ ███░░███  ░███ ░░███ ░███
 ░███ ░░░  ░███  ░███ ░███░███████ ░███ ░███  ░███  ░███ ░███
 ░███      ░███  ░███ ░███░███░░░  ░███ ░███  ░███  ░███ ░███
 █████     █████ ████████ ░░██████ ░░████████ █████ ░░███████
 ░░░░░     ░░░░░ ░░░░░░░░   ░░░░░░   ░░░░░░░░ ░░░░░   ░░░░░███
                                                       ███ ░███
        Made With <3 By ammar mohamed (ammar0xff)       ░░██████
                                                         ░░░░░░
"""

QUALITY_OPTIONS = ["144p", "360p", "480p", "720p", "1080p", "2k", "4k", "mp3"]


def default_output_dir() -> Path:
    home = Path.home()
    downloads = home / "Downloads"
    return downloads / "mbedly" if downloads.exists() else home / "mbedly"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mbedly",
        description="Full-featured video downloader & web scraper - makes a video from literally everything.",
    )
    parser.add_argument("url", nargs="?", help="page URL, direct video URL, or YouTube link")
    parser.add_argument(
        "-q", "--quality",
        choices=QUALITY_OPTIONS,
        default=None,
        help="download quality (default: prompt or 1080p for single videos)",
    )
    parser.add_argument(
        "-n", "--video",
        default=None,
        help="video number from the extracted list, or ALL to grab every one",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=default_output_dir(),
        help="output folder (default: ~/Downloads/mbedly)",
    )
    parser.add_argument(
        "-c", "--cookies",
        default=None,
        help="cookie header string (Cookie Editor export) for Mahara-Tech courses",
    )
    return parser


def list_videos(console: Console, items: list[engine.MediaItem]) -> None:
    table = Table(title="Extracted media", show_header=True, header_style="bold green")
    table.add_column("#", style="cyan", no_wrap=True)
    table.add_column("Kind", style="yellow")
    table.add_column("Title", style="green")
    table.add_column("Channel / Source", style="dim")
    for i, item in enumerate(items, start=1):
        title = item.title or item.url
        source = item.channel or item.url
        table.add_row(str(i), item.kind, title[:60], source[:50])
    console.print(table)


def pick_quality(console: Console, quiet: bool, default: str = "1080p") -> str:
    if quiet:
        return default
    console.print(
        "[bold green]Ready to download - pick a quality:[/] "
        "[cyan]1.144p 2.360p 3.480p 4.720p 5.1080p 6.2k 7.4k 8.mp3[/]"
    )
    choice = Prompt.ask(
        "[green]Quality [1-8][/]",
        choices=[str(i) for i in range(1, 9)],
        default="5",
    )
    return QUALITY_OPTIONS[int(choice) - 1]


def download_items(
    console: Console,
    items: list[engine.MediaItem],
    quality: str,
    output: Path,
    record: bool = False,
) -> None:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        BarColumn(bar_width=30),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console,
    )
    with progress:
        for raw in items:
            name = raw.title or Path(raw.url).name or raw.url
            task = progress.add_task(f"[cyan]{name[:44]}", total=None)

            def _hook(status: dict, _task=task) -> None:
                if status.get("status") != "downloading":
                    if status.get("status") == "finished":
                        progress.update(_task, completed=progress.tasks[_task].total or 1)
                    return
                total = status.get("total_bytes") or status.get("total_bytes_estimate")
                done = status.get("downloaded_bytes", 0)
                if total:
                    progress.update(_task, total=total, completed=done)

            dest = engine.download(raw.url, quality=quality, output_dir=output, progress_cb=_hook)
            progress.update(task, description=f"[green]saved: {dest}")
            if record:
                engine.record_history(
                    {
                        "url": raw.url,
                        "kind": raw.kind,
                        "title": raw.title or "",
                        "quality": quality,
                        "destination": str(dest),
                    }
                )


def run(
    console: Console,
    url: str,
    quality: str | None = None,
    video: str | None = None,
    output: Path = None,
    cookies: str | None = None,
    non_interactive: bool = False,
) -> int:
    output = output or default_output_dir()
    console.print(f"[dim]output dir:[/] [green]{output}[/]")

    quiet = non_interactive or not sys.stdin.isatty()

    try:
        with console.status("[yellow]analysing source for media...[/]", spinner="dots"):
            items = engine.scrape(url, cookies)
    except Exception as exc:
        console.print(f"[bold red]! error analysing source:[/] {exc}")
        return 1

    if not items:
        console.print("[bold red]! no supported media found on that page.[/]")
        return 1

    if len(items) == 1:
        one = items[0]
        console.print(f"[green]Detected media:[/] {one.title or one.url}")
        console.print(f"[dim]channel/source:[/] {one.channel or one.url}")
        selected = [one]
    else:
        list_videos(console, items)
        if quiet and not video:
            console.print(
                "[bold yellow]! multiple videos found; pass --video N or --video ALL[/]"
            )
            return 1
        if video and str(video).upper() == "ALL":
            selected = items
        elif video:
            try:
                selected = [items[int(video) - 1]]
            except (ValueError, IndexError):
                console.print(f"[bold red]! invalid video number:[/] {video}")
                return 1
        else:
            choice = Prompt.ask("[purple]Select video number or ALL[/]", default="1")
            selected = items if choice.upper() == "ALL" else items[int(choice) - 1]

    if not quality:
        quality = pick_quality(console, quiet)
    console.print(f"[bold green]> downloading {len(selected)} video(s) at {quality}...[/]")

    for item in selected:
        console.print(f"[green]> {item.title or item.url}[/]")
        try:
            download_items(console, [item], quality, output, record=True)
        except Exception as exc:
            console.print(f"[bold red]! download failed:[/] {exc}")
            return 1

    console.print("[bold green]done. Mbedly out. \\\\m/[/]")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    console = Console()
    console.print(Panel(BANNER, border_style="yellow", expand=False))
    console.print(
        "[dim]full-featured video downloader & web scraper - cross-platform TUI[/]\n"
    )

    if args.url:
        return run(
            console,
            args.url,
            quality=args.quality,
            video=args.video,
            output=args.output,
            cookies=args.cookies,
            non_interactive=True,
        )

    if not sys.stdin.isatty():
        parser.print_help()
        return 1

    # Interactive REPL: keep processing URLs until the user quits.
    while True:
        url = Prompt.ask("[yellow]Enter a URL containing an embedded video[/]")
        if not url or url.lower() in ("q", "quit", "exit"):
            break
        run(console, url, quality=args.quality, video=args.video, output=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())