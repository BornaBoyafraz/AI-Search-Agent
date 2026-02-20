@echo off
setlocal

set ROOT_DIR=%~dp0\..
cd /d "%ROOT_DIR%"

if exist ".venv\\Scripts\\python.exe" (
  .venv\\Scripts\\python.exe -m PyInstaller --noconfirm --clean ai_search_agent.spec
) else (
  py -m PyInstaller --noconfirm --clean ai_search_agent.spec
)

echo Built executable folder: %ROOT_DIR%\\dist\\AI Search Agent
endlocal
