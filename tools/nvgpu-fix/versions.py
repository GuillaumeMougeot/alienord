import sys, struct
d = open(sys.argv[1], 'rb').read()
shoff = struct.unpack_from('<Q', d, 0x28)[0]; es, n, si = struct.unpack_from('<HHH', d, 0x3A)
secs = [struct.unpack_from('<IIQQQQIIQQ', d, shoff+i*es) for i in range(n)]
st = secs[si][4]
for s in secs:
    if d[st+s[0]: d.index(b'\0', st+s[0])] == b'__versions':
        for i in range(0, s[5], 64):
            print('%08x %s' % (struct.unpack_from('<Q', d, s[4]+i)[0] & 0xffffffff, d[s[4]+i+8: s[4]+i+64].split(b'\0')[0].decode()))
