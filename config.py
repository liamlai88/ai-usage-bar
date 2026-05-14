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
