import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
b = open(sys.argv[1],'rb').read()
n = int(sys.argv[2]) if len(sys.argv)>2 else 160
print(f"size={len(b)} (0x{len(b):X}) magic={b[:4]!r}")
print("\n-- hex + u32/f32 interpretation of first words --")
for o in range(0, min(n,len(b)-3), 4):
    w = struct.unpack_from('<I', b, o)[0]
    f = struct.unpack_from('<f', b, o)[0]
    h = ' '.join('%02X'%c for c in b[o:o+4])
    fstr = f"{f: .4g}" if (abs(f)>1e-6 and abs(f)<1e6) else ""
    print(f"  0x{o:03X}: {h}  u32={w:<11} f32={fstr}")
print("\n-- full hex (first %d) --" % n)
for o in range(0, min(n,len(b)), 16):
    ch=b[o:o+16]
    hx=' '.join('%02X'%c for c in ch)
    asc=''.join(chr(c) if 32<=c<=126 else '.' for c in ch)
    print(f"  {o:04X}  {hx:<47}  {asc}")
