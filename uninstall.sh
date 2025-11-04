#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PLIST_NAME="com.user.siteblocker.plist"
PLIST_DEST="/Library/LaunchDaemons/$PLIST_NAME"
HOSTS_FILE="/etc/hosts"
MARKER_START="# BEGIN SITE-BLOCKER"
MARKER_END="# END SITE-BLOCKER"

echo -e "${YELLOW}Site Blocker Uninstaller${NC}"
echo "========================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This uninstaller must be run with sudo${NC}"
    echo "Usage: sudo ./uninstall.sh"
    exit 1
fi

# Unload daemon
if [ -f "$PLIST_DEST" ]; then
    echo "Stopping daemon..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true

    echo "Removing launch daemon..."
    rm -f "$PLIST_DEST"
else
    echo "Launch daemon not found (already uninstalled?)"
fi

# Clean up hosts file
echo "Cleaning up /etc/hosts..."
if grep -q "$MARKER_START" "$HOSTS_FILE" 2>/dev/null; then
    # Create temp file without blocker entries
    sed "/$MARKER_START/,/$MARKER_END/d" "$HOSTS_FILE" > /tmp/hosts.tmp
    mv /tmp/hosts.tmp "$HOSTS_FILE"
    echo "Removed blocker entries from /etc/hosts"

    # Flush DNS cache
    echo "Flushing DNS cache..."
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
else
    echo "No blocker entries found in /etc/hosts"
fi

echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
echo ""
echo "The site blocker has been removed and all sites are now unblocked."
echo "You can safely delete the site-blocker directory if you wish."
echo ""
