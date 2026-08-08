# The session-shared scratchpad tmpfs can fill to 100% mid-task, breaking every Bash call including trivial ones

**When it bites:** a Bash tool call fails with `Command output was lost:
the temp filesystem at .../tasks is full (0MB free)` — including for a
command as trivial as `echo hi` — partway through a session, especially
one where multiple agents (a forked escalation, a background subagent, an
earlier pass of the same overall session) have run substantial work before
you.

The scratchpad directory this agent is told to use for temp files
(`/tmp/claude-<uid>/<project>/<session-uuid>/scratchpad/`) is **shared
across every agent in the same session**, not private to the current
turn — and so is the adjacent `tasks/` directory the harness uses to
capture every Bash call's own stdout/stderr. Confirmed on Chaos Legion
(`flower` project): a prior pass's completed Drakengard/DMC work had left
several multi-gigabyte directories in this same shared scratchpad (a
2.4GB `dmc/` texture dump, a 1.2GB `export-bulk-test/`, a 346MB
`gltf-batch/`) — harmless leftovers from already-finished, already-
committed work, but never cleaned up. The whole `/tmp` tmpfs (16GB in this
environment) crept to 100% used while later work in the *same* session
(matplotlib probe renders, `npx tsx` runs) added its own smaller files on
top, and once it hit 100%, **every** subsequent Bash call failed at the
harness level — the shell itself never even executed, because the
harness's own per-call output-capture file couldn't be written.

**This is not the `vite-dev-server-enospc-large-cache-dir.md` issue** —
that one is an inotify *watch-count* limit tripped by a project's own
`build/cache/`/`public/assets/` tree and only breaks `npm run dev`. This is
raw tmpfs *disk space* exhaustion in a directory outside the project
entirely, and it breaks the Bash tool itself, not any one dev process.

**Recovery, and the judgment call it requires**: `df -h /tmp` confirms the
symptom (near-100% used, near-0 available) once at least one Bash call
succeeds again (a `dangerouslyDisableSandbox: true` call may get through
even when the sandboxed default doesn't, since the sandbox's own overlay
can have a separate, smaller effective ceiling than the raw tmpfs). The
scratchpad is shared with *other, possibly-still-relevant* agent work, so
blindly `rm -rf`-ing it risks deleting something a concurrent agent still
needs (see `shared-tool-session-clobbered-by-fork.md` for the general
"don't clobber shared session state" caution) — but doing nothing leaves
you completely unable to work. The defensible middle ground: delete only
the *largest, clearly-stale* directories (multi-GB dumps corresponding to
work items already documented as complete/committed elsewhere — e.g.
named after a game/feature whose corpus entry already reads "solved" —
not directories with a name suggesting active, unfinished work), leave
everything else untouched, and confirm the deletion actually freed enough
headroom (`df -h /tmp` again) before resuming normal work. Some files may
fail with `Permission denied` (owned by a different active process/agent
still holding them) — that's a real, useful signal the directory is
*not* safe to fully remove, not just an error to route around.
