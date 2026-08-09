# Tooling — PS2

`Read` this when your target is a PS2 (PlayStation 2) disc image or
executable. See `game-re-tooling/ghidra-loaders.md` for the Emotion Engine
(R5900 + VU macromode) and `.mdebug` symbol loaders if you need Ghidra.

## Disc-image parsing: prefer `xorriso`/`7z` over mounting

- `7z l <iso>` and `xorriso -indev <iso> -toc` both parse standard ECMA-119
  ISO9660 directly, no root/mount required. Check `xorriso`'s `ISO offers:`
  line — PS2 discs commonly carry **plain ISO9660 only** (`Only_ECMA_119`,
  no Joliet, no Rock Ridge, no UDF bridge); `7z l -tudf <iso>` failing to
  open at all is expected in that case, not a sign of a bad dump.
- `xorriso -osirrox on -indev <iso> -extract / <destdir>` extracts the
  catalogued tree without needing `sudo`/loopback mounting (useful in
  sandboxed environments where `mount` needs a password).
- `SYSTEM.CNF` at the ISO9660 root is the standard PS2 boot descriptor:
  `BOOT2 = cdrom0:\<EXE-NAME>;1` names the main EE ELF (`SLES_*.**`/
  `SLUS_*.**`/`SLPS_*.**`-style filename by region), plus `VER =` and
  `VMODE =` (PAL/NTSC) lines.

## The ISO9660 tree can be almost empty — check for a raw-LBA archive before concluding a bad rip

Several PS2-era Japanese developers (confirmed: tri-Ace) bypass ISO9660
entirely for their bulk asset data — the catalogued directory tree holds
only the boot files (`SYSTEM.CNF`, the main ELF, an IOP module bundle), and
everything else is unlisted raw sectors addressed by a proprietary in-house
table baked into the executable. See
`game-re-lessons/iso9660-tree-near-empty-check-raw-lba-toc.md` for the
general diagnostic and `game-re-corpora/valkyrie.md` for a fully-solved
worked example (tri-Ace's XOR-scrambled TOC, decoded in
`~/Development/valkyrie/tools/valkyrieprofile2/ps2-toc.ts`).

## Main executable format

The main boot ELF is a standard 32-bit LSB ELF (`EI_CLASS=1`,
`EI_DATA=1`), `e_machine=8` (`EM_MIPS`) — the PS2 Emotion Engine's R5900
core is a MIPS III-derived custom ISA, so generic MIPS ELF parsing gets you
the header/entry-point/section-table shape for free; a normal load base is
around `0x100000` (confirmed `e_entry=0x100008` on one title).
`disassemble`/`disassemble_function`/`xrefs_to`/`hexdump` all work fine via
`mcp__radare2__*` on a real EE ELF (used to trace VP2's SLE cipher, a VU0
key-derivation microprogram, and its FIS texture-chunk consumer). **The
`search` and `list_strings` tools do not**: both return "Sandbox restricts
search range" against a real EE ELF, reproducibly, regardless of the
`bits` parameter on `open_file`/reopen (tried both the auto-detected
default and an explicit `32` override) — confirmed on Valkyrie Profile 2's
`SLES_546.44`. Don't waste time retrying `search`/`list_strings` variations
on a PS2 EE target; go straight to a manual byte scan of the extracted ELF
(plain Python/Node `bytes.find`) to locate a magic/string, then hand the
resulting address to `disassemble`/`xrefs_to` for the actual tracing —
those still work normally once you have a starting address.

## IOP modules

PS2 titles bundle IOP (I/O Processor) driver modules as small standalone
MIPS ELF `.irx` files (`mcman.irx`, `mcserv.irx`, `sio2man.irx`,
`dbcman.irx`, and similar — look for these as plain ASCII strings inside
the main EE ELF; their presence as strings is a strong hint the same
filenames appear as real module files somewhere in the disc's real content,
whether catalogued in ISO9660 or hidden behind a raw-LBA scheme). These are
commonly stored **raw/uncompressed** inside whatever container wraps them
even when other resources in the same container are compressed — a module
loader typically needs the ELF structure directly usable from the loaded
buffer, so don't assume "wrapped in the same container format" implies
"compressed the same way as everything else in it."

