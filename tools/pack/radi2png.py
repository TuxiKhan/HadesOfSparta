#!/usr/bin/env python3
"""RADI (Ready at Dawn image) -> PNG, for GoW PSP Pack blobs. Stdlib only.

RADI header (LE): 0x00 'RADI'; 0x04 u32 PSM (4=T4,5=T8); 0x0C u32 width; 0x10 u32 height;
0x14 u32 clut bit-depth(=32); 0x18 u32 index-data offset. CLUT (RGBA8888) sits at 0x20,
index data at 0x18. T8=256-color/8bpp, T4=16-color/4bpp.
"""
import sys, os, glob, struct, zlib

def u32(b,o): return struct.unpack_from('<I',b,o)[0]

def write_png(path, w, h, rgba):
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    raw = bytearray()
    for y in range(h):
        raw.append(0); raw += rgba[y*w*4:(y+1)*w*4]
    with open(path,'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', struct.pack('>IIBBBBB',w,h,8,6,0,0,0))
                + chunk(b'IDAT', zlib.compress(bytes(raw),9))
                + chunk(b'IEND', b''))

def unswizzle(data, w_bytes, h):
    """PSP GE swizzle: 16-byte-wide x 8-tall blocks laid out block-by-block."""
    out = bytearray(len(data))
    blocks_x = w_bytes // 16
    src = 0
    for by in range(h // 8):
        for bx in range(blocks_x):
            for row in range(8):
                dst = (by*8+row)*w_bytes + bx*16
                out[dst:dst+16] = data[src:src+16]; src += 16
    return bytes(out)

def clut_swap8(i):  # PSP 8-bit CLUT index reorder (swap bit3<->bit4 group)
    return (i & 0xE7) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)

def to_png(path, out_dir, deswizzle=False, clutswap=False):
    b = open(path,'rb').read()
    if b[:4]!=b'RADI': return None
    fmt=u32(b,0x04); w=u32(b,0x0C); h=u32(b,0x10); doff=u32(b,0x18)
    pal_n = 256 if fmt==5 else 16
    pal = [b[0x20+j*4:0x20+j*4+4] for j in range(pal_n)]  # RGBA8888
    idx_bytes = w*h if fmt==5 else w*h//2
    data = b[doff:doff+idx_bytes]
    if deswizzle:
        wb = w if fmt==5 else w//2
        data = unswizzle(data, wb, h)
    rgba = bytearray(w*h*4)
    for i in range(w*h):
        if fmt==5:
            ci = data[i]
            if clutswap: ci = clut_swap8(ci)
        else:
            byte = data[i>>1]
            ci = (byte & 0x0F) if (i & 1)==0 else (byte >> 4)
        rgba[i*4:i*4+4] = pal[ci]
    os.makedirs(out_dir, exist_ok=True)
    name = os.path.splitext(os.path.basename(path))[0] + f"_{w}x{h}.png"
    outp = os.path.join(out_dir, name)
    write_png(outp, w, h, rgba)
    return outp, fmt, w, h

if __name__=='__main__':
    src, out = sys.argv[1], sys.argv[2]
    de = '--unswizzle' in sys.argv
    cs = '--clut-swap' in sys.argv
    files = glob.glob(os.path.join(src,'*RADI*.blob')) if os.path.isdir(src) else [src]
    for p in sorted(files):
        r = to_png(p, out, de, cs)
        if r: print(f"  {os.path.basename(r[0])}  (PSM{r[1]} {r[2]}x{r[3]})")
    print(f"done -> {out}  (unswizzle={de} clutswap={cs})")
