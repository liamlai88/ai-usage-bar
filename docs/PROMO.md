# 推广文案 · X / Twitter

> 多版本备选，按需选用。**第一条推文务必带截图** —— 图片决定 80% 的点击。

---

## 🇺🇸 英文 · 单推爆款版

> 适合直接发，钓鱼图 + 一句话价值主张。

```
I built a tiny macOS menu-bar widget that shows my Claude Pro AND ChatGPT Plus rate-limits in real time — no API key, no setup.

The exact numbers the official apps show, but always visible. 🤖

Open-source: github.com/liamlai88/ai-usage-bar
```
**附图**：`docs/screenshot.png`

**字符数**：~250 / 280

---

## 🇺🇸 英文 · Thread 版（推荐，互动数据更好）

**Tweet 1（带截图）：**
```
Ever hit your Claude or ChatGPT rate limit mid-flow and wonder how close you were? 😩

I built a tiny macOS menu-bar widget that shows both subscriptions' real-time usage — pulled from the same APIs the official apps use.

No API key needed. Open source.

🧵👇
```

**Tweet 2：**
```
Why it exists:

Both Claude and ChatGPT hide your 5-hour & 7-day usage 3 clicks deep in settings.

I wanted a number I could glance at — like the battery indicator, but for AI quotas.

So I wrote one. 🤖
```

**Tweet 3：**
```
How it works (technical, but read-only):

• Claude: decrypts session cookie from Chromium's Cookies SQLite via macOS Keychain → calls /api/organizations/{org}/usage
• ChatGPT/Codex: reads OAuth token from ~/.codex/auth.json → calls /backend-api/wham/usage

Nothing leaves your Mac.
```

**Tweet 4：**
```
Stack:

🐍 Python + rumps (~120MB RAM, 1% CPU)
🎨 Color-coded progress bars
🕒 Reset countdowns w/ local timezone
⚙️ LaunchAgent for auto-start
📦 One-shot installer

PRs welcome for Gemini / Cursor / SwiftUI rewrite.
```

**Tweet 5（CTA）：**
```
Free, MIT-licensed, takes 30 seconds to install:

github.com/liamlai88/ai-usage-bar

If you find it useful, a ⭐ goes a long way. RTs appreciated. 🙏

#buildinpublic #macOS #ClaudeAI #ChatGPT
```

---

## 🇨🇳 中文 · 单推

```
做了个 macOS 菜单栏小工具，实时显示 Claude Pro 和 ChatGPT Plus 的订阅额度用量。

直接拿官方接口的数据，不需要 API key。

5 小时窗口、7 天窗口、重置倒计时一目了然，开机自启。

开源：github.com/liamlai88/ai-usage-bar

#独立开发 #macOS
```
**附图**：`docs/screenshot.png`

---

## 🇨🇳 中文 · Thread

**T1（带截图）：**
```
每次 Claude / ChatGPT 用着用着突然到限额，是不是很想知道"我到底还剩多少"？

做了个 macOS 菜单栏小工具，把两家订阅的实时用量挂在菜单栏，随时一瞥就懂。

数据直接来自官方 API，不需要 key。开源免费。

🧵👇
```

**T2：**
```
为什么做：

Claude 和 ChatGPT 都把 5 小时 / 周配额藏在设置三层之下。

我想要一个像电池电量一样的"AI 配额指示器"。

找不到现成的，就自己写了一个。🤖
```

**T3：**
```
怎么拿数据（纯本地、只读）：

• Claude：用 macOS Keychain 解密 Cookies SQLite 里的 session cookie → 调 /api/organizations/{org}/usage
• ChatGPT/Codex：读 ~/.codex/auth.json 的 OAuth token → 调 /backend-api/wham/usage

跟桌面 App 拿的是同一份数据，但一直在菜单栏挂着。
```

**T4：**
```
技术栈：

🐍 Python + rumps（约 120MB 内存，1% CPU）
🎨 彩色进度条按用量分级
🕒 重置倒计时显示本地时区时间
⚙️ LaunchAgent 开机自启
📦 一行命令安装

接 Gemini / Cursor / SwiftUI 重写都欢迎 PR。
```

**T5（CTA）：**
```
完全免费 + MIT 协议，30 秒装好：

github.com/liamlai88/ai-usage-bar

觉得有用点个 ⭐，转发感谢 🙏

#独立开发 #macOS #ClaudeAI #ChatGPT
```

---

## 📌 发布技巧 Checklist

- [ ] 第一条 **务必带截图**，X 算法会优先推送有图推文
- [ ] 发布时间：北美工作日 9-11am PT 或晚 6-8pm PT
- [ ] 同时发 **Reddit r/MacApps / r/ClaudeAI** 互导流
- [ ] @ 一两个相关大 V（如 @AnthropicAI / @OpenAI / @simonw），但不要强行 at
- [ ] 第一小时盯着回复，每条都回 —— 互动权重决定推送量
- [ ] 24 小时后看下数据，反馈不错可以做 Show HN

---

## 🎁 加分项（可选）

录一段 ~10 秒 GIF，展示数字变化 + 颜色切换，会比静态图更吸睛：

```bash
# 用 ffmpeg 录屏（需要先安装：brew install ffmpeg）
ffmpeg -f avfoundation -i "1" -t 10 -vf "fps=15,scale=720:-1" docs/demo.gif
```

替换 README 顶部的 `screenshot.png` 引用即可。
