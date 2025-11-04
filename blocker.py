#!/usr/bin/env python3
"""
Site Blocker Daemon
Blocks configured websites during blocking hours (7pm-7am) by modifying /etc/hosts
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
SITES_FILE = SCRIPT_DIR / "sites.txt"
HOSTS_FILE = Path("/etc/hosts")
BLOCKER_MARKER_START = "# BEGIN SITE-BLOCKER"
BLOCKER_MARKER_END = "# END SITE-BLOCKER"
CHECK_INTERVAL = 300  # Check every 5 minutes
BLOCKING_START_HOUR = 19  # 7pm
BLOCKING_END_HOUR = 7     # 7am

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def is_blocking_hours():
    """Check if current time is within blocking hours (7pm-7am)"""
    current_hour = datetime.now().hour
    # Blocking hours: 19-23 and 0-6 (7pm to 7am)
    return current_hour >= BLOCKING_START_HOUR or current_hour < BLOCKING_END_HOUR

def load_sites():
    """Load sites to block from configuration file"""
    if not SITES_FILE.exists():
        log(f"Sites file not found: {SITES_FILE}")
        return []

    sites = []
    with open(SITES_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                sites.append(line)

    return sites

def get_current_blocks():
    """Read current blocker entries from hosts file"""
    if not HOSTS_FILE.exists():
        return []

    try:
        with open(HOSTS_FILE, 'r') as f:
            content = f.read()

        # Extract our block section
        if BLOCKER_MARKER_START in content and BLOCKER_MARKER_END in content:
            start = content.index(BLOCKER_MARKER_START)
            end = content.index(BLOCKER_MARKER_END) + len(BLOCKER_MARKER_END)
            return content[start:end]
        return ""
    except PermissionError:
        log("ERROR: Cannot read /etc/hosts - need sudo permissions")
        sys.exit(1)

def generate_block_entries(sites):
    """Generate hosts file entries to block sites"""
    if not sites:
        return ""

    entries = [BLOCKER_MARKER_START]
    for site in sites:
        # Add both www and non-www versions
        entries.append(f"127.0.0.1 {site}")
        if not site.startswith("www."):
            entries.append(f"127.0.0.1 www.{site}")
    entries.append(BLOCKER_MARKER_END)

    return "\n".join(entries) + "\n"

def update_hosts_file(block_entries):
    """Update /etc/hosts with new block entries"""
    try:
        # Read current hosts file
        with open(HOSTS_FILE, 'r') as f:
            content = f.read()

        # Remove existing blocker section if present
        if BLOCKER_MARKER_START in content:
            start = content.index(BLOCKER_MARKER_START)
            end = content.index(BLOCKER_MARKER_END) + len(BLOCKER_MARKER_END)
            content = content[:start] + content[end:]

        # Clean up extra newlines
        content = content.rstrip() + "\n"

        # Add new block entries if provided
        if block_entries:
            content += "\n" + block_entries

        # Write back to hosts file
        with open(HOSTS_FILE, 'w') as f:
            f.write(content)

        return True
    except PermissionError:
        log("ERROR: Cannot write to /etc/hosts - need sudo permissions")
        return False
    except Exception as e:
        log(f"ERROR: Failed to update hosts file: {e}")
        return False

def flush_dns_cache():
    """Flush DNS cache on macOS"""
    try:
        # macOS command to flush DNS cache
        subprocess.run(
            ["dscacheutil", "-flushcache"],
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["killall", "-HUP", "mDNSResponder"],
            check=True,
            capture_output=True
        )
        log("DNS cache flushed")
    except subprocess.CalledProcessError as e:
        log(f"Warning: Failed to flush DNS cache: {e}")
    except Exception as e:
        log(f"Warning: Error flushing DNS cache: {e}")

def ensure_correct_state():
    """Ensure hosts file matches the current time-based state"""
    should_block = is_blocking_hours()
    sites = load_sites()

    if should_block:
        # Generate block entries
        desired_entries = generate_block_entries(sites)
        current_entries = get_current_blocks()

        # Only update if different
        if desired_entries.strip() != current_entries.strip():
            log(f"Blocking hours active - blocking {len(sites)} sites")
            if update_hosts_file(desired_entries):
                flush_dns_cache()
                log("Sites blocked successfully")
    else:
        # Remove blocks
        current_entries = get_current_blocks()
        if current_entries:
            log("Outside blocking hours - removing blocks")
            if update_hosts_file(""):
                flush_dns_cache()
                log("Sites unblocked successfully")

def main():
    """Main daemon loop"""
    log("Site Blocker daemon starting")
    log(f"Blocking hours: {BLOCKING_START_HOUR}:00 - {BLOCKING_END_HOUR}:00")
    log(f"Checking every {CHECK_INTERVAL} seconds")

    # Check if running as root
    if os.geteuid() != 0:
        log("ERROR: Must run as root (use sudo)")
        sys.exit(1)

    # Ensure sites file exists
    if not SITES_FILE.exists():
        log(f"Warning: Sites file not found at {SITES_FILE}")
        log("Creating empty sites.txt - add sites to block there")
        SITES_FILE.write_text("# Add sites to block, one per line\n# Example:\n# reddit.com\n# twitter.com\n")

    # Initial state check
    ensure_correct_state()

    # Main loop
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            ensure_correct_state()
    except KeyboardInterrupt:
        log("Daemon stopping - cleaning up")
        # Remove blocks on exit
        update_hosts_file("")
        flush_dns_cache()
        log("Cleanup complete")
        sys.exit(0)

if __name__ == "__main__":
    main()
