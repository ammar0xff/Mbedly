# Mbedly

<p align="center">
  <img src="https://img.shields.io/github/stars/ammar0xff/Mbedly?style=for-the-badge&color=orange" />
  <img src="https://img.shields.io/github/license/ammar0xff/Mbedly?style=for-the-badge&color=orange" />
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-00FF41?style=for-the-badge" />
  <img src="https://img.shields.io/badge/language-python-blue?style=for-the-badge" />
</p>

**A full-featured video downloader & web scraper — makes a video from literally everything.**

Give Mbedly a page URL and it will hunt down every embedded video on it, let you pick a
quality (144p → 4K, or mp3), and download them all with a live progress bar. Fully
**cross-platform**: Windows, macOS, Linux, and Android (Termux).

## Features

- 🔍 **Scrapes any page** and extracts every embedded video URL (YouTube, Facebook, LiviVideo, native `.mp4`, HLS `.m3u8`).
- ▶️ **YouTube** — watch / youtu.be / embed / shorts / live URLs, with title & channel from oEmbed.
- 📚 **Mahara-Tech courses** — dump every lecture of a course (cookie header support).
- 🎚️ **Quality selection** — 144p, 360p, 480p, 720p, 1080p, 2K, 4K, and mp3 audio.
- ⬇️ **Batch mode** — grab one video, several, or *ALL* at once.
- 🖥️ **Textual dashboard** — a btop/opencode-style full-screen TUI. No mouse required.
- 📜 **Download history** kept in `~/.mbedly/history.json`.
- 🧩 **Clean engine layer** (`mbedly.engine`) — pure Python, ready to be reused by the upcoming Flutter app.

## Installation

> Requires **Python 3.9+**, **ffmpeg**, and the `textual` dependency (installed automatically).

```sh
git clone https://github.com/ammar0xff/Mbedly.git && cd Mbedly
./install.sh          # Debian/Ubuntu, macOS, Termux, Git Bash / WSL
```

or manually:

```sh
python -m pip install .
mbedly --help
```

- **Windows (native):** `py -m pip install .` (ffmpeg via `winget install ffmpeg`)
- **macOS:** `brew install ffmpeg && pip3 install .`
- **Termux:** `pkg install -y ffmpeg && pip install .`

## Usage

**Dashboard (like btop / opencode):**

```sh
mbedly                 # opens the full-screen dashboard on a terminal
mbedly --tui "URL"     # open the dashboard with a URL already loaded
```

> Dashboard keys: `Enter` on the URL box analyses a page and shows every video with its
> **real title** (labels resolved automatically). `↑/↓` select a result, `d` downloads it,
> `a` downloads all. Pick a quality (144p → mp3), watch live progress/speed, then hit
> download. `?` shows all shortcuts, `r` shows download history, `q` / `Ctrl+Q` quits,
> `/` focuses the URL box.

**Direct command:**

```sh
mbedly "https://www.youtube.com/watch?v=dQw4w9WgXcQ"          # 1080p default
mbedly "URL" -q 720p                                          # pick quality
mbedly "URL" -q mp3                                           # audio only
mbedly "URL" -q 1080p -n ALL -o ~/Videos                      # every video found
mbedly "https://maharatech.gov.eg/course/view.php?id=X" -c "cookie editor header"
mbedly -h                                                    # help
```

## Roadmap

- [x] Scrape any page for embedded video links & download them
- [x] YouTube (watch / embed / shorts / live) with metadata
- [x] Mahara-Tech course extraction (cookie support)
- [x] Facebook, LiviVideo, native `.mp4`, HLS `.m3u8`
- [x] Cross-platform full-screen dashboard (Textual) with progress bars & download history
- [ ] Flutter desktop / mobile app (planned — reuses `mbedly.engine`)
- [ ] Udemy, Coursera, Alison password-gated course extraction
- [ ] Playlist & serialized episode downloads
- [ ] Queue management + parallel downloads

## Development

```sh
pip install -e ".[dev]"
pytest
```

## License

Distributed under the MIT License.

## Contact

Ammar Mohamed — ammar0xf@gmail.com

Project Link: https://github.com/ammar0xff/Mbedly

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — the download engine
- [Rich](https://github.com/Textualize/rich) — the terminal UI
- [Textual](https://github.com/Textualize/textual) — the full-screen dashboard