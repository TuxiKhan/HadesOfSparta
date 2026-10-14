#!/usr/bin/env python3
"""Decode a PPSSPP GE frame dump -> OBJ. Separates skinned (character) draws from rigid.
Stdlib only (compression.zstd on Py3.14). Handles transform-mode tris/strips/fans,
position fmt s8/s16/float (normalized), skinning via GE bone-matrix palette + weights,
rigid via world matrix. UVs decoded when present."""
import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from compression import zstd

def load_dump(path):
    d=open(path,'rb').read()
    cc=struct.unpack_from('<I',d,0x18)[0]; psz=struct.unpack_from('<I',d,0x1c)[0]; csz=struct.unpack_from('<I',d,0x20)[0]
    commands=zstd.ZstdDecompressor().decompress(d[0x24:0x24+csz])
    zoff=d.find(b'\x28\xb5\x2f\xfd',0x24+csz)
    pushbuf=zstd.ZstdDecompressor().decompress(d[zoff:])
    return commands, pushbuf, cc

CSIZE={0:0,1:1,2:2,3:4}           # weight/normal/position/texcoord component byte size
def vfmt(vt):
    tc=vt&3; col=(vt>>2)&7; nrm=(vt>>5)&3; pos=(vt>>7)&3
    wfmt=(vt>>9)&3; idx=(vt>>11)&3; wcnt=((vt>>14)&7)+1 if (vt>>14)&7 else 0
    wcnt=((vt>>14)&7)+1 if ((vt>>14)&7) else 0
    morph=((vt>>18)&7)+1
    through=(vt>>23)&1
    csz={0:0,4:2,5:2,6:2,7:4}.get(col,0)
    ws=CSIZE[wfmt]; ts=CSIZE[tc]; ns=CSIZE[nrm]; ps=CSIZE[pos]
    off=0; align=1
    def place(sz,cnt):
        nonlocal off,align
        if sz==0: return None
        off=(off+sz-1)//sz*sz
        o=off; off+=sz*cnt; align=max(align,sz); return o
    woff=place(ws,wcnt)
    toff=place(ts,2)
    coff=place(csz,1) if csz else None
    noff=place(ns,3)
    poff=place(ps,3)
    if align: off=(off+align-1)//align*align
    stride=off
    return dict(stride=stride,pos=pos,poff=poff,tc=tc,toff=toff,wfmt=wfmt,wcnt=wcnt,woff=woff,
                nrm=nrm,through=through,morph=morph)

def rdfloat24(data):  # GE matrix data: 24-bit payload = top of float32
    return struct.unpack('<f', struct.pack('<I',(data&0xffffff)<<8))[0]

def matmul_point(m, x,y,z):  # m = 12 floats, column vectors (PSP 4x3): cols c0,c1,c2,c3
    return (m[0]*x+m[3]*y+m[6]*z+m[9],
            m[1]*x+m[4]*y+m[7]*z+m[10],
            m[2]*x+m[5]*y+m[8]*z+m[11])

def decode_pos(pb, base, fmt):
    if fmt==3:
        x,y,z=struct.unpack_from('<fff',pb,base); return x,y,z
    if fmt==2:
        x,y,z=struct.unpack_from('<hhh',pb,base); return x/32768.0,y/32768.0,z/32768.0
    if fmt==1:
        x,y,z=struct.unpack_from('<bbb',pb,base); return x/128.0,y/128.0,z/128.0
    return 0.0,0.0,0.0

def decode_w(pb, base, wfmt, wcnt):
    out=[]
    for i in range(wcnt):
        if wfmt==3: out.append(struct.unpack_from('<f',pb,base+i*4)[0])
        elif wfmt==2: out.append(struct.unpack_from('<H',pb,base+i*2)[0]/32768.0)
        elif wfmt==1: out.append(pb[base+i]/128.0)
    return out

