#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

APP_PATH="dist/AI Search Agent.app"
DMG_PATH="dist/AI Search Agent.dmg"

if [[ ! -d "$APP_PATH" ]]; then
  echo "App bundle not found at $APP_PATH. Build it first with scripts/build_mac_app.sh"
  exit 1
fi

hdiutil create -volname "AI Search Agent" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"
echo "Built DMG: $ROOT_DIR/$DMG_PATH"
