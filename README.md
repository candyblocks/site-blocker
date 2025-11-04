# Site Blocker

A macOS daemon that automatically blocks distracting websites during specific hours by modifying your system's `/etc/hosts` file.

## Features

- **Time-based blocking**: Blocks sites from 7:00 PM to 7:00 AM
- **Laptop-friendly**: Works correctly even if your computer sleeps/wakes during blocking hours
- **OS-level blocking**: Blocks all browsers and apps (not just a browser extension)
- **Automatic**: Runs as a background daemon, starts on boot
- **Easy configuration**: Simple text file to manage blocked sites

## How It Works

The daemon runs continuously in the background and checks every 5 minutes whether it's currently blocking hours. During blocking hours (7pm-7am), it adds entries to `/etc/hosts` that redirect blocked websites to `127.0.0.1` (localhost), making them unreachable.

## Installation

1. **Configure sites to block**:
   ```bash
   cd site-blocker
   nano sites.txt
   ```
   Uncomment or add the sites you want to block (one per line)

2. **Install the daemon**:
   ```bash
   sudo ./install.sh
   ```

That's it! The daemon is now running and will start automatically on boot.

## Configuration

### Blocked Sites

Edit `sites.txt` to add or remove sites:

```
# Add one domain per line (no https://)
reddit.com
twitter.com
youtube.com
```

Changes take effect within 5 minutes (next check cycle) or you can restart the daemon:
```bash
sudo launchctl unload /Library/LaunchDaemons/com.user.siteblocker.plist
sudo launchctl load /Library/LaunchDaemons/com.user.siteblocker.plist
```

### Blocking Hours

To change blocking hours, edit `blocker.py`:

```python
BLOCKING_START_HOUR = 19  # 7pm (use 24-hour format)
BLOCKING_END_HOUR = 7     # 7am
```

Then restart the daemon (see above).

### Check Interval

By default, checks every 5 minutes. To change, edit `blocker.py`:

```python
CHECK_INTERVAL = 300  # seconds (300 = 5 minutes)
```

## Usage

### View logs
```bash
tail -f ~/Code/site-blocker/blocker.log
```

### Check if daemon is running
```bash
sudo launchctl list | grep siteblocker
```

### Manually restart daemon
```bash
sudo launchctl unload /Library/LaunchDaemons/com.user.siteblocker.plist
sudo launchctl load /Library/LaunchDaemons/com.user.siteblocker.plist
```

### Temporarily disable (until next boot)
```bash
sudo launchctl unload /Library/LaunchDaemons/com.user.siteblocker.plist
```

### Re-enable
```bash
sudo launchctl load /Library/LaunchDaemons/com.user.siteblocker.plist
```

## Uninstallation

```bash
sudo ./uninstall.sh
```

This will:
- Stop and remove the daemon
- Clean up `/etc/hosts`
- Flush DNS cache

You can then safely delete the `site-blocker` directory.

## Troubleshooting

### Sites aren't blocked

1. Check if daemon is running: `sudo launchctl list | grep siteblocker`
2. Check logs: `tail -f ~/Code/site-blocker/blocker.log`
3. Verify it's blocking hours and sites are in `sites.txt`
4. Try flushing DNS manually: `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder`

### Changes to sites.txt not taking effect

Wait 5 minutes for the next check, or restart the daemon manually.

### Permission errors

The daemon needs root access to modify `/etc/hosts`. Make sure you used `sudo` when installing.

## Technical Details

- **Language**: Python 3
- **Scheduler**: macOS `launchd`
- **Method**: Modifies `/etc/hosts` to redirect blocked domains to `127.0.0.1`
- **DNS Cache**: Automatically flushed after changes
- **Check frequency**: Every 5 minutes (configurable)

## Files

- `blocker.py` - Main daemon script
- `sites.txt` - List of sites to block
- `install.sh` - Installation script
- `uninstall.sh` - Uninstallation script
- `com.user.siteblocker.plist` - launchd configuration
- `blocker.log` - Daemon log file (created after installation)
- `blocker.error.log` - Error log (created after installation)

## Notes

- The tool blocks both `example.com` and `www.example.com` automatically
- Blocking persists through sleep/wake cycles
- Works with all browsers and applications
- Does not require internet connection to function
- Clean uninstall removes all traces from your system
