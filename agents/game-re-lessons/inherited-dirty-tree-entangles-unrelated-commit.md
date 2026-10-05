# A working tree can already be dirty with unrelated uncommitted work at session start — no sibling agent required

**When it bites:** `git status` at the very start of a task already shows a
sizeable diff (several to dozens of files modified/deleted, or new
untracked directories) that has nothing to do with your assignment, and
no other agent is currently running concurrently — this is leftover,
uncommitted work from an *earlier*, now-finished session on the same
project. Before editing any already-modified file, and before your final
`git add`/`git commit`.

This is a distinct trigger from the whole `concurrent-sibling-*`/
`bare-git-commit-sweeps-concurrent-stage.md` cluster of lessons, which are
all about a *live*, currently-running sibling process touching the same
files while you work. Here there is no race and no sibling to converge
with — the dirty state is simply sitting there, static, because a prior
session's work was never committed. The risk is identical in shape (your
commit accidentally absorbing content you didn't write and haven't
vetted), but the cause and the fix are different.

## What happened

Confirmed on Valkyrie Profile (`valkyrie` project): a session started with
`git status` already showing ~30 modified/deleted files — a large,
in-progress migration moving several `tools/shared/*.ts` modules
(`psx-cd.ts`, `psx-str.ts`, `psx-spu-reverb.ts`, `psp-iso9660.ts`,
`wav-writer.ts`, `atlas-packer.ts`, `psp-atrac3p-audio.ts`) into a new
shared `@seer-project/playstation` package, plus new untracked directories
for an unrelated game project scaffold. This state predated the session
entirely (`git log` showed the branch's tip was an unrelated commit from
hours earlier; no other agent was addressable/active). `npx tsc --noEmit`
was *already broken* at session start — 5 pre-existing errors referencing
paths the migration had deleted but not every call site had been updated
for — entirely independent of anything the current task touched.

The task needed to add a new module that imports from one of the
already-modified shared files (`tools/shared/psp-vp-pfs.ts`, mid-migration)
and add wiring into two other already-modified pipeline files
(`psp-export-game-data.ts`, `psp-build-assets.ts`). Editing those files
further to add the wiring was avoided entirely — not because the pending
migration looked wrong (it looked like legitimate, deliberate, if
unfinished, work), but because there was no way to verify it was
finished/correct, and because staging an already-dirty file for commit
unavoidably includes 100% of its current diff, not just the lines you
personally just added. `git add <file>` stages the whole file's changes
against the last commit; a pathspec-scoped `git commit <file>` (the fix
`bare-git-commit-sweeps-concurrent-stage.md` recommends for the *bare*
commit trap) does not help here, because the file itself — not just the
index — already carries someone else's unreviewed content.

## The fix

1. **`git status` and `git diff --stat` before writing a single line**, on
   any project, even a solo session with no mentioned sibling — never
   assume a clean starting tree.
2. **Prefer new files over editing already-dirty ones**, whenever the task
   allows it. This session shipped a fully working, tested, committed
   contribution (a new decode module + probe + verify script + test file)
   entirely as new files, and left the pipeline-wiring step as an
   explicitly documented "next mechanical step" in the docs rather than
   touching the two already-dirty pipeline files to add it. A finding that
   is real, verified, and committed as a standalone module is worth more
   than a finding entangled with someone else's unfinished, unreviewed
   work.
3. **If editing an already-dirty file is unavoidable**, diff it in full
   (`git diff <file>`, not `--stat`) both before and after your edit, and
   confirm your own change is a clean, isolatable hunk — but still expect
   the eventual commit to include the pre-existing unrelated diff too,
   since there is no way to stage "only your lines" of one file
   non-interactively (`git add -p` requires an interactive loop this
   account's tooling can't drive).
4. **Before the final commit, run `git status --porcelain` and stage paths
   by exact name** (`git add <path1> <path2> ...`), never `-A`/`.` — then
   re-run `git status --porcelain` immediately after staging and confirm
   the staged (non-space first column) set is *exactly* the list you
   intended, nothing more. This is the same discipline
   `bare-git-commit-sweeps-concurrent-stage.md` prescribes for the
   concurrent case, but it matters here even with zero concurrency: it's
   what keeps a pre-existing dirty tree from ending up half-committed
   under a message that describes neither the old work nor accurately
   describes what actually changed.
5. **Leave the inherited dirty state exactly as found.** Don't try to
   finish, fix, or clean up someone else's evidently-incomplete migration
   as a side effect of your own task — you don't have the context to know
   it's finished, tested, or even the right direction, and folding it into
   your commit (or "helpfully" completing it) attributes work to you that
   you didn't do and haven't verified.