def run(path, outdir):
    commands, pushbuf, ncmd = load_dump(path)
    os.makedirs(outdir, exist_ok=True)
    world=[1,0,0, 0,1,0, 0,0,1, 0,0,0]
    bones=[[1,0,0,0,1,0,0,0,1,0,0,0] for _ in range(8)]
    wptr=0; bptr=0; vtype=0
    last_vptr=last_vsz=0
    draws=[]   # each: (skinned, verts[list of (x,y,z)], faces[list of (a,b,c) 0-based within draw])
    for i in range(ncmd):
        o=i*9; t=commands[o]; sz=struct.unpack_from('<I',commands,o+1)[0]; ptr=struct.unpack_from('<I',commands,o+5)[0]
        if t==2:   # VERTICES
            last_vptr=ptr; last_vsz=sz
        elif t==1: # REGISTERS: stream of u32 GE cmds
            for k in range(sz//4):
                w=struct.unpack_from('<I',pushbuf,ptr+k*4)[0]; c=(w>>24)&0xff; dat=w&0xffffff
                if c==0x12: vtype=dat
                elif c==0x3c: wptr=dat
                elif c==0x3d:
                    if wptr<12: world[wptr]=rdfloat24(dat); wptr+=1
                elif c==0x42: bptr=dat
                elif c==0x43:
                    bi=bptr//12; bj=bptr%12
                    if bi<8: bones[bi][bj]=rdfloat24(dat)
                    bptr+=1
                elif c==0x04:  # PRIM
                    n=w&0xffff; pt=(w>>16)&7
                    if pt not in (3,4,5) or n<3: continue
                    f=vfmt(vtype)
                    if f['through'] or f['poff'] is None: continue
                    stride=f['stride']
                    if stride==0 or last_vptr+stride*n> len(pushbuf): continue
                    verts=[]
                    for vi in range(n):
                        bb=last_vptr+vi*stride
                        x,y,z=decode_pos(pushbuf, bb+f['poff'], f['pos'])
                        if f['wcnt']>0:
                            wts=decode_w(pushbuf, bb+f['woff'], f['wfmt'], f['wcnt'])
                            px=py=pz=0.0; ws=sum(wts) or 1.0
                            for bi,wv in enumerate(wts):
                                if wv==0: continue
                                tx,ty,tz=matmul_point(bones[bi],x,y,z)
                                px+=wv*tx; py+=wv*ty; pz+=wv*tz
                            verts.append((px/ws,py/ws,pz/ws))
                        else:
                            verts.append(matmul_point(world,x,y,z))
                    skinned=f['wcnt']>0
                    faces=[]
                    if pt==3:
                        for tri in range(0,n-n%3,3): faces.append((tri,tri+1,tri+2))
                    elif pt==4:
                        for s in range(n-2):
                            faces.append((s,s+1,s+2) if s%2==0 else (s+1,s,s+2))
                    elif pt==5:
                        for s in range(1,n-1): faces.append((0,s,s+1))
                    # drop draws with non-finite coords (bad/stale matrices)
                    if all(all(abs(c)<1e6 for c in v) for v in verts):
                        draws.append((skinned, verts, faces))
    def bbox(V):
        if not V: return None
        xs=[v[0] for v in V]; ys=[v[1] for v in V]; zs=[v[2] for v in V]
        return (round(min(xs),1),round(max(xs),1),round(min(ys),1),round(max(ys),1),round(min(zs),1),round(max(zs),1))
    def write_obj(p,drawset):
        V=[]; F=[]
        for _,verts,faces in drawset:
            b0=len(V)
            V.extend(verts)
            for a,b,c in faces: F.append((b0+a+1,b0+b+1,b0+c+1))
        with open(p,'w') as fh:
            for v in V: fh.write("v %.5f %.5f %.5f\n"%v)
            for t in F: fh.write("f %d %d %d\n"%t)
        return len(V),len(F),bbox(V)
    skin=[d for d in draws if d[0]]
    rigid=[d for d in draws if not d[0]]
    # Tukey-fence filter on skinned draw centroids to isolate the main body cluster
    def centroid(verts):
        n=len(verts);
        return (sum(v[0] for v in verts)/n, sum(v[1] for v in verts)/n, sum(v[2] for v in verts)/n)
    cents=[centroid(v) for _,v,_ in skin]
    def fence(vals):
        s=sorted(vals); n=len(s); q1=s[n//4]; q3=s[(3*n)//4]; iqr=q3-q1
        return q1-1.5*iqr, q3+1.5*iqr
    if cents:
        fx=fence([c[0] for c in cents]); fy=fence([c[1] for c in cents]); fz=fence([c[2] for c in cents])
        body=[d for d,c in zip(skin,cents) if fx[0]<=c[0]<=fx[1] and fy[0]<=c[1]<=fy[1] and fz[0]<=c[2]<=fz[1]]
    else:
        body=[]
    sa=write_obj(os.path.join(outdir,'kratos_skinned_all.obj'), skin)
    sb=write_obj(os.path.join(outdir,'kratos_body.obj'), body)
    write_obj(os.path.join(outdir,'rigid_world.obj'), rigid)
    print(f"SKINNED all : {len(skin)} draws -> {sa[0]} verts {sa[1]} tris bbox={sa[2]}")
    print(f"KRATOS body : {len(body)} draws -> {sb[0]} verts {sb[1]} tris bbox={sb[2]}")
    print(f"RIGID       : {len(rigid)} draws")
    print("-> kratos_body.obj (filtered), kratos_skinned_all.obj in", outdir)

if __name__=='__main__':
    run(sys.argv[1], sys.argv[2])
