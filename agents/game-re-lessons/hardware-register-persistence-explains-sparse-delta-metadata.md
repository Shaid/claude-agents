# A small, per-record metadata field with a widely varying entry count is likely a stateful hardware-register delta, not a self-contained per-record table

**When it bites:** a repeating record (a draw-call/block header, a GPU
command packet) carries a small variable-length trailing array whose entry
count doesn't correlate cleanly with any other field in the SAME record
(here: block header `extraWords` ranged 0-5 with no fixed relationship to
the block's own `weightCount`, which should determine how many bone
matrices the block "needs"), and a per-record self-contained reading of
that array leaves some entries looking anomalous or under-specified
compared to siblings.

## What went wrong (and the fix)

The 3rd Birthday (PSP)'s `pack` container geometry blocks are literal PSP
GE (`sceGuDrawArray`) hardware vertex-array uploads. Each block header
carries `extraWords` (0-5) pointing at a small trailing `u32[extraWords]`
array, hypothesized across two prior sessions as "bone/matrix-palette
related" because the corpus's vertices carry real, confirmed skin weights
(sum-to-1.0, 0 exceptions across 318,336 vertices). A per-block reading
("this block's own complete bone list") looked plausible for a couple of
worked examples (`(0,1)`, `(1,2)`, `(2,3)` — an ascending range) but broke
on the very next sample (`(0,0)` for a different pack's first block) and
left `extraWords` counts that didn't scale with `weightCount` at all
(many `weightCount=2..5` blocks had only `extraWords=1`).

**The fix was to stop treating the array as self-contained and treat it as
a stateful delta against the REAL PSP GE hardware's own persistence
model.** The PSP's GE has a small bank of "bone matrix" registers
(`sceGuBoneMatrix(index, matrix)`), and — like most fixed-function GPU
register state — their contents **persist across draw calls**. A
competent renderer only reissues the registers that actually changed
since the previous draw, to save upload bandwidth. Once the block array's
`extra[]` words were re-read as `(slotIndex: u16 low half, boneId: u16
high half)` deltas applied to a **running, per-pack, cross-block** state
array (reset only at the start of each pack's geometry region, never
per-block), every single data point that had looked exception-shaped
resolved cleanly:

- The "anomalous" `(0,0)` first-block case is just "slot 0 <- bone 0" —
  the ordinary, unremarkable first assignment for a single-bone rigid prop
  (a building facade whose every block stayed at bone 0 throughout).
- `extraWords=1` blocks with `weightCount=2..5` are blocks that only
  introduce ONE new bone matrix relative to the previous block; the other
  slots are implicitly retained from whatever an earlier block last
  loaded into them.
- A 5-block vehicle prop resolved to 5 independent single-bone blocks
  (one bone id per rigid part — wheels/body/turret), while a 106-block
  environment/foliage prop resolved to smoothly overlapping *chains* of
  adjacent bone ids (block N retains most of block N-1's assignment and
  adds/replaces one slot) — two structurally different, both internally
  consistent, usage patterns from the *same* decode rule.

Verification: implementing the stateful delta decode and running it over
the WHOLE corpus (5,584 blocks, 231 packs) produced **zero contradictions**
— no block ever referenced a delta slot `>= weightCount`, and every slot
`0..weightCount-1` always resolved to a defined bone id once the running
state was applied (never `undefined`). A decode rule with zero exceptions
across a large real corpus, recovered from re-reading two failed
per-record hypotheses through a "this mirrors a real, documented hardware
persistence convention" lens, is strong evidence on its own — no external
oracle was needed to reach this confidence level.

## The generalizable check

Before concluding a small per-record metadata array is broken, sparse, or
holds "a second undiscovered id space," ask: **does the record type map to
a real GPU/hardware command whose target state is known to persist across
issues (register banks, cached texture bindings, blend/depth state,
bone/matrix palettes, uniform buffers)?** If so, try re-reading the array
as a **stateful delta list scoped across the whole draw sequence** (not
just this one record) before hunting for a second table or escalating.
The tell that you're looking at exactly this shape: entry counts that
don't scale with an otherwise-expected "this record's own full
requirement," and specific values that only make sense in light of an
assumed *carried-over* prior state rather than as a complete, self-
sufficient specification.

## What this does NOT solve

Decoding *which* weight slot maps to *which* bone-matrix-register id is a
different problem from finding the **matrix data itself**. In this case,
no static bone/matrix transform table was ever located anywhere in the
container (checked: the container's own small pointer-addressed
tables, a brute-force self-consistent block-header rescan of every
unexplained byte region, and a corpus-wide `u32 count` sweep for a
plausible-sized float32 table) — and the retail executable that would be
the authoritative source of any procedurally-computed transforms was a
`~PSP`-tagged (KIRK/AMCTRL-encrypted) EBOOT with no decryption tooling
available. A model can render correctly in **bind pose** with the bone
IDs alone (identity transforms are a no-op), which is exactly what let
this format ship as static geometry for two prior sessions without
anyone needing to solve the delta list at all — see
`bind-pose-render-blind-to-joints-index-space-bug.md` for why bind pose
can never be evidence that a skinning/rigging chain is complete.
