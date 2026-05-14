"""用 macOS 原生 AppKit 渲染高质量 README mockup。

依赖 PyObjC（已经在 rumps 的依赖里）。运行：
    .venv/bin/python docs/render_mockup.py

输出：docs/screenshot.png
"""
from pathlib import Path

from AppKit import (
    NSAttributedString, NSBezierPath, NSBitmapImageRep, NSColor, NSFont,
    NSFontAttributeName, NSForegroundColorAttributeName, NSGraphicsContext,
    NSImage, NSPNGFileType, NSShadow, NSShadowAttributeName,
)
from Foundation import NSMakeRect, NSMakePoint, NSMakeSize

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ROOT / "docs" / "screenshot.png"

# 整体画布尺寸
W, H = 800, 640
SCALE = 2  # 2x 高清


# ---------- 工具 ----------

def color(r, g, b, a=1.0):
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r/255, g/255, b/255, a)


def draw_text(s, x, y, font_size=13, weight="Regular", c=(20, 20, 22), align_right=None):
    """在 (x, y) 处画文本。y 是文本 baseline 坐标（AppKit 是从下往上）。
    align_right=True 时把 x 当成右边界。"""
    if weight == "Bold":
        font = NSFont.boldSystemFontOfSize_(font_size)
    elif weight == "Semibold":
        font = NSFont.fontWithName_size_("SF Pro Text Semibold", font_size) or NSFont.boldSystemFontOfSize_(font_size)
    else:
        font = NSFont.systemFontOfSize_(font_size)

    attrs = {NSFontAttributeName: font,
             NSForegroundColorAttributeName: color(*c)}
    attr = NSAttributedString.alloc().initWithString_attributes_(s, attrs)

    if align_right:
        size = attr.size()
        x = x - size.width
    attr.drawAtPoint_(NSMakePoint(x, y))


def rounded_rect(x, y, w, h, radius=8, fill=None, stroke=None, width=1.0):
    rect = NSMakeRect(x, y, w, h)
    path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
    if fill is not None:
        color(*fill).setFill()
        path.fill()
    if stroke is not None:
        color(*stroke).setStroke()
        path.setLineWidth_(width)
        path.stroke()


def progress_bar(x, y, pct, segments=14, seg_w=18, seg_h=10, gap=3):
    """彩色分段进度条"""
    if pct < 50:    fc = (52, 199, 89)     # 绿
    elif pct < 75:  fc = (255, 204, 0)     # 黄
    elif pct < 90:  fc = (255, 149, 0)     # 橙
    else:           fc = (255, 69, 58)     # 红
    ec = (220, 220, 224)
    filled = round(pct / 100 * segments)
    for i in range(segments):
        sx = x + i * (seg_w + gap)
        c = fc if i < filled else ec
        rounded_rect(sx, y, seg_w, seg_h, radius=2, fill=c)


def draw_image(path: Path, x: float, y: float, size: float):
    img = NSImage.alloc().initWithContentsOfFile_(str(path))
    if img is None:
        return
    img.drawInRect_(NSMakeRect(x, y, size, size))


# ---------- 主渲染 ----------

