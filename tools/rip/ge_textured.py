#!/usr/bin/env python3
"""PPSSPP GE dump -> textured Kratos: OBJ+MTL+PNG textures and glTF (positions+UV+texture).
Skinned (character) draws only, world-space posed. Stdlib only."""
import sys, os, struct, zlib, hashlib, json, base64
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from compression import zstd

def load(path):
    d=open(path,'rb').read()
    cc=struct.unpack_from('<I',d,0x18)[0]; csz=struct.unpack_from('<I',d,0x20)[0]
    commands=zstd.ZstdDecompressor().decompress(d[0x24:0x24+csz])
    zoff=d.find(b'\x28\xb5\x2f\xfd',0x24+csz)
    pushbuf=zstd.ZstdDecompressor().decompress(d[zoff:])
    return commands,pushbuf,cc

CSZ={0:0,1:1,2:2,3:4}
def vfmt(vt):
    tc=vt&3; col=(vt>>2)&7; nrm=(vt>>5)&3; pos=(vt>>7)&3; wfmt=(vt>>9)&3
    wcnt=((vt>>14)&7)+1 if ((vt>>14)&7) else 0; through=(vt>>23)&1
    csz={0:0,4:2,5:2,6:2,7:4}.get(col,0)
    ws=CSZ[wfmt]; ts=CSZ[tc]; ns=CSZ[nrm]; ps=CSZ[pos]
    off=0; align=1
    def place(sz,cnt):
        nonlocal off,align
        if sz==0: return None
        off=(off+sz-1)//sz*sz; o=off; off+=sz*cnt; align=max(align,sz); return o
    woff=place(ws,wcnt); toff=place(ts,2); coff=place(csz,1) if csz else None
    noff=place(ns,3); poff=place(ps,3)
    if align: off=(off+align-1)//align*align
    return dict(stride=off,pos=pos,poff=poff,tc=tc,toff=toff,wfmt=wfmt,wcnt=wcnt,woff=woff,through=through)

def f24(d): return struct.unpack('<f',struct.pack('<I',(d&0xffffff)<<8))[0]
def mp(m,x,y,z): return (m[0]*x+m[3]*y+m[6]*z+m[9], m[1]*x+m[4]*y+m[7]*z+m[10], m[2]*x+m[5]*y+m[8]*z+m[11])
def dpos(pb,b,f):
    if f==3: return struct.unpack_from('<fff',pb,b)
    if f==2: x,y,z=struct.unpack_from('<hhh',pb,b); return x/32768,y/32768,z/32768
    if f==1: x,y,z=struct.unpack_from('<bbb',pb,b); return x/128,y/128,z/128
    return 0.,0.,0.
def duv(pb,b,f):
    if f==3: return struct.unpack_from('<ff',pb,b)
    if f==2: u,v=struct.unpack_from('<HH',pb,b); return u/32768,v/32768
    if f==1: u,v=struct.unpack_from('<BB',pb,b); return u/128,v/128
    return 0.,0.
def dw(pb,b,wf,wc):
    out=[]
    for i in range(wc):
        if wf==3: out.append(struct.unpack_from('<f',pb,b+i*4)[0])
        elif wf==2: out.append(struct.unpack_from('<H',pb,b+i*2)[0]/32768)
        elif wf==1: out.append(pb[b+i]/128)
    return out

