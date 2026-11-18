# Can the knowledge base go public?

**Kind:** change · **Status:** RESOLVED. Yes, as a new repository with a fresh history:
`github.com/GuillaumeMougeot/alienord`, cloned at `~/codes/alienord`. Trifork's full history and
their internal framework stay in the private local repository `~/vd-biodiversity`.

## The decision (owner, 2026-11-18)

- Move all the vd-biodiversity files and code to the new public repository **alienord**; commit and
  push there.
- **Do not rewrite the history of the old local repository**; rewriting is fine for the public one.
  We did not rewrite anything: alienord starts from a single import commit of the tree as it stood.
- Trifork's code has no licence file. The owner chose to publish the project code but **not
  `vendor/trifork-ai-core-tech-stack`**, Trifork's generic internal framework (their staff are its
  named authors).
- Requesting key rotation is dropped: Trifork is not responding and their access is still needed
  ([credentials](2026-11-16-credentials-in-trifork-history.md)).
- The offsite copy of the data is on hold.

## What was held back or changed on the way in

| item | why | where it is |
|---|---|---|
| Trifork's Git history (`main` + 100 `trifork/*` branches) | contains a live cloud key and other credentials | `~/vd-biodiversity` (private, push blocked) |
| `vendor/trifork-ai-core-tech-stack/` | Trifork's internal framework, no licence (owner's choice) | the same, and the recovery backup |
| `manifests/cloud/*.manifest.csv` | every recording's file name carries its GPS position: where the vehicles drove and parked | the same |
| `.github/workflows/` | Trifork's CI: would start building and deploying on every push | moved to `docs/trifork/github-workflows/`, inactive |
| two passwords in `docs/trifork/flashing_jetson.md` (AnyDesk, device) | credentials | `[redacted]`; originals in the private repo |
| Trifork and Develco staff e-mail addresses (docs, Dockerfile labels) | personal data | replaced by the company name |

Kept, on purpose: the GCP project and bucket names and the service-account e-mail (identifiers, not
credentials, and needed to understand the system), the key file's *name*, and the journal account of
the leak (without values).

## The guard rail

`tools/check-secrets.sh`, installed as the pre-commit and pre-push hook by
`tools/install-hooks.sh`. It reads the live values (cloud key ID, GitHub token, both passwords, the
owner's private e-mail) from `/var/secrets/` and the private repository at run time, never prints
them, and refuses a commit or push that contains any of them or a credential-like pattern. It aborts
if a value comes back empty (an empty pattern matches everything: 2026-11-17). Self-tested on
11-18: a staged fake token and a staged copy of a live value were both refused. A first version
reported the leak but still exited 0 (flag set in a subshell); caught by that self-test, fixed.
