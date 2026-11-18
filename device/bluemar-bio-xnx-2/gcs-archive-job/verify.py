"""Check a local mirror against a bucket manifest: every object present with the right size.
gcloud already checks each file's hash while downloading; this catches anything missing."""
import csv
import os
import sys

manifest, root = sys.argv[1], sys.argv[2]
expected = missing = wrong_size = 0
seen = set()
versioned = set()
total = 0
problems = []
with open(manifest, newline='') as f:
    for name, size, _crc, _md5 in csv.reader(f):
        if name.endswith('/'):
            continue
        if name in seen:
            # a versioned bucket lists every generation under the same name; rsync only
            # fetches the live one, so older generations need fetching by generation number
            versioned.add(name)
            continue
        seen.add(name)
        expected += 1
        total += int(size)
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            missing += 1
            problems.append(f'missing {name}')
        elif os.path.getsize(path) != int(size):
            wrong_size += 1
            problems.append(f'size {name}')
for p in problems[:20]:
    print(p)
print(f'verify: {expected} objects, {total / 1e9:.2f} GB expected; {missing} missing, {wrong_size} wrong size')
if versioned:
    print(f'verify: {len(versioned)} names have older versions not fetched by rsync, e.g. {sorted(versioned)[0]}')
sys.exit(0 if missing == 0 and wrong_size == 0 and not versioned else 1)
