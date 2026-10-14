import sys, struct, zlib
V=[]
for line in open(sys.argv[1]):
    if line[:2]=='v ':
        _,x,y,z=line.split(); V.append((float(x),float(y),float(z)))
print("verts",len(V))
S=256
def png(path,w,h,gray):
    def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    raw=bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w): raw.append(gray[y*w+x])
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,0,0,0,0))+ch(b'IDAT',zlib.compress(bytes(raw),9))+ch(b'IEND',b''))
def proj(ai,bi,flipb,name):
    a=[v[ai] for v in V]; b=[v[bi] for v in V]
    amin,amax,bmin,bmax=min(a),max(a),min(b),max(b)
    buf=bytearray(S*S)
    for v in V:
        px=int((v[ai]-amin)/(amax-amin+1e-9)*(S-1))
        py=int((v[bi]-bmin)/(bmax-bmin+1e-9)*(S-1))
        if flipb: py=S-1-py
        idx=py*S+px
        if buf[idx]<255: buf[idx]=min(255,buf[idx]+60)
    png(name,S,S,buf)
    print("wrote",name,f"axes({ai},{bi}) range a[{amin:.1f},{amax:.1f}] b[{bmin:.1f},{bmax:.1f}]")
base=sys.argv[2]
proj(0,1,True,base+"_XY.png")
proj(0,2,True,base+"_XZ.png")
proj(2,1,True,base+"_ZY.png")
