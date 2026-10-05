# An isolated agent worktree can be locked at a commit far behind `main`'s tip, missing every file the task references

**When it bites:** starting work in a freshly-assigned isolated worktree
(`.claude/worktrees/<id>/`) and a `Read`/`Edit`/`Bash find` for a file the
task brief explicitly names — or that the shared main checkout clearly
has — reports it as simply not existing. `git status` in the worktree
shows a clean tree ("nothing to commit"), so it isn't an uncommitted-work
problem; the worktree is just checked out at an old commit.

**Why this happens, and how it differs from the other two worktree
traps.** `absolute-path-silently-escapes-isolated-worktree.md` is about
accidentally reading the *main checkout's* copy via a stale path; `worktree-
missing-gitignored-data-and-build-cache.md` is about gitignored directories
that were never meant to be per-worktree. This is a third, distinct
failure: the worktree's own git branch is real and correctly scoped, but it
was created (or last advanced) for an earlier, unrelated task and never
fast-forwarded — `git worktree list` shows it locked dozens or hundreds of
commits behind `main`. Confirmed on a Valkyrie Profile (PSX) session: the
assigned worktree was locked at a commit 113 commits behind `main`'s tip,
entirely predating the feature branch the task was about (`src/engine/`
and `docs/valkyrieprofile/psx/battle-engine-spec.md` did not exist in the
worktree at all, despite the task brief quoting their exact contents). The
mistake surfaced the same way the first worktree trap does — a `Read`
against the shared-checkout path (to sanity-check the missing files)
worked fine, and the first `Edit` call against that path was refused by the
harness ("Edit the worktree copy of this file instead"), which is what
actually revealed the worktree itself was the problem, not the path.

**The fix, confirmed safe and working.** Don't reset or rebase blindly —
first confirm the worktree branch has no divergent work of its own:
`git status` (clean), then `git merge-base --is-ancestor <worktree-HEAD>
main` (exits 0 if the worktree's current commit is a strict ancestor of
`main`, i.e. zero unpushed/unique commits sitting only on this branch).
When both hold, `git merge --ff-only main` from inside the worktree is a
plain, non-destructive fast-forward — no `reset --hard`, no risk of
discarding anything, and it fails loudly (refuses to merge) instead of
silently overwriting if the branch turns out to have diverged after all.
After fast-forwarding, re-verify: `md5sum` the specific files the task
referenced in both the worktree and the shared checkout and confirm they
match byte-for-byte before trusting any analysis already done against the
shared-checkout copy (reading it to diagnose the missing-file problem in
the first place doesn't taint the session — re-reading everything through
the now-correct worktree path afterward, or confirming the hashes match,
is what makes it safe to keep using). This generalizes to any
worktree-isolated agent task in this account's fleet setups, not just
game-RE or this project.
