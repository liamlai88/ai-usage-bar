"""i18n strings for the widget UI."""
import locale
from config import LANG

STRINGS = {
    "zh": {
        "loading":         "🤖 加载中…",
        "fetch_failed":    "取数失败",
        "live":            "实时",
        "5h":              "5 小时",
        "7d":              "7 天",
        "left":            "剩 {:.0f}%",
        "extra":           "💎 Extra：${:.2f} / ${:.0f} {}",
        "extra_empty":     "💎 Extra：—",
        "credits":         "💎 Credits 余额：{}",
        "credits_empty":   "💎 Credits：—",
        "refresh":         "🔄 立即刷新",
        "quit":            "👋 退出",
        "updated":         "🕘 Claude: {} · Codex: {}",
        "fix_hint":        "💡 修复：{}",
        "fix_claude":      "打开 Claude 桌面 App 登录",
        "fix_codex":       "终端运行 codex login",
        "fix_generic":     "请检查登录状态",
        "claude_plan":     "Claude Pro",
        "codex_plan":      "Codex {}",
        "now":             "刚刚",
        "sec_ago":         "{}秒前",
        "min_ago":         "{}分钟前",
        "hour_ago":        "{}小时前",
        "day_ago":         "{}天前",
        "reset_min":       "{}分钟后重置",
        "reset_hour_min":  "{}小时{}分后重置",
        "reset_day":       "{}天后重置",
        "reset_day_hour":  "{}天{}小时后重置",
        "weekdays":        ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        "no_data":         "—",
        "alert_title":     "AI Usage Bar",
        "alert_subtitle":  "{} {} 已达 {:.0f}%",
    },
    "en": {
        "loading":         "🤖 loading…",
        "fetch_failed":    "fetch failed",
        "live":            "live",
        "5h":              "5h window",
        "7d":              "7d window",
        "left":            "{:.0f}% left",
        "extra":           "💎 Extra: ${:.2f} / ${:.0f} {}",
        "extra_empty":     "💎 Extra: —",
        "credits":         "💎 Credits: {}",
        "credits_empty":   "💎 Credits: —",
        "refresh":         "🔄 Refresh now",
        "quit":            "👋 Quit",
        "updated":         "🕘 Claude: {} · Codex: {}",
        "fix_hint":        "💡 Fix: {}",
        "fix_claude":      "Sign in to Claude Desktop",
        "fix_codex":       "Run `codex login` in terminal",
        "fix_generic":     "Check sign-in status",
        "claude_plan":     "Claude Pro",
        "codex_plan":      "Codex {}",
        "now":             "now",
        "sec_ago":         "{}s ago",
        "min_ago":         "{}m ago",
        "hour_ago":        "{}h ago",
        "day_ago":         "{}d ago",
        "reset_min":       "resets in {}m",
        "reset_hour_min":  "resets in {}h {}m",
        "reset_day":       "resets in {}d",
        "reset_day_hour":  "resets in {}d {}h",
        "weekdays":        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "no_data":         "—",
        "alert_title":     "AI Usage Bar",
        "alert_subtitle":  "{} {} at {:.0f}%",
    },
}


def _detect():
    code, _ = locale.getlocale()
    if code and code.lower().startswith("zh"):
        return "zh"
    return "en"


_lang = LANG if LANG in STRINGS else _detect()
T = STRINGS[_lang]
