# Refresh interval in seconds. The widget polls both APIs at this rate.
REFRESH_INTERVAL = 30

# UI language: "zh" (简体中文), "en" (English), or "auto" (detect from system).
LANG = "auto"

# ---------------- HTTP Proxy ----------------
# When the widget is started from Login Items / launchd / Finder, it does NOT
# inherit HTTP_PROXY/HTTPS_PROXY from your shell, so requests to api.anthropic.com
# and chatgpt.com may fail with timeouts or "Connection refused" if you need a
# proxy. Set this to force a proxy regardless of how the widget was launched.
# Leave as None to use whatever's already in the environment.
# Example: "http://127.0.0.1:7897"  (Clash Verge default mixed port)
HTTP_PROXY = None

# ---------------- Threshold alerts ----------------
# When the 5h or 7d usage crosses one of these thresholds upward,
# a native macOS notification fires once. Drops back below the lowest
# threshold to re-arm.
ALERT_ENABLED = True
ALERT_THRESHOLDS = [80, 95]    # percentages
ALERT_SOUND = False            # play default notification sound

# ---------------- Local HTTP server (for M5Stick / external devices) ----------------
# Exposes GET /usage returning the latest fetched data as JSON.
# Disabled by default; enable when you want a hardware widget to poll your Mac.
SERVER_ENABLED = False
SERVER_HOST    = "0.0.0.0"     # bind 0.0.0.0 so LAN devices can reach
SERVER_PORT    = 8089

# ---------------- USB Serial bridge (for M5Stick over USB) ----------------
# Pushes JSON snapshots to a USB-serial device so the hardware widget can
# work without WiFi. Auto-detects /dev/cu.usbserial-* / /dev/cu.wchusbserial-*.
SERIAL_ENABLED = False
SERIAL_PORT    = None          # None = auto-detect; or set e.g. "/dev/cu.usbserial-XXX"
SERIAL_BAUD    = 115200
SERIAL_PUSH_EVERY = 5          # seconds; M5Stick reads continuously


