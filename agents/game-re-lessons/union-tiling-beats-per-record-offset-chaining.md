# Verify a data section by union-tiling every referenced extent, not by chaining each record's offsets

**When it bites:** you are deriving an unknown quantity (a per-record field
count, an element width, a record stride) by requiring each record's data
offsets to *chain* — record `k+1`'s data starts exactly where record `k`'s
ended. Two symptoms say the chain model itself is wrong rather than your
layout:

- the chain succeeds on a **minority** of the corpus and specifically on its
  **simplest** members (files with one record, one channel, one entry), and
  fails on everything larger; or
- two candidate values are **locally indistinguishable** because alignment
  padding rounds them to the same block size, so no amount of spacing
  evidence can separate them.

Both are fixed by the same move: stop asking "does each record own a
contiguous run?" and start asking "does the **set union** of every extent
any record references exactly tile the section, start to end, with no gap
and no trailing slack?"

## What went wrong

Cracking G1A (`_A1G`, Fire Emblem Warriors: Three Hopes, `~/Development/chimera`).
Each spline block lists `c` components as `{keyframeCount, dataOffset}`
pairs, and `c` is not stored anywhere — it is implied by an opcode. Two
attempts to derive it:

**Per-record chaining failed on 355/583 files.** Requiring each component's
data to start where the previous one ended "worked" on 228 files and broke
on the rest. The layout was not wrong — the format **deduplicates identical
constant channels**, so several components, in several *different* spline
blocks, point at the same 16-byte-aligned slot. (A scale channel pinned at
1.0 is stored once and referenced from everywhere.) The 228 files it did
pass were exactly the single-block files, where there is nothing to share
with. Any format that can dedupe identical payloads breaks a chain walk
this way, and it will always look most convincing on the trivial files you
naturally sample first.

**Block spacing could not resolve an off-by-one.** Spline blocks are laid
out contiguously and 16-byte aligned, so `align16(4 + 8c)` gives an 80-byte
block for both `c = 8` and `c = 9`. Spacing is blind to the difference by
construction.

## The fix

Union tiling settled both, with zero deviations across all 583 files:
collect every `[dataOffset, dataOffset + size)` extent any record
references, deduplicate them, sort, and require them to cover
`[sectionStart, sectionEnd)` exactly — no hole between consecutive extents,
no two extents claiming the same start at different sizes, and critically
**no trailing slack**. `c = 9` tiled 583/583 with 0 bytes left over; `c = 8`
also tiled with no hole, but orphaned exactly one 32-byte slot at the end of
each of the 227 affected files. That single trailing-slack byte count is
what separated two readings nothing local could.

The same run refuted the alternates for three other opcodes (their wrong
counts produced 123-144 files with holes or out-of-range extents), so one
invariant confirmed the whole table at once.

**Rule:** a conservation check over the whole section is strictly stronger
than any per-record adjacency check, and it is the only one that survives
payload sharing. Score it on three separate counters — gaps, extent-size
conflicts, and *trailing slack* — because a wrong answer often fails only
the last one. Note the contrast with
`self-consistent-chain-wrong-unit.md`: there, a chain with 0 internal
deviations still needed an independent *terminal* check; here, the chain
premise is wrong outright and the terminal check is the entire test.
