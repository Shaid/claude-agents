# When a field is stored obfuscated, its mask — not its offset — is the census key that finds every writer

**When it bites:** a struct field is stored XOR-masked, complemented, or
checksummed with a per-field constant (an anti-cheat habit in later console
RPGs), and you are about to name that field's role from one decompiled
function, from prior doc prose, or from an offset-keyed census — or to write
a negative like "no damage routine writes it in any module."

An offset-keyed census (`lw $v0, 0x0C($s0)`) is scoped to whatever code you
happened to disassemble and is defeated by every biased base pointer in the
corpus. The obfuscation constant is not: it is a wide, unique literal that
**every** reader and writer must materialize in-line, with no indirection.
On a fixed-immediate-width ISA that means a `lui`+`ori` (or
`movw`/`movt`, `mov`+`orr`, a 64-bit literal pool entry) you can scan for
byte-wise across the whole image — main executable, every overlay, every
decrypted blob — in one pass, with no dataflow analysis at all.

The *set* of writers is what names the field. One decompile tells you a
store happens; the writer census tells you which subsystem owns it.

**Check / fix:**

1. Scan every code region in the corpus for the mask's materialization,
   not for the field's displacement.
2. Classify each hit by the function it lands in — constructor/loader,
   per-tick update, heal/revive, equipment recompute, HUD/draw, save/load.
3. Read the role off the classification: a field written by heal and revive
   and clamped by an equipment-percent function is *current* HP; the one the
   clamp reads is *max*. A field only ever read by a draw routine is
   display cache, not state.
4. Only now is a negative safe to write, and it is now a real one — "no hit
   in any module" rather than "no hit in the function I read."
5. Verify from raw bytes with a null control (apply the unmask to an
   unrelated field or a shuffled copy and show it yields nonsense).

Do **not** inherit the role from the first decompile or from prose: a
decompile naming an offset "current" survived unchallenged until the writer
census showed the pair was the other way round.

**Canonical example:** Valkyrie Profile 2 (PS2, `valkyrie`). The character
record's `+0x0C`/`+0x10` pair was documented from a decompile as
current/max HP. Scanning every payload for the 32-bit XOR mask's `lui`/`ori`
pair enumerated the full writer set — setter, per-tick, heal, constructor,
HUD — and the heal/revive writers plus the equipment-percent clamp proved
the labels were **swapped** (`+0x0C` = max, `+0x10` = current), confirmed
from raw disc bytes with null controls in
`tools/valkyrieprofile2/verify-character-record-hp-fields.ts`. The same
census supplied the negative "no damage routine in any module writes it."

Same inversion-of-search-direction as
`field-centric-bit-census-blind-to-sibling-reuse-and-split-mask.md` and
`value-construction-narrows-flooded-address-census.md` — there to find a
consumer a chase missed, here to find *all* of them and read a semantic
label off the set. Sibling trap:
`format-doc-semantic-labels-swapped.md` (a fully byte-verified layout can
still carry two labels the wrong way round).

**History:** 1 recorded instance (`valkyrie`).
