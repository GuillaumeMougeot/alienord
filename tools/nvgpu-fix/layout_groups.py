import sys, struct, os, collections, time
sys.path.insert(0, os.path.dirname(__file__))
loaded = {l.split()[0] for l in open('/proc/modules')}
g = collections.defaultdict(list)
for root, _, files in os.walk('/lib/modules/5.10.104-tegra'):
    for f in files:
        if not f.endswith('.ko'): continue
        p = os.path.join(root, f); d = open(p,'rb').read()
        i = d.find(b'module_layout\0')
        crc = struct.unpack_from('<Q', d, i-8)[0] & 0xffffffff if i > 0 else None
        g[crc].append((f[:-3].replace('-','_') in loaded, time.strftime('%Y-%m-%d', time.gmtime(os.path.getmtime(p))), os.path.relpath(p,'/lib/modules/5.10.104-tegra')))
for crc, lst in g.items():
    dates = collections.Counter(x[1] for x in lst)
    print(hex(crc) if crc else None, 'modules', len(lst), 'loaded', sum(x[0] for x in lst), dict(dates))
    print('   loaded e.g.', [x[2] for x in lst if x[0]][:6])
    print('   dirs', collections.Counter(x[2].split('/')[0] + '/' + (x[2].split('/')[1] if '/' in x[2] else '') for x in lst).most_common(5))
