#!/usr/bin/env python3
"""tools/notify.py — best-effort cross-platform agent notification.

Tries (in order): AUTO_PRODUCTION_NOTIFY_URL webhook → notify-send (linux desktop)
→ osascript (macOS) → stdout. Always exits 0 (notification is advisory).
"""
import os, subprocess, sys, urllib.request

def main():
    msg = " ".join(sys.argv[1:]) or sys.stdin.read().strip()
    if not msg:
        return

    url = os.environ.get("AUTO_PRODUCTION_NOTIFY_URL", "")
    if url:
        try:
            req = urllib.request.Request(url, data=msg.encode(), method="POST")
            urllib.request.urlopen(req, timeout=5)
            return
        except Exception:
            pass

    for cmd in (["notify-send", "auto-production", msg],
                ["osascript", "-e", f'display notification "{msg}" with title "auto-production"']):
        try:
            subprocess.run(cmd, capture_output=True, timeout=3, check=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue

    print(f"[notify] {msg}")

if __name__ == "__main__":
    main()
