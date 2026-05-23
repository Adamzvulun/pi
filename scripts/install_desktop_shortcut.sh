#!/bin/bash
# install_desktop_shortcut.sh — create a Laser Tracker launcher icon on
# the Pi's desktop, so the control panel can be opened with a double-click
# instead of a terminal command.
#
# Run once on the Pi over SSH or in a Pi-desktop terminal:
#
#     bash ~/pi/scripts/install_desktop_shortcut.sh
#
# After this an icon labeled "Laser Tracker" appears on the desktop.
# Double-click it to launch control_panel.py — venv activation, working
# directory, and DISPLAY are all handled automatically.

set -euo pipefail

# --- Resolve paths from the script's own location -------------------------
# This means the script works no matter where the repo is cloned; it
# always points the launcher at the control_panel.py sitting next to it.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"
TARGET_SCRIPT="$PROJECT_DIR/control_panel.py"
DESKTOP_DIR="$HOME/Desktop"
DESKTOP_FILE="$DESKTOP_DIR/laser-tracker.desktop"

# --- Sanity checks --------------------------------------------------------
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "ERROR: venv python not found at $VENV_PYTHON" >&2
    echo "Create the venv first:" >&2
    echo "    cd $PROJECT_DIR" >&2
    echo "    python3 -m venv --system-site-packages venv" >&2
    echo "    source venv/bin/activate" >&2
    echo "    pip install -r requirements.txt" >&2
    exit 1
fi

if [[ ! -f "$TARGET_SCRIPT" ]]; then
    echo "ERROR: control_panel.py not found at $TARGET_SCRIPT" >&2
    echo "Make sure the repo is up to date: cd $PROJECT_DIR && git pull" >&2
    exit 1
fi

if [[ ! -d "$DESKTOP_DIR" ]]; then
    echo "ERROR: Desktop folder not found at $DESKTOP_DIR" >&2
    echo "Are you running this on a desktop environment (not headless)?" >&2
    exit 1
fi

# --- Write the .desktop file ---------------------------------------------
# Spec reference: https://specifications.freedesktop.org/desktop-entry-spec/
# - Exec uses the venv python directly so the activate step is unnecessary
# - Path sets the working directory so relative imports (config, servo,
#   laser, etc.) inside control_panel.py resolve correctly
# - Icon "applications-engineering" is a standard freedesktop icon name
#   that exists in the default Bookworm icon theme
# - Terminal=false because this is a GUI app; no console is needed
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Laser Tracker
GenericName=Tracker Control Panel
Comment=Central operator GUI — servos, laser, tracking, system
Exec=$VENV_PYTHON $TARGET_SCRIPT
Path=$PROJECT_DIR
Icon=applications-engineering
Terminal=false
Categories=Utility;Development;
StartupNotify=true
EOF

# Mark executable. Bookworm's pcmanfm will then treat the file as a
# launcher (showing the icon + name) rather than as a regular text file.
chmod +x "$DESKTOP_FILE"

echo "✓ Created $DESKTOP_FILE"
echo
echo "The 'Laser Tracker' icon should appear on your desktop within a"
echo "few seconds. If it doesn't, log out and back in to refresh the"
echo "desktop session, or run:"
echo "    pcmanfm --reload"
echo
echo "On Bookworm's first launch you may see a 'This file isn't trusted'"
echo "dialog. Click 'Trust and Launch' (or 'Execute'). Subsequent"
echo "launches won't prompt."
