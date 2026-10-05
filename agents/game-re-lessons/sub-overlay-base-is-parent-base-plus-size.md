# A missing overlay's load base can be an already-known overlay's base plus that overlay's own size, not a fresh fixed constant

**When it bites:** a whole-corpus census for a writer/caller has come back
empty across every already-cached top-level overlay (a real, structural
negative — the code genuinely isn't in any of them), and the leading
hypothesis is "the code lives in an overlay this project hasn't
extracted/based yet." Before falling back to a blind load-address sweep
over a huge range, or giving up on locating it at all, check whether the
missing overlay is a **sub-overlay layered arithmetically on top of an
already-known overlay's own extent**.

Most projects in this account's corpus establish "multiple overlays share
one fixed load address" (several top-level overlays entered at the same
literal constant, at different times in the game) as their baseline
overlay model. This is a *different*, second pattern worth checking
separately: a menu/sub-system overlay whose own base is not any
already-known fixed constant, but is derived as `knownOverlayBase +
knownOverlaySize` — i.e. it's linked to load immediately after another,
already-cached overlay's own decompressed extent, forming a two-tier
stack (parent overlay first, then its own sub-overlay layered on top)
rather than sharing one address independently.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project): two structurally
distinct negatives (a whole-corpus fixed-displacement census, then a
second whole-corpus computed-base census) both failed to find a real
field writer, because the writer's overlay (a "menu sub-overlay" family)
was never in the cached file set at all. A `re-codebreaker` escalation
found it by first locating the missing overlay's **callers** via a
corpus-wide `jal`-target scan for a sibling function's own known address,
which pinned the caller code inside 3 specific compressed blocks — then
recovered those blocks' real load base with the project's own already-
established base-*dependent* prologue-density test (the same technique
used to confirm ordinary overlay bases), swept over a plausible address
range. The base that won decisively (10/43, 13/58, 5/36 prologue hits vs.
≤3 for every runner-up in the sweep) turned out to **exactly equal**
`slot2174_base + slot2174_decompressedSize` — slot 2174 being an already
fully-cached, already-based sibling overlay found earlier in the same
project.

**How to apply it:** when a base-recovery sweep is needed for a newly-
located but not-yet-based code block, don't only try round/plausible
fixed addresses (`0x80050000`, `0x80060000`, ...) — also compute
`existingOverlayBase + existingOverlayDecompressedSize` for every
already-confirmed overlay in the project and add those as candidates to
the same base-dependent prologue test. A sub-overlay adjacency hit is
cheap to test and, when it's the real answer, is indistinguishable from
luck only until you check it — the size-derived candidate either wins
the sweep decisively (as here) or it doesn't, at effectively no added
cost over the sweep you were already running.

**Second instance, and the cheaper direct test (Valkyrie Profile, PSX,
2026-09-27, `re-oracle`).** Four rounds (~2.4 GB/disc, four call
mechanisms) found no caller for an "item-table build routine" cited at
`0x8002fa9c` inside TOC slot 2293 — because that address was derived by
applying the *resident overlay runner's* fixed destination (`0x8002f824`,
true for every overlay that runner launches) to a slot the runner never
touches. Slot 2293 is a sub-module the **field overlay loads itself**, and
the field overlay's own loader decompresses it to `fieldBase +
fieldDecompressedSize = 0x8002f824 + 0x5a18c = 0x800899b0` and `jal`s
`0x800899b0 + 0x278` directly, 60 bytes later. No sweep was needed: **grep
the slot number as an immediate** (`addiu $rX,$zero,0x8f5` = 2293) next to
the project's already-confirmed resource-load primitives (`resourceSize`/
`loadSlot`/`decompress`) — the loader's own `lui`/`addiu` destination
operand is the base, as ground truth, in one read. Three tells that the
inherited base was wrong were visible in the file's own bytes all along:
its internal `jal`s "called into another module's base" instead of its own
function starts; its absolute `j`s were read as "trampolines out"; and it
`jal`'d nine functions of the very overlay it was supposedly loaded on top
of. A sub-module that calls its parent overlay's functions cannot share the
parent's base — that alone refutes the premise before any search.
