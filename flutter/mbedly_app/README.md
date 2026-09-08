# mbedly_app

Flutter frontend for **Mbedly**. Talks to the local `mbedly-api` (Python) over
JSON - no yt-dlp inside the app, the engine stays in Python where ffmpeg &
yt-dlp already run.

## Run

1. Start the backend on the machine that has the engine:
   ```bash
   pip install -e . && mbedly-api --port 8765
   ```
   (for Flutter web run from the same machine, keep `127.0.0.1`; for a mobile
   device on your LAN start it with `--host 0.0.0.0`.)
2. Run the app:
   ```bash
   cd flutter/mbedly_app
   flutter pub get
   flutter run -d chrome    # or any device
   ```
   Default API base is `http://127.0.0.1:8765`.

## What's inside

- `HomeScreen` - paste a URL (page, playlist, direct video), analyze, pick a
  quality chip, download selection or everything.
- `DownloadsScreen` - live progress (percent, bytes, transfer speed), auto
  polls `/jobs` until every job finishes.
- `HistoryScreen` - past downloads, newest first.
- `ApiClient` - typed JSON client over `package:http`; swap in a fake for tests.

## Tests

`flutter test` - uses an in-memory `FakeApiClient`, never touches the network.