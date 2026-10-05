# A community tool's per-game address constants live in ITS OWN loader's coordinate space, not necessarily yours

**When it bites:** using a third-party multi-ROM-file reference tool's
per-game offset/address table (vgmtrans's `mame_roms.json`, a 010-editor
template, an XeNTaX/community MAME-XML-derived config) against your own
project's already-assembled ROM region, when that region was built by
replicating the *original hardware's* memory map (including any gaps a
split `ROM_LOAD`+`ROM_CONTINUE`/bankswitch layout leaves) — especially when
a constant that should be a straightforward address gives garbage or an
implausible value at the naive offset.

Two independent tools reading the "same" ROM files can disagree on what an
address *means* without either being wrong: they just assemble the files
into different flat byte arrays. Confirmed on D&D: Shadows over Mystara
(CPS2, `kolbold`): vgmtrans's `bin/mame_roms.json` declares ddsom's
top-level music sequence-pointer table at `seq_table: "0x9005"`. This
project's own `buildAudioCpuRegion()` replicates MAME's real
`ROM_LOAD`+`ROM_CONTINUE` region layout for the Z80 sound ROM — which has a
genuine *unused gap* at region offsets `[0x8000, 0x10000)` (the switchable
16KB banked window's real hardware address space needs room for every bank,
so MAME's region reserves `0x4000` bytes per bank starting at `0x10000`,
even though only ~6 banks' worth of file data actually exist there).
vgmtrans's own loader (`MAMELoader::loadRomGroup()`, `LoadMethod::APPEND`)
instead does a **naive, gapless concatenation** of the raw ROM files in
declaration order — so vgmtrans's own "`0x9005`" is a raw *file offset*
within the first ROM chip, not a MAME-region address with the gap
included. Reading region offset `0x9005` directly in this project's own
gapped array landed inside the unused gap (all zero) instead of the real
table.

**The fix is not "always add/subtract a fixed constant" — derive the
conversion from BOTH loaders' own semantics.** Read the community tool's
loader source (in this case `MAMELoader.cpp`'s `switch (entry.loadmethod)`
block) to learn exactly how it assembles multi-file/multi-chunk ROM
regions, then work out the affine map between its coordinate space and
your own project's (here: `regionOffset = addr < 0x8000 ? addr :
addr + 0x8000`, derived algebraically from the fact both loaders place
`dd2.01`'s own bytes contiguously past the split point, just at different
final addresses). **Cross-check the derived formula on a value you can
already validate independently** before trusting it on a value you can't —
this project confirmed the exact same conversion was a no-op (correct
either way) for three OTHER vgmtrans-declared literal pointer values that
happened to sit below the fixed bank's `0x8000` boundary, then applied the
same formula with confidence to the one value (`seq_table`) that needed
the real conversion, and it produced a real, densely-packed, monotonically
addressed 923-entry directory — strong positive confirmation the formula
was right, not just "no longer zero."