`IOPRP300.IMG` (or similarly-named `IOPRP*.IMG` files) is a standard PS2
SDK IOP reset-image bundle name seen across many unrelated commercial
titles — treat it as boilerplate SDK content, not game-specific, unless a
specific task requires digging into IOP-side code.

## `TIM2` textures — industry-standard, already solved with a shared decoder

Sony's official PS2 SDK `TIM2` texture format (`TIM2` magic, `version=4`)
shows up across most commercial PS2 titles regardless of developer — seeing
it is confirmation of normal middleware, not a new format to crack.
**Pixel/palette decode is already solved and shared**:
`~/Development/flower/tools/shared/tim2.ts` (byte-exact picture-header
layout, 4/8bpp indexed with the standard PS2 GS CSM1 CLUT unswizzle,
16/24/32bpp direct color, the PS2 GS 0-128 alpha convention). Cross-checked
against a real, actively-maintained third-party reference implementation
(marco-calautti/Rainbow, GPL2, C#) rather than hand-derived — see that
module's doc comment for the byte tables and
`~/Development/flower/docs/chaoslegion/ps2/data-structure.md` §12 for the
verification evidence (real logo/title-screen/font/icon renders across two
unrelated Capcom titles). Check for this decoder before re-deriving TIM2
from scratch on a new PS2 target. Two real variants found so far, worth
checking for on a new title: a same-struct-with-image-zeroed standalone-CLUT
sibling magic (`CLT2`, one instance in Chaos Legion, see
`game-re-lessons/sibling-magic-may-be-same-struct-zeroed-field.md`), and a
flat concatenation of many independent, individually-sector-padded `TIM2`
sub-files bundled into one larger asset-pack file (Chaos Legion's
`IHS/IHJ/IHF/IHE.DAT` per-language texture packs) — `parseTim2Bundle` in
the same module handles that shape via a literal magic-byte scan. **That
scan technique doesn't always transfer**: a structurally-different
multi-`TIM2` bundle (Devil May Cry's 22 `.ITM`-extension files with a
`count`+offset-table header) produces a 10x-inflated false-positive count
under the same magic-scan approach — a strong hint (an exact small-integer
multiple of the container's own declared count) that the bundle uses an
explicit offset table rather than magic-scannable content, needing that
table parsed directly instead.

## VIF1/GS display-list packets: register state persists across draw calls — a "missing" material/render-state block is often deliberate reuse, not missing data

A pre-built VU1/GS display-list packet (`UNPACK` vertex-attribute payloads
+ a `GIFtag`+`A+D` register-write block selecting texture/blend state, the
classic PS2 batched-draw-call shape) very commonly has render-state blocks
on only a **minority** of its draw-call batches. This is real PS2 GS
hardware semantics, not a decode gap or an "optional field, sometimes
just not set" artifact worth writing off: the GS is an immediate-mode
GPU whose registers (`TEX0_1`, `ALPHA_1`, etc.) hold their value across
draw calls until explicitly rewritten — the same convention as legacy
OpenGL's bound-texture/blend-mode state. A batch with no material block
is deliberately reusing whichever state the *most recent* batch that did
carry one left active, not lacking a texture assignment.

Confirmed on Valkyrie Profile 2 (PS2): a per-batch texture-resolution
scheme that only looked up each batch's *own* material block resolved
72.2% of texture-bearing character-mesh records. Walking the batch list
in its original stream order while tracking "the current render state,"
updating it only when a batch declares its own block, and applying that
carried-forward state to every batch (declaring one or not) raised real
per-record resolution to 83.9% — the missing 11.7 points were entirely
batches correctly inheriting state from an earlier sibling batch, not a
decode failure. Before concluding a render-state/material field is
"often absent" or hunting for a second encoding to explain the gap in any
PS2 GS-flavoured command stream, try state carry-forward across the
stream's own draw order first — it is usually the actual answer, not a
fallback heuristic.
