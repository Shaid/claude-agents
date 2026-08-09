# A correctly-traced sub-routine's own boundary tells you nothing about how far its caller's body continues

**When it bites:** you've confirmed a called routine (`BSR`/`JSR` target) end
to end — real entry, real `RTS`, byte-exact behaviour — and are treating the
surrounding investigation of its *caller* as therefore also complete, especially
when the caller's own disassembly window happened to stop right around the
call site.

## What went wrong

Carrier Command (Amiga) had `$BCCA`/`$BCE6` (a face-list/backface-cull
primitive) traced, confirmed, and documented across two prior sessions —
correctly, down to the exact instruction sequence, with a real `RTS` closing
each routine. A third session's docs explicitly stated "no BSP-node traversal
has been located in the Amiga's `$BCCA`-adjacent code," reasoned from this as
circumstantial support for "real engine simplification vs. the DOS port."

The BSP traversal was not missing. It starts at the very next instruction
after `$BCCA`'s caller (`$B742`) issues `BSR $BCCA` and gets control back —
straight-line code in the *same enclosing routine*, ~4 bytes past the call.
Two sessions' disassembly windows had each stopped examining `$B742` right
around where they'd already confirmed the `$BCCA` call, because `$BCCA`
itself was fully understood and looked like "the end of the interesting
part." Nobody had disassembled the ~250 bytes immediately following the call
instruction in the caller. A fourth session found it in minutes once a wider
`CODE` range in the `.cnf` happened to include that span — not because of new
tooling or a new idea, just because the disassembly output extended a few
hundred bytes further than before.

This is a different trap from `trace-stopped-at-staging-buffer.md` (a
routine's *own* cited end is wrong — not ending in `RTS`, or ending at a
buffer write nothing reads) and from `committed-ira-asm-silent-coverage-gap.md`
(a whole-binary `.cnf` under-covers so most of the file never got
disassembled at all). Here, both the callee *and* the caller up to the call
site were correctly disassembled and confirmed — the gap was purely "nobody
kept reading past the call inside the caller," in code that was already
inside a declared `CODE` range, just past the point investigation happened to
lose interest.

## Fix

When you've confirmed a sub-routine and are about to close out the
investigation of the function that calls it, explicitly check: does the
caller's disassembly continue past the call site, and have you read that
continuation? A `BSR`/`JSR` returning doesn't mean the caller is done — the
very next instruction is still part of the same routine until its own `RTS`.
If a "no X was found nearby" claim in your docs is scoped to "the routine we
already understood" rather than "the enclosing function all the way to its
own end," treat it as unverified, not as a negative result — widen the `CODE`
range a few hundred bytes past the last confirmed call site and re-check
before writing the claim up as evidence either way.
