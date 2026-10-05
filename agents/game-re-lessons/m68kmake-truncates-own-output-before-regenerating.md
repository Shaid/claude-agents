# musashi's m68kmake truncates its own output files to 0 bytes before regenerating them

**When it bites:** vendoring or rebuilding a musashi 68000-core checkout
that ships pre-generated `m68kops.c`/`.h` (the bulk of the core's opcode
handler tables, produced from `m68k_in.c` templates), and a build script's
"do I need to regenerate?" guard checks for the `m68kmake` *binary*'s
presence rather than the *generated files themselves* — or an `m68kmake`
run is about to be started, retried, or killed partway through.

`m68kmake` opens `m68kops.c`/`.h` for writing (truncating them to 0 bytes)
at the *start* of a run, before it has generated any replacement content —
so an already-vendored, known-working copy of these files is destroyed the
instant a regeneration run starts, regardless of whether that run ever
finishes. This is a real risk because the run can take many CPU-minutes
with zero progress output in a constrained/sandboxed environment (confirmed
12+ CPU-minutes of steady 99% CPU with negligible memory growth on one
session's environment, for a job that behaves as near-instant on typical
unconstrained hardware) — long enough that a caller times out, gets
impatient, or kills it, and by then the previously-working files are
already gone.

Confirmed on Powermonger (Amiga): rsyncing a vendored `musashi/` tree from
a sibling project while excluding the prebuilt `m68kmake` binary (but
keeping the already-generated `m68kops.c`, 794 KB) caused a build script's
`if [ ! -x m68kmake ] || [ ! -f m68kops.c ]; then regenerate; fi` guard to
trigger regeneration anyway (the binary's absence alone was enough) —
killing the resulting runaway process left `m68kops.c`/`.h` as 0-byte
files, requiring a fresh copy from the sibling project's own already-built
vendoring of the same musashi checkout to recover.

**Fix:** when vendoring a pre-built `musashi/` tree (or any
codegen-then-compile C library with this same "generator truncates its own
output first" shape) for reuse in a new project, treat the *already-
generated* output files as the thing worth checking for and reusing
directly — gate the skip-regeneration check on their presence/non-emptiness
(`[ -s m68kops.c ]`), not on the disposable `m68kmake` binary (which is
safe to exclude from a vendoring copy without consequence, since you're not
regenerating anyway). If regeneration is genuinely needed (e.g. upgrading
musashi versions), do it as a deliberate, isolated step — never as a build
script's automatic fallback triggered by an incidental missing file.