def unswz(data,wb,h):
    if wb%16 or h%8 or len(data)<wb*h: return data
    out=bytearray(len(data)); bx=wb//16; s=0
    for by in range(h//8):
        for b in range(bx):
            for r in range(8):
                dst=(by*8+r)*wb+b*16; out[dst:dst+16]=data[s:s+16]; s+=16
    return bytes(out)

def clut_rgba(clut, cfmt, i):
    # cfmt low 2 bits: 0=5650,1=5551,2=4444,3=8888
    pf=cfmt&3
    if pf==3:
        o=i*4
        if o+4>len(clut): return (0,0,0,0)
        return tuple(clut[o:o+4])
    o=i*2
    if o+2>len(clut): return (0,0,0,0)
    v=clut[o]|(clut[o+1]<<8)
    if pf==0: r=(v&0x1f)<<3; g=((v>>5)&0x3f)<<2; b=((v>>11)&0x1f)<<3; a=255
    elif pf==1: r=(v&0x1f)<<3; g=((v>>5)&0x1f)<<3; b=((v>>10)&0x1f)<<3; a=255 if (v>>15) else 0
    else: r=(v&0xf)<<4; g=((v>>4)&0xf)<<4; b=((v>>8)&0xf)<<4; a=((v>>12)&0xf)<<4
    return (r,g,b,a)

def decode_tex(tex, w, h, fmt, swizzle, clut, cfmt):
    rgba=bytearray(w*h*4)
    if fmt in (4,5):
        palcount=256 if fmt==5 else 16
        bper=len(clut)//palcount if palcount else 0
        if bper==4: cfmt=3            # RGBA8888 CLUT (inferred from entry size)
        elif bper==2 and (cfmt&3)==3: cfmt=1
        bpp=4 if fmt==4 else 8
        wb=w*bpp//8
        data=unswz(tex,wb,h) if swizzle else tex
        for i in range(w*h):
            if fmt==5:
                if i>=len(data): break
                ci=data[i]
            else:
                bi=i>>1
                if bi>=len(data): break
                ci=(data[bi]&0xf) if (i&1)==0 else (data[bi]>>4)
            rgba[i*4:i*4+4]=bytes(clut_rgba(clut,cfmt,ci))
    elif fmt==3:
        data=unswz(tex,w*4,h) if swizzle else tex
        rgba[:min(len(data),w*h*4)]=data[:w*h*4]
    elif fmt==0:
        data=unswz(tex,w*2,h) if swizzle else tex
        for i in range(w*h):
            if i*2+2>len(data): break
            v=data[i*2]|(data[i*2+1]<<8)
            rgba[i*4]= (v&0x1f)<<3; rgba[i*4+1]=((v>>5)&0x3f)<<2; rgba[i*4+2]=((v>>11)&0x1f)<<3; rgba[i*4+3]=255
    return bytes(rgba)

def wpng(path,w,h,rgba):
    def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    raw=bytearray()
    for y in range(h): raw.append(0); raw+=rgba[y*w*4:(y+1)*w*4]
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+ch(b'IDAT',zlib.compress(bytes(raw),9))+ch(b'IEND',b''))

