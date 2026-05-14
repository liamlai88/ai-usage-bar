"""调 ChatGPT 内部 API 获取 Codex CLI 的实时 rate_limits。
依赖：~/.codex/auth.json (Codex CLI 登录后生成)"""
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUTH_FILE = Path.home() / ".codex" / "auth.json"
USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"


@dataclass
class CodexUsage:
    five_hour_pct: Optional[float] = None
    seven_day_pct: Optional[float] = None
    five_hour_resets_at: Optional[datetime] = None
    seven_day_resets_at: Optional[datetime] = None
    plan_type: Optional[str] = None
    limit_reached: bool = False
    credits_balance: Optional[str] = None
    fetched_at: Optional[datetime] = None
    available: bool = False
    error: Optional[str] = None


def _load_access_token() -> Optional[str]:
    if not AUTH_FILE.exists():
        return None
    try:
        data = json.loads(AUTH_FILE.read_text())
        return (data.get("tokens") or {}).get("access_token")
    except (json.JSONDecodeError, OSError):
        return None


def fetch_codex_usage() -> CodexUsage:
    token = _load_access_token()
    if not token:
        return CodexUsage(error="Codex 未登录（~/.codex/auth.json 缺失）")

    req = urllib.request.Request(USAGE_URL, headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "codex_cli/0",
        "Accept": "application/json",
        "Originator": "codex_cli",
    })

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return CodexUsage(error="Codex token 过期，请 codex login")
        return CodexUsage(error=f"HTTP {e.code}")
    except Exception as e:
        return CodexUsage(error=str(e)[:100])

    rl = data.get("rate_limit") or {}
    pw = rl.get("primary_window") or {}
    sw = rl.get("secondary_window") or {}
    credits = data.get("credits") or {}

    return CodexUsage(
        five_hour_pct=pw.get("used_percent"),
        seven_day_pct=sw.get("used_percent"),
        five_hour_resets_at=(datetime.fromtimestamp(pw["reset_at"], tz=timezone.utc)
                              if pw.get("reset_at") else None),
        seven_day_resets_at=(datetime.fromtimestamp(sw["reset_at"], tz=timezone.utc)
                              if sw.get("reset_at") else None),
        plan_type=data.get("plan_type"),
        limit_reached=rl.get("limit_reached", False),
        credits_balance=credits.get("balance"),
        fetched_at=datetime.now(timezone.utc),
        available=True,
    )


if __name__ == "__main__":
    u = fetch_codex_usage()
    print(json.dumps({
        "available": u.available,
        "error": u.error,
        "plan": u.plan_type,
        "5h_pct": u.five_hour_pct,
        "5h_resets": u.five_hour_resets_at.isoformat() if u.five_hour_resets_at else None,
        "7d_pct": u.seven_day_pct,
        "7d_resets": u.seven_day_resets_at.isoformat() if u.seven_day_resets_at else None,
        "credits_balance": u.credits_balance,
    }, indent=2))
