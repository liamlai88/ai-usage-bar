import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# In a frozen .app, Python.framework doesn't find system CA certs automatically.
# Construct the path to certifi's cacert.pem from the bundle structure.
if getattr(sys, "frozen", False):
    import glob as _glob
    _resources = os.path.normpath(
        os.path.join(os.path.dirname(sys.executable), "..", "Resources")
    )
    _matches = _glob.glob(os.path.join(_resources, "lib", "python*", "certifi", "cacert.pem"))
    if _matches and os.path.exists(_matches[0]):
        os.environ["SSL_CERT_FILE"] = _matches[0]
        os.environ["REQUESTS_CA_BUNDLE"] = _matches[0]

import rumps
from datetime import datetime, timezone
from data_sources import fetch_realtime_usage, fetch_codex_usage
from config import (
    REFRESH_INTERVAL,
    ALERT_ENABLED, ALERT_THRESHOLDS, ALERT_SOUND,
    SERVER_ENABLED, SERVER_HOST, SERVER_PORT,
    SERIAL_ENABLED,
)
from i18n import T
from notifier import notify
import server as usage_server
import serial_bridge


EMPTY_BLOCK = "⬜"

def _block_color(pct: float) -> str:
    """根据用量百分比选填充色 —— 绿/黄/橙/红"""
    if pct < 50:   return "🟩"   # 安全
    if pct < 75:   return "🟨"   # 中等
    if pct < 90:   return "🟧"   # 警戒
    return "🟥"                  # 危险


def _status_dot(pct) -> str:
    """菜单栏小圆点（搭在百分比前）"""
    if pct is None:  return "⚪"
    if pct < 50:     return "🟢"
    if pct < 75:     return "🟡"
    if pct < 90:     return "🟠"
    return "🔴"


def progress_bar(pct: float, width: int = 10) -> str:
    """彩色方块拼成的进度条 —— 颜色随用量等级变化。"""
    pct = max(0.0, min(pct / 100.0, 1.0))
    filled = int(round(pct * width))
    color = _block_color(pct * 100)
    return color * filled + EMPTY_BLOCK * (width - filled)


def mood(pct: float) -> str:
    if pct is None:    return "❔"
    if pct < 30:       return "😺"
    if pct < 60:       return "😸"
    if pct < 85:       return "😼"
    if pct < 100:      return "🙀"
    return "💥"


def fmt_countdown(target: datetime) -> str:
    """格式化倒计时 + 本地绝对时间。"""
    now = datetime.now(timezone.utc)
    sec = max(0, int((target - now).total_seconds()))

    local = target.astimezone()
    if sec >= 86400:
        abs_str = f"{T['weekdays'][local.weekday()]} {local.strftime('%H:%M')}"
        d, h = sec // 86400, (sec % 86400) // 3600
        rel = T["reset_day_hour"].format(d, h) if h else T["reset_day"].format(d)
    else:
        abs_str = local.strftime("%H:%M")
        h, m = sec // 3600, (sec % 3600) // 60
        rel = T["reset_hour_min"].format(h, m) if h else T["reset_min"].format(m)

    return f"{rel} · {abs_str}"


