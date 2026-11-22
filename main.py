#!/usr/bin/env python3
"""news-image-20261122: one-page newspaper summing up Sunday 22 November 2026.

Pure Python 3.13 standard library. Hand-built 5x7 bitmap font, software
rasterizer, manual PNG encoder. Deterministic: no clock, no randomness.

Stories (all verified against reputable reporting, all dated 22 Nov 2026):
- LEAD: COP31 climate talks in Antalya, Turkey, run into double
  overtime; a new draft deal released early Sunday aims for consensus
  from nearly 200 nations. The text drops fossil fuels but sets a
  1 billion tonne carbon capture goal and a 35% electricity target.
  (Reuters, Sunday; BBC, 22 Nov 05:26)
- SEOUL: education minister Choi Kyo-jin resigns on Sunday over the
  AI-cheating row at the Suneung exam; 111 device violations found.
  (AJP, 22 Nov; AFP)
- MARKETS: Bitcoin rebounds from Saturday's two-year low of $55,100
  to around $59,500 on Sunday, briefly topping $60,000.
  (CoinPaprika data, 22 Nov 04:06 UTC; CoinMarketCap, 22 Nov)

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib
from math import isqrt

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (178, 34, 34)
SKY = (52, 68, 92)
SKY_DARK = (40, 52, 72)
RAIN = (180, 200, 220)
WATER = (70, 105, 135)
GREEN = (74, 140, 74)
WAVE = (220, 235, 245)
TENT = (201, 168, 106)
PANEL = (220, 225, 230)
WHITE = (255, 255, 255)
GREY = (150, 150, 145)

# 5x7 bitmap font: each glyph is 7 rows of 5 characters ('#' = ink).
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "·": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}
BLANK = (".....",) * 7


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = color[0]
                self.px[i + 1] = color[1]
                self.px[i + 2] = color[2]

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color):
        # Bresenham.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = isqrt(r * r - dy * dy)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def fill_triangle(self, x1, y1, x2, y2, x3, y3, color):
        # Scanline fill: sort vertices by y, interpolate edges.
        pts = sorted(((x1, y1), (x2, y2), (x3, y3)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        def edge_x(y, p, q):
            if p[1] == q[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])
        for y in range(ay, cy + 1):
            if y < by:
                xa = edge_x(y, (ax, ay), (bx, by))
            else:
                xa = edge_x(y, (bx, by), (cx, cy))
            xb = edge_x(y, (ax, ay), (cx, cy))
            lo, hi = (xa, xb) if xa <= xb else (xb, xa)
            self.fill_rect(int(lo), y, int(hi) - int(lo) + 1, 1, color)

    def text_width(self, s, scale):
        return len(s) * 6 * scale

    def draw_text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(
                            cx + col * scale, y + row * scale, scale, scale, color
                        )
            cx += 6 * scale

    def draw_text_centered(self, s, cx, y, scale, color):
        self.draw_text(s, cx - self.text_width(s, scale) // 2, y, scale, color)

    def wrap(self, text, max_w, scale):
        lines = []
        for para in text.split("\n"):
            words = para.split(" ")
            cur = ""
            for word in words:
                trial = word if not cur else cur + " " + word
                if self.text_width(trial, scale) <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines


def draw_climate_art(cv, x0, y0, w, h):
    # Warming globe: blue globe with green land, red thermometer at right.
    cv.fill_rect(x0, y0, w, h, PANEL)
    # Sun, top left.
    cv.fill_circle(x0 + 44, y0 + 40, 20, (230, 180, 60))
    for (dx1, dy1, dx2, dy2) in (
        (26, 0, 36, 0), (-26, 0, -36, 0), (0, 26, 0, 36), (0, -26, 0, -36),
        (18, 18, 25, 25), (18, -18, 25, -25), (-18, 18, -25, 25), (-18, -18, -25, -25),
    ):
        cv.line(x0 + 44 + dx1, y0 + 40 + dy1, x0 + 44 + dx2, y0 + 40 + dy2, (230, 180, 60))
    # Heat squiggle above the globe.
    cv.line(x0 + 100, y0 + 46, x0 + 120, y0 + 36, RED)
    cv.line(x0 + 120, y0 + 36, x0 + 140, y0 + 46, RED)
    cv.line(x0 + 140, y0 + 46, x0 + 160, y0 + 36, RED)
    cv.line(x0 + 160, y0 + 36, x0 + 180, y0 + 46, RED)
    cv.line(x0 + 180, y0 + 46, x0 + 200, y0 + 36, RED)
    # Globe: ink ring, blue sea, green land.
    cv.fill_circle(x0 + 150, y0 + 150, 90, INK)
    cv.fill_circle(x0 + 150, y0 + 150, 88, WATER)
    cv.fill_circle(x0 + 120, y0 + 120, 22, GREEN)
    cv.fill_circle(x0 + 180, y0 + 170, 26, GREEN)
    cv.fill_circle(x0 + 165, y0 + 105, 14, GREEN)
    cv.fill_triangle(x0 + 130, y0 + 190, x0 + 175, y0 + 190, x0 + 150, y0 + 160, GREEN)
    # Thermometer at right: white tube, red mercury, bulb.
    cv.fill_rect(x0 + 278, y0 + 60, 18, 168, WHITE)
    cv.rect(x0 + 278, y0 + 60, 18, 168, INK, 2)
    cv.fill_rect(x0 + 281, y0 + 110, 12, 115, RED)
    cv.fill_circle(x0 + 287, y0 + 238, 22, INK)
    cv.fill_circle(x0 + 287, y0 + 238, 20, RED)
    cv.rect(x0, y0, w, h, INK, 2)


def draw_exam_art(cv, x0, y0, w, h):
    # Exam paper with a pair of smart glasses and an AI tag.
    cv.fill_rect(x0, y0, w, h, PANEL)
    cv.fill_rect(x0 + 30, y0 + 20, 200, 140, WHITE)
    cv.rect(x0 + 30, y0 + 20, 200, 140, INK, 2)
    for i in range(5):
        ly = y0 + 44 + i * 20
        cv.hline(x0 + 46, ly, 168, GREY, 2)
    # Glasses: two rings + bridge + temples.
    for gx in (x0 + 100, x0 + 180):
        cv.fill_circle(gx, y0 + 92, 26, INK)
        cv.fill_circle(gx, y0 + 92, 21, WHITE)
        cv.fill_circle(gx, y0 + 92, 21, PANEL)
        cv.fill_circle(gx, y0 + 92, 16, WHITE)
    cv.fill_rect(x0 + 126, y0 + 88, 28, 5, INK)
    cv.line(x0 + 74, y0 + 88, x0 + 44, y0 + 76, INK)
    cv.line(x0 + 206, y0 + 88, x0 + 236, y0 + 76, INK)
    # Red AI tag.
    cv.fill_rect(x0 + 248, y0 + 12, 52, 28, RED)
    cv.draw_text("AI", x0 + 262, y0 + 17, 2, WHITE)
    cv.rect(x0, y0, w, h, INK, 2)


def build():
    cv = Canvas(W, H, PAPER)

    # --- Masthead ---
    cv.draw_text_centered("THE WORLD IN ONE PAGE", W // 2, 20, 4, INK)
    cv.draw_text_centered("SUNDAY · 22 NOVEMBER 2026", W // 2, 80, 2, INK)
    cv.hline(40, 112, 944, INK, 3)
    cv.hline(40, 118, 944, INK, 1)

    # --- Lead: COP31 climate talks ---
    cv.draw_text("LEAD · CLIMATE", 40, 134, 2, RED)
    lead_head = "CLIMATE TALKS NEAR DEAL IN OVERTIME"
    y = 158
    for line in cv.wrap(lead_head, 600, 3):
        cv.draw_text(line, 40, y, 3, INK)
        y += 27
    y = 222
    for line in cv.wrap("NEW DRAFT DROPS FOSSIL FUELS. 200 NATIONS VOTE SUNDAY.", 600, 2):
        cv.draw_text(line, 40, y, 2, INK)
        y += 18
    draw_climate_art(cv, 660, 132, 324, 288)
    cv.draw_text_centered("CLIMATE SUMMIT IN ANTALYA, TURKEY", 660 + 162, 428, 1, INK)
    body = (
        "COP31 IN ANTALYA, TURKEY, RAN PAST ITS FRIDAY DEADLINE THROUGH "
        "SATURDAY INTO SUNDAY. EARLY SUNDAY, CO-PRESIDENTS TURKEY AND "
        "AUSTRALIA TABLED A NEW DRAFT DEAL AND CALLED A PLENARY VOTE "
        "FROM 0600 GMT.\n"
        "THE TEXT DROPS ANY MENTION OF FOSSIL FUELS, THE CAUSE OF GLOBAL "
        "WARMING. IT RECALLS THE COP28 PLEDGE INSTEAD, AND SETS A "
        "1 BILLION TONNE CARBON CAPTURE GOAL PLUS A 35% ELECTRICITY "
        "TARGET BY 2035.\n"
        "NEARLY 200 NATIONS MUST AGREE. PRESIDENT MURAT KURUM SAID THE "
        "TEXT WAS ONE ALL PARTIES COULD ACCEPT."
    )
    y = 280
    for para in body.split("\n"):
        for line in cv.wrap(para, 600, 2):
            cv.draw_text(line, 40, y, 2, INK)
            y += 18
        y += 10

    # --- Divider ---
    cv.hline(40, 560, 944, INK, 2)

    # --- Story 2: Seoul ---
    cv.draw_text("SEOUL", 40, 580, 2, RED)
    cv.draw_text("MINISTER QUITS OVER AI-CHEATING EXAM ROW", 40, 604, 2, INK)
    body2 = (
        "EDUCATION MINISTER CHOI KYO-JIN RESIGNED ON SUNDAY, TAKING BLAME "
        "FOR LAST-MINUTE ANTI-CHEATING RULES AT THE SUNEUNG EXAM.\n"
        "111 CANDIDATES WERE CAUGHT WITH SMART DEVICES; FIVE USED THEM. "
        "PRESIDENT LEE ORDERED AN OVERHAUL."
    )
    y = 634
    for para in body2.split("\n"):
        for line in cv.wrap(para, 600, 2):
            cv.draw_text(line, 40, y, 2, INK)
            y += 18
        y += 10
    draw_exam_art(cv, 660, 580, 324, 180)
    cv.draw_text_centered("SMART GLASSES AT THE SUNEUNG EXAM", 660 + 162, 768, 1, INK)

    # --- Divider ---
    cv.hline(40, 820, 944, INK, 2)

    # --- Markets strip ---
    cv.draw_text("MARKETS", 40, 840, 2, RED)
    cv.draw_text("BITCOIN REBOUNDS FROM TWO-YEAR LOW", 40, 864, 2, INK)
    y = 894
    for line in cv.wrap(
        "AFTER SATURDAY'S TWO-YEAR LOW OF $55,100, BITCOIN RECOVERED TO AROUND $59,500 ON SUNDAY, BRIEFLY TOPPING $60,000.",
        944, 2,
    ):
        cv.draw_text(line, 40, y, 2, INK)
        y += 18

    # --- Footer ---
    cv.hline(40, 950, 944, INK, 2)
    cv.draw_text_centered("SUNDAY 22 NOVEMBER 2026 · THE WORLD IN ONE PAGE", W // 2, 962, 1, INK)
    cv.draw_text_centered("SOURCES: REUTERS · AJP · COINPAPRIKA", W // 2, 978, 1, INK)

    return cv.px


def png_bytes(rgb, w, h):
    raw = b"".join(b"\x00" + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build(), W, H)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
