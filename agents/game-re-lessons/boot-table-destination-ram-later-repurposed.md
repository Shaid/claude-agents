# A confirmed ROM->RAM boot copy's destination can be repurposed later for something unrelated

**When it bites:** a static ROM data table's copy-to-RAM mechanism is fully
traced and confirmed (real loop, real count/stride, real source), and you're
about to infer its semantic role from *other* code that reads/writes the
same RAM destination — especially on RAM-scarce hardware (arcade boards,
8/16-bit home systems) where a handful of KB of work RAM is the norm.

## What went wrong

Knights of the Round (CPS1, `kolbold` project): a boot-init routine copies a
confirmed 50-record x 12-byte ROM table into work RAM at a fixed address,
via a fully-traced loop (explicit count, explicit stride, a zero-slack
boundary check against the next known function). Searching for that RAM
address's *other* references (the natural next step to learn the table's
semantic role) found real consumer code — but that code treats the exact
same address as the *head of an unrelated dynamic object-pointer list*
(one of 4 parallel category-pointer slots, each initialized elsewhere to
point at a small buffer), gated by a runtime counter that starts at 0 at
the same boot init. The two roles cannot both be true of the same bytes at
the same time: either the ROM table's content is consumed once early and
then the RAM is overwritten/reinterpreted for the unrelated purpose, or the
"pointer list" consumer code never actually runs against this specific
buffer in practice (its guard counter stays 0). Either way, naively reading
the pointer-list consumer's field offsets as "this is what the ROM table's
records mean" would have produced a confidently wrong semantic label.

## The fix

When a RAM address that received a confirmed one-time ROM copy is also
referenced by other code, do not assume both references describe the same
semantic content. Check, before attaching a label:

1. **Ordering** — does the "other" consumer only run *after* the copied
   table's presumed one-time job is already done (e.g., after a specific
   game-state transition, or gated by a counter/flag the table's own copy
   routine also touches)? If so, the RAM is very likely being reused/
   repurposed, not read back as the original table.
2. **Shape mismatch** — does the "other" consumer's own field layout
   (offsets, stride, pointer semantics) match the ROM table's confirmed
   record shape, or does it imply an entirely different structure (e.g.
   treating the first 2 bytes of record 0 as an address, when the ROM
   table's own bytes there don't look like one)? A mismatch is a strong
   signal of RAM reuse, not a single coherent format.
3. **Guard state at the relevant call site** — if the "other" consumer is
   gated by a counter/flag that is provably 0 (or otherwise inactive) at
   every point the ROM table's content would still be intact, its
   real-world relevance to the table's semantics is moot regardless of
   what its code *would* do if triggered.

Document the ROM table's structure/mechanism as confirmed on its own
evidence (the copy loop, internal field self-consistency), and the RAM-
reuse finding as a separate, explicit open complication — not as grounds to
either force a semantic label onto the table or dismiss the reuse finding
as irrelevant noise.
