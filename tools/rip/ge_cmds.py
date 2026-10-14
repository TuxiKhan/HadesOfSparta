import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from collections import Counter, defaultdict
commands=open(sys.argv[1],'rb').read(); pushbuf=open(sys.argv[2],'rb').read()
ncmd=len(commands)//9
cnt=Counter(); samp=defaultdict(set)
for i in range(ncmd):
    o=i*9; t=commands[o]
    if t!=1: continue
    sz=struct.unpack_from('<I',commands,o+1)[0]; ptr=struct.unpack_from('<I',commands,o+5)[0]
    for k in range(sz//4):
        w=struct.unpack_from('<I',pushbuf,ptr+k*4)[0]; c=(w>>24)&0xff; d=w&0xffffff
        cnt[c]+=1
        if len(samp[c])<6: samp[c].add(d)
# known GE command names
GE={0x00:'NOP',0x04:'PRIM',0x12:'VTYPE',0x13:'OFFSETADDR',0x15:'ORIGIN',0x18:'DRAWREGION1',
0x1E:'CULL',0x21:'LIGHTING',0x3A:'?',0x3C:'WMATNUM',0x3D:'WMATDATA',0x42:'BONEMATNUM',0x43:'BONEMATDATA',
0x47:'?',0x48:'?',0xAB:'TEXSCALEU',0xAC:'TEXSCALEV',0xAD:'TEXOFFU',0xAE:'TEXOFFV',
0x1A:'?',0xA0:'TEXADDR0',0xA8:'TEXBUFW0',0xB8:'TEXSIZE0',0xBC:'?',0xC0:'TEXFLUSH',
0xB0:'CLUTADDR',0xB1:'CLUTADDRU',0xC8:'TEXFORMAT?',0xC9:'CLUTFORMAT?',0x4D:'?'}
for c in sorted(cnt):
    ss=' '.join('0x%06x'%v for v in sorted(samp[c])[:6])
    print(f"  GE 0x{c:02x} {GE.get(c,''):12} x{cnt[c]:<6} samples: {ss}")