def fmt_age(dt: datetime) -> str:
    if not dt:
        return T["no_data"]
    sec = int((datetime.now(timezone.utc) - dt).total_seconds())
    if sec < 5:     return T["now"]
    if sec < 60:    return T["sec_ago"].format(sec)
    if sec < 3600:  return T["min_ago"].format(sec // 60)
    if sec < 86400: return T["hour_ago"].format(sec // 3600)
    return T["day_ago"].format(sec // 86400)


_NOOP = lambda _: None

def _get_resource_path(relative_path: str) -> str:
    if getattr(sys, "frozen", False):
        resources_dir = os.path.join(os.path.dirname(sys.executable), "..", "Resources")
        return os.path.normpath(os.path.join(resources_dir, relative_path))
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

CLAUDE_LOGO = _get_resource_path("assets/claude_logo.png")
OPENAI_LOGO = _get_resource_path("assets/openai_logo.png")


def _mi(title: str, icon: str = None) -> rumps.MenuItem:
    item = rumps.MenuItem(title, callback=_NOOP)
    if icon and os.path.exists(icon):
        item.set_icon(icon, dimensions=(18, 18), template=False)
    return item


class UsageApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="AIUsage",
            title=T["loading"],
            menu=[
                # Claude 区 (header 带 Claude logo)
                _mi("c_header", icon=CLAUDE_LOGO),
                _mi("c_5h"),
                _mi("c_5h_bar"),
                _mi("c_5h_reset"),
                _mi("c_7d"),
                _mi("c_7d_bar"),
                _mi("c_7d_reset"),
                _mi("c_extra"),
                None,
                # Codex 区 (header 带 OpenAI logo)
                _mi("x_header", icon=OPENAI_LOGO),
                _mi("x_5h"),
                _mi("x_5h_bar"),
                _mi("x_5h_reset"),
                _mi("x_7d"),
                _mi("x_7d_bar"),
                _mi("x_7d_reset"),
                _mi("x_credits"),
                None,
                _mi("last_updated"),
                rumps.MenuItem(T["refresh"], callback=self.refresh),
                None,
                rumps.MenuItem(T["quit"], callback=rumps.quit_application),
            ],
            quit_button=None,
        )

        items = list(self.menu.values())
        # Claude (0..7), sep(8), Codex(9..16), sep(17), updated(18), refresh(19), sep(20), quit(21)
        (self._c_header, self._c_5h, self._c_5h_bar, self._c_5h_reset,
         self._c_7d, self._c_7d_bar, self._c_7d_reset, self._c_extra) = items[0:8]
        (self._x_header, self._x_5h, self._x_5h_bar, self._x_5h_reset,
         self._x_7d, self._x_7d_bar, self._x_7d_reset, self._x_credits) = items[9:17]
        self._last_updated = items[18]

        # 阈值告警状态：{(provider, window): 上次已触发的阈值百分比}
        self._alert_state = {}
        self._alert_initialized = False  # 首次刷新不发通知，只初始化基线

        self._do_refresh()

    @rumps.timer(REFRESH_INTERVAL)
    def auto_refresh(self, _):
        self._do_refresh()

    def refresh(self, _):
        self._do_refresh()

    def _do_refresh(self):
        claude = None
        codex = None
        try:
            claude = fetch_realtime_usage()
            if not claude.available:
                print(f"[refresh] Claude unavailable: {claude.error}", flush=True)
        except Exception as e:
            print(f"[refresh] Claude exception: {e}", flush=True)
            claude = type("X", (), {"available": False, "error": str(e)[:80]})()
        try:
            codex = fetch_codex_usage()
            if not codex.available:
                print(f"[refresh] Codex unavailable: {codex.error}", flush=True)
        except Exception as e:
            print(f"[refresh] Codex exception: {e}", flush=True)
            codex = type("X", (), {"available": False, "error": str(e)[:80]})()
        self._update_ui(claude, codex)
        if ALERT_ENABLED:
            self._check_alerts(claude, codex)
        if SERVER_ENABLED:
            usage_server.update_snapshot(claude, codex)

    def _check_alerts(self, claude, codex):
        sources = [
            ("c", "Claude", claude),
            ("x", "ChatGPT", codex),
        ]
        any_data = False
        for prefix, name, data in sources:
            if not (data and getattr(data, "available", False)):
                continue
            any_data = True
            for window_label, pct, reset_at in [
                (T["5h"], data.five_hour_pct, data.five_hour_resets_at),
                (T["7d"], data.seven_day_pct, data.seven_day_resets_at),
            ]:
                if pct is None:
                    continue
                self._maybe_fire_alert(prefix, name, window_label, pct, reset_at)

        # 第一次有数据后，告警机制正式启动
        if any_data and not self._alert_initialized:
            self._alert_initialized = True

    def _maybe_fire_alert(self, prefix, name, window_label, pct, reset_at):
        key = (prefix, window_label)
        last_bucket = self._alert_state.get(key, 0)

        # 找出当前 pct 跨过的最高阈值
        current_bucket = 0
        for t in sorted(ALERT_THRESHOLDS):
            if pct >= t:
                current_bucket = t

        # 首次刷新只记录基线，不发通知
        if not self._alert_initialized:
            self._alert_state[key] = current_bucket
            return

        if current_bucket > last_bucket:
            subtitle = T["alert_subtitle"].format(name, window_label, pct)
            body = fmt_countdown(reset_at) if reset_at else ""
            notify(T["alert_title"], body, subtitle=subtitle, sound=ALERT_SOUND)
            self._alert_state[key] = current_bucket
        elif current_bucket < last_bucket:
            self._alert_state[key] = current_bucket

    # ---------- 渲染 ----------
    @staticmethod
    def _fix_hint(prefix: str) -> str:
        """根据 provider 给出可操作的修复提示。"""
        if prefix == "c":
            return T["fix_claude"]
        if prefix == "x":
            return T["fix_codex"]
        return T["fix_generic"]

    def _render_section(self, prefix, header_item, bar5_item, reset5_item, bar7_item, reset7_item,
                        h5_item, d7_item, data, badge: str, label: str):
        ok = data and getattr(data, "available", False)
        prefix_str = (badge + "  ") if badge else ""
        if ok:
            header_item.title = f"{prefix_str}{label} ({T['live']})"
        else:
            msg = getattr(data, "error", T["no_data"]) if data else T["no_data"]
            header_item.title = f"{prefix_str}{label}  ⚠️  {msg}"

        p5 = getattr(data, "five_hour_pct", None) if ok else None
        if p5 is not None:
            h5_item.title    = f"  ⏱ {T['5h']}: {p5:.0f}%"
            bar5_item.title  = f"     {progress_bar(p5)}  " + T["left"].format(max(0, 100 - p5))
            r5 = getattr(data, "five_hour_resets_at", None)
            reset5_item.title = f"     🕒 {fmt_countdown(r5)}" if r5 else f"     🕒 {T['no_data']}"
        elif not ok:
            hint = self._fix_hint(prefix)
            h5_item.title = "  " + T["fix_hint"].format(hint)
            bar5_item.title = "     "
            reset5_item.title = "     "
        else:
            h5_item.title = f"  ⏱ {T['5h']}: {T['no_data']}"
            bar5_item.title = "     "
            reset5_item.title = "     "

        p7 = getattr(data, "seven_day_pct", None) if ok else None
        if p7 is not None:
            d7_item.title   = f"  📅 {T['7d']}: {p7:.0f}%"
            bar7_item.title = f"     {progress_bar(p7)}  " + T["left"].format(max(0, 100 - p7))
            r7 = getattr(data, "seven_day_resets_at", None)
            reset7_item.title = f"     🕒 {fmt_countdown(r7)}" if r7 else f"     🕒 {T['no_data']}"
        elif not ok:
            d7_item.title = ""
            bar7_item.title = ""
            reset7_item.title = ""
        else:
            d7_item.title = f"  📅 {T['7d']}: {T['no_data']}"
            bar7_item.title = "     "
            reset7_item.title = "     "

    def _update_ui(self, claude, codex):
        # —— 菜单栏标题：两家的 5h 都显示 ——
        c_ok = bool(claude and claude.available)
        x_ok = bool(codex and codex.available)
        c5 = claude.five_hour_pct if c_ok else None
        x5 = codex.five_hour_pct if x_ok else None

        # 菜单栏图标随状态变：两边都正常 = 🤖，任一异常 = ⚠️，全挂 = ❌
        if c_ok and x_ok:
            self.title = "🤖"
        elif c_ok or x_ok:
            self.title = "⚠️"
        else:
            self.title = "❌"

        # —— Claude 区 ——
        self._render_section(
            "c", self._c_header,
            self._c_5h_bar, self._c_5h_reset, self._c_7d_bar, self._c_7d_reset,
            self._c_5h, self._c_7d,
            claude, "", T["claude_plan"],
        )
        if claude and claude.available and getattr(claude, "extra_credits_limit", None):
            used = claude.extra_credits_used or 0
            limit = claude.extra_credits_limit
            cur = claude.extra_currency or "USD"
            self._c_extra.title = "  " + T["extra"].format(used, limit, cur)
        else:
            self._c_extra.title = "  " + T["extra_empty"]

        # —— Codex 区 ——
        codex_label = "Codex"
        if codex and codex.available and codex.plan_type:
            codex_label = T["codex_plan"].format(codex.plan_type.title())
        self._render_section(
            "x", self._x_header,
            self._x_5h_bar, self._x_5h_reset, self._x_7d_bar, self._x_7d_reset,
            self._x_5h, self._x_7d,
            codex, "", codex_label,
        )
        if codex and codex.available:
            bal = codex.credits_balance or "0"
            self._x_credits.title = "  " + T["credits"].format(bal)
        else:
            self._x_credits.title = "  " + T["credits_empty"]

        # —— 更新时间 ——
        c_age = fmt_age(claude.fetched_at) if (claude and getattr(claude, "fetched_at", None)) else T["no_data"]
        x_age = fmt_age(codex.fetched_at) if (codex and getattr(codex, "fetched_at", None)) else T["no_data"]
        self._last_updated.title = T["updated"].format(c_age, x_age)


if __name__ == "__main__":
    # 隐藏 Dock 图标 —— 让它成为纯菜单栏 agent
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    except Exception:
        pass

    # 启动局域网 HTTP server（给 M5Stick 等外设用 / WiFi 方式）
    if SERVER_ENABLED:
        try:
            usage_server.start(SERVER_HOST, SERVER_PORT)
        except Exception as e:
            print(f"[server] failed to start: {e}", flush=True)

    # 启动 USB 串口推送（M5Stick over USB 方式，免 WiFi）
    if SERIAL_ENABLED:
        try:
            serial_bridge.start()
        except Exception as e:
            print(f"[serial] failed to start: {e}", flush=True)

    UsageApp().run()