def run(path,outdir):
    commands,pb,nc=load(path); os.makedirs(outdir,exist_ok=True)
    texdir=os.path.join(outdir,'textures'); os.makedirs(texdir,exist_ok=True)
    world=[1,0,0,0,1,0,0,0,1,0,0,0]; bones=[[1,0,0,0,1,0,0,0,1,0,0,0] for _ in range(8)]
    wptr=bptr=vtype=0; texfmt=0; texwexp=texhexp=0; swizzle=0; cfmt=3
    last_v=last_t=last_tsz=last_c=last_csz=0
    draws=[]; texcache={}; tex_list=[]
    for i in range(nc):
        o=i*9; t=commands[o]; sz=struct.unpack_from('<I',commands,o+1)[0]; ptr=struct.unpack_from('<I',commands,o+5)[0]
        if t==2: last_v=ptr
        elif t==16: last_t=ptr; last_tsz=sz
        elif t==4: last_c=ptr; last_csz=sz
        elif t==1:
            for k in range(sz//4):
                w=struct.unpack_from('<I',pb,ptr+k*4)[0]; c=(w>>24)&0xff; d=w&0xffffff
                if c==0x12: vtype=d
                elif c==0x3c: wptr=d
                elif c==0x3d:
                    if wptr<12: world[wptr]=f24(d); wptr+=1
                elif c==0x42: bptr=d
                elif c==0x43:
                    bi=bptr//12
                    if bi<8: bones[bi][bptr%12]=f24(d)
                    bptr+=1
                elif c==0xc3: texfmt=d&0xf
                elif c==0xb8: texwexp=d&0xff; texhexp=(d>>8)&0xff
                elif c==0xc2: swizzle=d&1
                elif c==0xc9: cfmt=(d&3)
                elif c==0x04:
                    n=w&0xffff; pt=(w>>16)&7
                    if pt not in (3,4,5) or n<3: continue
                    f=vfmt(vtype)
                    if f['through'] or f['poff'] is None or f['wcnt']==0: continue
                    st=f['stride']
                    if st==0 or last_v+st*n>len(pb): continue
                    tw=1<<texwexp if texwexp<=11 else 0; th=1<<texhexp if texhexp<=11 else 0
                    tkey=None
                    if tw and th and last_tsz:
                        tdata=pb[last_t:last_t+last_tsz]
                        cdata=pb[last_c:last_c+last_csz] if last_csz else b''
                        h=hashlib.md5(tdata+cdata+bytes([texfmt,swizzle,cfmt])+struct.pack('<HH',tw,th)).hexdigest()[:10]
                        if h not in texcache:
                            idx=len(tex_list); texcache[h]=idx
                            tex_list.append((h,tdata,tw,th,texfmt,swizzle,cdata,cfmt))
                        tkey=texcache[h]
                    V=[]; UV=[]
                    for vi in range(n):
                        bb=last_v+vi*st
                        x,y,z=dpos(pb,bb+f['poff'],f['pos'])
                        wts=dw(pb,bb+f['woff'],f['wfmt'],f['wcnt']); ws=sum(wts) or 1.
                        px=py=pz=0.
                        for bi2,wv in enumerate(wts):
                            if wv==0: continue
                            tx,ty,tz=mp(bones[bi2],x,y,z); px+=wv*tx; py+=wv*ty; pz+=wv*tz
                        V.append((px/ws,py/ws,pz/ws))
                        UV.append(duv(pb,bb+f['toff'],f['tc']) if f['toff'] is not None else (0.,0.))
                    if not all(all(abs(cc)<1e6 for cc in v) for v in V): continue
                    faces=[]
                    if pt==3:
                        for tr in range(0,n-n%3,3): faces.append((tr,tr+1,tr+2))
                    elif pt==4:
                        for s in range(n-2): faces.append((s,s+1,s+2) if s%2==0 else (s+1,s,s+2))
                    elif pt==5:
                        for s in range(1,n-1): faces.append((0,s,s+1))
                    draws.append((V,UV,faces,tkey))
    # Tukey body filter
    def cen(V): n=len(V); return (sum(v[0] for v in V)/n,sum(v[1] for v in V)/n,sum(v[2] for v in V)/n)
    cs=[cen(d[0]) for d in draws]
    def fen(a): s=sorted(a); n=len(s); q1=s[n//4]; q3=s[3*n//4]; r=q3-q1; return q1-1.5*r,q3+1.5*r
    fx=fen([c[0] for c in cs]); fy=fen([c[1] for c in cs]); fz=fen([c[2] for c in cs])
    body=[d for d,c in zip(draws,cs) if fx[0]<=c[0]<=fx[1] and fy[0]<=c[1]<=fy[1] and fz[0]<=c[2]<=fz[1]]
    # decode textures (only those used by body)
    used=set(d[3] for d in body if d[3] is not None)
    texpng={}
    for h,tdata,tw,th,fmt,sw,cdata,cf in tex_list:
        idx=texcache[h]
        if idx not in used: continue
        print(f"  tex{idx}: {tw}x{th} fmt={fmt} swz={sw} texdata={len(tdata)}b clut={len(cdata)}b cfmt={cf}")
        rgba=decode_tex(tdata,tw,th,fmt,sw,cdata,cf)
        fn=f"tex_{idx:03d}_{tw}x{th}_fmt{fmt}.png"
        wpng(os.path.join(texdir,fn),tw,th,rgba); texpng[idx]=fn
    # write OBJ + MTL grouped by texture
    objp=os.path.join(outdir,'kratos_textured.obj'); mtlp=os.path.join(outdir,'kratos_textured.mtl')
    with open(mtlp,'w') as mf:
        for idx,fn in texpng.items():
            mf.write(f"newmtl tex{idx}\nmap_Kd textures/{fn}\n\n")
        mf.write("newmtl notex\nKd 0.6 0.6 0.6\n")
    V=[]; VT=[]; groups={}
    for Vd,UVd,faces,tk in body:
        b0=len(V); V.extend(Vd); VT.extend(UVd)
        g=groups.setdefault(tk if tk is not None else -1,[])
        for a,b,c in faces: g.append((b0+a+1,b0+b+1,b0+c+1))
    with open(objp,'w') as of:
        of.write("mtllib kratos_textured.mtl\n")
        for v in V: of.write("v %.5f %.5f %.5f\n"%v)
        for t in VT: of.write("vt %.5f %.5f\n"%(t[0],1.0-t[1]))
        for tk,fs in groups.items():
            of.write(f"usemtl {'tex'+str(tk) if tk>=0 and tk in texpng else 'notex'}\n")
            for a,b,c in fs: of.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")
    write_gltf(outdir, body, texpng)
    print(f"body draws={len(body)} verts={len(V)} tris={sum(len(g) for g in groups.values())} textures={len(texpng)}")
    print("-> kratos_textured.obj/.mtl + textures/ + kratos.gltf in", outdir)
    return outdir

def write_gltf(outdir, body, texpng):
    groups={}
    for Vd,UVd,faces,tk in body:
        groups.setdefault(tk if (tk is not None and tk in texpng) else -1, []).append((Vd,UVd,faces))
    buf=bytearray(); bufferViews=[]; accessors=[]; prims=[]
    images=[]; textures=[]; materials=[]; matindex={}
    for tk,fn in texpng.items():
        images.append({"uri":"textures/"+fn}); textures.append({"source":len(images)-1,"sampler":0})
        materials.append({"name":f"tex{tk}","doubleSided":True,"pbrMetallicRoughness":{"baseColorTexture":{"index":len(textures)-1},"metallicFactor":0.0,"roughnessFactor":1.0}})
        matindex[tk]=len(materials)-1
    materials.append({"name":"notex","doubleSided":True,"pbrMetallicRoughness":{"baseColorFactor":[0.6,0.6,0.6,1],"metallicFactor":0.0,"roughnessFactor":1.0}})
    default_mat=len(materials)-1
    def view(data,target):
        while len(buf)%4: buf.append(0)
        off=len(buf); buf.extend(data)
        bv={"buffer":0,"byteOffset":off,"byteLength":len(data)}
        if target: bv["target"]=target
        bufferViews.append(bv); return len(bufferViews)-1
    for tk,drs in groups.items():
        verts=[]; uvs=[]; idx=[]
        for Vd,UVd,faces in drs:
            b0=len(verts); verts.extend(Vd); uvs.extend(UVd)
            for a,b,c in faces: idx.extend([b0+a,b0+b,b0+c])
        if not idx: continue
        pb_=bytearray();
        for v in verts: pb_+=struct.pack('<fff',*v)
        ub=bytearray()
        for u in uvs: ub+=struct.pack('<ff',u[0],1.0-u[1])
        ib=bytearray()
        for ii in idx: ib+=struct.pack('<I',ii)
        pv=view(pb_,34962); uv=view(ub,34962); iv=view(ib,34963)
        xs=[v[0] for v in verts]; ys=[v[1] for v in verts]; zs=[v[2] for v in verts]
        accessors.append({"bufferView":pv,"componentType":5126,"count":len(verts),"type":"VEC3","min":[min(xs),min(ys),min(zs)],"max":[max(xs),max(ys),max(zs)]}); pa=len(accessors)-1
        accessors.append({"bufferView":uv,"componentType":5126,"count":len(uvs),"type":"VEC2"}); ua=len(accessors)-1
        accessors.append({"bufferView":iv,"componentType":5125,"count":len(idx),"type":"SCALAR"}); ia=len(accessors)-1
        prims.append({"attributes":{"POSITION":pa,"TEXCOORD_0":ua},"indices":ia,"material":matindex.get(tk,default_mat)})
    gltf={"asset":{"version":"2.0","generator":"ge_textured"},"scene":0,"scenes":[{"nodes":[0]}],
          "nodes":[{"mesh":0,"name":"Kratos"}],"meshes":[{"name":"Kratos","primitives":prims}],
          "materials":materials,"textures":textures,"images":images,
          "samplers":[{"magFilter":9729,"minFilter":9729,"wrapS":10497,"wrapT":10497}],
          "accessors":accessors,"bufferViews":bufferViews,"buffers":[{"uri":"kratos.bin","byteLength":len(buf)}]}
    open(os.path.join(outdir,'kratos.bin'),'wb').write(buf)
    json.dump(gltf, open(os.path.join(outdir,'kratos.gltf'),'w'), indent=1)

if __name__=='__main__':
    run(sys.argv[1], sys.argv[2])
