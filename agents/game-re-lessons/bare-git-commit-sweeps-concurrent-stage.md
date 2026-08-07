# A bare `git commit` after `git add` commits the whole index, not just your files

**When it bites:** about to run `git commit -m "..."` (no pathspec) in a
repo where other agents may be concurrently working — which several
seer-framework projects explicitly are, per that mission's multi-agent note.

`git add <your files>` only stages your files, but a bare `git commit`
snapshots the *entire index* — including anything another concurrent
process already `git add`-staged for its own future commit. This is silent:
`git status --short` shows other files as staged (first column non-space)
before you commit, and nothing warns you at commit time that you're about
to sweep them in under your own message.

Confirmed: after staging 3 of my own doc files, a bare `git commit -m ...`
picked up 6 files (docs, a shared decoder, viewer code) another agent had
already staged for unrelated work, folding them into my commit with my
commit message describing neither.

**The fix, safe and non-destructive:** `git reset --soft HEAD~1` undoes the
commit while restoring the index to exactly its pre-commit state (staged
stays staged, nothing lost, working tree untouched) — this is not the
`git reset --hard`/`git checkout .` class of destructive command the
Git Safety Protocol warns about. Then re-commit with an explicit pathspec:
`git commit <file1> <file2> ... -m "message"` commits only those paths'
current content regardless of what else sits in the index, and leaves
everything else in the index exactly as it was for its owner to commit
later.

**The habit:** always run `git status --short` immediately before
committing and check for staged (non-space first column) entries you don't
recognize as yours. Never run a bare `git commit` after `git add` in a
shared working directory — pass the exact pathspec to `git commit` itself,
every time, even when you're confident you only staged your own files.

**The mirror direction — it happens *to* you, not just *by* you.** In a
heavily concurrent session (3-4 agents committing on the same branch), a
different agent's bare commit can just as easily sweep up files *you*
staged with `git add` before you got to commit them — you'll only notice
because your own next `git status` shows fewer staged files than expected,
or a `git log` you didn't expect to see. This is not data loss and does not
call for any `git reset`/rebase/history rewrite on a commit you don't own —
in a repo with concurrent agents, treat commit hashes as unstable and
re-check `git log --oneline` before citing one (an agent may amend/rewrite
its own commit's hash between your checks, even against the house style
guidance not to). Instead, verify the content survived intact:
`git show <their-commit> -- <your-file>` (or `git diff HEAD -- <your-file>`
if it's still ahead) to confirm your changes are present and correct, note
the misattribution transparently in your own report, and move on — the
repo state is fine, only the commit message/grouping is imperfect, and
that's a cosmetic cost worth accepting over touching someone else's commit.

**Concurrent modification isn't limited to git's index, and isn't limited
to commits.** Confirmed on `flower` (Drakengard 3): mid-task, `git status`
showed `package.json`/`package-lock.json`/a viewer source file modified
that this session never touched — a different concurrent agent adding an
unrelated dependency/feature — and the shared scratchpad directory already
contained several dozen files from what was evidently that same concurrent
session (matching filenames like `verify_audio_bar.mjs` tied to the
package it was editing). No commit was even in play here; this was pure
`git status`/report-scoping hygiene: before writing a final "files
changed" summary, run `git status`/`git diff --stat` scoped to (or
manually filtered to) only the paths your own task actually touched, and
never assume a scratchpad directory is exclusively yours mid-task — use a
task-unique filename prefix there rather than trusting the directory to
be empty or session-private.
