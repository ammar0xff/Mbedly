import math
import struct
import zlib

SIZE = 256
CX = CY = 128.0
R = 92.0


def in_triangle(px, py):
    x1, y1 = 100.0, 86.0
    x2, y2 = 100.0, 170.0
    x3, y3 = 176.0, 128.0
    d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    a = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / d
    b = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / d
    c = 1.0 - a - b
    return a >= 0 and b >= 0 and c >= 0


rows = []
for y in range(SIZE):
    row = bytearray()
    for x in range(SIZE):
        dist = math.hypot(x - CX, y - CY)
        if in_triangle(x, y):
            c = (0, 255, 65, 255)
        elif R - 3.5 <= dist < R:
            c = (0, 255, 65, 255)
        elif 5 <= R - dist < 5.5:
            c = (0, 255, 65, 255)
        elif dist < R:
            c = (10, 15, 12, 255)
        else:
            c = (10, 15, 12, 255)
        row += bytes(c)
    rows.append(b"\x00" + bytes(row))

raw = b"".join(rows)


def chunk(tag, data):
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


png = (
    b"\x89PNG\r\n\x1a\n"
    + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
    + chunk(b"IDAT", zlib.compress(raw, 9))
    + chunk(b"IEND", b"")
)
open("icon.png", "wb").write(png)
print("icon.png written (%d bytes)" % len(png))