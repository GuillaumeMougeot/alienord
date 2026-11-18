# Vendored dependencies

Recovered on 2026-09-08 from the running `deepstream-l4t:base` container
(`/usr/local/lib/python3.8/dist-packages/`), because the originals are only reachable through Trifork:

| Package | Version | Original source | Why it matters |
|---|---|---|---|
| `trifork-ai-core-tech-stack` (`core/`), **not in this public repository**: in `~/vd-biodiversity/vendor/` and the recovery backup | 0.0.1 | private repo `github.com/trifork/ai-core-tech-stack` @ `90c0b92f519beee8069d35a48e56c4fcf9969921` | the pipeline framework: `Driver`, `Controller`, `PipelineBuilder`, probe base classes. The app cannot be built without it. |
| `dataclass-wizard` (`dataclass_wizard/`) | 0.22.2 (fork) | `github.com/cgrtrifork/dataclass-wizard` @ `3adedbec5afd04d82cbc5f52e9daf80c709961f3` | config loading |

To build without Trifork, change the two `git+https://` lines in `bio/requirements.txt` to install from
these folders. Licence: as delivered to the project by Trifork; see `docs/dependencies.md`. Trifork's framework has no
licence and is their internal product, so the owner kept it out of the public repository (2026-11-18).
