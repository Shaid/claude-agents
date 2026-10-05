# A common-`jsr`-target census across per-type entry stubs can miss a shared subroutine called from deeper inside each body

**When it bites:** hunting for a shared/engine-wide subroutine (a generic
render/animate/build-record primitive) among many per-type or per-object
handler routines, and a "census the calls made from each routine's own
entry point / shared prologue" pass comes back with only the already-known
generic prologue calls (pause-check, collision-check, etc.) — tempting a
write-up that "no shared consumer subroutine exists" or "needs one more
level of dispatch resolution, not reached this session."

## What went wrong

D&D: Shadows over Mystara (CPS2, `kolbold`): two prior sessions searched
for whatever writes a boss object's real hardware sprite tile code. Both
scoped their search to what each of 23 large-monster-type routines calls
**at or near its own entry point** — first a per-type field census
(`$7e(a0)`/`$80(a0)`), then a "common `jsr` target across all 23 routine
*addresses*" census. The second found exactly two near-universal targets,
both reached from the identical shared per-frame prologue every routine
starts with, and concluded no shared "build my sprite record" subroutine
existed reachable from there — a structurally sound-looking negative.

The real routine (`opcodes+0x1a32`, a genuinely engine-wide "start
animation #N" primitive, also called from an unrelated item/chest-reveal
system) is called from **inside** a type's own state-0 body, well past
the shared prologue — reached via ordinary state-machine logic specific
to that type, not from the entry stub the census scoped its search to. No
per-caller census bounded to "what the routine's top level calls" could
ever find it, no matter how many sibling routines were compared, because
the call site's *position* inside the body (not just its target) was the
part the census design couldn't see.

## Fix

When a scoped "common callee across N sibling entry points" census comes
back with only known/generic hits, don't conclude the target subroutine
doesn't exist — flip the search direction. Byte-pattern-census the
**callee's own call instruction** (e.g. a 68k `jsr $ADDR.l`'s literal
opcode bytes) across the **whole** binary, not just the sibling set
already in hand. This is unbounded by call depth or by which specific
routines you already knew to compare, and it directly answers "is this a
real, shared, non-type-specific primitive" — a large hit count (524 sites
here) across unrelated subsystems is itself strong confirmation. Only
after finding at least one real call site should you trace inward from
there to resolve type-specific parameters (the per-type animation-table
address, in this case) — trying to find the shared machinery by comparing
entry-point call lists is the wrong direction entirely.

This is a close sibling of `sibling-functions-outside-callgraph-scope.md`
(an input can live in a caller's sibling, not caller/callee) and
`jump-table-noop-means-handled-elsewhere.md` (the real reader is a
separate routine reached a different way) — the common thread across all
three is that a caller-side/entry-point-side search has an implicit scope
boundary the target doesn't respect, and the fix is always to search from
the target's own identity (its address, its opcode bytes) outward, not
from an assumed caller set inward.

**Once you do run that unbounded whole-binary census, one more trap
waits:** a wide-looking caller-address spread doesn't by itself prove the
callee is genuinely shared/external — it can just as easily be many
internal call sites inside ONE large per-type routine. See
`unbounded-caller-census-crosses-sibling-routine-boundary.md` before
treating hit-count spread as confirmation of sharing.
