# 📣 X / Twitter Thread 发布指南

完整流程：从打开 X 到 thread 发出去，再到第一波互动。

---

## 1️⃣ 怎么发 Thread（操作步骤）

### Web 端（推荐，方便复制粘贴）

1. 浏览器打开 [x.com](https://x.com/home)
2. 点左边 `Post`（发推）按钮 → 弹出输入框
3. 把准备好的 **第 1 条推文** 粘进去
4. **添加图片**：点输入框下方的 🖼️ 图标，选择 `docs/demo.gif`（首推用 GIF 最吸睛）
5. 看到 "280" 计数器变小 —— 别超
6. **关键一步**：点击输入框下方的 **`+`（Add post）** 按钮 → 会出现第二个输入框，挂在第一条下面
7. 重复粘第 2 条、第 3 条…… 想几条加几个 `+`
8. 全部填完 → 点右下角 **`Post all`**

整条 thread 一起发出去，按时间顺序自动串联。

### iPhone / iPad App

1. 长按 X App 的撰写按钮，或点 `+` 写第一条
2. 填好后 **不要发**，点输入框下面那个 **小 ⊕ 圈圈**
3. 出现第二条 → 继续填
4. 全部完成 → 点 `Post all`

### 中途想改？

- 发出去**之前**：每条都可以单独编辑、删除
- 发出去**之后**：单条可在 30 分钟内 Edit（需要订阅 X Premium），thread 顺序不能改
- 后悔了：删除第 1 条会把整条 thread 全删（其它推文还在但脱链）

---

## 2️⃣ 复制即用的英文 Thread 文案

> 直接复制每一段到 X，按上面步骤逐条挂上。

### 🪧 第 1 条（带 `docs/demo.gif`）

```
Ever hit your Claude or ChatGPT rate limit mid-flow and wonder how close you were? 😩

I built a tiny macOS menu-bar widget that shows both subscriptions' real-time usage — pulled from the same APIs the official apps use.

No API key. Open source.

🧵👇
```
**附图**：上传 `docs/demo.gif`

---

### 🪧 第 2 条（带 `docs/screenshot-en.png`）

```
Why it exists:

Both Claude and ChatGPT bury your 5-hour & 7-day usage 3 clicks deep.

I wanted a number I could glance at — like the battery indicator, but for AI quotas.

So I built one. 🤖
```
**附图**：上传 `docs/screenshot-en.png`

---

### 🪧 第 3 条（技术细节，钓技术读者）

```
How it works — read-only, fully local:

• Claude: decrypts the session cookie from Chromium's Cookies DB via macOS Keychain → /api/organizations/{org}/usage
• ChatGPT: reads OAuth token from ~/.codex/auth.json → /backend-api/wham/usage

Nothing leaves your Mac.
```

---

### 🪧 第 4 条（卖点列表）

```
Stack:

🐍 Python + rumps (~120MB RAM, 1% CPU)
🎨 Color-coded progress bars: green → yellow → orange → red
🕒 Reset countdowns with local timezone
⚙️ LaunchAgent for auto-start on login
📦 One-shot installer
🌐 Bilingual (EN / 中文)
```

---

### 🪧 第 5 条（CTA + 标签）

```
Free, MIT-licensed, takes 30s to install:

github.com/liamlai88/ai-usage-bar

If it saves you 5 minutes a week, a ⭐ would mean a lot 🙏

#buildinpublic #macOS #ClaudeAI #ChatGPT #indiedev
```

---

## 3️⃣ 发布时机 & 数据放大

### 黄金时间窗（北京时间）

| 目标人群 | 建议发布时间 |
|---|---|
| 北美开发者 | **23:00 – 02:00**（PT 早 8-11 点） |
| 欧洲开发者 | **17:00 – 19:00**（GMT 早 10-12 点） |
| 国内中文圈 | **20:00 – 22:30** 或 **早 9-10 点** |

**不要** 周末发，工程师周末不刷推；周二/周三/周四上午最好。

### 发布后第一小时

这一小时决定了 X 算法给你多少推送量。**全力盯着**：

1. 每条评论都回 —— 哪怕只是 "thanks!"
2. 自己引用转发自己的 thread，加一句新见解（"Btw, here's the trickiest part…"）
3. 找 3 个相关圈子的小 V，私信请他们看看（不要群发，太 spammy）

### 数据 OK 的话

- 第 1 小时：> 50 impressions, > 3 likes → 可继续发力
- 第 24 小时：> 1000 impressions, > 10 ⭐  → 准备做 Show HN
- 反应平淡：48 小时后换个角度再发一次（如改 "Why I built this" 视角）

---

## 4️⃣ 同步分发渠道（互导流）

发完 X 后 24 小时内陆续投：

| 渠道 | 链接 | 备注 |
|---|---|---|
| Reddit r/MacApps | reddit.com/r/MacApps | 上传 GIF，标题：`[Free] Real-time Claude & ChatGPT usage in your macOS menu bar` |
| Reddit r/ClaudeAI | reddit.com/r/ClaudeAI | 类似标题 |
| Hacker News | news.ycombinator.com/submit | 标题：`Show HN: AI Usage Bar – real-time Claude & ChatGPT quotas in macOS menu bar` |
| V2EX 分享创造 | v2ex.com/go/create | 用中文 thread 文案 |
| 即刻 | jike.app | 中文版，多带几张图 |
| ProductHunt | producthunt.com | 周一/周二上架最好 |

---

## 5️⃣ 常见坑

1. **第 1 条没图 = 自杀**。算法对带图推文的初始推送量是无图的 3-5 倍
2. **标签别放第 1 条**。会被算法降权当 spam。放最后一条
3. **链接放第 1 条会减少推送量**。X 不喜欢"导流出去"。链接放最后一条最安全
4. **别 at @AnthropicAI / @OpenAI** 求 RT，没用还反感。让产品质量本身去钓
5. **回复别带链接**。同样会降权

---

## 6️⃣ 一键复制
所有文案在 `docs/PROMO.md` 也有备份，包括单推爆款版和中文版。

祝爆推 🚀
