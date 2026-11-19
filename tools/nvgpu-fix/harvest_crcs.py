# Collect the CRCs that Lenovo-built modules recorded for kernel symbols (their __versions tables),
# then rewrite Module.symvers with them. Reports conflicts.
import sys, struct, os, collections
symvers_in, symvers_out, moddir = sys.argv[1:4]
seen = collections.defaultdict(set)
def versions(path):
    d = open(path, 'rb').read()
    if d[:4] != b'\x7fELF': return
    shoff = struct.unpack_from('<Q', d, 0x28)[0]; es, n, si = struct.unpack_from('<HHH', d, 0x3A)
    secs = [struct.unpack_from('<IIQQQQIIQQ', d, shoff+i*es) for i in range(n)]
    st = secs[si][4]
    for s in secs:
        if d[st+s[0]: d.index(b'\0', st+s[0])] == b'__versions':
            for i in range(0, s[5], 64):
                crc = struct.unpack_from('<Q', d, s[4]+i)[0] & 0xffffffff
                yield d[s[4]+i+8: s[4]+i+64].split(b'\0')[0].decode(), crc
nmods = 0
for root, _, files in os.walk(moddir):
    for f in files:
        if f.endswith('.ko'):
            nmods += 1
            for sym, crc in versions(os.path.join(root, f)): seen[sym].add(crc)
conflicts = {k: v for k, v in seen.items() if len(v) > 1}
out = []; changed = same = 0
known = set()
for line in open(symvers_in):
    p = line.rstrip('\n').split('\t'); known.add(p[1])
    if p[1] in seen and len(seen[p[1]]) == 1:
        c = next(iter(seen[p[1]]))
        if c != int(p[0], 16): changed += 1
        else: same += 1
        p[0] = '0x%08x' % c
    out.append('\t'.join(p))
open(symvers_out, 'w').write('\n'.join(out) + '\n')
print('modules', nmods, 'symbols harvested', len(seen), 'conflicts', len(conflicts), list(conflicts)[:5])
print('rewritten', changed, 'already equal', same, 'harvested but not in symvers', len(set(seen) - known))
