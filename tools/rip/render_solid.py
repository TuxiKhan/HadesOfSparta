import sys, struct, zlib, math
V=[]; F=[]
for l in open(sys.argv[1]):
    if l[:2]=='v ': _,x,y,z=l.split(); V.append((float(x),float(y),float(z)))
    elif l[:2]=='f ':
        idx=[int(p.split('/')[0]) for p in l.split()[1:]]
        for i in range(1,len(idx)-1): F.append((idx[0]-1,idx[i]-1,idx[i+1]-1))
S=360
xs=[v[0] for v in V]; ys=[v[1] for v in V]; zs=[v[2] for v in V]
minx,maxx=min(xs),max(xs); miny,maxy=min(ys),max(ys); minz,maxz=min(zs),max(zs)
def render(ax,ay,az,flipy,name):
    sc=(S-20)/max(maxx-minx,maxy-miny,maxz-minz)
    ca=[v[ax] for v in V]; cb=[v[ay] for v in V]
    amin=min(ca); bmin=min(cb)
    img=bytearray([20])*(S*S); zb=[-1e9]*(S*S)
    for a,b,c in F:
        p=[V[a],V[b],V[c]]
        # screen coords
        S2=[]
        for q in p:
            sx=int((q[ax]-amin)*sc)+10; sy=int((q[ay]-bmin)*sc)+10
            if flipy: sy=S-1-sy
            S2.append((sx,sy,q[az]))
        # normal for shading (in 3D)
        u=(p[1][0]-p[0][0],p[1][1]-p[0][1],p[1][2]-p[0][2]); w=(p[2][0]-p[0][0],p[2][1]-p[0][1],p[2][2]-p[0][2])
        nx=u[1]*w[2]-u[2]*w[1]; ny=u[2]*w[0]-u[0]*w[2]; nz=u[0]*w[1]-u[1]*w[0]
        nl=math.sqrt(nx*nx+ny*ny+nz*nz) or 1
        # light along az axis
        L=[0,0,0]; L[az]=1
        sh=abs((nx*L[0]+ny*L[1]+nz*L[2])/nl); col=int(40+sh*200)
        # rasterize triangle
        (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=S2
        minxx=max(min(x0,x1,x2),0); maxxx=min(max(x0,x1,x2),S-1)
        minyy=max(min(y0,y1,y2),0); maxyy=min(max(y0,y1,y2),S-1)
        den=((y1-y2)*(x0-x2)+(x2-x1)*(y0-y2))
        if den==0: continue
        for py in range(minyy,maxyy+1):
            for px in range(minxx,maxxx+1):
                wa=((y1-y2)*(px-x2)+(x2-x1)*(py-y2))/den
                wb=((y2-y0)*(px-x2)+(x0-x2)*(py-y2))/den
                wc=1-wa-wb
                if wa<0 or wb<0 or wc<0: continue
                z=wa*z0+wb*z1+wc*z2
                i=py*S+px
                if z>zb[i]: zb[i]=z; img[i]=col
    def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    raw=bytearray()
    for y in range(S): raw.append(0); raw+=img[y*S:(y+1)*S]
    open(name,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',S,S,8,0,0,0,0))+ch(b'IDAT',zlib.compress(bytes(raw),9))+ch(b'IEND',b''))
    print("wrote",name)
base=sys.argv[2]
render(0,1,2,True,base+"_front.png")   # X,Y, light +Z
render(2,1,0,True,base+"_side.png")    # Z,Y, light +X
