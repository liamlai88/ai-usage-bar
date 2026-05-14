"""Tiny HTTP server that exposes the latest fetched usage as JSON.

Runs in a daemon thread inside the widget. Consumed by external hardware
widgets (M5Stick, etc.) that poll over LAN.

Endpoints:
    GET /usage   → JSON with both providers
    GET /healthz → "ok"

Note: this is intended for trusted LAN use only — no authentication.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone
from typing import Optional


# 这个全局变量由 widget 在每次刷新时更新
_latest_payload: dict = {
    "ts": None,
    "claude": None,
    "codex": None,
}


def update_snapshot(claude, codex):
    """Called by the widget on each successful refresh."""
    _latest_payload["ts"] = datetime.now(timezone.utc).isoformat()
    _latest_payload["claude"] = _serialize(claude)
    _latest_payload["codex"] = _serialize(codex)


def _serialize(d) -> Optional[dict]:
    if not d:
        return None
    available = getattr(d, "available", False)
    out = {"available": available}
    if not available:
        out["error"] = getattr(d, "error", None)
        return out

    out["five_hour_pct"] = getattr(d, "five_hour_pct", None)
    out["seven_day_pct"] = getattr(d, "seven_day_pct", None)
    r5 = getattr(d, "five_hour_resets_at", None)
    r7 = getattr(d, "seven_day_resets_at", None)
    out["five_hour_resets_at"]  = r5.isoformat() if r5 else None
    out["seven_day_resets_at"]  = r7.isoformat() if r7 else None
    # Claude 独有
    if hasattr(d, "extra_credits_used"):
        out["extra_credits_used"]  = d.extra_credits_used
        out["extra_credits_limit"] = d.extra_credits_limit
    # Codex 独有
    if hasattr(d, "plan_type"):
        out["plan_type"]       = d.plan_type
        out["credits_balance"] = d.credits_balance
    return out


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass  # 抑制 stdout 日志

    def do_GET(self):
        if self.path == "/usage":
            body = json.dumps(_latest_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/healthz":
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def start(host: str, port: int):
    """Start the server in a daemon thread. Idempotent."""
    if getattr(start, "_started", False):
        return
    server = HTTPServer((host, port), _Handler)

    def _run():
        try:
            server.serve_forever()
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True, name="UsageHttpServer")
    t.start()
    start._started = True
    print(f"[server] listening on http://{host}:{port}/usage", flush=True)
