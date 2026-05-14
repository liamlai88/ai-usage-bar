"""通过解密 Claude Desktop 的 session cookie，直接调 claude.ai /api/organizations/{org}/usage
获取官方实时 rate_limits 数据。"""
import json
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

COOKIES_DB = Path.home() / "Library/Application Support/Claude/Cookies"
ORG_CACHE = Path.home() / ".claude" / "org_id.cache"


# ---------- Cookie decryption ----------

def _get_keychain_password() -> bytes:
    out = subprocess.run(
        ["security", "find-generic-password",
         "-s", "Claude Safe Storage", "-a", "Claude Key", "-w"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip().encode()


def _derive_key(password: bytes) -> bytes:
    return PBKDF2(password, b"saltysalt", dkLen=16, count=1003)


def _decrypt_v10(enc: bytes, key: bytes) -> str:
    if enc[:3] != b"v10":
        raise ValueError(f"unsupported prefix {enc[:3]!r}")
    cipher = AES.new(key, AES.MODE_CBC, iv=b" " * 16)
    pt = cipher.decrypt(enc[3:])
    pad = pt[-1]
    if pad and pad <= 16:
        pt = pt[:-pad]
    # 新 Chromium 在密文前加 32 字节 SHA256(host_key) 校验位
    if len(pt) > 32:
        try:
            return pt[32:].decode("utf-8")
        except UnicodeDecodeError:
            pass
    return pt.decode("utf-8")


def load_claude_cookies() -> dict:
    pwd = _get_keychain_password()
    key = _derive_key(pwd)
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy(COOKIES_DB, tmp)
    con = sqlite3.connect(tmp)
    rows = con.execute(
        "SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%claude.ai%'"
    ).fetchall()
    out = {}
    for name, enc in rows:
        try:
            out[name] = _decrypt_v10(enc, key)
        except Exception:
            pass
    return out


# ---------- API client ----------

def _http_get(url: str, cookies: dict) -> dict:
    headers = {
        "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Anthropic-Client-Platform": "web_claude_ai",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_org_id(cookies: dict) -> str:
    if ORG_CACHE.exists():
        try:
            return ORG_CACHE.read_text().strip()
        except OSError:
            pass

    # 优先用 lastActiveOrg cookie（精确匹配你最后用的 org）
    last = cookies.get("lastActiveOrg")
    if last:
        ORG_CACHE.write_text(last)
        return last

    data = _http_get("https://claude.ai/api/organizations", cookies)
    if isinstance(data, list) and data:
        org_id = data[0].get("uuid")
        if org_id:
            ORG_CACHE.write_text(org_id)
            return org_id

    raise RuntimeError("could not discover organization id")


# ---------- Data model ----------

@dataclass
class RealtimeUsage:
    five_hour_pct: Optional[float] = None
    seven_day_pct: Optional[float] = None
    five_hour_resets_at: Optional[datetime] = None
    seven_day_resets_at: Optional[datetime] = None
    extra_credits_used: Optional[float] = None
    extra_credits_limit: Optional[float] = None
    extra_currency: Optional[str] = None
    fetched_at: Optional[datetime] = None
    available: bool = False
    error: Optional[str] = None


def _parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def fetch_realtime_usage() -> RealtimeUsage:
    try:
        cookies = load_claude_cookies()
        if "sessionKey" not in cookies:
            return RealtimeUsage(error="no sessionKey cookie")

        org_id = get_org_id(cookies)
        data = _http_get(
            f"https://claude.ai/api/organizations/{org_id}/usage",
            cookies,
        )
    except urllib.error.HTTPError as e:
        return RealtimeUsage(error=f"HTTP {e.code}")
    except Exception as e:
        return RealtimeUsage(error=str(e)[:100])

    fh = data.get("five_hour") or {}
    sd = data.get("seven_day") or {}
    extra = data.get("extra_usage") or {}

    return RealtimeUsage(
        five_hour_pct=fh.get("utilization"),
        seven_day_pct=sd.get("utilization"),
        five_hour_resets_at=_parse_iso(fh.get("resets_at")),
        seven_day_resets_at=_parse_iso(sd.get("resets_at")),
        extra_credits_used=extra.get("used_credits"),
        extra_credits_limit=extra.get("monthly_limit"),
        extra_currency=extra.get("currency"),
        fetched_at=datetime.now(timezone.utc),
        available=True,
    )


if __name__ == "__main__":
    u = fetch_realtime_usage()
    print(json.dumps({
        "available": u.available,
        "error": u.error,
        "5h_pct": u.five_hour_pct,
        "5h_resets": u.five_hour_resets_at.isoformat() if u.five_hour_resets_at else None,
        "7d_pct": u.seven_day_pct,
        "7d_resets": u.seven_day_resets_at.isoformat() if u.seven_day_resets_at else None,
        "extra": f"{u.extra_credits_used}/{u.extra_credits_limit} {u.extra_currency}",
    }, indent=2))
