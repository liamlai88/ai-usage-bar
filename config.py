# Refresh interval in seconds. The widget polls both APIs at this rate.
REFRESH_INTERVAL = 30

# UI language: "zh" (简体中文), "en" (English), or "auto" (detect from system).
LANG = "auto"

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
SERVER_ENABLED = True
SERVER_HOST    = "0.0.0.0"     # bind 0.0.0.0 so LAN devices can reach
SERVER_PORT    = 8089

# ---------------- USB Serial bridge (for M5Stick over USB) ----------------
# Pushes JSON snapshots to a USB-serial device so the hardware widget can
# work without WiFi. Auto-detects /dev/cu.usbserial-* / /dev/cu.wchusbserial-*.
SERIAL_ENABLED = True
SERIAL_PORT    = None          # None = auto-detect; or set e.g. "/dev/cu.usbserial-XXX"
SERIAL_BAUD    = 115200
SERIAL_PUSH_EVERY = 5          # seconds; M5Stick reads continuously


