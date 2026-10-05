# A code-block corpus builder's own `isPrologue(word0)` gate can silently drop a whole legitimate overlay from every subsequent census

**When it bites:** about to trust a "zero hits anywhere in the widened
corpus" result — especially one being used to close an item as "provably
safe" / "confirmed absent" / "never reassigned" — that was produced by a
from-scratch code-block or overlay corpus builder which filters candidate
blocks by "does this look like code" (an `isPrologue(word0)` check, or any
similar structural start-of-block heuristic) before including them. Bites
hardest on a multi-link/chained container format, where a block's own
declared start offset need not coincide with any function boundary at all.

## What went wrong

Valkyrie Profile (PSX, `valkyrie` project): several rounds' worth of
"widened corpus" censuses (nested SLZ code sub-blocks + top-level overlays
+ both boot executables) had committed a check reading "Pool base-pointer
slot `*(0x8007f0e8)` is never reassigned anywhere in the widened corpus" —
PASS, "0 write site(s)", every time it ran. That result was trusted as
strong evidence for closing an open item about whether a resident task
pool's backing memory could ever be freed/reallocated.

It was wrong in the specific way that matters most: not just incomplete,
but *structurally blind to the one place the answer could ever live*. The
corpus builder's `collectNestedCodeBlocks()` requires a decoded block's
very first 32-bit word to be a canonical `addiu $sp,$sp,-N` stack-frame
prologue before accepting it into the searchable corpus at all. The one
overlay that actually contains the pool's cold-boot tag-registration/
publish routine (`codeoverlay_slot2293.bin`) is itself SLZ-chained — its
own container format links several compressed sub-blocks end to end via a
`chainStride` field — and that overlay's first chain link happens to
*start* mid-function (word 0 disassembles as `lw $v1,0x1c($sp)`, not a
prologue at all, because the link boundary and a function boundary don't
coincide). The gate rejected the block outright, so the ENTIRE overlay —
22,528 real bytes on disc 1 — was invisible to every census built on top
of this corpus, across multiple prior rounds, with zero indication anything
was missing. A second, compounding gap in the same tool chain made it
worse: the project's own `loadFlatSlotImage()` helper (used by many other
scripts, not just this census) only decodes the FIRST `chainStride` link of
a chained overlay in the first place — so even a fix to the `isPrologue`
gate alone would still have missed the other 19,584 bytes.

The fix that closed it: read the overlay directly from its own leftover
build-cache file (a full, non-chain-truncated decode from an earlier
session) and scan its raw bytes for the target pattern with **no**
`isPrologue`/structural gate of any kind. The expected single write was
found immediately, exactly where a *different*, earlier investigation into
an unrelated question had already located the same registration routine
(`dungeon-field-mechanics.md`'s tag-7 publish site) — the project's own
docs already contained the fix for this exact overlay, just not cross-
applied to this census (`doc-self-cross-reference-before-fresh-
disassembly.md`, yet again).

## Fix

An `isPrologue`/"does this look like a function start" filter is a
reasonable heuristic for *classifying candidates you intend to name and
disassemble as functions* — it is not a safe gate for **corpus membership**
in a census whose whole point is proving a global negative ("this value is
never written/read/freed anywhere"). Before trusting such a negative:

- Check whether the corpus builder that fed it filters blocks by any
  structural "looks like code" test, and if so, whether the item you care
  about could plausibly live in a block that test would reject (a mid-chain
  SLZ/compressed link, a jump-table-preceded routine, anything not starting
  exactly at its own function's first instruction).
- For a chained/multi-link container format specifically, verify the
  corpus actually covers **every** link, not just the first — a helper
  that "decodes the block" may silently mean "decodes the first chain
  link" for this format, which is its own separate, compounding gap.
- When in doubt, re-run the search directly against the raw decoded bytes
  of the specific suspect unit with the gate removed entirely — this is
  cheap (one targeted script) and turns a corpus-wide "maybe blind"
  worry into a definite yes/no for the one block that matters most.

Related but distinct traps this isn't a duplicate of: a hardcoded
tag/magic-offset assumption silently skipping real instances outside the
sampled range (`detector-offset-generalized-from-partial-corpus-silently-skips-rest.md`),
a chain-walker stopping at the first block magic it doesn't recognize
(`block-chain-walk-stops-at-unknown-sibling-block-magic.md`), and
back-scanning to the wrong function entry point for a single, specific
target (`spawner-install-literal-outranks-backscan-prologue.md`) — this
lesson is about a corpus **builder's own inclusion filter** dropping a
whole unit before any target-specific search logic even runs.
