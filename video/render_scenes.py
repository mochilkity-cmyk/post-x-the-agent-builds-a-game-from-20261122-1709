#!/usr/bin/env python3
"""Render the video's non-gameplay scenes with PIL (deterministic frames).

Scene A (0-5s, 15fps): the one prompt, typed into a terminal.
Scene B (5-13s, 15fps): the agent working — game code lines + build log.
Output: video/frames-a/a-%04d.png, video/frames-b/b-%04d.png (1920x1080).
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
FPS = 15
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

BG = (5, 6, 15)
PANEL = (11, 14, 31)
PANEL_EDGE = (27, 33, 64)
CYAN = (0, 240, 255)
PINK = (255, 46, 136)
GOLD = (255, 211, 25)
WHITE = (232, 246, 255)
GREY = (139, 147, 184)
GREEN = (64, 224, 130)


def font(path, size):
    return ImageFont.truetype(path, size)


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # faint stars
    import random
    rng = random.Random(7)
    for _ in range(120):
        x, y = rng.randint(0, W - 1), rng.randint(0, H - 1)
        r = rng.choice([1, 1, 2])
        d.ellipse([x, y, x + r, y + r], fill=(120, 150, 200))
    return img, d


def panel(d, x0, y0, x1, y1):
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=PANEL, outline=PANEL_EDGE, width=3)


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(" "), [], ""
    for wrd in words:
        trial = (cur + " " + wrd).strip()
        if d.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wrd
    if cur:
        lines.append(cur)
    return lines


PROMPT = ("Build a tiny browser game: Neon Dodger. Steer the ship with arrow keys, "
          "dodge falling asteroids, collect stars for points. 3 lives. "
          "Win at 300 points. Neon style, dark space, one HTML file.")


def scene_a():
    os.makedirs(os.path.join(HERE, "frames-a"), exist_ok=True)
    f_title = font(MONO_B, 54)
    f_body = font(MONO, 46)
    f_small = font(MONO, 34)
    total = 5 * FPS
    # pre-wrap the prompt
    probe = Image.new("RGB", (W, H))
    pd = ImageDraw.Draw(probe)
    lines = wrap(pd, PROMPT, f_body, 1500)
    n_chars = len(PROMPT)
    for i in range(total):
        img, d = base()
        d.text((96, 84), "THE PROMPT", font=f_title, fill=CYAN)
        d.text((96, 160), "one prompt. one game. no edits after.", font=f_small, fill=GREY)
        panel(d, 96, 260, 1824, 900)
        # terminal dots
        for j, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([140 + j * 44, 296, 140 + j * 44 + 22, 318], fill=c)
        d.text((300, 288), "agent — make.fun", font=f_small, fill=GREY)
        # typed text: reveal chars progressively
        shown = int(n_chars * (i + 1) / total)
        # map shown chars back onto wrapped lines
        remaining = shown
        y = 380
        for ln in lines:
            if remaining <= 0:
                break
            take = min(len(ln), remaining)
            d.text((140, y), ln[:take], font=f_body, fill=WHITE)
            remaining -= len(ln) + 1  # +1 for the space between wrapped lines
            y += 64
        # blinking cursor after the last shown char
        if i % 10 < 7:
            # cursor at end of current line
            cx, cy = 140, 380
            rem = shown
            for ln in lines:
                if rem <= len(ln):
                    cx = 140 + d.textlength(ln[:rem], font=f_body)
                    break
                rem -= len(ln) + 1
                cy += 64
            d.rectangle([cx + 4, cy, cx + 14, cy + 48], fill=GOLD)
        d.text((96, 950), "make.fun — where people and their AI agents build things", font=f_small, fill=GREY)
        img.save(os.path.join(HERE, "frames-a", f"a-{i:04d}.png"))
    print("scene A:", total, "frames")


CODE_LINES = [
    ("const ship = { x: .5, y: .82, hp: 3 };", CYAN),
    ("function spawnAsteroid() { /* rng */ }", WHITE),
    ("function step(dt) { move(); collide(); }", WHITE),
    ("if (score >= 300) status = 'won';", GOLD),
    ("// one file. no network. no deps.", GREY),
]
LOG_LINES = [
    ("$ agent: building Neon Dodger ...", GREY),
    ("✓ game written — game/index.html", GREEN),
    ("✓ 3 lives · stars · asteroids · win at 300", GREEN),
    ("✓ running — 0 errors, 60 fps", GREEN),
]


def scene_b():
    os.makedirs(os.path.join(HERE, "frames-b"), exist_ok=True)
    f_title = font(MONO_B, 54)
    f_code = font(MONO, 40)
    f_log = font(MONO, 40)
    f_small = font(MONO, 34)
    total = 8 * FPS
    for i in range(total):
        img, d = base()
        d.text((96, 84), "THE AGENT, WORKING", font=f_title, fill=PINK)
        d.text((96, 160), "watch it write the game — live, in one session.", font=f_small, fill=GREY)
        # code panel (left)
        panel(d, 96, 260, 1150, 900)
        d.text((140, 296), "game/index.html", font=f_small, fill=GREY)
        y = 370
        n_code = min(len(CODE_LINES), (i * len(CODE_LINES)) // (total // 2) + 1)
        for ln, col in CODE_LINES[:n_code]:
            d.text((140, y), ln, font=f_code, fill=col)
            y += 62
        # log panel (right)
        panel(d, 1200, 260, 1824, 900)
        d.text((1240, 296), "build log", font=f_small, fill=GREY)
        y = 370
        n_log = min(len(LOG_LINES), max(0, ((i - total // 2) * len(LOG_LINES) + (total // 2 - 1)) // (total // 2)))
        for ln, col in LOG_LINES[:n_log]:
            for sub in wrap(d, ln, f_log, 540):
                d.text((1240, y), sub, font=f_log, fill=col)
                y += 56
            y += 8
        # progress bar
        frac = min(1.0, (i + 1) / total)
        d.text((96, 950), "BUILDING", font=f_small, fill=GREY)
        d.rectangle([280, 948, 1640, 978], outline=PANEL_EDGE, width=2)
        d.rectangle([282, 950, 282 + int(1354 * frac), 976], fill=CYAN)
        d.text((1660, 948), f"{int(frac * 100)}%", font=f_small, fill=CYAN)
        img.save(os.path.join(HERE, "frames-b", f"b-{i:04d}.png"))
    print("scene B:", total, "frames")


if __name__ == "__main__":
    scene_a()
    scene_b()
