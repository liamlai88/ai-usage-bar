"""Render menu mockups for README in zh / en.

Usage:
    .venv/bin/python docs/render_mockup.py [--lang zh|en] [--out path] [--c5 65 --c7 8 --x5 8 --x7 63]
"""
import argparse
from pathlib import Path

from AppKit import (
    NSAttributedString, NSBezierPath, NSBitmapImageRep, NSColor, NSFont,
    NSFontAttributeName, NSForegroundColorAttributeName, NSGraphicsContext,
    NSImage, NSPNGFileType, NSShadow,
)
from Foundation import NSMakeRect, NSMakePoint, NSMakeSize

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

W, H = 800, 640
SCALE = 2


def color(r, g, b, a=1.0):
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r/255, g/255, b/255, a)


def draw_text(s, x, y, font_size=13, weight="Regular", c=(20, 20, 22), align_right=False):
    if weight == "Bold":
        font = NSFont.boldSystemFontOfSize_(font_size)
    elif weight == "Semibold":
        font = NSFont.fontWithName_size_("SF Pro Text Semibold", font_size) or NSFont.boldSystemFontOfSize_(font_size)
    else:
        font = NSFont.systemFontOfSize_(font_size)

    attrs = {NSFontAttributeName: font, NSForegroundColorAttributeName: color(*c)}
    attr = NSAttributedString.alloc().initWithString_attributes_(s, attrs)
    if align_right:
        x = x - attr.size().width
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
    if pct < 50:    fc = (52, 199, 89)
    elif pct < 75:  fc = (255, 204, 0)
    elif pct < 90:  fc = (255, 149, 0)
    else:           fc = (255, 69, 58)
    ec = (220, 220, 224)
    filled = round(pct / 100 * segments)
    for i in range(segments):
        sx = x + i * (seg_w + gap)
        c = fc if i < filled else ec
        rounded_rect(sx, y, seg_w, seg_h, radius=2, fill=c)


def draw_image(path: Path, x: float, y: float, size: float):
    img = NSImage.alloc().initWithContentsOfFile_(str(path))
    if img is not None:
        img.drawInRect_(NSMakeRect(x, y, size, size))


# ---------- 文案模板 ----------

COPY = {
    "en": {
        "claude_header":   "Claude Pro (live)",
        "codex_header":    "Codex Plus (live)",
        "5h":              "⏱  5h window",
        "7d":              "📅  7d window",
        "left":            "{}% left",
        "reset_5h_c":      "🕒 resets in 1h 28m · 18:43",
        "reset_7d_c":      "🕒 resets in 6d 4h · Wed 22:15",
        "reset_5h_x":      "🕒 resets in 4h 6m · 21:21",
        "reset_7d_x":      "🕒 resets in 1d 22h · Sat 16:15",
        "extra":           "💎  Extra: $0.00 / $2000 USD",
        "credits":         "💎  Credits: 0",
        "updated":         "🕘  Claude: 5s ago  ·  Codex: 5s ago",
        "refresh":         "🔄  Refresh now",
        "quit":            "👋  Quit",
    },
    "zh": {
        "claude_header":   "Claude Pro（实时）",
        "codex_header":    "Codex Plus（实时）",
        "5h":              "⏱  5 小时",
        "7d":              "📅  7 天",
        "left":            "剩 {}%",
        "reset_5h_c":      "🕒 1 小时 28 分后重置 · 18:43",
        "reset_7d_c":      "🕒 6 天 4 小时后重置 · 周三 22:15",
        "reset_5h_x":      "🕒 4 小时 6 分后重置 · 21:21",
        "reset_7d_x":      "🕒 1 天 22 小时后重置 · 周六 16:15",
        "extra":           "💎  Extra：$0.00 / $2000 USD",
        "credits":         "💎  Credits 余额：0",
        "updated":         "🕘  Claude: 5 秒前  ·  Codex: 5 秒前",
        "refresh":         "🔄  立即刷新",
        "quit":            "👋  退出",
    },
}


