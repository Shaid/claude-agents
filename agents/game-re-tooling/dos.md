# Tooling — MS-DOS 16-bit real-mode (MZ executables, segmented addressing)

`Read` this when working on a DOS target (an `MZ`-magic executable, a
`.com`/`.ovr`/`.drv` binary). Covers MZ header basics and the segment-
resolution trap that makes a naive radare2 pass unreliable for string/data
cross-references.

## MZ header, quick reference

`MZ` magic at file offset 0. Key fields (all `u16` LE): `HeaderParagraphs`
(header size in 16-byte paragraphs — the load module, i.e. "flat offset 0"
for most tools' address display, starts right after this many bytes),
`InitialCS`/`InitialIP` (entry point, `CS` relative to the *load segment*
the OS picks at runtime, not an absolute segment), `InitialSS`/`InitialSP`
(stack setup, same load-segment-relative convention), `NumRelocs` +
`RelocTableOffset` (a table of far pointers needing the load segment added
in — often just 1-2 entries in a small/tiny-model program, patching things
like the stack segment word in the compiler's startup stub; a near-empty
reloc table is normal and does **not** mean the binary has few segments).

## The CS/DS segment-resolution trap

radare2 opens MZ files fine and disassembles arbitrary offsets, and by
default displays one flat "VA" per byte (`= file offset - header size`).
**That flat VA is not necessarily the value that appears as an immediate
operand in the code** — a small/compact-model DOS program routinely uses
a separate data segment (`DS`) computed at startup as `CS + constant`
(a fixed number of paragraphs, baked in by the linker/compiler, not
requiring a relocation entry since it's CS-relative) rather than `DS == CS`
or `DS == load segment`. Two symptoms this produces if missed:

- Searching the whole file for a string's *flat* VA as a 16-bit LE
  immediate (e.g. `mov dx, <flatVA>`) finds **zero hits**, even though the
  string is definitely referenced somewhere in code — because the real
  operand is `flatVA - DSbase`, a different (usually much smaller) number.
- A flat VA computed as `segment:offset` display (e.g. r2 rendering
  `0x103bb` as `1000:03bb`) can *look* like it's telling you the real
  segment split, but that's r2's own paragraph-aligned display heuristic,
  not a verified fact about the binary's actual `DS`.

**Before trusting any single-string/data xref search on a DOS target**,
establish the real `CS`/`DS` relationship first: check the MZ relocation
table for an entry patching a `mov ax, <seg>` (or similar) instruction near
the entry point — but note this may only cover `SS` (the stack), not `DS`,
if `DS` is computed CS-relatively and therefore needs no runtime patch at
all. If no reloc entry resolves it, look for the startup stub's own
`mov ax, cs` / `add ax, <imm>` / `mov ds, ax` idiom near the entry point —
the `<imm>` there is the paragraph offset from `CS` to `DS`, letting you
convert any flat VA in the data region to its real DS-relative operand
value (`op = flatVA - imm*16`) before searching for it as an immediate.

**Confirmed recipe (small-model C startup, the common case): the reloc
entry usually patches a register later committed to *both* `SS` and
`DS`, not just `SS`.** A small-model C startup stub typically loads the
one relocation-patched word (often disguised as a `mov <reg>,
<InitialSs-shaped constant>` right at the entry point, taking its value
straight from the MZ header's own `InitialSs` field) into a scratch
register, uses it for other early setup (memory-block resizing via
`int 21h AH=4Ah`, environment-segment bookkeeping), and only *later*
writes that same register into both `SS` and `DS` (`mov ss, reg` then,
a bit further down, `mov ds, reg`) — i.e. search forward from the reloc-
patched instruction for the *next* `mov ds, <reg>` using that same
register, not just the first `mov ss`. Cracked this way on Wizardry 6's
`wroot.exe`: the one reloc entry patches `mov bp, 0x0fd8` (the MZ
header's own `InitialSs`) at the very first instruction; `bp` is later
written to `ss` (`mov ss, bp`) and, several dozen instructions further
into the same startup stub, to `ds` (`mov ds, bp`) — giving
`DS = CS + 0x0fd8` paragraphs for the whole process lifetime. **Verify
by computing a real string's file offset from a nearby `int 21h AH=9`
call's `DS`-relative immediate** (`fileOffset = headerSize + dsBase*16 +
immediate`) and checking the bytes there are legible — a startup routine
almost always has at least one `$`-terminated print-string call nearby
(hardware-requirement or out-of-memory messages) to use as the check.

## Validating a medium-model executable's far-pointer addressing model cheaply

A medium-model program (multiple code segments, one shared data segment —
the common shape once a DOS game's code exceeds 64 KB) has many `lcall
seg:off` far calls whose `seg` values are compiler-assigned linker segments,
not runtime-meaningful until the loader adds the actual load segment at
`EXEC` time. For **static** analysis of an EXEPACK/LZEXE-unpacked (or
otherwise already-decompressed) flat load image, it's usually unnecessary to
model that runtime relocation at all: test the hypothesis that every stored
`seg:off` is already usable directly as `flatImageOffset = seg*16 + off`
(i.e. the compiler's segment numbering starts at paragraph 0 of the load
module itself, exactly the load image you already have) by resolving a
handful of *unrelated* far-call targets this way and checking each one lands
on a plausible function prologue (`push bp; mov bp,sp` or
`push si; push di; push bp; mov bp,sp` are the common x86-16 C-compiler
shapes). If 3+ independently-chosen targets all land cleanly on a prologue,
trust the model for the whole binary — including **data** far pointers, not
just call targets — without ever tracing the loader's own relocation-fixup
stub. Confirmed on WIME's DOS VGA `START.EXE` (`middilgard` project): far
calls `0:0x252`, `0x833:0xc7c` and `0x1507:0x119b`, computed this way,
landed exactly on 3 unrelated function prologues, letting a scoped
disassembly of the animation-rendering code proceed without any relocation
modeling — the same convention this project's data segment already used
(`DS = 0x1772` paragraphs, i.e. `DS_BASE = 0x17720`, established in an
earlier session via the CS/DS-trap recipe above) turned out to extend
uniformly to every code segment too.

## `.ovr` overlay files (common on 1990s DOS games too large for one segment)

A game with several `.ovr`/`.ovl` files loaded on demand into a shared
memory region is a completely different mechanism from a compiler's
built-in overlay manager (Borland/Microsoft's automatic overlay support,
which embeds its own header format) — check whether the game rolled its
own loader before assuming a known overlay-manager format. A hand-rolled
loader's own error strings (e.g. `"Error %d loading overlay: %s$"`) plus a
back-to-back table of overlay base names in the main executable are a
cheap, code-free way to enumerate every overlay module and confirm the
file-to-module mapping — check strings before disassembling the loader.
If each `.ovr` file shares an identical short byte prefix across the whole
set (a magic + a per-file variable field), that's very likely a small
in-house header (module-size/checksum-shaped), not literal executable
code at offset 0 — even if disassembling from byte 0 doesn't immediately
throw an error (arbitrary bytes almost always "disassemble" to *something*
syntactically valid, see `rle-decode-succeeds-on-garbage.md`'s sibling
warning for compression — the same "ran without error ≠ correct" caution
applies to disassembling the wrong start offset as code).

### Recognizing a Borland-style **in-file** overlay (no separate `.ovr` at all)

A single `.exe` with no companion `.ovr`/`.ovl` files can still be an
overlay executable — Borland/Turbo compilers' built-in overlay manager
embeds overlay segments inside the same file, swapped in and out of one
memory region at runtime, so much of the visible CODE region in a static
disassembly never coexists in one running image. This is a materially
harder static-tracing target than a straightforwardly-compressed
executable (e.g. LZEXE, which just needs decompressing once before the
real code is fully present and traceable — see the `middilgard` project's
Conan `CONAN.EXE` for that simpler case). **A verified TypeScript LZEXE
v0.90/0.91 decompressor already exists** at middilgard's
`tools/shared/lzexe.ts` (a faithful port of the classic `unlzexe.c`,
checked byte-exact against the reference C tool across three real files
from two different games) — reuse it directly rather than re-deriving the
algorithm or shelling out to a native `unlzexe` binary (which isn't a
committed, reproducible dependency). Also note: a target being
LZEXE-compressed can silently defeat a cross-platform known-content byte
search that "should" find shared static data — see
`cross-platform-decode-oracles.md`. Tells, all checkable without
disassembling anything: an embedded string resembling `"Runtime overlay
error"` (or similar wording — Borland's runtime prints this on an overlay
load failure); an `MZ` header with `HeaderParagraphs` far larger than a
typical startup stub (thousands of bytes rather than tens/hundreds — the
extra space is overlay-manager bookkeeping, not code); and a static
strings scan (radare2's `list_all_strings`/`list_strings` or plain
`strings`) turning up almost nothing readable anywhere in the binary, even
though the game obviously has text somewhere. If more than one of these
holds, expect a symbol-less binary where large stretches of "found 700+
functions" analysis output are overlay-swapped code that only partially
reflects what actually runs at any one time — check the game's other
shipped files (config, save/restart state) for the data you need before
sinking time into tracing the overlay structure itself; see
`canned-save-state-mirrors-exe-struct.md`.

## CGA/EGA/Tandy video mode: source-file bank layout and palette confirmation

A CGA/Tandy 16-color asset file meant for direct blitting to video memory
can be pre-formatted to match the **hardware's own bank-interleaved
layout**, not stored as a plain top-to-bottom bitmap — check for this
before assuming a packed-pixel image just needs the right width. Real IBM
CGA 320x200 4-color video memory is split into two fixed 0x2000-byte
(8192-byte) banks (even scanlines at segment offset 0, odd scanlines at
+0x2000), each holding only ~8000 bytes of real row data (the rest is
unused padding to the fixed bank boundary) — not a tightly-packed
`rows_per_bank * rowBytes` size. Symptom of getting this wrong: a plain
linear (non-interleaved) decode renders a legible-but-vertically-repeated/
blurred image (each field, read out of order, forms its own coarse
2x-vertically-squished copy of the whole picture); guessing an interleave
with a *tight* bank size instead produces a blurry combing/interlace
artifact, not a clean image — only the hardware-accurate fixed bank size
works. Confirm this by disassembling the platform's own CGA video driver's
screen-blit routine: look for a `rep movsw`/`rep movsb` copy loop where
`add si,0x2000` (or `0x4000`/`0x6000` for 4-way-interleaved Tandy 16-color
video memory) is applied to *both* the source and destination pointers —
that's proof the source asset file itself is pre-banked, not just real
video memory. Whether the *source* file is pre-banked or plain-linear
varies even between sibling drivers on the same game: confirmed one game's
CGA driver bank-interleaves its source assets (matching video memory
exactly) while that same game's Tandy driver keeps its source assets
plain-linear and only de-interleaves at blit time (destination pointer
takes the bank jumps, source pointer only advances by a plain row
stride) — don't assume one driver's convention for its sibling.

**Confirming a CGA/EGA/Tandy palette via `INT 10h` disassembly** is far
more direct than inferring it from rendered pixel statistics, and cheap
once you know which call to look for: `AH=00h` sets the video mode
(`AL`=4/5 for CGA 320x200 4-color, `AL`=9 for Tandy/PCjr 320x200
16-color, `AL`=0Dh for EGA 320x200 16-color); `AH=0Bh BH=01h` selects one
of CGA's two fixed 4-color hardware palettes via `BL` (0=green/red/brown
family, 1=cyan/magenta/white family) — note this call alone doesn't touch
the intensity bit, so if no separate `AH=0Bh BH=00h` "set background
color" call appears nearby, intensity is whatever the mode-set left it
(usually low); `AH=10h AL=02h` ("Set All Palette Registers", EGA/VGA-
compatible hardware only, works for Tandy in EGA-compatible modes too)
points `ES:DX` at a literal 16-or-17-byte table in the executable that
directly programs the Attribute Controller's palette registers — dump
that table and read it as "register `i` gets standard-EGA-order color
`table[i]`" to recover the exact palette with zero pixel-level guessing.
This nailed a DOS Tandy port's 16-color palette as byte-for-byte identical
to its EGA sibling's already-confirmed table, straight from the BIOS
call's own embedded parameter table.

## The launcher `.bat`/error-table trick

A DOS game's own launcher batch file, when present, is often a free,
code-free map of the executable's startup sequence: a chain of
`if ERRORLEVEL N goto errN` checks against a numbered list of specific
failure messages ("Unable to load MAZEDATA", "Unable to open SCENARIO.DBS",
...) is a direct enumeration of the load order, in order, with zero
disassembly needed. Check for this before tracing a startup routine by
hand.

## The game may ship its own symbol table as a data file

Before deep-disassembling a DOS game's overlay loader (`.OVR`-system games),
`strings` every non-obvious file in the install — the overlay system's
symbol/relocation table is sometimes shipped as plain data, naming the
game's internal routines for free. Confirmed on Might and Magic I (DOS):
`MM.RSM` (6.6 KB) holds 22 null-terminated symbol names — `$ovbgn`,
`main_`, `ovloader_`, `Bpcomand`, `Zsetspell`, `readmaze_`, `readrost_`,
`writrost_`, `readwall_`, `readmon_`, `readpix_`, `readscr_`, `chkopen_`,
`scrnset_`, `setequip_`, `getseg_`, `mach_set_`, `egaxref`, `cga_movsw`,
`ega_movsw`, `grmovax`, `grmovsw` — each followed by a 4-byte address
field (`seg-byte, 0x28, u16LE offset`; exact encoding unconfirmed). That
is the game's own I/O + video routine inventory, which names what the
`.OVR` overlay loader binds and is a ready-made head start for decoding
the per-map overlay scripts. The `$`-prefixed symbol (`$ovbgn` = overlay
begin?) and the overlay-loader/machine-setup names (`ovloader_`,
`mach_set_`, `adapter`, `adapter6`, `hertable`) are the tell — a mixed
code + video routine table is a loader symbol map, not game data. (Amiga
analog: check for a `HUNK_SYMBOL` block before counting bytes through a
disassembly — see amiga.md; on DOS, the shipped symbol table is a plain
data file, found by `strings`, not by parsing the executable format.)

