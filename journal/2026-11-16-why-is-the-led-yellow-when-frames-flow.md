# Why is the LED yellow while frames are flowing?

**Kind:** incident · **Status:** RESOLVED (2026-11-16): the LED check's log query had become too slow
to work. It now reads the end of the log. Our mistake, in the 2026-10-23 version.

The pipeline ran at ~1.1 fps per camera, yet the monitor reported `No frame rate reported in the last
30 s`. The check used `docker logs --since 30s`, which reads the container's log **from the start**.
The deepstream container has been the same one since 2026-09-08, so its log had reached **1.2 GB**,
with 6 lines damaged by power cuts (NUL bytes). The query took 31 s and returned nothing. `--tail` reads
from the end: 0.1 s, reliable.

**Change:** `docker logs --timestamps --tail 50`, the age of the newest `PERF` line checked by the
script itself, and a 10 s timeout. 15 stub cases × 3 locales pass (45/45), including a report 120 s
old, an unreadable timestamp and a hung `docker logs`. Live: on during a restart (`Last frame rate
report is 38 s old`), off once frames resumed. Previous version kept as `launch.sh.prev-20261116`.

A side lesson: my own timing helper had printed a bogus count ("3 lines") because bash `printf`
rejects `.` decimals under the en_DK locale. Locale traps appear three times in this project.
