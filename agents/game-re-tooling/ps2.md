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

## Node `readFileSync` caps at 2 GiB — use positional reads on retail ISOs

Retail PS2 single-layer DVDs are ~4.4 GB images; `fs.readFileSync(iso)` in
a Node/tsx pipeline throws `RangeError: File size (N) is greater than 2
GiB`. Decode multi-GB images with `openSync` + positional `readSync(fd,
buf, 0, n, offset)` (or `fs.promises.FileHandle#read`) — this bites on
*any* platform whose disc images exceed 2 GiB (PS2 dual-layer, GameCube/
Wii, PS3/PS4 PKG), not just PS2. Confirmed on Odin Sphere's 3.4 GB ISO
(CRI CVM decode, `vanille`).

## Main executable format

The main boot ELF is a standard 32-bit LSB ELF (`EI_CLASS=1`,`EI_DATA=1`), `e_machine=8` (`EM_MIPS`) — the PS2 Emotion Engine's R5900
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
`SLES_546.44`, and independently reproduced on Drakengard's `SLUS_207.32`
(this is an environment/MCP-server-level restriction on the `search`
command family, not a one-title fluke — running `analyze` at any depth
first does not lift it, and it blocks all three of `search`'s hex/value/
string modes, not just one). `list_all_strings` (the whole-binary `izz`-
style scan) is a **different** underlying command and is NOT affected —
it still works and is the fastest way to confirm a literal string exists
and read short surrounding context, even though (unlike `list_strings`) it
doesn't surface an address you can feed to `xrefs_to` directly. Don't
waste time retrying `search`/`list_strings` variations on a PS2 EE target;
go straight to a manual byte scan of the extracted ELF (plain Python/Node
`bytes.find`, or construct the exact MIPS `lui`/`ori` instruction-word
bytes if hunting a magic-check code site built from split immediates
rather than a literal string) to locate a magic/string/instruction
pattern, then hand the resulting address to `disassemble`/`xrefs_to` for
the actual tracing — those still work normally once you have a starting
address.

## R5900 3-operand `MULT`/`MADD` decode as "invalid" in capstone/radare2

The Emotion Engine extends MIPS with 3-operand forms that generic MIPS
disassemblers (capstone, radare2) report as `invalid` or misdecode with
wrong register names:

- `MULT rd, rs, rt` — opcode `0x00` (special), funct `0x18`, with the `rd`
  field nonzero: **rd = LO32(rs × rt)** (and HI:LO updated). The standard
  2-op `mult` has bits 15-0 zero; a nonzero `rd` there is the 3-op form.
  Confirmed load-bearing in the ZOE2 STAGE cipher
  (`mult $t0, $v1, $a2` at 0x100fe8 — the doc-level key advance
  `keyX' = LO32(keyX*0x02E90EDD)+keyY` only works if you know rd gets the
  product low; see `docs/zoe2anubis/ps2/data-structure.md` §2.4) and in
  `DG_MODEL::Init`'s node walk (0x131710: `madd t7, zero, a3` = rd ← LO,
  then accumulate).
- `MADD rd, rs, rt` — special2 (opcode `0x1C`), funct `0x00`, nonzero `rd`:
  rd ← LO; LO:HI ← LO:HI + rs×rt.

When a traced EE function shows `invalid` instructions or a `mult` with an
impossible operand (e.g. `mult t0, zero, s4`), hand-decode the word —
don't skip the instruction or trust radare2's register guesses. The
`mtlo`/`mflo` around these forms is often the accumulator plumbing, and a
"product of zero" reading usually means the disassembler picked the wrong
register field.

**The real, general fix for this whole class of misdecode (not just
`MULT`/`MADD`) is Ghidra headless batch analysis with the EE SLEIGH
language directly — confirmed decoding ALL R5900 MMI/VU0-macromode
instructions correctly, not just the two hand-documented above.** No live
GhidraMCP server or GUI session is needed; `analyzeHeadless` works
standalone as a real fallback when the MCP connection isn't reachable:

```
analyzeHeadless <projectDir> <projectName> -import <file> \
  -loader BinaryLoader -loader-baseAddr 0x<loadAddr> -loader-blockName ram \
  -processor r5900:LE:32:default
```

Key points: (1) this works on a **raw, headerless code blob** too, not
just a real PS2 ELF/IRX — `ghidra-emotionengine-reloaded`'s PS2 loaders
aren't needed if you already know the load address (e.g. a decompressed
code overlay pulled out of a game's own resource container); Ghidra's
stock `BinaryLoader` plus an explicit `-loader-baseAddr` and the
extension's own `r5900:LE:32:default` processor id is enough. (2) Confirmed
zero unimplemented/bad-opcode instructions across a 277,453-instruction,
1.2 MB real game module (`sq`/`lq` 128-bit quadword moves, `lqc2`/`sqc2`,
and VU0-macromode arithmetic all decoded cleanly) where radare2/capstone
misread the same bytes as `addu.qb`/`ext`/`aver_u.h`/`xori.b` garbage —
`~/Development/valkyrie`'s VP2 battle-engine-overlay investigation,
`docs/valkyrieprofile2/ps2/battle-logic.md` § 2.1. Prefer this whenever a
target needs more than a handful of hand-decoded instructions; the
MULT/MADD hand-decode above is still useful for a quick radare2-only spot
check, but stop reaching for it as the primary strategy once real function
census/call-graph/decompilation work is needed.

