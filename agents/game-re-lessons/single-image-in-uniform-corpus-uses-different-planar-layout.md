# One image in an otherwise-uniform planar-bitmap corpus can use a different bitplane layout

**When it bites:** several same-size, same-bit-depth full-screen bitmaps in
one game all confirm cleanly under one planar layout (e.g. plane-major), and
one more file — identical byte count, identical declared bit depth — decodes
as pure noise (vertical banding, horizontal banding, or a scrambled mix)
under that same layout. The temptation is to conclude the file is
compressed differently, corrupted, or a non-image resource, and move on to
disassembly or escalation before trying a different **layout**, not a
different size/depth.

Confirmed on Powermonger (Amiga): five 320×200, 4-bitplane, headerless full
screens (QAZ.PAK, END_PIC1, LOSE.PAK, WIN.PAK, and CAPGRAPH) all share the
exact same 32000-byte size and bit depth. Four of them are plane-major (all
of plane 0's rows, then plane 1's, …) — the layout every OCS full-screen
picture in the game's other files uses. CAPGRAPH alone decodes as
incoherent vertical-banding noise under plane-major, but renders perfectly
— a clean 3×2 grid of six distinct character portraits — under
**word-interleaved** with a 2-byte interleave unit (the layout native to
the *Atari ST*, not the Amiga). Nothing about the file's size, bit depth, or
declared resource type predicted this; it was found only by actually trying
the alternative layout after the "obvious" one failed.

**The fix:** when a same-shaped sibling in an already-solved bitmap corpus
renders as noise, don't assume the corpus's dominant layout applies
uniformly — retry the SAME dimensions/bit-depth under each of the other
layouts your decoder already supports (plane-major / row-interleaved /
word-interleaved, see `game-re-tooling/amiga.md`'s `@seer-project/gfx`
section) before widening the search to different dimensions, bit depths, or
escalating. This is cheap (a config field change, not new code) precisely
because a layout-parameterized decoder like `@seer-project/gfx`'s
`decodePlanar` already exists — there is no reason not to try all of them.
Greyscale-first rendering (Method §3) makes the noise-vs-coherent
distinction immediate and palette-independent, so this check costs almost
nothing even before any colour data is recovered.
