#!/usr/bin/env python3
"""One-page newspaper summing up Sunday 22 November 2026 world news.

Draws the whole image from scratch with a hand-built 5x7 bitmap font,
a pixel rasterizer and a manual PNG encoder. Python 3.13 standard
library only, no network, no clock, no randomness: two runs write
byte-identical output.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 230)
INK = (20, 20, 20)
RED = (179, 39, 30)
NAVY = (31, 58, 95)
TEAL = (15, 118, 110)
TEAL_LT = (153, 200, 193)
GREEN = (30, 122, 52)
GREEN_LT = (120, 220, 140)
GREY = (120, 116, 108)
WHITE = (255, 255, 255)
GOLD = (212, 160, 32)

# ---------------------------------------------------------------- font ----
# Each glyph: 7 rows of 5 cells, '#' = ink, '.' = empty.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '/': ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '&': (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '·': (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
}

# ------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=3):
        for a in range(0, 360):
            rad = math.radians(a)
            for k in range(t):
                rr = r - k
                self.set(int(cx + rr * math.cos(rad)),
                         int(cy + rr * math.sin(rad)), c)

    def ellipse_outline(self, cx, cy, rx, ry, c):
        for a in range(0, 360, 2):
            rad = math.radians(a)
            self.set(int(cx + rx * math.cos(rad)),
                     int(cy + ry * math.sin(rad)), c)


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    for ch in s:
        g = FONT.get(ch, FONT.get(ch.upper(), FONT[' ']))
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '#':
                    cv.rect(x + c * scale, y + r * scale, scale, scale, color)
        x += 6 * scale


def draw_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, max_w, scale):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, scale, color, max_w, leading):
    """Draw wrapped text; returns the y just below the block."""
    for line in wrap(s, max_w, scale):
        draw_text(cv, x, y, line, scale, color)
        y += leading
    return y


# --------------------------------------------------------------- image ----
def build():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ------------------------------------------------------
    cv.hline(48, 26, 928, RED, 6)
    draw_centered(cv, 512, 44, "THE WORLD IN ONE PAGE", 6, INK)
    draw_centered(cv, 512, 102, "SUNDAY · 22 NOVEMBER 2026", 3, RED)
    cv.hline(48, 140, 928, INK, 3)
    cv.hline(48, 147, 928, INK, 1)

    # ---- lead: COP31 ---------------------------------------------------
    lx, lw = 48, 592
    y = 172
    draw_text(cv, lx, y, "CLIMATE — ANTALYA, TURKEY", 2, RED)
    y += 30
    draw_text(cv, lx, y, "COP31 NEARS DEAL", 5, INK)
    y += 46
    draw_text(cv, lx, y, "IN OVERTIME", 5, INK)
    y += 56
    body = ("After running past its Friday deadline, climate talks in "
            "Antalya tabled a new draft deal early Sunday. Nearly 200 "
            "nations will vote from 0600 GMT. The text drops any mention "
            "of fossil fuels, recalling the COP28 pledge instead, and "
            "sets a 1-billion-tonne carbon-capture goal and a 35% "
            "electricity target by 2035.")
    y = draw_block(cv, lx, y, body, 2, INK, lw, 21)
    y += 10
    facts = ("FACTS: NO FOSSIL-FUEL MENTION · 1BN TONNES CARBON "
             "CAPTURE · 35% ELECTRIC BY 2035")
    y = draw_block(cv, lx, y, facts, 2, RED, lw, 21)

    # ---- lead art: warming globe + thermometer -------------------------
    ax, ay = 672, 168
    cv.rect(ax, ay, 304, 330, NAVY)
    cv.disc(ax + 130, ay + 140, 96, TEAL)
    cv.ring(ax + 130, ay + 140, 96, TEAL_LT, 2)
    cv.ellipse_outline(ax + 130, ay + 140, 96, 34, TEAL_LT)
    cv.ellipse_outline(ax + 130, ay + 140, 40, 96, TEAL_LT)
    cv.ellipse_outline(ax + 130, ay + 140, 78, 96, TEAL_LT)
    cv.hline(ax + 44, ay + 140, 172, TEAL_LT, 2)
    draw_centered(cv, ax + 152, ay + 268, "COP31", 3, WHITE)
    # thermometer
    tx, ty = ax + 228, ay + 60
    cv.rect(tx, ty, 26, 150, WHITE)
    cv.rect(tx + 4, ty + 4, 18, 142, RED)
    cv.rect(tx + 4, ty + 4, 18, 60, WHITE)
    cv.disc(tx + 13, ty + 168, 24, WHITE)
    cv.disc(tx + 13, ty + 168, 18, RED)
    draw_text(cv, tx - 4, ty + 200, "1.5C", 2, WHITE)

    # ---- divider -------------------------------------------------------
    cv.hline(48, 540, 928, INK, 3)

    # ---- Seoul: exam row ----------------------------------------------
    sy = 566
    # art: exam paper + smart glasses
    cv.rect(48, sy + 8, 210, 150, WHITE)
    cv.rect(48, sy + 8, 210, 150, INK)  # border via outline below
    cv.rect(52, sy + 12, 202, 142, WHITE)
    for i in range(4):
        cv.hline(66, sy + 34 + i * 20, 160, GREY, 2)
    draw_text(cv, 66, sy + 104, "SUNEUNG", 2, INK)
    # smart glasses over the paper
    gx, gy = 78, sy + 122
    cv.rect(gx, gy, 74, 34, INK)
    cv.rect(gx + 4, gy + 4, 66, 26, (200, 220, 235))
    cv.rect(gx + 84, gy, 74, 34, INK)
    cv.rect(gx + 88, gy + 4, 66, 26, (200, 220, 235))
    cv.rect(gx + 74, gy + 12, 12, 6, INK)
    cv.disc(gx + 140, gy + 10, 5, RED)

    tx2, tw2 = 300, 676
    y = sy
    draw_text(cv, tx2, y, "SOUTH KOREA — SEOUL", 2, RED)
    y += 30
    draw_text(cv, tx2, y, "MINISTER QUITS OVER", 4, INK)
    y += 40
    draw_text(cv, tx2, y, "AI-CHEATING EXAM ROW", 4, INK)
    y += 50
    body2 = ("Education Minister Choi Kyo-jin offered his resignation "
             "Sunday and President Lee Jae Myung accepted it, after "
             "last-minute anti-cheating rules for the Suneung exam. "
             "111 smart-device cases were detected: 54 via emergency "
             "alerts, 52 for possession or Wi-Fi, 5 for actual use.")
    draw_block(cv, tx2, y, body2, 2, INK, tw2, 21)

    # ---- markets strip -------------------------------------------------
    my = 800
    cv.rect(48, my, 928, 128, NAVY)
    draw_text(cv, 72, my + 18, "MARKETS", 2, GOLD)
    draw_text(cv, 72, my + 44, "BITCOIN HOLDS NEAR $59,500", 3, WHITE)
    draw_text(cv, 72, my + 74, "AFTER TWO-YEAR LOW", 3, WHITE)
    draw_text(cv, 72, my + 104, "SAT LOW $55,106, WEAKEST SINCE SEPT 2024", 2, (200, 210, 230))
    # rising chart line
    pts = [(700, 896), (740, 884), (780, 892), (820, 862), (860, 848),
           (900, 836), (940, 840)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(x0, y0, x1, y1, GREEN_LT, 4)
    for (x, yy) in pts:
        cv.disc(x, yy, 4, GREEN_LT)
    draw_text(cv, 700, my + 104, "+8% FROM LOW", 2, GREEN_LT)

    # ---- footer --------------------------------------------------------
    draw_text(cv, 48, 956, "SOURCES: REUTERS · AJP · COINPAPRIKA", 2, INK)
    draw_text(cv, 1024 - 48 - text_w("SUNDAY 22 NOVEMBER 2026", 2), 956,
              "SUNDAY 22 NOVEMBER 2026", 2, INK)
    cv.hline(48, 986, 928, INK, 2)

    return cv


def chunk(tag, data):
    c = tag + data
    return struct.pack(">I", len(data)) + c + struct.pack(
        ">I", zlib.crc32(c) & 0xFFFFFFFF)


def write_png(cv, path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    write_png(build(), os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
