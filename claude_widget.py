import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rumps
from datetime import datetime, timezone
from data_sources import fetch_realtime_usage, fetch_codex_usage
from config import REFRESH_INTERVAL


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
    now = datetime.now(timezone.utc)
    sec = max(0, int((target - now).total_seconds()))
    if sec >= 86400:
        d, h = sec // 86400, (sec % 86400) // 3600
        return f"{d}天{h}小时后重置" if h else f"{d}天后重置"
    h, m = sec // 3600, (sec % 3600) // 60
    if h:
        return f"{h}小时{m}分后重置"
    return f"{m}分钟后重置"


def fmt_age(dt: datetime) -> str:
    if not dt:
        return "—"
    sec = int((datetime.now(timezone.utc) - dt).total_seconds())
    if sec < 60:    return f"{sec}秒前"
    if sec < 3600:  return f"{sec // 60}分钟前"
    if sec < 86400: return f"{sec // 3600}小时前"
    return f"{sec // 86400}天前"


_NOOP = lambda _: None

_BASE = os.path.dirname(os.path.abspath(__file__))
CLAUDE_LOGO = os.path.join(_BASE, "assets", "claude_logo.png")
OPENAI_LOGO = os.path.join(_BASE, "assets", "openai_logo.png")


def _mi(title: str, icon: str = None) -> rumps.MenuItem:
    item = rumps.MenuItem(title, callback=_NOOP)
    if icon and os.path.exists(icon):
        item.set_icon(icon, dimensions=(18, 18), template=False)
    return item


class UsageApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="AIUsage",
            title="🐱 加载中…",
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
                rumps.MenuItem("🔄 立即刷新", callback=self.refresh),
                None,
                rumps.MenuItem("👋 退出", callback=rumps.quit_application),
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
        except Exception as e:
            claude = type("X", (), {"available": False, "error": str(e)[:80]})()
        try:
            codex = fetch_codex_usage()
        except Exception as e:
            codex = type("X", (), {"available": False, "error": str(e)[:80]})()
        self._update_ui(claude, codex)

    # ---------- 渲染 ----------
    def _render_section(self, prefix, header_item, bar5_item, reset5_item, bar7_item, reset7_item,
                        h5_item, d7_item, data, badge: str, label: str):
        ok = data and getattr(data, "available", False)
        prefix = (badge + "  ") if badge else ""
        if ok:
            header_item.title = f"{prefix}{label}（实时）"
        else:
            msg = getattr(data, "error", "—") if data else "—"
            header_item.title = f"{prefix}{label}：{msg}"

        p5 = getattr(data, "five_hour_pct", None) if ok else None
        if p5 is not None:
            h5_item.title    = f"  ⏱ 5 小时：{p5:.0f}%"
            bar5_item.title  = f"     {progress_bar(p5)}  剩 {max(0,100-p5):.0f}%"
            r5 = getattr(data, "five_hour_resets_at", None)
            reset5_item.title = f"     🕒 {fmt_countdown(r5)}" if r5 else "     🕒 —"
        else:
            h5_item.title = "  ⏱ 5 小时：—"
            bar5_item.title = f"     {progress_bar(0)}"
            reset5_item.title = "     🕒 —"

        p7 = getattr(data, "seven_day_pct", None) if ok else None
        if p7 is not None:
            d7_item.title   = f"  📅 7 天：{p7:.0f}%"
            bar7_item.title = f"     {progress_bar(p7)}  剩 {max(0,100-p7):.0f}%"
            r7 = getattr(data, "seven_day_resets_at", None)
            reset7_item.title = f"     🕒 {fmt_countdown(r7)}" if r7 else "     🕒 —"
        else:
            d7_item.title = "  📅 7 天：—"
            bar7_item.title = f"     {progress_bar(0)}"
            reset7_item.title = "     🕒 —"

    def _update_ui(self, claude, codex):
        # —— 菜单栏标题：两家的 5h 都显示 ——
        c5 = claude.five_hour_pct if (claude and claude.available) else None
        x5 = codex.five_hour_pct if (codex and codex.available) else None

        # 菜单栏：🟡 Claude 品牌色  ·  ⚫ ChatGPT 品牌色
        parts = []
        if c5 is not None:
            parts.append(f"🟡 {c5:.0f}%")
        if x5 is not None:
            parts.append(f"⚫ {x5:.0f}%")
        self.title = "  ".join(parts) if parts else "取数失败"

        # —— Claude 区 ——
        self._render_section(
            "c", self._c_header,
            self._c_5h_bar, self._c_5h_reset, self._c_7d_bar, self._c_7d_reset,
            self._c_5h, self._c_7d,
            claude, "", "Claude Pro",
        )
        # Claude 额外信息：Extra Usage
        if claude and claude.available and getattr(claude, "extra_credits_limit", None):
            used = claude.extra_credits_used or 0
            limit = claude.extra_credits_limit
            cur = claude.extra_currency or "USD"
            self._c_extra.title = f"  💎 Extra：${used:.2f} / ${limit:.0f} {cur}"
        else:
            self._c_extra.title = "  💎 Extra：—"

        # —— Codex 区 ——
        codex_label = "Codex"
        if codex and codex.available and codex.plan_type:
            codex_label = f"Codex {codex.plan_type.title()}"
        self._render_section(
            "x", self._x_header,
            self._x_5h_bar, self._x_5h_reset, self._x_7d_bar, self._x_7d_reset,
            self._x_5h, self._x_7d,
            codex, "", codex_label,
        )
        # Codex credits
        if codex and codex.available:
            bal = codex.credits_balance or "0"
            self._x_credits.title = f"  💎 Credits 余额：{bal}"
        else:
            self._x_credits.title = "  💎 Credits：—"

        # —— 更新时间 ——
        c_age = fmt_age(claude.fetched_at) if (claude and getattr(claude, "fetched_at", None)) else "—"
        x_age = fmt_age(codex.fetched_at) if (codex and getattr(codex, "fetched_at", None)) else "—"
        self._last_updated.title = f"🕘 Claude: {c_age}  ·  Codex: {x_age}"


if __name__ == "__main__":
    UsageApp().run()
