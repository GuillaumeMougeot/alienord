# Read exported-symbol CRCs straight out of an arm64 kernel Image (5.10, PREL32 ksymtab, 12-byte entries).
# usage: image_crcs.py Image Module.symvers sym1 sym2 ...
# Module.symvers supplies known (harvested) CRCs used only to locate the kcrctab arrays.
import sys, struct, numpy as np
img = open(sys.argv[1], 'rb').read(); known = {}
for l in open(sys.argv[2]):
    p = l.split('\t'); known[p[1]] = int(p[0], 16)
v = np.frombuffer(img[:len(img)//4*4], dtype='<i4').astype(np.int64)
pos = np.arange(len(v), dtype=np.int64) * 4
def cstr(off):
    e = img.index(b'\0', off); return img[off:e]
def entry_for(name):
    hits = []
    pat = name.encode() + b'\0'      # no leading NUL: the linker merges string tails
    so = img.find(pat)
    while so >= 0:
        k = np.nonzero(v + pos == so)[0]            # name_offset field: *(int32*)q + q == string
        hits += [int(pos[i]) - 4 for i in k if name_at(int(pos[i]) - 4) == name]
        so = img.find(pat, so + 1)
    return hits
def name_at(e):
    q = e + 4; o = struct.unpack_from('<i', img, q)[0] + q
    if not (0 <= o < len(img)): return None
    try: n = cstr(o).decode()
    except Exception: return None
    return n if n and all(c.isalnum() or c == '_' for c in n) else None
def section(e):
    a = e
    while name_at(a - 12): a -= 12
    b = e
    while name_at(b + 12): b += 12
    return a, (b - a)//12 + 1
tables = {}
def crc(name):
    for e in entry_for(name):
        start, n = section(e)
        if start not in tables:
            names = [name_at(start + 12*i) for i in range(n)]; votes = {}
            # find kcrctab: n u32 values; anchor on a run of 4 consecutive known CRCs
            for i in range(n - 4):
                if all(x in known for x in names[i:i+4]):
                    pat = struct.pack('<4I', *[known[x] for x in names[i:i+4]])
                    j = img.find(pat)
                    if j >= 0 and img.find(pat, j + 1) < 0:
                        votes[j - 4*i] = votes.get(j - 4*i, 0) + 1
            best = max(votes, key=votes.get) if votes else None
            tables[start] = (names, best if best is not None and votes[best] >= 3 else None)
        names, kc = tables[start]
        if kc is None: continue
        i = names.index(name)
        return struct.unpack_from('<I', img, kc + 4*i)[0], len(names)
    return None, None
syms = sys.argv[3:]
if syms and syms[0] == '--ko':   # check every import of a module
    import subprocess
    out = subprocess.run(['python3', '-I', __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'versions.py'), syms[1]], capture_output=True, text=True).stdout.split('\n')
    ok = bad = nf = 0
    for l in filter(None, out):
        c0, s = l.split(); c, n = crc(s)
        if c is None: nf += 1; print('NOT FOUND', s)
        elif c == int(c0, 16): ok += 1
        else: bad += 1; print('MISMATCH', s, 'module=' + c0, 'kernel=0x%08x' % c)
    print('imports checked against the kernel image: match %d, mismatch %d, not found %d' % (ok, bad, nf))
else:
    for s in syms:
        c, n = crc(s)
        print(s, ('0x%08x' % c) if c is not None else 'NOT FOUND', 'symvers=' + ('0x%08x' % known[s] if s in known else '-'), 'table=%s' % n)
