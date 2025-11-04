#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_NAME="com.user.siteblocker.plist"
PLIST_DEST="/Library/LaunchDaemons/$PLIST_NAME"

echo -e "${GREEN}Site Blocker Installer${NC}"
echo "======================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This installer must be run with sudo${NC}"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

echo "Installing to: $SCRIPT_DIR"
echo ""

# Make blocker script executable
echo "Making blocker.py executable..."
chmod +x "$SCRIPT_DIR/blocker.py"

# Create plist with correct paths
echo "Configuring launch daemon..."
sed "s|SCRIPT_DIR|$SCRIPT_DIR|g" "$SCRIPT_DIR/$PLIST_NAME" > "$PLIST_DEST"

# Set correct permissions
chmod 644 "$PLIST_DEST"
chown root:wheel "$PLIST_DEST"

# Unload if already loaded (ignore errors)
echo "Unloading existing daemon (if any)..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# Load the daemon
echo "Loading daemon..."
launchctl load "$PLIST_DEST"

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "The site blocker daemon is now running."
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit $SCRIPT_DIR/sites.txt to add sites you want to block"
echo "2. The daemon checks every 5 minutes and blocks sites from 7pm-7am"
echo "3. View logs: tail -f $SCRIPT_DIR/blocker.log"
echo "4. To uninstall: sudo ./uninstall.sh"
echo ""
echo "The daemon will:"
echo "  - Block sites from 7:00 PM to 7:00 AM"
echo "  - Start automatically on boot"
echo "  - Continue running even after sleep/wake"
echo ""
