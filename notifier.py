"""Send native macOS notifications.

In a bundled .app (py2app), uses rumps.notification so the notification
appears under the app's own name in Notification Center.
When running as a plain script, falls back to osascript which works without
a bundle ID but shows "Script Editor" as the sender.
"""
import sys
import subprocess


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _notify_osascript(title: str, message: str, subtitle: str, sound: bool) -> bool:
    parts = [f'display notification "{_escape(message)}" with title "{_escape(title)}"']
    if subtitle:
        parts.append(f'subtitle "{_escape(subtitle)}"')
    if sound:
        parts.append('sound name "Glass"')
    try:
        subprocess.run(["osascript", "-e", " ".join(parts)], timeout=3,
                       check=False, capture_output=True)
        return True
    except Exception:
        return False


def notify(title: str, message: str, subtitle: str = "", sound: bool = False) -> bool:
    """Fire a macOS notification. Returns True on success, False otherwise."""
    if getattr(sys, "frozen", False):
        try:
            import rumps
            rumps.notification(title=title, subtitle=subtitle, message=message,
                               sound=sound)
            return True
        except Exception:
            pass
    return _notify_osascript(title, message, subtitle, sound)


if __name__ == "__main__":
    notify("AI Usage Bar", "Resets in 1h 28m", subtitle="Claude 5h at 85%", sound=True)
