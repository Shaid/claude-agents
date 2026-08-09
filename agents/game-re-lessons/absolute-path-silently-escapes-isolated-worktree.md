# An absolute path handed to you in the task prompt (e.g. "project root: /path") can silently read/write the wrong checkout in an isolated-worktree session

**When it bites:** You're told you're running in an isolated git worktree
(the environment block's "Working directory" line, and/or an explicit
instruction like "you're in an isolated worktree, so you don't need to worry
about concurrent agents' uncommitted work here"), but the task prompt also
states a bare project-root path (e.g. "Project root: `/home/user/project`")
that predates the worktree and points at the shared main checkout instead.
Any `Read`/`Bash`/`Grep`/`Glob` call built from that bare root — rather than
the actual worktree root — resolves successfully to a real, existing
directory and returns real-looking content, with no error, no warning, and
no indication anything is wrong.

**What actually happens.** `Read`, `Bash` (`cat`, `grep`, etc.), `Grep`, and
`Glob` have no awareness of "which checkout you're supposed to be scoped
to" — they just resolve whatever absolute path they're given. Only `Edit`
and `Write` are guarded: attempting to edit a path outside the recognized
worktree tree triggers a hard refusal ("Edit the worktree copy of this file
instead of the shared-checkout path"). This means a long stretch of
research (reading docs, tracing code, grepping for a symbol) can happen
entirely against the wrong copy before the first `Edit` call finally
surfaces the mistake — by which point every fact gathered needs
re-verification, and if the two checkouts have already diverged (a
concurrent session committed to the main checkout, or main advanced past
where the worktree branched), there's no way to tell from content alone
which copy is "correct" without an explicit diff.

**Confirmed cost**: a FFVI (SNES) session read `docs/ffvi/TODO.md`,
`docs/ffvi/snes/data-structure.md`, and five `tools/ffvi/*.ts` source files
via the main checkout's absolute path (taken from the task prompt's "Project
root: ..." line) for the first third of the session — the `Bash` tool's cwd
was correctly the worktree the entire time, but that has no bearing on
whether an *absolute* path passed to `Read`/`Bash`/`Grep` happens to land
inside it. The mistake was only caught when an `Edit` call on
`tools/shared/snes-ppu.ts` was refused by the harness's safety check. A
`diff` between the two checkouts at that point revealed the main checkout
had already been modified by a concurrent, unrelated session (a different
`TODO.md` row, a new doc section) — meaning some of what had been "read"
minutes earlier no longer even matched the main checkout's current state,
on top of never having matched the worktree at all.

**The fix.** Never reuse a bare project-root path stated in the task prompt
for building absolute paths once you know you're in an isolated worktree —
construct every absolute path by joining the actual worktree root instead
(read it from the environment block's "Working directory" line, or from
`git rev-parse --show-toplevel` run via `Bash`, whose cwd *is* reliably the
worktree). If a path handed to you or recalled from context doesn't
visibly start with the worktree's own prefix (typically containing
`.claude/worktrees/<id>/`), treat it as suspect before trusting a `Read` of
it. When in doubt, `diff` the same relative path under both roots before
proceeding — a clean diff means no harm done yet; a divergent one means
everything read from the wrong root needs re-verification against the real
worktree copy.
