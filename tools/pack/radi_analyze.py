import sys, os, struct, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# PSP GU pixel storage modes
PSM = {0:'5650',1:'5551',2:'4444',3:'8888',4:'T4',5:'T8',6:'T16',7:'T32',
       8:'DXT1',9:'DXT3',10:'DXT5'}

def u32(b,o): return struct.unpack_from('<I',b,o)[0]

for path in sorted(glob.glob(os.path.join(sys.argv[1], '*RADI*.blob'))):
    b = open(path,'rb').read()
    assert b[:4]==b'RADI'
    fmt  = u32(b,0x04)
    f08  = u32(b,0x08)
    w    = u32(b,0x0C)
    h    = u32(b,0x10)
    f14  = u32(b,0x14)
    dataoff = u32(b,0x18)
    name = b[0x1C:0x20].split(b'\x00')[0].decode('latin1')
    size = len(b)
    # hypothesis: header+palette then index data at dataoff
    palbytes = dataoff - 0x20
    palentries = palbytes // 4
    idxbytes = size - dataoff
    # expected index bytes for given format
    if fmt==5:   exp = w*h          # 8bpp
    elif fmt==4: exp = w*h//2       # 4bpp
    elif fmt==3: exp = w*h*4        # 32bpp (no pal)
    elif fmt in (0,1,2): exp = w*h*2
    else: exp = None
    ok = (exp==idxbytes) if exp is not None else '?'
    print(f"{os.path.basename(path):28} fmt={fmt}({PSM.get(fmt,'?')}) {w}x{h} "
          f"f08={f08} f14={f14} dataoff=0x{dataoff:x} pal={palentries}e({palbytes}b) "
          f"idx={idxbytes}b exp={exp} match={ok} name={name!r}")
