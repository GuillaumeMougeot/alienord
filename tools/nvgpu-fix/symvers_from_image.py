# Rewrite Module.symvers with CRCs read from the kernel Image; verify against CRCs harvested from installed modules.
# usage: symvers_from_image.py Image Module.symvers.in Module.symvers.out <dir of modules built for this kernel>
import sys, os, struct, collections
here = os.path.dirname(os.path.abspath(__file__))
image, symvers_in, symvers_out, harvested_dir = sys.argv[1:5]
sys.argv = ['x', image, symvers_in]
exec(open(os.path.join(here, 'image_crcs.py')).read().split('syms = sys.argv[3:]')[0])
crc('module_layout')
img_crc = {}
for start, (names, kc) in tables.items():
    for i, n in enumerate(names):
        img_crc[n] = struct.unpack_from('<I', img, kc + 4*i)[0]
print('symbols read from the Image:', len(img_crc))
def versions(path):
    d = open(path, 'rb').read()
    shoff = struct.unpack_from('<Q', d, 0x28)[0]; es, n, si = struct.unpack_from('<HHH', d, 0x3A)
    secs = [struct.unpack_from('<IIQQQQIIQQ', d, shoff+i*es) for i in range(n)]
    st = secs[si][4]
    for s in secs:
        if d[st+s[0]: d.index(b'\0', st+s[0])] == b'__versions':
            for i in range(0, s[5], 64):
                yield d[s[4]+i+8: s[4]+i+64].split(b'\0')[0].decode(), struct.unpack_from('<Q', d, s[4]+i)[0] & 0xffffffff
seen = collections.defaultdict(set)
for root, _, fs in os.walk(harvested_dir):
    for f in fs:
        if f.endswith('.ko'):
            for s, c in versions(os.path.join(root, f)): seen[s].add(c)
agree = sum(1 for s, c in seen.items() if s in img_crc and img_crc[s] in c)
disagree = [s for s, c in seen.items() if s in img_crc and img_crc[s] not in c]
missing = [s for s in seen if s not in img_crc]
print('harvested', len(seen), 'agree', agree, 'disagree', len(disagree), disagree[:5], 'not in image (module exports)', len(missing))
out = []; changed = 0; absent = 0
for l in open(symvers_in):
    p = l.rstrip('\n').split('\t')
    if p[1] in img_crc:
        if int(p[0], 16) != img_crc[p[1]]: changed += 1
        p[0] = '0x%08x' % img_crc[p[1]]
    elif p[2] == 'vmlinux': absent += 1
    out.append('\t'.join(p))
open(symvers_out, 'w').write('\n'.join(out) + '\n')
print('Module.symvers lines changed vs NVIDIA headers:', changed, '; vmlinux symbols not found in image:', absent)