(3) **A raw `BinaryLoader` import with no declared entry point defeats
headless auto-analysis's Function Start Search** — it seeds disassembly
from call targets and known entry points, and a raw code blob imported
this way has neither, so real code sitting right after a small fixed
header (e.g. VP2's `SP*` dungeon-script overlays, whose real code starts
at a constant file offset `0x80` past an `MWo3` header) gets silently
skipped; auto-analysis only finds later functions reachable by a `jal`
from somewhere it *did* find. Confirmed on 2 more VP2 overlay files
(`docs/valkyrieprofile2/ps2/battle-logic.md` § 12.2) — zero
unimplemented/bad-instruction warnings in the real code once fixed. Fix
with a small Ghidra post-script forcing disassembly to start at the
known offset:

```java
Address entry = currentProgram.getMinAddress().add(0x80);
disassemble(entry);
createFunction(entry, null);
```

Note `getImageBase()` returns `0` for a raw `BinaryLoader` import (no
image base concept without a real container format) — use
`getMinAddress()` instead, which reflects the `-loader-baseAddr` you
passed in.

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

## PCSX2 savestates are a complete static VU1-tracing oracle — no live emulator needed

When a PS2 format's field semantics resist EE-side/statistical analysis,
the VU1 microprogram that consumes the data is the authoritative reader,
and a single PCSX2 savestate contains everything needed to trace it
offline (proven on ZOE2's `.mdz` vertex record, where one static VU1 pass
overturned two full EE-side statistical escalation passes — see
`game-re-lessons/model-silhouette-render-confirmed-by-placement-layer.md`):

1. **Extraction:** a savestate is a zip whose entries use compress-type 93
   (Zstandard) — Python ≥3.14 `zipfile` reads them natively, no manual
   zstd step. Relevant members: `eeMemory.bin` (32 MB EE RAM),
   `vu1MicroMem.bin` (16 KB microcode), `vu1Memory.bin` (16 KB VU data),
   `Scratchpad.bin`, `eeHwRegs.bin`.
2. **Find the built packets, not the file templates.** Engines commonly
   build per-resource VIF1 DMA chains at load time (the ELF holds only
   patch templates); the resource's runtime-pointer fields (zeros in the
   file) hold the packet addresses in EE RAM. Decode DMA source-chain tags
   (16 bytes: `u64 {qwc | id<<28 | addr<<32}` + 2 VIF-code words,
   ids cnt/next/ref/refs/call/ret/end) plus VIF codes
   (STCYCL/UNPACK/MSCAL/MSCNT/DIRECT). A `ref` tag pointing at the raw
   file records with an `UNPACK Vn-format NUM addr` declares the exact
   per-record VU-memory layout (e.g. `V3-16 NUM=3N` = three qwords per
   18-byte vertex).
3. **Find the per-frame display list** by searching EE RAM for a word
   containing a known packet address — it is typically double-buffered
   (two copies ~0x100000 apart) and carries per-node constant uploads
   (matrix/light rows to fixed VU addresses) plus the `MSCAL` entries.
4. **Read the kernel.** A ~200-line hand-rolled VU disassembler suffices
   (upper/lower 32-bit instruction pairs; reusable worked example:
   `~/Development/flower/tools/zoe2anubis/vudis.py`). Enumerate kernel
   entries by grepping for `XTOP`; note that dispatch is often `JR` on a
   per-node control word uploaded in the display list, and `MSCNT` batch
   kernels self-sustain by ending `[E] NOP | B <own entry>`. Field
   semantics then read off directly:
   - the **ITOF variant** applied to each input qword declares its
     fixed-point scale: ITOF0 = integer, ITOF4 = /16, ITOF12 = /4096,
     ITOF15 = /32768 — an ITOF12'd field is a ±1.0 quantity (normal/UV),
     an ITOF4/ITOF0'd one is a coordinate;
   - `MULAx/MADDAy/MADDAz/MADDw` chains against constant registers =
     matrix × position; a 3-term dot + `MAX` vs 0 feeding a `MADD` into a
     colour = lighting normal; `ADD` to a global + `MINIi 255` = prelit
     vertex colour; a per-vertex bit ORed into the output XYZ2 qword's
     bit15 = the GS ADC strip-restart flag.
