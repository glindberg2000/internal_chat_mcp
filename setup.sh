#!/bin/bash
set -e

# Universal reproducible setup for internal_chat_mcp

# 1. Checkout known-good commit
echo "[INFO] Checking out known-good commit..."
git fetch origin d75f5eea1b1ac2338ce42a544acb6205519d01df || true
git checkout d75f5eea1b1ac2338ce42a544acb6205519d01df

# 2. Create venv if not exists
if [ ! -d ".venv" ]; then
  echo "[INFO] Creating Python 3.13 venv..."
  python3.13 -m venv .venv
fi

# 3. Activate venv
echo "[INFO] Activating venv..."
source .venv/bin/activate

# 4. Upgrade pip and install dependencies
echo "[INFO] Installing frozen dependencies..."
pip install --upgrade pip
pip install -e .

# 5. Print binary path for .cursor/mcp.json
BINARY_PATH="$(pwd)/.venv/bin/internal-chat-mcp"
echo "\n[INFO] Setup complete!"
echo "[INFO] Use this path in your .cursor/mcp.json config:"
echo "    $BINARY_PATH"
echo "[INFO] Set your INTERNAL_CHAT_USER in the config to your username."
echo "[INFO] Example .cursor/mcp.json entry:"
echo '  "command": "'$BINARY_PATH'",'
echo '  "args": ["--mode", "stdio"],'
echo '  "cwd": "'$(pwd)'",'
echo '  "env": {'
echo '    "INTERNAL_CHAT_TEAM_ID": "PDF_Extractor",'
echo '    "INTERNAL_CHAT_USER": "<YOUR_USERNAME>",'
echo '    "BACKEND_HOST": "localhost:8000"'
echo '  }'
echo '}'
echo "\n[INFO] Done! Restart Cursor and you should see tools enabled." 