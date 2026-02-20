# AI Search Agent

AI Search Agent is a packaged desktop chat application for running your existing search/summarization pipeline in a ChatGPT-style interface.

Run main.py to launch the app.

## Features

- Desktop window titled **AI Search Agent**
- Chat-style conversation panel with message bubbles
- Multi-line input + **Send** button
- **Enter** sends, **Shift+Enter** inserts a newline
- Shows user message immediately
- Shows assistant **Thinking...** bubble while searching
- Replaces thinking bubble with the final answer/results
- **Clear chat** button clears only the current conversation panel
- In-memory chat only: no chat/history persistence

## Architecture

- `main.py`: single app entry point (launches GUI by default; optional `--cli` terminal mode)
- `ui_app.py`: desktop GUI (Tkinter, desktop-native)
- `ui_agent.py`: wrapper integration layer with:
  - `run_agent(query: str) -> str`
- `models.py`: UI response/result models
- `agent/`: existing core search/fetch/extract/summarize logic (kept intact)
- `ai_search_agent.spec`: PyInstaller build spec

This repository currently uses the Tkinter fallback (PySide6 is not installed in this environment).

## Installation

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-build.txt
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-build.txt
```

## Build A Clickable App

### macOS `.app`

```bash
./scripts/build_mac_app.sh
```

Built output:

- `dist/AI Search Agent.app`

Run by clicking:

1. Open Finder
2. Go to `dist/`
3. Double-click `AI Search Agent.app`

Optional DMG:

```bash
./scripts/build_mac_dmg.sh
```

DMG output:

- `dist/AI Search Agent.dmg`

### Windows `.exe`

```powershell
scripts\build_windows_exe.bat
```

Built output folder:

- `dist\AI Search Agent\`

Main executable:

- `dist\AI Search Agent\AI Search Agent.exe`

Run by double-clicking `AI Search Agent.exe`.

## Development Run (without packaging)

```bash
python3 main.py
```

## Notes

- GUI calls agent logic in a background thread so the UI stays responsive.
- Search/network failures are rendered as friendly assistant messages in the chat panel.

## Author

Seyedborna Boyafraz

## License

MIT License. See `LICENSE`.
