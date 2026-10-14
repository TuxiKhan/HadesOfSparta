#!/usr/bin/env python3
"""PPSSPP GE dump -> textured Kratos: OBJ+MTL+PNG textures and glTF (positions+UV+texture).

    python ge_textured.py <dump.ppdmp> --list                 # show character clusters
    python ge_textured.py <dump.ppdmp> <outdir> --cluster K [--pose posed|bind]

Skinned (character) draws only. Characters are separated by spatial clustering of draw
centroids in posed space (gedump.clusters); pick the hero's cluster from --list and a quick
render (render_solid.py). --pose bind writes the SAME draws in model/bind space. Stdlib only.
Decoding (bones/world/CLUT registers) lives in gedump.py.
"""
import argparse, os, sys, struct, zlib, hashlib, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gedump import draws, clusters, describe  # noqa: E402


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

def run(path, outdir, pose="posed", cluster=0):
    os.makedirs(outdir, exist_ok=True)
    texdir = os.path.join(outdir, 'textures'); os.makedirs(texdir, exist_ok=True)
    texcache = {}; tex_list = []; body = []
    posed = [d for d in draws(path, "posed") if d['skinned']]
    pick = sorted(clusters(posed)[cluster])
    src = posed if pose == "posed" else [d for d in draws(path, "bind") if d['skinned']]
    ds = [src[i] for i in pick]
    print(f"[{pose}] cluster {cluster}: {describe(posed, pick)}")
    for d in ds:
        tkey = None
        if d['tex']:
            tptr, tsz, tw, th, fmt, sw, cptr, csz, cf = d['tex']
            pb = d['pb']; tdata = pb[tptr:tptr + tsz]; cdata = pb[cptr:cptr + csz] if csz else b''
            h = hashlib.md5(tdata + cdata + bytes([fmt, sw, cf]) + struct.pack('<HH', tw, th)).hexdigest()[:10]
            if h not in texcache:
                texcache[h] = len(tex_list); tex_list.append((tdata, tw, th, fmt, sw, cdata, cf))
            tkey = texcache[h]
        body.append((d['verts'], d['uvs'], d['faces'], tkey))
    used = {b[3] for b in body if b[3] is not None}
    texpng = {}
    for idx, (tdata, tw, th, fmt, sw, cdata, cf) in enumerate(tex_list):
        if idx not in used: continue
        print(f"  tex{idx}: {tw}x{th} fmt={fmt} swz={sw} texdata={len(tdata)}b clut={len(cdata)}b cfmt={cf}")
        fn = f"tex_{idx:03d}_{tw}x{th}_fmt{fmt}.png"
        wpng(os.path.join(texdir, fn), tw, th, decode_tex(tdata, tw, th, fmt, sw, cdata, cf)); texpng[idx] = fn
    objp = os.path.join(outdir, 'kratos_textured.obj'); mtlp = os.path.join(outdir, 'kratos_textured.mtl')
    with open(mtlp, 'w') as mf:
        for idx, fn in texpng.items(): mf.write(f"newmtl tex{idx}\nmap_Kd textures/{fn}\n\n")
        mf.write("newmtl notex\nKd 0.6 0.6 0.6\n")
    V = []; VT = []; groups = {}
    for Vd, UVd, faces, tk in body:
        b0 = len(V); V.extend(Vd); VT.extend(UVd)
        g = groups.setdefault(tk if tk is not None else -1, [])
        for a, b, c in faces: g.append((b0 + a + 1, b0 + b + 1, b0 + c + 1))
    with open(objp, 'w') as of:
        of.write("mtllib kratos_textured.mtl\n")
        for v in V: of.write("v %.5f %.5f %.5f\n" % v)
        for t in VT: of.write("vt %.5f %.5f\n" % (t[0], 1.0 - t[1]))
        for tk, fs in groups.items():
            of.write(f"usemtl {'tex' + str(tk) if tk >= 0 and tk in texpng else 'notex'}\n")
            for a, b, c in fs: of.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")
    write_gltf(outdir, body, texpng)
    print(f"[{pose}] body draws={len(body)} verts={len(V)} tris={sum(len(g) for g in groups.values())} textures={len(texpng)}")
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

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("dump"); ap.add_argument("outdir", nargs="?")
    ap.add_argument("--pose", choices=("posed", "bind"), default="posed")
    ap.add_argument("--cluster", type=int, default=0, help="cluster index from --list (0 = largest)")
    ap.add_argument("--list", action="store_true", help="list character clusters and exit")
    a = ap.parse_args()
    if a.list or not a.outdir:
        posed = [d for d in draws(a.dump, "posed") if d['skinned']]
        for k, idx in enumerate(clusters(posed)[:12]):
            print(f"  cluster {k}: {describe(posed, idx)}")
    else:
        run(a.dump, a.outdir, a.pose, a.cluster)
