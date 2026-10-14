import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from collections import Counter, defaultdict
if len(sys.argv)<3: sys.exit('usage: ge_cmds.py <commands.bin> <pushbuf.bin>   (outputs of ge_extract.py)')
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
GE={0x00:'NOP',0x04:'PRIM',0x12:'VTYPE',0x13:'OFFSETADDR',0x14:'ORIGIN',0x15:'REGION1',
0x1D:'CULLFACEENABLE',0x1E:'TEXTUREMAPENABLE',0x2A:'BONEMATNUM',0x2B:'BONEMATDATA',0x3A:'WMATNUM',0x3B:'WMATDATA',0x3C:'VMATNUM',0x3D:'VMATDATA',0x42:'VPXSCALE',0x43:'VPYSCALE',
0x47:'VPZCENTER',0x48:'TEXSCALEU',0x49:'TEXSCALEV',0x4A:'TEXOFFU',0x4B:'TEXOFFV',
0x1A:'LIGHTENABLE2',0xA0:'TEXADDR0',0xA8:'TEXBUFW0',0xB8:'TEXSIZE0',0xBC:'?',0xC0:'TEXMAPMODE',
0xB0:'CLUTADDR',0xB1:'CLUTADDRU',0xC2:'TEXMODE',0xC3:'TEXFORMAT',0xC5:'CLUTFORMAT',0xC9:'TEXFUNC',0xCB:'TEXFLUSH',0x4D:'OFFSETY'}
for c in sorted(cnt):
    ss=' '.join('0x%06x'%v for v in sorted(samp[c])[:6])
    print(f"  GE 0x{c:02x} {GE.get(c,''):12} x{cnt[c]:<6} samples: {ss}")
