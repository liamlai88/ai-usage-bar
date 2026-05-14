# 🟡⚫ AI Usage Bar

> 一个极小的 macOS 菜单栏小工具，**实时显示 Claude Pro / ChatGPT Plus 的订阅限额用量**，数据直接来自官方接口 —— 不需要 API key。

[English](README.md) · 简体中文

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![macOS](https://img.shields.io/badge/macOS-12%2B-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)

<p align="center">
  <img src="docs/screenshot.png" width="520" alt="screenshot"/>
</p>

Claude / ChatGPT 桌面 App 把 5 小时窗口和周用量藏得很深，每次都要点进设置才能看。这个小工具拿的是**完全一样的数据**，但常驻菜单栏，随时可看。

```
菜单栏：    🤖                ← 单个图标，正常运行
            ⚠️                ← 一边异常
            ❌                ← 两边都挂

点开后：    [Claude logo] Claude Pro（实时）
              ⏱ 5 小时：65%   🟨🟨🟨🟨🟨🟨🟨⬜⬜⬜
                 🕒 1 小时 28 分后重置 · 18:43
              📅 7 天：8%    🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜
                 🕒 6 天 4 小时后重置 · 周三 22:15
            ──────────────────────────────────
            [OpenAI logo] Codex Plus（实时）
              ⏱ 5 小时：8%   🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜
              📅 7 天：63%  🟨🟨🟨🟨🟨🟨⬜⬜⬜⬜
```

---

## ✨ 特性

- **实时** —— 每 30 秒拉一次官方接口
- **零配置** —— 自动从桌面 App / CLI 提取登录态
- **不需要 API key** —— 用已登录的浏览器/桌面应用凭证
- **纯本地** —— 数据不出本机，只跟官方域名通信
- **轻量** —— 约 120 MB 内存，1% CPU
- **开机自启** —— 一行命令配 LaunchAgent
- **彩色进度条** —— 绿 → 黄 → 橙 → 红，按用量分级
- **阈值通知** —— 用量跨过 80% / 95% 时弹 macOS 原生通知
- **错误可见** —— 异常时菜单栏图标变化 + 给出修复提示

---

## 📦 前置条件

下面两个**至少装一个**：

| 平台 | 要求 |
|---|---|
| **Claude** | [Claude 桌面 App](https://claude.ai/download) 已登录（Pro / Max / Team 任一方案都行） |
| **ChatGPT / Codex** | [Codex CLI](https://github.com/openai/codex) 已登录 ChatGPT Plus/Pro 账号（命令行跑一次 `codex login`） |

只装一个的话，widget 会只显示这一个，另一个标为不可用。

系统：**macOS 12+**，**Python 3.10+**（系统自带 `python3` 即可）。

---

## 🚀 安装

```bash
git clone https://github.com/liamlai88/ai-usage-bar.git
cd ai-usage-bar
./install.sh
```

脚本会：
1. 在 `.venv/` 建虚拟环境
2. 装 `rumps` 和 `pycryptodome`
3. 配 LaunchAgent → 每次登录自动启动

完事看菜单栏右侧。

---

## 🔧 手动跑（调试用）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python claude_widget.py
```

---

## ⚙️ 配置

编辑 `config.py`：

```python
REFRESH_INTERVAL    = 30           # 刷新间隔（秒）
LANG                = "auto"       # "zh" | "en" | "auto"
ALERT_ENABLED       = True
ALERT_THRESHOLDS    = [80, 95]     # 跨过这些百分比时弹通知
ALERT_SOUND         = False
```

---

## 🔐 工作原理（以及为什么安全）

### Claude
1. 从 `~/Library/Application Support/Claude/Cookies` 读加密的 session cookie（SQLite 数据库）
2. 用 macOS Keychain 里的 `Claude Safe Storage` 密钥解密
3. 调用 `GET https://claude.ai/api/organizations/{org_id}/usage` —— 跟桌面 App 内部用的是同一个接口

### Codex / ChatGPT
1. 读 `~/.codex/auth.json`（`codex login` 后生成）
2. 用其中的 OAuth access token 调 `GET https://chatgpt.com/backend-api/wham/usage` —— 跟 Codex CLI 内部用的是同一个接口

**所有数据都只在你电脑上**。网络流量只去 Anthropic / OpenAI 官方域名，用的是你机器上已经存在的登录凭证。代码**只读**，不会修改任何 cookie 或 token。

---

## 🎛 常用命令

```bash
# 停止 / 启动
launchctl unload ~/Library/LaunchAgents/com.aiusagebar.plist
launchctl load -w  ~/Library/LaunchAgents/com.aiusagebar.plist

# 查日志
tail -f /tmp/aiusagebar.err.log

# 卸载干净
launchctl unload ~/Library/LaunchAgents/com.aiusagebar.plist
rm ~/Library/LaunchAgents/com.aiusagebar.plist
rm -rf .venv
```

---

## 🐛 排错

**菜单栏显示 ❌ / "取数失败"**
- 确认 Claude 桌面 App 和/或 Codex CLI 都装好且至少登录过一次
- 第一次跑会弹 Keychain 授权框，问"是否允许访问 Claude Safe Storage"，点 **始终允许**
- 点开菜单看具体哪边异常，会有修复提示
- 日志：`tail -f /tmp/aiusagebar.err.log`

**"Codex token 过期，请 codex login"**
- 终端跑 `codex login` 重新授权

**数字跟官方面板对不上**
- widget 每 30 秒刷新一次。点 **🔄 立即刷新** 强制取一次
- Anthropic / OpenAI 自己的 UI 也有几秒延迟

---

## 🤝 欢迎贡献

特别欢迎以下方向的 PR：
- 支持 **Gemini** / Cursor / 其他 AI 工具
- 用 SwiftUI 重写以降低内存
- 真正的卡通宠物 widget（设计稿见 [`UI_DESIGN.md`](UI_DESIGN.md)）
- 英语之外的更多本地化

---

## ⚠️ 免责声明

本项目**与 Anthropic / OpenAI 无任何关联**。使用的是未公开的内部接口，可能随时被官方变更。如果某天 widget 挂了，欢迎来开 issue。

---

## 📜 License

MIT © Liam Lai
