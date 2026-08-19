# Format-doc semantic labels can be swapped while every layout fact is right

**When it bites:** a format is structurally decoded (record sizes, field
offsets, bit packing all verified) but the *semantic labels* of small
enum-like fields came from prose — a sibling game's doc, a fan
transcription, a header comment — and the prose swapped two values (this
project ported "code 2 = torch, code 3 = door" into three files and a
minimap before the walker work caught it). Every byte-level check passes;
only the meaning of the 2-bit code is wrong.

**The fix / the tell:** when two independent artifacts disagree — the doc
prose says X, a renderer/consumer derived from the actual game code (an
ASM trace, a disassembly, a running reimplementation) says Y — arbitrate
with ground truth from the game data itself, not by trusting the louder
artifact. For wall-code semantics, the **collision page** decided it:
code-2 faces were passable doorways (30 walkable vs 12 blocked in
Sorpigal) and code-3 faces sat on blocked walls (68 blocked vs 4
walkable) — matching the ASM-traced walker (2=door, 3=torch), not the
prose. A pure layout check can never catch a swapped label; check what the
data *does* with the field.

**Confirmed on:** Might and Magic I/II (crawl): Vairn's `21/22-map-dat-
format.md` prose ("2 wall+torch, 3 door") conflicts with his own
ASM-traced walkers (`view3d_indoor.py` legend "code=2 door, code=3 torch")
and with the .32 sheet layout (door frames 0x10+). The earlier decode
passes ported the prose; the walker pass caught it via the collision
statistics and corrected the codec comments, minimap colours, and both
data-structure docs (with Correction blocks).
