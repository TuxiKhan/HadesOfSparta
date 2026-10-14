import sys, os, glob, struct, re, math
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from collections import Counter

def entropy(bs):
    if not bs: return 0
    c=Counter(bs); n=len(bs)
    return -sum((k/n)*math.log2(k/n) for k in c.values())

def classify(b):
    N=len(b)
    strs=[m.group().decode('latin1') for m in re.finditer(rb'[\x20-\x7e]{5,}', b)]
    # int16 triplet "vertex-like": many small-ish signed shorts
    # count fraction of int16 in [-4096,4096]
    sh=struct.unpack_from('<%dh'%(N//2), b, 0)
    small=sum(1 for v in sh if -8192<v<8192)
    frac=small/max(1,len(sh))
    H=entropy(b)
    tags=[]
    joined=' '.join(strs).lower()
    if 'scriptset' in joined or 'animation:' in joined: tags.append('SCRIPT/ANIM')
    if re.search(r'exp_[clr]\d', joined) or 'spine' in joined or 'pelvis' in joined: tags.append('SKELETON')
    if 'user data' in joined: tags.append('USERDATA')
    if frac>0.85 and H>3.5 and not tags: tags.append('?GEOM(int16?)')
    return N, H, round(frac,2), tags, strs[:3]

for p in sorted(glob.glob(os.path.join(sys.argv[1],'*CfCm*.blob'))):
    b=open(p,'rb').read()
    N,H,frac,tags,strs=classify(b)
    nm=os.path.basename(p)
    print(f"{nm:30} {N:6}b H={H:4.2f} i16f={frac:4} {','.join(tags) or '-':14} {strs}")