def render(lang: str, c5: float, c7: float, x5: float, x7: float, out: Path):
    cp = COPY[lang]
    rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, W * SCALE, H * SCALE, 8, 4, True, False, "NSCalibratedRGBColorSpace", 0, 0
    )
    rep.setSize_(NSMakeSize(W, H))

    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    NSGraphicsContext.setCurrentContext_(ctx)
    ctx.saveGraphicsState()

    # background
    color(232, 234, 238).setFill()
    NSBezierPath.fillRect_(NSMakeRect(0, 0, W, H))

    # menu bar
    bar_h = 26
    rounded_rect(0, H - bar_h, W, bar_h, radius=0, fill=(255, 255, 255, 0.96))
    color(0, 0, 0, 0.08).setFill()
    NSBezierPath.fillRect_(NSMakeRect(0, H - bar_h - 1, W, 1))

    right = W - 16
    draw_text("21:32", right, H - 18, font_size=13, align_right=True)
    right -= 60
    draw_text("🤖", right, H - 19, font_size=14, align_right=True)
    icon_x_center = right - 7
    right -= 28
    for emoji in ["🔋", "📶", "🔍"]:
        draw_text(emoji, right, H - 19, font_size=14, align_right=True)
        right -= 28

    # dropdown
    mw = 470
    mh = 460
    mx = icon_x_center - mw + 20
    my = H - bar_h - mh - 8

    shadow = NSShadow.alloc().init()
    shadow.setShadowOffset_(NSMakeSize(0, -2))
    shadow.setShadowBlurRadius_(12)
    shadow.setShadowColor_(color(0, 0, 0, 0.18))
    shadow.set()

    rounded_rect(mx, my, mw, mh, radius=10, fill=(252, 252, 254, 1.0),
                 stroke=(0, 0, 0, 0.12), width=0.5)

    NSShadow.alloc().init().set()

    cy = my + mh - 24

    def item(text, indent=22, font_size=13, weight="Regular", c=(30, 30, 32), icon=None, advance=24):
        nonlocal cy
        if icon is not None:
            draw_image(icon, mx + 14, cy - 4, 18)
        draw_text(text, mx + indent, cy, font_size=font_size, weight=weight, c=c)
        cy -= advance

    def separator():
        nonlocal cy
        cy -= 4
        color(0, 0, 0, 0.08).setFill()
        NSBezierPath.fillRect_(NSMakeRect(mx + 10, cy + 12, mw - 20, 0.5))
        cy -= 8

    def usage_row(label, pct, reset_text):
        nonlocal cy
        draw_text(f"{label}    {pct:.0f}%", mx + 42, cy, font_size=13)
        progress_bar(mx + 188, cy + 1, pct)
        draw_text(cp["left"].format(int(100 - pct)), mx + mw - 14, cy, font_size=11,
                  c=(110, 110, 120), align_right=True)
        cy -= 22
        draw_text(reset_text, mx + 60, cy, font_size=11, c=(110, 110, 120))
        cy -= 22

    cy -= 4
    item(cp["claude_header"], indent=40, weight="Semibold", icon=ASSETS / "claude_logo.png")
    cy -= 2
    usage_row(cp["5h"], c5, cp["reset_5h_c"])
    usage_row(cp["7d"], c7, cp["reset_7d_c"])
    item(cp["extra"], indent=40, font_size=12, c=(80, 80, 90))

    separator()

    item(cp["codex_header"], indent=40, weight="Semibold", icon=ASSETS / "openai_logo.png")
    cy -= 2
    usage_row(cp["5h"], x5, cp["reset_5h_x"])
    usage_row(cp["7d"], x7, cp["reset_7d_x"])
    item(cp["credits"], indent=40, font_size=12, c=(80, 80, 90))

    separator()
    item(cp["updated"], indent=14, font_size=12, c=(110, 110, 120))
    item(cp["refresh"], indent=14)
    separator()
    item(cp["quit"], indent=14)

    ctx.restoreGraphicsState()
    ctx.flushGraphics()

    png_data = rep.representationUsingType_properties_(NSPNGFileType, None)
    out.parent.mkdir(parents=True, exist_ok=True)
    png_data.writeToFile_atomically_(str(out), True)
    print(f"✅ Saved: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=["en", "zh"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--c5", type=float, default=65)
    ap.add_argument("--c7", type=float, default=8)
    ap.add_argument("--x5", type=float, default=8)
    ap.add_argument("--x7", type=float, default=63)
    args = ap.parse_args()
    out = Path(args.out) if args.out else (ROOT / "docs" / f"screenshot-{args.lang}.png")
    render(args.lang, args.c5, args.c7, args.x5, args.x7, out)
