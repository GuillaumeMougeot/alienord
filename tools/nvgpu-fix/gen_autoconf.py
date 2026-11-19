import sys, re
cfg, out_h, out_conf = sys.argv[1:4]
h = ['/*', ' * Automatically generated file; DO NOT EDIT.', ' */']
conf = ['#', '# Automatically generated file; DO NOT EDIT.', '#']
for line in open(cfg):
    m = re.match(r'^(CONFIG_[A-Za-z0-9_]+)=(.*)$', line.rstrip('\n'))
    if not m: continue
    k, v = m.groups(); conf.append(f'{k}={v}')
    if v == 'y': h.append(f'#define {k} 1')
    elif v == 'm': h.append(f'#define {k}_MODULE 1')
    elif v == 'n': pass
    else: h.append(f'#define {k} {v}')
open(out_h, 'w').write('\n'.join(h) + '\n'); open(out_conf, 'w').write('\n'.join(conf) + '\n')
