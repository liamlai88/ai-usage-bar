"""Send native macOS notifications via osascript.

Why osascript instead of rumps.notification?
- rumps.notification requires a bundled app (py2app) with a unique bundle ID;
  it silently fails when running as a plain Python script.
- osascript hits AppleScript's `display notification` which always works,
  needs no bundle, and renders in Notification Center the same way.
"""
import shlex
import subprocess


def _escape(s: str) -> str:
    """Escape backslashes and double quotes for AppleScript string literals."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str, subtitle: str = "", sound: bool = False) -> bool:
    """Fire a macOS notification. Returns True on success, False otherwise."""
    parts = [f'display notification "{_escape(message)}" with title "{_escape(title)}"']
    if subtitle:
        parts.append(f'subtitle "{_escape(subtitle)}"')
    if sound:
        parts.append('sound name "Glass"')
    script = " ".join(parts)
    try:
        subprocess.run(["osascript", "-e", script], timeout=3, check=False,
                       capture_output=True)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    notify("AI Usage Bar", "Resets in 1h 28m", subtitle="Claude 5h at 85%", sound=True)
