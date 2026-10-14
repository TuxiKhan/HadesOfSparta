#!/usr/bin/env python3
"""
Ready at Dawn PSP "Pack" archive tool  (God of War: Ghost of Sparta / Chains of Olympus).

Format (little-endian), reverse-engineered from the retail USA GoS UMD:
  0x00  char[4]  magic "Pack"
  0x04  u32      version   (observed 0x00020004)
  0x08  u32      id / build hash
  0x0C  u32      entry_count
  0x10  0x30 bytes  secondary header (preserved verbatim, except:)
  0x28  u32      data end = end of the last blob, rounded up to 16
  ...   after that offset: a trailer (116..1828 B seen on Kratos packs) - preserved verbatim
  0x40  entry[entry_count] { u32 nameHash; u32 offset; u32 size; u32 flags }
        -> entries are sorted ascending by nameHash (binary search by hashed name)
  data  blobs, each starting at its offset, 16-byte aligned, padded between blobs.
        sub-blob magics seen: 'RADI' (RAD image/texture), 'CfCm' (mesh/model chunk), raw.

Commands:
  info      <pack.bin>
  extract   <pack.bin> <out_dir>           # writes blobs + manifest.json (+ padding, for exact round-trip)
  repack    <in_dir> <out.bin>             # rebuild from manifest.json, resize-aware (recomputes offsets &
                                           #   0x28, re-aligns blobs to 16, keeps the trailer)
  roundtrip <pack.bin>                     # extract to temp, repack, assert byte-identical
"""
import sys, os, json, struct, hashlib, tempfile, shutil, re

MAGIC = b'Pack'
TABLE_OFF = 0x40
REC = 16
ALIGN = 16

def _tag(b):
    return ''.join(chr(c) if 32 <= c <= 126 else '.' for c in b[:4])

def parse(data):
    assert data[:4] == MAGIC, f"not a Pack file (magic={data[:4]!r})"
    version = struct.unpack_from('<I', data, 0x04)[0]
    pid     = struct.unpack_from('<I', data, 0x08)[0]
    count   = struct.unpack_from('<I', data, 0x0C)[0]
    entries = []
    for i in range(count):
        o = TABLE_OFF + i * REC
        h, off, size, flags = struct.unpack_from('<IIII', data, o)
        entries.append(dict(index=i, hash=h, offset=off, size=size, flags=flags,
                            tag=_tag(data[off:off+4])))
    return version, pid, count, entries

def cmd_info(path):
    data = open(path, 'rb').read()
    version, pid, count, entries = parse(data)
    print(f"{os.path.basename(path)}  size={len(data)} (0x{len(data):X})")
    print(f"  version=0x{version:08x} id=0x{pid:08x} entries={count}")
    data_start = min(e['offset'] for e in entries)
    print(f"  table=0x40..0x{TABLE_OFF+count*REC:X}  data_start=0x{data_start:X}")
    from collections import Counter
    c = Counter(e['tag'] for e in entries)
    print("  blob types:", dict(c))
    for e in entries[:6]:
        print(f"    [{e['index']:3}] hash={e['hash']:#010x} off={e['offset']:#08x} "
              f"size={e['size']:#x}({e['size']}) fl={e['flags']} tag={e['tag']!r}")

def cmd_extract(path, out_dir):
    data = open(path, 'rb').read()
    version, pid, count, entries = parse(data)
    os.makedirs(out_dir, exist_ok=True)
    data_start = min(e['offset'] for e in entries)
    prefix = data[:data_start]          # header + table, preserved verbatim
    # order by offset to capture inter-blob padding
    by_off = sorted(entries, key=lambda e: e['offset'])
    man_entries = []
    for i, e in enumerate(by_off):
        blob = data[e['offset']:e['offset'] + e['size']]
        nxt = by_off[i+1]['offset'] if i+1 < len(by_off) else len(data)
        pad = data[e['offset'] + e['size']:nxt]
        safe = re.sub(r'[^A-Za-z0-9]', '_', e['tag'])
        fn = f"{e['index']:04d}_{e['hash']:08x}_{safe}.blob"
        with open(os.path.join(out_dir, fn), 'wb') as fh:
            fh.write(blob)
        man_entries.append(dict(index=e['index'], hash=e['hash'], flags=e['flags'],
                                file=fn, pad_hex=pad.hex()))
    data_end = struct.unpack_from('<I', data, 0x28)[0]
    manifest = dict(version=version, id=pid, count=count,
                    prefix_hex=prefix.hex(),
                    data_start=data_start,
                    size_field_0x28=data_end,
                    file_size=len(data),
                    trailer_hex=data[data_end:].hex(),
                    entries=man_entries)
    with open(os.path.join(out_dir, 'manifest.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1)
    print(f"extracted {count} blobs -> {out_dir}")

def cmd_repack(in_dir, out_path, exact=True):
    man = json.load(open(os.path.join(in_dir, 'manifest.json')))
    prefix = bytes.fromhex(man['prefix_hex'])
    count = man['count']
    # layout blobs in offset order (manifest entries are already offset-ordered)
    out = bytearray(prefix)
    table = {}   # index -> (offset, size)
    for me in man['entries']:
        blob = open(os.path.join(in_dir, me['file']), 'rb').read()
        offset = len(out)
        out += blob
        table[me['index']] = (offset, len(blob))
        if exact:
            out += bytes.fromhex(me['pad_hex'])
        else:
            pad = (-len(out)) % ALIGN
            out += b'\x00' * pad
    # rewrite entry table with (possibly) new offsets/sizes, keep hash+flags
    base = bytes.fromhex(man['prefix_hex'])
    out[0:len(base)] = base
    for me in man['entries']:
        i = me['index']
        off, size = table[i]
        struct.pack_into('<IIII', out, TABLE_OFF + i * REC,
                         me['hash'], off, size, me['flags'])
    if not exact:
        if 'trailer_hex' not in man:
            sys.exit("manifest predates trailer support - re-run `extract` before a resize repack")
        struct.pack_into('<I', out, 0x28, len(out))     # data end (already 16-aligned above)
        out += bytes.fromhex(man['trailer_hex'])
    with open(out_path, 'wb') as fh:
        fh.write(out)
    print(f"repacked {count} blobs -> {out_path} ({len(out)} bytes)")

def cmd_roundtrip(path):
    tmp = tempfile.mkdtemp(prefix='packrt_')
    try:
        cmd_extract(path, tmp)
        out = os.path.join(tmp, 'rebuilt.bin')
        cmd_repack(tmp, out, exact=True)
        a = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        b = hashlib.sha256(open(out, 'rb').read()).hexdigest()
        ok = a == b
        print(f"  original sha256 {a}")
        print(f"  rebuilt  sha256 {b}")
        print("  ROUND-TRIP:", "IDENTICAL [OK]" if ok else "MISMATCH [FAIL]")
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'info':        cmd_info(sys.argv[2])
    elif cmd == 'extract':   cmd_extract(sys.argv[2], sys.argv[3])
    elif cmd == 'repack':    cmd_repack(sys.argv[2], sys.argv[3], exact=False)
    elif cmd == 'roundtrip': sys.exit(0 if cmd_roundtrip(sys.argv[2]) else 1)
    else: print(__doc__); sys.exit(2)
