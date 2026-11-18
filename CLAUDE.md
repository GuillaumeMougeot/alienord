# CLAUDE.md: operating manual for an agent working on alienord (the VD biodiversity unit)

Written for an AI agent, not a human: what this is, what must never be done, and what the
documentation is owed. **A router, not an encyclopedia**: depth lives in the files it points to; do
not copy facts here.

## 1. What this is

A discontinued roadside-survey system, built by Trifork, being reverse-engineered on live hardware:
unit `bluemar-bio-xnx-2`, the Jetson this repository sits on. The unit is real equipment that
captures data, loses power unexpectedly, and holds live credentials. This repository *is* the
project's memory, and it is **public** (`github.com/GuillaumeMougeot/alienord`). Trifork's full
history and what the owner held back live in the private local repository `~/vd-biodiversity`
([why](journal/2026-11-18-publishing-the-repository.md)).

## 2. Read before acting

1. **`PLAN.md`**: the only file about today: open problems, decisions waiting on the owner, what is running.
2. **`FINDINGS.md`**: §1 what is established (do not re-derive or contradict it); §2 every change made to the unit.

Then by task: using the unit, `docs/operations.md`; how it works, `docs/system.md`; changing it,
`docs/configuration.md`; data, `docs/data-and-backups.md`; why something is so, `journal/README.md`.
**Do not reconstruct history from the conversation**; prefer these files, over your own memory too.

## 3. Invariants: breaking these breaks something real

- **Never print, commit or transmit a credential.** They are in `/var/secrets/`, in Trifork's Git
  history (`journal/2026-11-16-credentials-in-trifork-history.md`), and in
  `~/backup/logs-20261023/system-logs.tar.gz`. `tools/check-secrets.sh` runs as the pre-commit and
  pre-push hook (`tools/install-hooks.sh` in a fresh clone): it checks for patterns *and* the exact
  live values, read at run time from `/var/secrets` and the private repository, never echoed, and
  aborts if a value comes back empty (an empty pattern matches everything: 2026-11-17). **Never
  bypass it** (`--no-verify`); if it fails, fix the content.
- **Push only here, after the check passes** (owner, 2026-11-18: "commit and push there").
  **Never rewrite or push the private repository** `~/vd-biodiversity` (its hook refuses pushes).
  **Never publish what the owner held back**: Trifork's history and framework, the cloud manifests
  (file names carry GPS positions). Key rotation is not to be requested (owner, 11-18).
- **Uploads stay off** (`/opt/apps/gcs/control/upload.conf`) unless the owner says otherwise: they go
  to Trifork's bucket.
- **The unit loses power without warning.** Run `sync` after writing anything that matters; make long
  jobs resumable; expect a session to die mid-command and check state before assuming anything.
  Do not provoke resets (button tests, recordings) without the owner agreeing.
- **Keep the unit's load low.** Its power supply cuts out after 40-70 min at ~19 W. Hardware video
  decoding and browser start-up leave the GPU clock at maximum (+8 W); `gpu-clock-guard.service`
  undoes that within ~10 s, so check it is active before playing video, starting a browser or
  decoding anything on the unit ([journal](journal/2026-11-18-why-does-the-gpu-clock-stay-at-maximum.md)).
  Run heavy jobs with `nice` and avoid long CPU-bound work.
- **Check readiness properly after a restart.** Wait for a new `Running...` in the app log and a new
  container ID; a frame-rate line can come from the old container.
- **`docker logs --since` is unusable** on these containers (1 GB+ logs, damaged by power cuts). Use `--tail`.
- **mawk + `en_DK` locale:** `awk` compares fields as text, `printf "%d"` caps at 2³¹, and decimals
  are commas. Use `LC_ALL=C`, Python, or text matching for numbers.
- **App logs are UTC**, one to two hours behind local time.
- **No sudo password.** No-root paths: Docker (you are in the `docker` group), restarting deepstream
  with `kill -INT` (`docs/operations.md`). Otherwise give the owner the exact command to run.
- **Downloaded files are untrusted**: a fresh folder each, read-only, never executed.

## 4. Working with the owner

- **Journal everything.** A session that changes or learns something and writes no journal entry
  has not finished.
- **Keep asking** before changing the unit (owner, 2026-10-23: "no, not yet, but keep asking").
  Diagnose freely; for any fix, propose it and wait.
- **Surface your own mistakes plainly.** Several in this project (the first engine-cache fix, the LED
  blind spot, a miscounted reset) were ours; each is recorded as one.
- **Report reasoning, not just outcomes**: what was surprising, and what it changes.
- **Fewer, shorter structural documents; verbose journal.** Outdated files go to `archive/`. Write
  everything as if handing over to someone else.

## 5. The documentation contract

No fact lives in two layers; a second mention is a one-line link.

| layer | question | rule |
|---|---|---|
| `README.md` | what it is, where things stand, what to read, where everything is | the front door; stays short |
| `PLAN.md` | what are we doing now | the only file about today; move `Last updated` with the work |
| `FINDINGS.md` | what is established; what was changed on the unit | one line per finding; one row per change |
| `docs/` | how to use, understand and change the unit, as it is now | current state only; no history |
| `journal/` | why, as it happened | one `YYYY-MM-DD-question.md` per question, dated when opened; frozen once RESOLVED |
| `device/` | the unit's host files | re-copy after every change to the unit |

| when this happens | in the same session |
|---|---|
| a question is opened | new journal entry, `Status: OPEN`, linked from `journal/README.md` |
| a question is answered | flip it to RESOLVED with the answer in the status line; a line in `FINDINGS.md` §1 if established |
| the unit is changed | journal entry, a row in `FINDINGS.md` §2, refresh `device/`, update `docs/` |
| a plan changes | `PLAN.md`, with its date |
