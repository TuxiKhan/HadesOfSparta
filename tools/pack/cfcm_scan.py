import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
b=open(sys.argv[1],'rb').read()
N=len(b)
print(f"size={N}")

# 1) find ascii strings
import re
print("-- ascii strings >=4 --")
for m in re.finditer(rb'[\x20-\x7e]{4,}', b):
    print(f"  0x{m.start():04X}: {m.group().decode('latin1')!r}")

# 2) scan for runs of plausible float32 vertex coords (|v| in [1e-3, 1e4])
def plausible(f):
    import math
    if f!=f: return False
    a=abs(f)
    return a==0 or (1e-3 < a < 1e4)
print("\n-- float32 runs (>=12 consecutive plausible, i.e. >=4 verts-ish) --")
o=0; runs=[]
while o+4<=N:
    f=struct.unpack_from('<f',b,o)[0]
    if plausible(f):
        s=o; cnt=0
        while o+4<=N:
            f=struct.unpack_from('<f',b,o)[0]
            if plausible(f): cnt+=1; o+=4
            else: break
        if cnt>=12: runs.append((s,cnt))
    else: o+=4
for s,c in runs[:20]:
    sample=[round(struct.unpack_from('<f',b,s+i*4)[0],3) for i in range(min(9,c))]
    print(f"  0x{s:04X}: {c} floats  sample={sample}")

# 3) entropy by 256-byte window (to spot compressed vs structured)
print("\n-- byte entropy per 256B window --")
import math
for w in range(0,N,256):
    chunk=b[w:w+256]
    if not chunk: break
    from collections import Counter
    c=Counter(chunk); e=-sum((n/len(chunk))*math.log2(n/len(chunk)) for n in c.values())
    bar='#'*int(e)
    print(f"  0x{w:04X}: H={e:4.2f} {bar}")
