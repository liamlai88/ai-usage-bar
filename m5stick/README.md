# 🔌 M5StickC Plus client

A tiny hardware companion to **[AI Usage Bar](../README.md)** — shows Claude & ChatGPT usage on an M5StickC Plus.

<p align="center">
  <img src="../docs/m5stick-preview.jpg" width="420" alt="placeholder — add your photo here"/>
</p>

```
┌──────────────────────────────┐
│ AI USAGE          [5 hour] 🟢│
│                              │
│ Claude              65%      │
│ ████████████░░░░░░░░░░       │
│ resets in 1h 28m             │
│                              │
│ GPT                  8%      │
│ ██░░░░░░░░░░░░░░░░░░░        │
│ resets in 4h 6m              │
└──────────────────────────────┘
```

---

## 📦 What you need

- **M5StickC Plus** (135×240 LCD, ESP32-PICO) — the original "Plus", not "Plus 2"
- USB-C cable for flashing
- WiFi network that can reach your Mac
- Mac running [AI Usage Bar](../README.md) with `SERVER_ENABLED = True` in `config.py`

---

## 🚀 Flash it

```bash
# 1. Install PlatformIO (one-time)
brew install platformio   # or `pip install -U platformio`

# 2. Configure your secrets
cd m5stick
cp include/secrets.h.template include/secrets.h
$EDITOR include/secrets.h
#   ↓ fill in WIFI_SSID, WIFI_PASSWORD
#   ↓ set USAGE_HOST to your Mac's LAN IP
#       → on the Mac:  ipconfig getifaddr en0

# 3. Plug in M5StickC Plus and upload
pio run -t upload
pio device monitor   # (optional) watch serial logs
```

The device reboots, connects to WiFi, fetches your Mac at `http://<MAC_IP>:8089/usage`,
and starts rendering. Refresh interval: **30 seconds**.

---

## 🎮 Buttons

| Button | Action |
|---|---|
| **A** (front, "M5") | toggle 5h ↔ 7d view |
| **B** (side) | force refresh immediately |

---

## 🐛 Troubleshooting

**"offline" on screen** — Mac widget HTTP server is not reachable.
- Confirm `SERVER_ENABLED = True` in the Mac's `config.py`
- On the Mac: `curl http://localhost:8089/healthz` should return `ok`
- From another machine: `curl http://<MAC_IP>:8089/healthz`
- macOS Firewall may block —  System Settings → Network → Firewall → allow Python / Terminal

**WiFi failed** — check SSID/password in `secrets.h`, confirm the network is 2.4 GHz (M5Stick doesn't do 5 GHz).

**HTTP 4xx/5xx** — wait until Mac has fetched at least once (`/usage` returns `null` before first fetch).

**Compile error: `M5StickCPlus.h: No such file`** — run `pio lib install` once, or just `pio run` again (PlatformIO downloads on first build).

---

## 🛠️ How it works

```
Mac widget (Python)              M5StickC Plus
┌───────────────────────┐        ┌──────────────────────┐
│ fetches Claude+Codex  │        │ on boot:             │
│ usage every 30s       │        │   connect WiFi       │
│                       │        │ every 30s:           │
│ exposes JSON at       │ ◄───── │   GET /usage         │
│ /usage on port 8089   │ HTTP   │   parse with         │
│                       │ ──────►│   ArduinoJson        │
└───────────────────────┘        │   render on LCD      │
                                 └──────────────────────┘
```

Both clients (menu bar + M5Stick) read the same snapshot — they're always in sync.

---

## 📜 License

MIT, same as the parent project.
