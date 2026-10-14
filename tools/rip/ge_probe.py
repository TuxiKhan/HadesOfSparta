import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from compression import zstd

data = open(sys.argv[1], 'rb').read()
print("magic:", data[:8], "version:", struct.unpack_from('<I',data,8)[0], "gid:", data[12:21])
for o in (0x18,0x1c,0x20):
    print(f"  field 0x{o:x} = {struct.unpack_from('<I',data,o)[0]}")
zoff = data.find(b'\x28\xb5\x2f\xfd')
print("zstd frame at 0x%x" % zoff)
blob = data[zoff:]
# decompress possibly multiple concatenated frames
d = zstd.ZstdDecompressor()
out = d.decompress(blob)
print("decompressed:", len(out), "bytes; eof=", d.eof, "unused=", len(d.unused_data))
# keep going if more frames
total = out
rest = d.unused_data
while rest and rest[:4]==b'\x28\xb5\x2f\xfd':
    d2 = zstd.ZstdDecompressor(); total += d2.decompress(rest); rest = d2.unused_data
print("total decompressed:", len(total))
open(sys.argv[2],'wb').write(total)
print("wrote ->", sys.argv[2])
# peek head
print("head hex:", ' '.join('%02X'%c for c in total[:48]))
# count GE command-ish: PPSSPP Command {u8 type; u32 sz; u32 ptr} is 9 bytes but likely padded.
# Just histogram first bytes if it's a command array. Show some ascii strings.
import re
ss=[m.group().decode('latin1') for m in re.finditer(rb'[\x20-\x7e]{4,}', total[:4096])]
print("early strings:", ss[:20])
