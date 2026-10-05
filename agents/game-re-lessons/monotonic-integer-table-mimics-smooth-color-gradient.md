# A monotonically-incrementing integer table decodes as a smooth colour gradient under any confirmed bit-packed palette format — smoothness alone is not the oracle

**When it bites:** hunting for palette/CLUT *data* in an unidentified region
by applying an already-confirmed palette-word bit layout (nibble+extra-bit
RGB, or similar) across a wide search space and looking for "smooth,
plausible-looking gradients" as the signal that a candidate block is real
color data.

**Why it happens:** a bit-packed colour format is just an affine unpacking
of a few small integer fields (e.g. a 4-bit nibble plus a 1-bit extra,
combined as `(nibble << 1) | extra`). Any **plain counting sequence** —
`0x0000, 0x0001, 0x0002, 0x0003, ...` — increments those same low bits by
exactly 1 each step, which decodes to a smoothly-changing colour value
purely as an arithmetic consequence of counting upward, with zero relation
to real colour data. A "smoothness" scorer (sum of absolute deltas between
consecutive decoded channel values, or similar) cannot tell the two apart:
both score as maximally smooth. Confirmed on Golden Axe (Sega System 16,
`kolbold` project): a scripted scan for smooth palette-word gradients
across `maincpu.bin` surfaced several strong-looking hits at
`+0x36B4C`/`+0x37A20`/`+0x587AE` that were, on inspection, nothing but
`0x0000, 0x0001, 0x0002, ...` counting tables (likely an index/jump-table
constant, unrelated to colour) — genuinely indistinguishable from real
palette data by the smoothness metric alone.

**The fix — judge candidates on non-monotonicity and semantic specificity,
not smoothness:**
1. Reject (or heavily discount) any candidate block whose raw 16-bit words
   form (or nearly form) a plain `+1` arithmetic sequence — check this
   directly, it's a one-line test, before trusting a smoothness score.
2. Prefer candidates whose decoded output lands on **specific,
   real-world-recognizable colours** (pure red `#ff0000`, pure white
   `#ffffff`, gold/orange tones) via **non-monotonic** raw word values,
   rather than an arbitrary smooth ramp — a real effect-palette table
   (fire, explosion, flash) has semantically meaningful anchor colours a
   counting table does not.
3. Still label the result **hypothesis**, not confirmed, unless a code
   cross-reference (or emulator capture) proves the region is actually
   copied into palette RAM — smoothness plus semantic plausibility is
   corroborating evidence, not a byte-exact oracle. See
   `~/Development/kolbold/docs/goldenaxe/sys16/data-structure.md` §3 for
   the full worked example, including the specific fire/explosion gradient
   that passed this stricter bar and the counting-table false positives
   that didn't.
