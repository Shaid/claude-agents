# Partial-hunk commits from concurrent agents can leave HEAD uncompilable while the working tree is green

**When it bites:** several agents edit the same file (a build registry, a shared doc) in one work tree, and each commits "only my hunks" by staging a filtered diff (`git apply --cached`, a hand-trimmed patch). Every agent's `tsc`/tests pass, because they run against the working tree. HEAD is a file state that never existed on disk.

A hunk applied to the index against a different base than the one it was cut from can land at the wrong context: a call inside an object literal, a line after a closing brace, a property outside its object. Nothing checks HEAD, so the breakage surfaces only for the next clean checkout, CI, or a worktree. A sibling who instead stages the whole file commits your hunks under their message.

**Check / fix:**
- After each partial commit, `git diff HEAD -- <file>` for every touched file. None of your own hunks should remain, and what is left should be recognisably the siblings'.
- Type-check HEAD itself, not the tree: `git worktree add <scratch>/head HEAD`, symlink `node_modules`, run `tsc --noEmit` (and the build's own smoke step) there, then `git worktree remove`. An orchestrator should do this once per batch of concurrent agents.
- An agent that cannot stage its change cleanly should hand the commit to the orchestrator rather than partial-stage. Commit docs together with the code they describe, so siblings don't sweep them up.
- Repair is a forward fix commit built from the working tree's known-good file, never a history rewrite.

**Canonical example:** lucina (FE / 3DS builds), 2026-11-21. After a batch of four concurrent agents, HEAD had `buildBevCameras(...)` inside the audio-spec array, `buildFeSheets` after `source.close()`, and `effect: 'Effects'` outside its object. That was 5 `tsc` errors at HEAD and 0 in the working tree. A forward fix commit repaired it, and an earlier commit had swept another agent's uncommitted doc hunks in.

Related: `bare-git-commit-sweeps-concurrent-stage.md` (whole-index sweep), `inherited-dirty-tree-entangles-unrelated-commit.md`, `concurrent-sibling-live-edit-collision-on-shared-source.md`, `worktree-missing-gitignored-data-and-build-cache.md` (what a HEAD worktree lacks).

**History:** 1 project (lucina), 2026-11.
