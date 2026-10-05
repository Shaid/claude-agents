# Bit order in a 1bpp grid is decidable with no oracle at all — compare horizontal vs vertical transition counts

**When it bites:** a 1-bit-per-cell bitmap (navigation/collision grid,
tile-passability mask, fog-of-war map, 1bpp font page) has been located and
its dimensions are known, but MSB-first vs LSB-first within each byte is a
coin flip — and the available ground-truth oracle either doesn't exist yet
or separates the two options only weakly.

Count adjacent-cell differences in both axes: `H` = pairs differing along a
row, `V` = pairs differing along a column. **`V` is bit-order-invariant by
construction** — swapping bit order permutes cells *within* a row and never
moves a cell between rows, so the column pairings are untouched. That makes
`V` a free, built-in control: the correct bit order is the one whose `H` is
comparable to `V` (a real 2D shape is roughly isotropic), and the wrong one
inflates `H` alone, because reversing bits inside every byte injects
high-frequency noise along the row axis only.

Confirmed on Fire Emblem Warriors (Switch, `chimera`), a 256x256 1bpp stage
navigation grid, 19 stages:

| Bit order | H | V | H/V |
|---|---|---|---|
| LSB-first | 22,412 | 23,872 | **0.94** |
| MSB-first | 43,236 | 23,872 | 1.81 |

`V` identical across both rows is the control firing exactly as predicted,
which is what makes the `H` comparison trustworthy rather than just
suggestive. The same corpus's independent oracle — already-decoded
`EventPoint` markers landing on walkable cells — separated the two orders
only 53/54 vs 48/54, i.e. it *preferred* the right answer but nowhere near
decisively. The transition ratio separated them nearly 2:1, needed no
ground truth, and cost one numpy expression.

Two extensions of the same idea, both cheap:
- **Axis order** (is the row index X or Z?) is *not* decidable this way —
  transposing preserves the multiset {H, V}. Use an external oracle for
  that; on the same corpus, transposing dropped the EventPoint hit rate
  from 53/54 to 26/54, i.e. to chance.
- **Sense** (does bit set mean walkable or blocked?) is likewise invariant
  — transitions don't care which side is which. Settle it from the
  dominant value (a stage bitmap is mostly "outside") or from the oracle.

Note this is a different measurement from
`autocorrelation-period-is-the-scanline-stride.md`, which recovers an
*unknown row stride* from a repeat period; here the stride is already known
and the question is the packing order inside each byte.
