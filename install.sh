#!/usr/bin/env bash
# Mbedly cross-platform installer.
# Works on: Debian/Ubuntu, macOS (Homebrew), Termux, Windows (Git Bash / WSL).
# For plain Windows: `py -m pip install .` after installing Python + ffmpeg.

set -e

PYTHON="python3"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON="python"
fi

echo "[mbedly] installing dependencies via $PYTHON"

# ffmpeg: merged mp4 (video+audio), mp3 conversion, m3u8/HLS support.
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[mbedly] ffmpeg not found - installing for your platform..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y ffmpeg python3-pip
  elif command -v pkg >/dev/null 2>&1; then          # Termux
    pkg install -y ffmpeg python
  elif command -v brew >/dev/null 2>&1; then          # macOS
    brew install ffmpeg
  else
    echo "[mbedly] ! install ffmpeg manually, then run: $PYTHON -m pip install ."
    exit 1
  fi
fi

"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install .

echo
echo "[mbedly] installed. Run: mbedly --help"