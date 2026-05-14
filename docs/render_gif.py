"""Render an animated GIF showing the menu UI as Claude usage rises 0% → 100%.

Output: docs/demo.gif
"""
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_mockup import render

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "docs" / "_frames"
OUT = ROOT / "docs" / "demo.gif"


def make_frames():
    TMP.mkdir(exist_ok=True)
    # Claude 5h 从 5% 涨到 98%（10 帧）；7d 同步从 5% 涨到 35%。
    # Codex 保持稳定，给视觉对比。
    steps = [(5, 5, 8, 63),
             (18, 8, 8, 63),
             (32, 11, 9, 63),
             (45, 14, 11, 64),
             (58, 17, 13, 64),
             (70, 20, 16, 64),
             (80, 24, 18, 64),
             (88, 27, 20, 65),
             (94, 30, 22, 65),
             (98, 33, 24, 65)]
    paths = []
    for i, (c5, c7, x5, x7) in enumerate(steps):
        p = TMP / f"frame_{i:02d}.png"
        render("en", c5, c7, x5, x7, p)
        paths.append(p)
    return paths


def build_gif(frames):
    imgs = [Image.open(p).convert("RGB") for p in frames]
    # 缩小成 GIF 友好尺寸（节省体积）
    imgs = [im.resize((640, 512), Image.LANCZOS) for im in imgs]
    # 每帧停 700ms，最后一帧停 1500ms 让人看清"快爆表"状态
    durations = [700] * (len(imgs) - 1) + [1500]
    imgs[0].save(
        OUT, save_all=True, append_images=imgs[1:],
        duration=durations, loop=0, optimize=True,
    )
    print(f"✅ GIF saved: {OUT}  ({len(frames)} frames)")


if __name__ == "__main__":
    frames = make_frames()
    build_gif(frames)
    # 清理临时 PNG
    for p in frames:
        p.unlink()
    TMP.rmdir()
