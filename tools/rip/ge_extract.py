import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from compression import zstd
from collections import Counter, defaultdict

data = open(sys.argv[1],'rb').read()
cmd_count = struct.unpack_from('<I',data,0x18)[0]
pushsize  = struct.unpack_from('<I',data,0x1c)[0]
cmd_csize = struct.unpack_from('<I',data,0x20)[0]
print(f"commands={cmd_count} pushbuf={pushsize} cmd_csize={cmd_csize}")

cmd_blob = data[0x24:0x24+cmd_csize]
commands = zstd.ZstdDecompressor().decompress(cmd_blob)
print("commands decompressed:", len(commands), "expected", cmd_count*9)

# pushbuf frame follows
poff = 0x24 + cmd_csize
# skip to zstd magic
zoff = data.find(b'\x28\xb5\x2f\xfd', poff)
print("pushbuf zstd at 0x%x (poff=0x%x)" % (zoff, poff), "gap bytes:", data[poff:zoff].hex())
pushbuf = zstd.ZstdDecompressor().decompress(data[zoff:])
print("pushbuf decompressed:", len(pushbuf), "expected", pushsize)

open(sys.argv[2],'wb').write(commands)
open(sys.argv[3],'wb').write(pushbuf)

# parse 9-byte command records: u8 type, u32 sz, u32 ptr
types = Counter()
bytype_sz = defaultdict(list)
recs=[]
for i in range(cmd_count):
    o=i*9
    t=commands[o]; sz=struct.unpack_from('<I',commands,o+1)[0]; ptr=struct.unpack_from('<I',commands,o+5)[0]
    recs.append((t,sz,ptr)); types[t]+=1; bytype_sz[t].append(sz)
print("\ntype histogram (type: count, sz-range):")
for t in sorted(types):
    szs=bytype_sz[t]
    print(f"  type {t} (0x{t:02x}): {types[t]:6}  sz[min={min(szs)},max={max(szs)}]")
