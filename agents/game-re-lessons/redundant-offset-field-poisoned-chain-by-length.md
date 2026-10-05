# A directory's redundant cumulative-offset field can be poisoned two different ways in one format family — chain by `length` instead

**When it bites:** a container's directory stores both a per-slot `length`
*and* a redundant absolute/cumulative end offset, your shared parser
resolves each slot from the redundant field, and either (a) some files come
back with fewer slots than the header's `slotCount` declares while the
lengths all look real, or (b) the header's `firstBlockStart` disagrees with
`8 + slotCount * entrySize`.

The redundant field is redundant precisely because nothing needs it to be
right, so producers poison it in ways that never break the game:

- **End-of-table sentinel.** The *last* slot's cumulative-end word carries a
  marker instead of an offset while its `length` stays real. A parser
  computing `start = cumulativeEnd - length` gets a negative or absurd
  start, fails a bounds check, and drops a genuine payload **silently** —
  no error, and the slot simply doesn't appear in the result. Observed
  values in one game alone: `0` (`nx/stage/info/S###-Info.bin.gz` — a real
  2,488-byte slot vanished), `0` again (`nx/stage/obj/S###-ObjInfo.bin.gz`),
  and `0xFF000000` (`common/battle/stage/area*.gz`).
- **Truncated descriptor table.** The producer simply never writes the final
  redundant word, and `firstBlockStart` points 4 bytes *before* the nominal
  table end — so the last "cumulativeEnd" you'd read is actually the first
  word of slot 0's payload. Confirmed on the same game's
  `common/StageNature.bin.gz`: `slotCount = 3` implies a table ending at
  `8 + 3*8 = 32`, but `firstBlockStart = 28`, i.e. `8 + (n-1)*8 + 4`. Its
  nested packs do the same (`<1, 12>`, `<2, 20>`). Nothing is corrupt; the
  last slot's end is simply implied by EOF.

**Fix, and it handles both:** ignore the redundant field entirely and chain
from `firstBlockStart` by each slot's own `length`. Then assert the chain's
terminal value against the file's real size — on the corpus above,
`firstBlockStart + sum(length) === fileSize - 8` held with 0 deviations
across all 19 files (the 8 bytes being zero padding), and `=== fileSize`
exactly for `StageNature`. That single terminal check is what upgrades
"my walker didn't throw" into a real invariant; see
`self-consistent-chain-wrong-unit.md` for why internal self-consistency of
a running sum proves almost nothing on its own.

**The silent-drop failure mode deserves its own alarm.** If
`firstBlockStart + sum(length)` equals the file size but your shared parser
returns fewer slots than there are non-zero lengths, you are looking at a
dropped sentinel slot, not at padding. Twice in one project that was
misread as "that slot is unused padding," and each time the dropped slot
held a real, undecoded payload. Don't "fix" the shared helper in place
either if other callers depend on its drop-on-out-of-range behaviour —
export a length-chaining walker alongside it and document which files need
which.
