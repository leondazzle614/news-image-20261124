#!/usr/bin/env python3
"""Draw one image summing up Tuesday 24 November 2026's world news.

A Python 3.13 standard-library-only program. It draws a newspaper front
page -- masthead, date bar, one lead story, five more stories in a grid and
a ticker of further news -- onto a 1024x1024 canvas and writes it as a PNG
to $MAKEFUN_OUTPUT_DIR/entry.png (or out/entry.png). No network, no clock,
no randomness: two runs write identical bytes.

Stories (all first reported Tuesday 24 November 2026, verified against
real reporting that day):
  lead  Russian strike on Zaporizhzhia kills 2, wounds ~40 incl. children
  1     Israeli strikes kill Hamas security chief Naeem Abu Nahel in Gaza
  2     Record Iranian attacks in the Strait of Hormuz; US blockade holds
  3     Blast at a Hanoi hot pot eatery kills six
  4     Oregon and Virginia sue SpaceX over Grok-generated images
  5     Moscow says it downed nearly 700 Ukrainian drones overnight
Ticker: COP31 post-mortem, Nvidia brings back Jensen Huang, Nepal 5.4
quake, Russian jets enter South Korea's air zone, Spain votes Sunday,
Merz says Europe is ready to talk with Russia.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (251, 248, 240)
INK = (26, 26, 26)
RED = (176, 30, 36)
DARKRED = (128, 20, 25)
GREY = (110, 108, 100)
LIGHT = (238, 233, 220)
BLUE = (31, 58, 95)
GOLD = (176, 132, 40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ---------------------------------------------------------------- font ----
# 5x7 bitmap font. Each glyph is 7 rows; each row is a 5-bit value, bit 4
# (0x10) is the leftmost pixel. Lowercase letters sit on the same 7-row
# cell with a one-row x-height offset where natural.

FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    'a': (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    'b': (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x1E),
    'c': (0x00, 0x00, 0x0E, 0x10, 0x10, 0x10, 0x0E),
    'd': (0x01, 0x01, 0x0D, 0x13, 0x11, 0x11, 0x0F),
    'e': (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    'f': (0x06, 0x08, 0x08, 0x1E, 0x08, 0x08, 0x08),
    'g': (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'h': (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x11),
    'i': (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    'j': (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    'k': (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    'l': (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'm': (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    'n': (0x00, 0x00, 0x16, 0x19, 0x11, 0x11, 0x11),
    'o': (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    'p': (0x00, 0x00, 0x1E, 0x11, 0x1E, 0x10, 0x10),
    'q': (0x00, 0x00, 0x0D, 0x13, 0x0F, 0x01, 0x01),
    'r': (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    's': (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    't': (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    'u': (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    'v': (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'w': (0x00, 0x00, 0x11, 0x15, 0x15, 0x15, 0x0A),
    'x': (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    'y': (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'z': (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ',': (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ':': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ';': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    '-': (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '+': (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    '=': (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '*': (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    '~': (0x00, 0x00, 0x00, 0x0E, 0x15, 0x00, 0x00),
    '<': (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    '>': (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    '[': (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
    ']': (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
    '_': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
    '@': (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    '|': (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
}
# The bullet used in the ticker and the em dash both render as drawn marks.
FONT['\u2022'] = (0x00, 0x00, 0x04, 0x0E, 0x0E, 0x04, 0x00)
FONT['\u2014'] = (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00)
FONT['\u2019'] = FONT["'"]
FONT['\u201c'] = FONT['"']
FONT['\u201d'] = FONT['"']

CHAR_W, CHAR_H = 6, 8  # advance and line height, in font units


def text_width(text, scale):
    return len(text) * CHAR_W * scale


def wrap_text(text, scale, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    max_chars = max(1, max_w // (CHAR_W * scale))
    lines = []
    for para in text.split('\n'):
        words = para.split(' ')
        cur = ''
        for word in words:
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= max_chars:
                cur += ' ' + word
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0, y0, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self._set(xx, yy, color)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self._set(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        # Filled triangle via scanline fill.
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        def interp(y, p, q):
            if q[1] == p[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])
        for y in range(ay, cy + 1):
            if y < by:
                xa, xb = interp(y, (ax, ay), (bx, by)), interp(y, (ax, ay), (cx, cy))
            else:
                xa, xb = interp(y, (bx, by), (cx, cy)), interp(y, (ax, ay), (cx, cy))
            self.fill_rect(int(min(xa, xb)), y, int(abs(xb - xa)) + 1, 1, color)

    def draw_char(self, x, y, ch, scale, color):
        glyph = FONT.get(ch, FONT['?'])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (0x10 >> col):
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            self.draw_char(cx, y, ch, scale, color)
            cx += CHAR_W * scale
        return cx

    def draw_text_center(self, x, y, w, text, scale, color):
        tw = text_width(text, scale)
        self.draw_text(x + (w - tw) // 2, y, text, scale, color)

    def draw_lines(self, x, y, lines, scale, color, leading=None):
        lh = CHAR_H * scale if leading is None else leading
        for i, ln in enumerate(lines):
            self.draw_text(x, y + i * lh, ln, scale, color)
        return y + len(lines) * lh


# ----------------------------------------------------------------- png ----
def _chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        i = y * canvas.w * 3
        raw += canvas.px[i:i + canvas.w * 3]
    ihdr = struct.pack('>IIBBBBB', canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n'
           + _chunk(b'IHDR', ihdr)
           + _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + _chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- icons ----
def icon_explosion(c, x, y, s, col):
    """Starburst: rays from a centre blob, with flying debris dots."""
    import math
    cx, cy = x + s // 2, y + s // 2
    c.circle(cx, cy, s // 6, col, fill=True)
    c.circle(cx - s // 10, cy - s // 12, s // 12, col, fill=True)
    c.circle(cx + s // 9, cy + s // 10, s // 14, col, fill=True)
    for k in range(12):
        rad = math.radians(k * 30)
        r1 = s // 5
        r2 = s // 2 if k % 2 == 0 else s // 3
        c.line(cx + int(r1 * math.cos(rad)), cy + int(r1 * math.sin(rad)),
               cx + int(r2 * math.cos(rad)), cy + int(r2 * math.sin(rad)),
               col, t=max(2, s // 28))
    for dx, dy, r in ((-s // 3, -s // 4, 3), (s // 3, -s // 3, 2),
                      (-s // 4, s // 3, 2), (s // 3, s // 4, 3)):
        c.circle(cx + dx, cy + dy, max(2, r * s // 96), col, fill=True)


def icon_building(c, x, y, s, col):
    """A tall block with windows and a jagged crack down its side."""
    bw, bh = s * 3 // 5, s * 4 // 5
    bx, by = x + s // 5, y + s // 10
    c.rect(bx, by, bw, bh, col, t=max(2, s // 32))
    for r in range(3):
        for cc in range(2):
            wx = bx + bw // 4 + cc * bw // 2 - s // 24
            wy = by + bh // 5 + r * bh // 4
            c.fill_rect(wx, wy, s // 12, s // 12, col)
    c.line(bx + bw // 2, by, bx + bw // 2 - s // 12, by + bh // 3,
           col, t=max(2, s // 32))
    c.line(bx + bw // 2 - s // 12, by + bh // 3, bx + bw // 2 + s // 14,
           by + 2 * bh // 3, col, t=max(2, s // 32))
    c.line(bx + bw // 2 + s // 14, by + 2 * bh // 3, bx + bw // 2 - s // 16,
           by + bh, col, t=max(2, s // 32))
    c.fill_rect(bx - s // 10, by + bh, bw + s // 5, s // 16, col)


def icon_ship(c, x, y, s, col):
    """A tanker on waves: hull, bridge tower, two wave lines."""
    hx, hy = x + s // 8, y + s // 3
    hw, hh = s * 3 // 4, s // 5
    c.triangle(hx, hy, hx + hw, hy, hx + hw - s // 8, hy + hh, col)
    c.fill_rect(hx + s // 10, hy + hh, hw - s // 4, s // 12, col)
    c.fill_rect(hx + hw // 2, hy - s // 6, s // 8, s // 6, col)
    c.fill_rect(hx + hw // 2 + s // 24, hy - s // 4, s // 24, s // 12, col)
    for wy in (y + 2 * s // 3, y + 5 * s // 6):
        for k in range(3):
            wx = x + s // 8 + k * s // 4
            c.line(wx, wy, wx + s // 8, wy - s // 16, col, t=max(2, s // 32))
            c.line(wx + s // 8, wy - s // 16, wx + s // 4, wy, col,
                   t=max(2, s // 32))


def icon_flame(c, x, y, s, col):
    """A flame: outer teardrop, inner flame, small base line."""
    cx = x + s // 2
    c.circle(cx, y + s // 2, s // 4, col, fill=True)
    c.triangle(cx - s // 4, y + s // 2, cx + s // 4, y + s // 2,
               cx, y + s // 10, col)
    c.circle(cx, y + 2 * s // 3, s // 8, PAPER, fill=True)
    c.triangle(cx - s // 8, y + 2 * s // 3, cx + s // 8, y + 2 * s // 3,
               cx, y + s // 2, PAPER)
    c.fill_rect(x + s // 6, y + 5 * s // 6, s * 2 // 3, s // 16, col)


def icon_court(c, x, y, s, col):
    """A courthouse front: pediment roof, three columns, steps."""
    c.triangle(x + s // 10, y + s // 4, x + 9 * s // 10, y + s // 4,
               x + s // 2, y + s // 12, col)
    c.fill_rect(x + s // 10, y + s // 4, s * 4 // 5, s // 14, col)
    for k in range(3):
        cx = x + s // 4 + k * s // 4
        c.fill_rect(cx - s // 24, y + s // 3, s // 12, s // 3, col)
    c.fill_rect(x + s // 8, y + 2 * s // 3, s * 3 // 4, s // 16, col)
    c.fill_rect(x + s // 6, y + 2 * s // 3 + s // 12, s * 2 // 3, s // 16, col)


def icon_drone(c, x, y, s, col):
    """A quadcopter drone: body, four arms, four rotor discs."""
    cx, cy = x + s // 2, y + s // 2
    arm = s // 3
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        c.line(cx, cy, cx + dx * arm, cy + dy * arm, col, t=max(2, s // 28))
        rx, ry = cx + dx * arm, cy + dy * arm
        c.circle(rx, ry, s // 10, col)
        c.fill_rect(rx - s // 6, ry - max(1, s // 48), s // 3,
                    max(2, s // 24), col)
    c.fill_rect(cx - s // 8, cy - s // 10, s // 4, s // 5, col)
    c.circle(cx, cy, s // 16, PAPER, fill=True)


# -------------------------------------------------------------- layout ----
M = 28
CW = W - 2 * M  # 968


def draw_page():
    c = Canvas(W, H, PAPER)

    # ---- masthead ----
    c.hline(M, 18, CW, INK, 3)
    c.draw_text_center(0, 30, W, "THE WORLD IN ONE DAY", 6, INK)
    c.draw_text_center(0, 80, W, "ONE DAY  \u2022  ONE PAGE  \u2022  THE WHOLE WORLD",
                       2, GREY)
    c.hline(M, 100, CW, INK, 2)
    c.hline(M, 105, CW, INK, 1)

    # ---- red date bar ----
    c.fill_rect(M, 112, CW, 34, RED)
    c.draw_text_center(M, 118, CW,
                       "TUESDAY, 24 NOVEMBER 2026 \u2014 WORLD NEWS",
                       3, WHITE)

    # ---- lead story ----
    lead_x = M
    lead_w = 612
    c.draw_text(lead_x, 162, "UKRAINE \u2014 WAR IN EUROPE", 2, RED)
    lead_head = wrap_text("RUSSIAN STRIKE KILLS 2, WOUNDS 40 IN ZAPORIZHZHIA",
                          4, lead_w)
    c.draw_lines(lead_x, 190, lead_head, 4, INK, leading=32)
    c.hline(lead_x, 266, lead_w, INK, 2)
    lead_sum = wrap_text(
        "An overnight Russian attack strikes an apartment block in the "
        "southern Ukrainian city of Zaporizhzhia, killing two people and "
        "wounding about 40, including four children, officials say.",
        2, lead_w)
    c.draw_lines(lead_x, 280, lead_sum, 2, INK, leading=18)
    c.draw_text(lead_x, 366, "2 KILLED  \u2022  ABOUT 40 WOUNDED  \u2022  4 CHILDREN HURT",
                2, RED)

    # lead picture box, right of the lead text
    pic_x, pic_y, pic_w, pic_h = 664, 158, 332, 246
    c.fill_rect(pic_x, pic_y, pic_w, pic_h, LIGHT)
    c.rect(pic_x, pic_y, pic_w, pic_h, INK, 2)
    icon_explosion(c, pic_x + 66, pic_y + 14, 200, RED)
    c.draw_text_center(pic_x, pic_y + pic_h - 28, pic_w,
                       "ZAPORIZHZHIA, UKRAINE", 2, INK)

    c.hline(M, 416, CW, INK, 2)

    # ---- grid of five stories ----
    stories = [
        ("GAZA \u2014 WAR", "ISRAELI STRIKES KILL HAMAS SECURITY CHIEF",
         "Airstrikes kill Naeem Abu Nahel, the director of Hamas's "
         "internal security, and six others in Gaza.",
         icon_building),
        ("THE GULF", "IRAN TENSIONS RISE IN THE STRAIT",
         "Britain logs a record run of Iranian attacks in the Strait of "
         "Hormuz as a US naval blockade holds.",
         icon_ship),
        ("VIETNAM", "BLAST AT HANOI EATERY KILLS SIX",
         "A suspected gas blast tears through a hot pot restaurant in the "
         "capital, injuring more than a dozen.",
         icon_flame),
        ("UNITED STATES", "STATES SUE SPACEX OVER GROK IMAGES",
         "Oregon and Virginia sue SpaceX, alleging its Grok chatbot "
         "generated child sexual abuse images.",
         icon_court),
        ("RUSSIA \u2014 UKRAINE", "MOSCOW SAYS IT DOWNED 700 DRONES",
         "Russia says it shot down nearly 700 Ukrainian drones overnight, "
         "across a wide area including the Moscow region and Crimea.",
         icon_drone),
    ]

    def draw_cell(x, y, w, story):
        kicker, head, summ, icon = story
        c.fill_rect(x, y + 12, 56, 56, LIGHT)
        c.rect(x, y + 12, 56, 56, INK, 2)
        icon(c, x + 3, y + 15, 50, RED)
        c.draw_text(x + 68, y + 16, kicker, 2, RED)
        c.draw_text(x + 68, y + 40, "24 NOV 2026", 2, GREY)
        head_lines = wrap_text(head, 3, w)
        c.draw_lines(x, y + 80, head_lines, 3, INK, leading=22)
        summ_lines = wrap_text(summ, 2, w)
        c.draw_lines(x, y + 86 + len(head_lines) * 22, summ_lines,
                     2, INK, leading=16)

    row1_y, row2_y = 428, 656
    row_h = 220
    cells1 = [(M, 316), (354, 316), (680, 316)]
    cells2 = [(M, 479), (517, 479)]
    for (x, w), story in zip(cells1, stories[:3]):
        draw_cell(x, row1_y, w, story)
    for (x, w), story in zip(cells2, stories[3:]):
        draw_cell(x, row2_y, w, story)
    # vertical dividers between cells, horizontal rule between rows
    for x in (346, 672):
        c.vline(x, row1_y + 8, row_h - 16, GREY, 1)
    c.vline(509, row2_y + 8, row_h - 16, GREY, 1)
    c.hline(M, 652, CW, GREY, 1)

    # ---- ticker ----
    tick_y = 884
    c.fill_rect(M, tick_y, CW, 76, BLACK)
    ticker = [
        "ALSO TODAY: COP31 POST-MORTEM \u2014 FIRST FAILED CLIMATE SUMMIT SINCE 2009",
        "NVIDIA BRINGS BACK JENSEN HUANG \u2022 5.4 QUAKE SHAKES NEPAL \u2022 SPAIN VOTES SUNDAY",
        "RUSSIAN JETS ENTER S. KOREA AIR ZONE \u2022 MERZ: EUROPE READY TO TALK TO RUSSIA",
    ]
    for i, line in enumerate(ticker):
        c.draw_text_center(M, tick_y + 10 + i * 20, CW, line, 2, WHITE)

    # ---- footer ----
    c.draw_text_center(0, 976, W,
                       "THE WORLD IN ONE DAY \u2022 ALL STORIES FIRST REPORTED "
                       "TUESDAY 24 NOVEMBER 2026",
                       2, GREY)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(draw_page(), path)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
