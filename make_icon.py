"""Generate a simple app icon for Cozy Games."""
import struct, zlib, math

W, H = 256, 256

pixels = []
for y in range(H):
    row = [0]  # filter byte
    for x in range(W):
        cx, cy = x - W//2, y - H//2
        d = math.sqrt(cx*cx + cy*cy) / (W//2)
        if d < 1:
            # gradient from warm beige to soft teal
            r = int(200 - d * 60)
            g = int(190 - d * 40)
            b = int(170 + d * 40)
        else:
            r = g = b = 245
        row.extend([b, g, r, 255])  # BGRA
    pixels.append(bytes(row))

def make_png(w, h, rows):
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    raw = b''.join(rows)
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend

png = make_png(W, H, pixels)
with open(r'C:\Users\Ultra Dell\Desktop\TETRIS\icon.png', 'wb') as f:
    f.write(png)
print("icon.png created")
