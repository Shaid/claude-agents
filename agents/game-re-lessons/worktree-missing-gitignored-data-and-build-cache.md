# An isolated git worktree genuinely lacks `data/`, `build/cache/`, and any other gitignored directory — a real gap, not a path-resolution bug

**When it bites:** starting work in a fresh isolated worktree (`.claude/
worktrees/<id>/`) for a seer-framework (or similarly-shaped) project whose
`data/` (original game files), `build/cache/` (vendored tool binaries,
non-web pipeline intermediates), and `public/assets/` directories are all
gitignored — the first `Read`/`Bash` touching `data/<game>/<platform>/...`
or a vendored tool path (e.g. `build/cache/tools/vgmstream/...`) returns
"file not found," even though the exact same path is real and populated in
the main checkout.

**Why this happens, and why it's different from the "wrong checkout"
trap.** `git worktree add` only materializes tracked files — anything the
project's own `.gitignore` excludes (multi-GB original game dumps, vendored
tool builds, generated pipeline output) simply doesn't exist in the new
worktree directory at all, by design. This is not the same failure as
`absolute-path-silently-escapes-isolated-worktree.md` (accidentally reading
the *main checkout's* copy via a stale absolute path from the task prompt)
— here the worktree's own relative path is correct, the content is just
genuinely absent, because it was never meant to be per-worktree in the
first place. `data/`, `build/cache/`, and `public/assets/` are large,
slow-to-regenerate, and identical across every worktree of the same
project — there's no reason to duplicate them, and every worktree is
expected to share the one real copy sitting in the main repo.

**The fix, confirmed working**: symlink the gitignored directory (or the
specific subpath actually needed) from the worktree root back to the main
repo's real path — `ln -s /path/to/main-repo/data data` (run from the
worktree root) makes `data/<game>/<platform>/...` resolve transparently for
every tool in the session (Node's `fs`, Python, shell redirection) exactly
as if it were a real local directory, with zero code changes needed. Same
technique for a vendored build artifact discovered mid-session (e.g. a
prebuilt `vgmstream-cli` binary already sitting in the main repo's
`build/cache/tools/vgmstream/` from an earlier pass): `mkdir -p
build/cache/tools && ln -s /path/to/main-repo/build/cache/tools/vgmstream
build/cache/tools/vgmstream` avoids a redundant from-source rebuild.
Confirmed on a NieR (2010, Xbox 360) first-pass session in
`~/Development/flower` — both `data/` (a 7.8GB ISO) and a vendored
`vgmstream-cli` binary were missing from the isolated worktree at session
start; both were resolved with a one-line symlink each, with no impact on
git status (a symlink named exactly what an already-`.gitignore`d pattern
matches doesn't get staged even by an unqualified `git add`, but double-
check `git status` shows it as untracked/ignored before any broad `git
add`, rather than assuming the trailing-slash `.gitignore` pattern always
catches a symlink the same way it catches a real directory).