def main():
    # 创建画布（2x 分辨率）
    rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, W * SCALE, H * SCALE, 8, 4, True, False, "NSCalibratedRGBColorSpace", 0, 0
    )
    rep.setSize_(NSMakeSize(W, H))

    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    NSGraphicsContext.setCurrentContext_(ctx)
    ctx.saveGraphicsState()

    # —— 背景：浅色桌面 ——
    color(232, 234, 238).setFill()
    NSBezierPath.fillRect_(NSMakeRect(0, 0, W, H))

    # —— 顶部菜单栏 ——
    bar_h = 26
    rounded_rect(0, H - bar_h, W, bar_h, radius=0, fill=(255, 255, 255, 0.96))
    # 底部分隔线
    color(0, 0, 0, 0.08).setFill()
    NSBezierPath.fillRect_(NSMakeRect(0, H - bar_h - 1, W, 1))

    # 菜单栏右侧图标 + 时间
    right = W - 16
    draw_text("21:32", right, H - 18, font_size=13, align_right=True)
    right -= 60
    draw_text("🤖", right, H - 19, font_size=14, align_right=True)
    icon_x_center = right - 7  # 给下拉菜单对齐参考
    right -= 28
    for emoji in ["🔋", "📶", "🔍"]:
        draw_text(emoji, right, H - 19, font_size=14, align_right=True)
        right -= 28

    # —— 下拉菜单 ——
    mw = 470
    mh = 460
    mx = icon_x_center - mw + 20
    my = H - bar_h - mh - 8

    # 阴影
    shadow = NSShadow.alloc().init()
    shadow.setShadowOffset_(NSMakeSize(0, -2))
    shadow.setShadowBlurRadius_(12)
    shadow.setShadowColor_(color(0, 0, 0, 0.18))
    shadow.set()

    rounded_rect(mx, my, mw, mh, radius=10, fill=(252, 252, 254, 1.0),
                 stroke=(0, 0, 0, 0.12), width=0.5)

    # 清掉阴影
    NSShadow.alloc().init().set()

    # 渲染菜单项（从顶部往下）
    cy = my + mh - 24  # 当前 y baseline

    def item(text, indent=22, font_size=13, weight="Regular", c=(30, 30, 32), icon=None, advance=24):
        nonlocal cy
        if icon is not None:
            draw_image(icon, mx + 14, cy - 4, 18)
        draw_text(text, mx + indent, cy, font_size=font_size, weight=weight, c=c)
        cy -= advance

    def small(text, indent=46, c=(110, 110, 120), advance=22):
        nonlocal cy
        draw_text(text, mx + indent, cy, font_size=11, c=c)
        cy -= advance

    def separator():
        nonlocal cy
        cy -= 4
        color(0, 0, 0, 0.08).setFill()
        NSBezierPath.fillRect_(NSMakeRect(mx + 10, cy + 12, mw - 20, 0.5))
        cy -= 8

    def usage_row(label, pct, reset_text):
        nonlocal cy
        # 第 1 行：label + bar + 剩余%
        draw_text(label, mx + 42, cy, font_size=13)
        progress_bar(mx + 188, cy + 1, pct)
        draw_text(f"剩 {100 - pct:.0f}%", mx + mw - 14, cy, font_size=11,
                  c=(110, 110, 120), align_right=True)
        cy -= 22
        # 第 2 行：重置倒计时
        draw_text(reset_text, mx + 60, cy, font_size=11, c=(110, 110, 120))
        cy -= 22

    # —— Claude 区 ——
    cy -= 4
    item("Claude Pro（实时）", indent=40, weight="Semibold", icon=ASSETS / "claude_logo.png")
    cy -= 2
    usage_row("⏱  5 小时   65%", 65, "🕒 1 小时 28 分后重置 · 18:43")
    usage_row("📅  7 天        8%",  8, "🕒 6 天 4 小时后重置 · 周三 22:15")
    item("💎  Extra：$0.00 / $2000 USD", indent=40, font_size=12, c=(80, 80, 90))

    separator()

    # —— Codex 区 ——
    item("Codex Plus（实时）", indent=40, weight="Semibold", icon=ASSETS / "openai_logo.png")
    cy -= 2
    usage_row("⏱  5 小时    8%",  8, "🕒 4 小时 6 分后重置 · 21:21")
    usage_row("📅  7 天       63%", 63, "🕒 1 天 22 小时后重置 · 周六 16:15")
    item("💎  Credits 余额：0", indent=40, font_size=12, c=(80, 80, 90))

    separator()
    item("🕘  Claude: 5 秒前  ·  Codex: 5 秒前", indent=14, font_size=12, c=(110, 110, 120))
    item("🔄  立即刷新", indent=14)
    separator()
    item("👋  退出", indent=14)

    ctx.restoreGraphicsState()
    ctx.flushGraphics()

    # 保存 PNG
    png_data = rep.representationUsingType_properties_(NSPNGFileType, None)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    png_data.writeToFile_atomically_(str(OUT), True)
    print(f"✅ Saved: {OUT}")


if __name__ == "__main__":
    main()
