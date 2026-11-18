# Can this repository's history be published?

**Kind:** incident · **Status:** RESOLVED 2026-11-18. Not as it is: Trifork's history contains
credentials, one of them **live**. The owner chose option (b) below: a new public repository with a
fresh history, the old one kept private and unchanged, and no key-rotation request
([2026-11-18](2026-11-18-publishing-the-repository.md)).

| Credential | Commits | Branches | Valid? |
|---|---|---|---|
| Google Cloud key for all the data, `secrets/nordfou-biodiversity-2cd0fb3af162.json` | 9274ed3 | `trifork/jwme/refactor_makefile` | **yes**: same key ID as the unit's live key |
| GitHub token, `secrets/.env` | 7111b76, 9274ed3 | same | unknown |
| Search-database key, `Search/infra/BioDiversityService/cloudfire-biodiversity.json` (+`_old`) | e519d73, f7a7a52 | **`main`** and four `trifork/allu/*` | unknown |
| a 6-character device password | `docs/trifork/flashing_jetson.md` line 32, and history | `main` | unknown |

Found by pattern scans of every branch, comparing fingerprints without printing any value. The bucket
key has been readable by anyone with access to Trifork's GitHub since August 2023, so **it should be
rotated** by the project's admin, now that the data is local.

**Options before any remote:** (a) rewrite history without those files with `git filter-repo`, which
keeps the history but changes every commit ID. An attempt to install the tool was blocked by Claude
Code's permission check, and the decision belongs to the owner. (b) Publish a fresh history (one
commit of today's files), with the full history kept only in the bundle. Meanwhile a `pre-push` hook in
`.git/hooks/` refuses every push.

**Decision, 2026-11-18 (owner):** option (b). The knowledge base and code moved to the public
repository alienord with a fresh history; this history stays in the private local repository,
**not rewritten**. Key rotation is not requested: Trifork does not respond and their access is
still needed. The key therefore stays live and leaked in Trifork's own repository; it is not in
alienord. Details: [2026-11-18](2026-11-18-publishing-the-repository.md).
