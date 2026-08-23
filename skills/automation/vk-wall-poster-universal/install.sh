#!/usr/bin/env bash
# install.sh — Universal installer for vk-wall-poster skill (Linux / macOS)

set -e

TARGET="${1:-hermes}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Installing vk-wall-poster Skill ==="

# 1. Install python dependencies
echo "[1/3] Checking Python dependencies..."
python3 -m pip install --quiet websocket-client requests pillow
echo "  Dependencies verified."

# 2. Deploy to target agent
echo "[2/3] Deploying skill to target: $TARGET..."
if [ "$TARGET" = "hermes" ]; then
    DEST="$HOME/.hermes/skills/vk-wall-poster"
    mkdir -p "$DEST"
    cp -r "$SCRIPT_DIR"/* "$DEST/"
    echo "  Deployed to Hermes skills: $DEST"
elif [ "$TARGET" = "claude" ]; then
    DEST=".claude/skills/vk-wall-poster"
    mkdir -p "$DEST"
    cp -r "$SCRIPT_DIR"/* "$DEST/"
    echo "  Deployed to Claude Code skills: $DEST"
elif [ "$TARGET" = "opencode" ]; then
    DEST="$HOME/.gemini/antigravity/skills/vk-wall-poster"
    mkdir -p "$DEST"
    cp -r "$SCRIPT_DIR"/* "$DEST/"
    echo "  Deployed to OpenCode/Antigravity: $DEST"
else
    echo "  Source ready at $SCRIPT_DIR"
fi

# 3. Test check
echo "[3/3] Testing VK connection..."
python3 "$SCRIPT_DIR/scripts/vk_wall_poster.py" --check || true

echo -e "\n=== Installation Complete! ==="
