# MAME / arcade ROM-set targets

Applies whenever the original data is a MAME-format arcade ROM set — a ZIP
bundling one file per physical ROM chip (68000/Z80/6502/etc program ROMs,
gfx mask ROMs, sample ROMs, a `.key` file, ...), the norm for CPS1/CPS2/
CPS3, System 16/18/24/32, Neo Geo, and most other arcade boards. Treat the
zip as a container of independently-labeled chip dumps first — `unzip -l`/
`-v` it and identify every file by name/size/CRC32 before assuming anything
about internal layout.

## MAME's own driver source is the authoritative container spec — use it as an oracle, not a guess

Every ROM's role, load offset, region, and load semantics (byteswap?
interleaved with siblings? banked?) are declared, byte-exact, in the
driver's `ROM_START(<shortname>)` block in mamedev/mame's source
(`src/mame/<manufacturer>/<driver>.cpp`). This turns "identify an unfamiliar
container" into "CRC32-match every file against a public, versioned spec" —
usually a five-minute win instead of hours of structural guessing:

1. Compute (or read via `unzip -v`) every file's CRC32.
2. Fetch the driver source (`raw.githubusercontent.com/mamedev/mame/master/
   src/mame/<vendor>/<driver>.cpp` via `curl`, or `WebFetch`/`WebSearch` —
   see the caveat below) and find the `ROM_START` block whose CRC32s match
   every file in your zip exactly. This also names the *exact revision*
   (parent/World vs. a regional/bootleg variant) — different revisions of
   "the same" game can have entirely different file lists/offsets/keys.
3. `ROM_REGION(size, "name", flags)` gives the destination region size and
   logical name (`"maincpu"`, `"gfx"`, `"audiocpu"`, `"key"`, ...).
4. Each `ROM_LOAD*` macro's flags say exactly how that file's bytes land in
   the region — see the macro semantics table below. Get these from
   `src/emu/romentry.h`'s macro definitions and, if the exact byte-copy
   algorithm matters (it usually does), `src/emu/romload.cpp`'s
   `read_rom_data()` — the macro names alone (`WORD_SWAP` vs plain) don't
   tell you the exact byte-level loop; the `read_rom_data()` `reversed`/
   `groupsize`/`skip` branches do.

**WebFetch caveat on a large driver file:** a "summarize this file" prompt
to `WebFetch` can miss the exact block you need on a 10,000+-line driver
source (confirmed on `cps2.cpp` at 12,895 lines — a `WebFetch` summarization
pass reported "not found" for a block later found instantly with `curl -sL
<url> -o file.cpp && grep -n <shortname> file.cpp`). Prefer `curl`+`grep`/
`sed` on the raw file directly over relying on a fetch tool's summarization
for anything you need byte-exact.

**Locating a shared constant's *definition* (not just its uses) needs plain
`curl`, not a code-search index.** MAME factors many small building blocks
(a `gfx_layout` named `gfx_8x8x3_planar`, a shared macro, a small helper) out
of the driver file that references them, into some other header/source file
in the tree — and every unauthenticated web code-search tool tried for
finding *that* file failed outright: GitHub's own code search demands
login even for public repos, and third-party indexes (grep.app,
Sourcegraph) either rate-limited (HTTP 429) or rendered an empty JS shell
via `WebFetch`. What worked: guess a short list of plausible candidate
paths from MAME's directory conventions (`src/emu/*.h`, `src/devices/
video/*.h`, a shared per-vendor header like `src/mame/sega/segaic16.h`) and
`curl` + `grep` each one directly — cheap even across a dozen wrong
guesses, and the only approach that actually returned a hit. If every
guess misses, don't burn more budget guessing further file paths — treat
the shared constant's *effect* as reconstructible from its two or three
call sites plus the platform's extremely standard conventions instead (see
`decodeSega16Tiles8x8` in the goldenaxe/sys16 corpus entry for a worked
example: the ROM byte-count arithmetic plus a legible-text render confirmed
the layout `gfx_8x8x3_planar` implies, without ever finding its literal
struct definition).

### `ROM_LOAD*` macro semantics (`src/emu/romentry.h` + `romload.cpp`)

| Macro | Groupsize | Reversed | Skip | Effect |
|---|---|---|---|---|
| `ROM_LOAD` | 1 | no | 0 | Straight copy, no transform |
| `ROM_LOAD16_BYTE` | 1 | no | 1 | Every other byte (odd/even ROM pair) |
| `ROM_LOAD16_WORD_SWAP` | 2 | **yes** | 0 | Swap each adjacent byte pair (16-bit-word byteswap) — universal for 68000 program ROMs dumped in a different byte order than the CPU's native big-endian words |
| `ROM_LOAD32_WORD[_SWAP]` | 2 | opt | 2 | 2-of-4-byte interleave (2 chips forming a 32-bit bus), optionally word-swapped |
| `ROM_LOAD64_WORD[_SWAP]` | 2 | opt | 6 | 4-way word interleave (4 chips forming a 64-bit-wide gfx/data bus) — the norm for CPS1/CPS2 tile-graphics mask ROMs |

The reversed-group byte copy (confirmed from `romload.cpp`'s
`read_rom_data()`): for `groupsize=2, reversed=true`, `dest[0]=src[1],
dest[1]=src[0]` per word, repeating every `skip+groupsize` bytes in the
destination. Port this loop directly rather than assuming "SWAP just means
big/little-endian" — get the loop from the source, not from the macro name.

## A protection-MCU dump's file size alone identifies the protection scheme, before reading any code

Sega (and other vendors') arcade boards from this era shipped several
mutually-exclusive protection schemes across different revisions of "the
same" game — most commonly a discrete protection microcontroller (Intel
8751, socketed, its internal ROM readable/dumpable) vs. a CPU-encryption
daughterboard (FD1089/FD1094 on Sega System 16-family boards) that instead
scrambles the *main* CPU's opcode fetches. These are easy to conflate by
name alone ("Golden Axe (8751 317-123A)" vs. "Golden Axe (FD1094
317-0122)" — same base game, different revision). The file size of a
socketed-MCU dump is a free, instant tell: an i8751 has exactly 4 KiB
(0x1000 bytes) of internal ROM, so **any ~4096-byte file in the romset is
almost certainly an 8751 dump, not a key** — a real FD1089/FD1094 key file
is a different size and role entirely (it decrypts the *main* program
ROM's opcode-fetch space in place; there is no separate small MCU dump for
that scheme). Confirmed on Golden Axe (`goldnaxe` MAME set): `317-0123a.c2`
at exactly 4096 bytes, cross-referenced against `ROM_REGION(0x1000, "mcu")
// Intel i8751 protection MCU` in `segas16b.cpp`, identified the set as the
non-FD1094 revision on sight, before reading any driver code at all.

## Per-game encryption keys: check `historic-mame` before assuming they're lost to `.key` files only

Older CPS2 (and other MAME arcade drivers with per-game ciphers) shipped
their decryption keys **hardcoded directly in driver source** before the
modern convention of a separate `<game>.key` ROM-region file. Current
mamedev/mame has moved on to `.key` files for new sets, but the historical
hardcoded tables are still findable in `mamedev/historic-mame`'s frozen
source tree (e.g. `src/mame/machine/cps2crpt.c` for CPS2) and are a free,
independent cross-check for whatever your own key-file decode produces —
confirmed useful even when the current driver only ships a `.key` region:
decode the `.key` bytes yourself, then diff the result against the historic
table's hardcoded entry for the exact same romset name. Agreement across
multiple independent fields (master key, plus any documented watchdog-
instruction/range fields) is strong evidence your key-decode is correct.

## Sega System 16-family palette RAM word format is shared across the whole generation, not just one game

`sega_16bit_common_base::paletteram_w` (`src/mame/sega/segaic16.cpp`) is
the palette-word decoder for System 16A/16B and siblings sharing the same
video hardware (System 18, the Out Run family, etc.) — one 16-bit word per
color, `sBGR BBBB GGGG RRRR` (bit 15 = shadow/hilight select, bits
14/13/12 = an extra low-order bit for B/G/R respectively, then the B/G/R
nibbles), fed through a resistor-ladder DAC (not a linear scale) per game.
Confirmed for Golden Axe (uses the default handler, not a
philko/hangon-style override) — see
`~/Development/kolbold/docs/goldenaxe/sys16/data-structure.md` §3 for the
full bit table and a reusable TypeScript decoder
(`src/assets/formats/segas16-gfx.ts`'s `decodeSega16PaletteWord`). Worth
checking against this source before re-deriving a palette format from
scratch for any other System 16-family game.

## Confirming a runtime-programmable palette/register write: byte-scan for the register's literal address, then check whether the write is unconditional

For any board with a movable/base-register hardware resource (palette RAM
base, tilemap base, sprite RAM base — common on CPS1/CPS2 and any other
MAME-driver family with a `cps1_base()`-style indirection layer), a cheap
and reliable technique beats a blind data-region byte-pattern census for
finding both the *mechanism* and any *static source data* copied through
it:

1. Get the exact register name/offset/semantics from the emulator driver
   source itself (not a guess) — e.g. CPS1's `CPS1_PALETTE_BASE`
   (`$80010a`) and `palette_control` (`$800170`) from `cps1.h`/
   `cps1_v.cpp`'s `cps1_base()`/`cps1_cps_a_w()`.
2. Byte-scan the assembled, unencrypted ROM for that register's literal
   4-byte absolute address (as it would appear as a `MOVE.W #imm,
   $ADDR.L`-style instruction's operand bytes). This is a narrow, targeted
   scan, not a blind census — expect a small number of hits (confirmed on
   Knights of the Round: exactly 2 hits each for two different CPS-A/CPS-B
   registers, both immediately useful).
3. Disassemble around each hit. **The deciding test for "is this real
   confirmed data" vs. "just plausible-looking ROM bytes" is whether the
   write is unconditional** — a hardcoded constant written at boot *and*
   (if applicable) every single interrupt/frame, with no branch depending
   on runtime state, is strong, code-path-verified evidence. A write
   that's only reachable through data-dependent branches needs more care
   before trusting what it writes. **A raw hit is not proof of an
   absolute-address reference by itself** — a 4-byte match can also be two
   unrelated 16-bit fields concatenating to the target value by
   coincidence, most commonly a `d16(An)` addressing mode's two
   displacement words (confirmed on D&D: Shadows over Mystara, `kolbold`:
   scanning for a different literal address got 7 raw hits, every one a
   false positive from exactly this concatenation, not a real absolute
   operand) — disassembling around the hit and checking the instruction's
   actual addressing mode (not just eyeballing the 4 bytes) is what step 3
   is really for; don't skip it even when the hit count looks encouragingly
   small.
4. If the register's value points at a fixed RAM shadow address that's
   itself initialized from ROM (a boot-time copy loop), trace that loop's
   *source* pointer back into ROM to find the actual static data table,
   and decode it with the driver-source-derived word format.

Confirmed on Knights of the Round (CPS1, `kolbold`): this exact sequence
found and decoded a genuine, code-path-verified 512-color/32-bank
boot-time palette table (maincpu ROM offset `0x1554`) in well under an
hour of disassembly — a stronger and cheaper result than Golden Axe's
palette work on the same project, which only found an unconfirmed
gradient-shaped candidate via byte-pattern plausibility scanning (see
`monotonic-integer-table-mimics-smooth-color-gradient.md`). The technique
generalizes past palettes to any MAME-driver hardware resource with a
runtime-programmable base register and public emulator source describing
it. See `~/Development/kolbold/docs/knights/cps1/data-structure.md` §§
2.3, 3.3 for the full worked example (register map, boot trace, VBLANK
interrupt handler, and the palette-word format ported to
`tools/shared/cps2/palette.ts`).

**When you don't even know the register's own address yet** (unlike CPS1's
`CPS1_PALETTE_BASE`, a memory-mapper's *config*-register addresses may not
be locatable in the disassembly at all — see the 315-5195 case below), a
system-wide census of only `LEA An,(abs).L` / `PEA (abs).L` opcodes,
bucketed by 64 KB bank, is a stronger and cheaper alternative to a raw
4-byte absolute-address byte scan for finding a *content* address instead
(i.e. skip the register write, go straight for where its target region
gets read/written). Restricting to these two opcodes' operand bytes
sidesteps the `d16(An)` false-positive class in step 3 above entirely — a
`LEA`/`PEA` absolute-long operand is unambiguously the address, unlike a
raw 4-byte window that can also be two unrelated 16-bit fields (an
immediate word + a displacement word) concatenating to the target value
by coincidence. Bucketing broadly by 64 KB bank (not a narrow guessed
range around one hypothesis) also matters: a real hardware/RAM region
tends to be one of only a handful of banks referenced this way in the
*entire* program, so the bucket counts alone (a handful of banks with
dozens-to-hundreds of hits each, vs. everything else at zero) point
straight at the real candidates without needing a hypothesis to test
first. Confirmed on Golden Axe (System 16B, `kolbold`): this census (only
6 distinct 64 KB banks referenced by `LEA`/`PEA` anywhere in `maincpu.bin`)
immediately surfaced the already-confirmed I/O region (`$C40000`, 10 hits)
alongside a new one — text/tile RAM (mapper region 4) at `$100000`/
`$110000` (57/155 hits) — where a prior session's raw byte scan for the
mapper's own literal config-register addresses had found only `d16(An)`
coincidences (6 hits, all false positives, all resolving to an unrelated
local scratch-struct write once disassembled). A second, independent
confirmation (a disassembled boot-time RLE tile-RAM clear routine whose
destination address and byte extent matched the region's documented 64 KB
size exactly) corroborated the census result. See
`~/Development/kolbold/docs/goldenaxe/sys16/data-structure.md` § "maincpu"
→ "Tile/text RAM physical address" for the full worked example.

## A community hardware-notes doc is a second oracle, independent of MAME's own source — and can confirm physical addresses by literal matching, without full disassembly

Several MAME-covered arcade boards have a hand-written, publicly-hosted
hardware-notes document from the reverse-engineering community (Charles
MacDonald's write-ups are the best-known example — Sega VDP/System
16B/Genesis, among others) that describes the same hardware **from an
independent methodology** (real-hardware probing/datasheets, not reading
MAME's emulator source). Treat this as a second, independent ground truth
alongside the driver source, not a redundant restatement of it — two
sources agreeing bit-for-bit on a format is stronger evidence than either
alone, and the hardware-notes doc often documents things the emulator
source doesn't need to spell out (register-address conventions, "why" a
mystery write exists, `# of colors per palette bank` broken down by layer).

**It can also confirm a physical bus/mapper address without a deep
disassembly trace**, when the doc lists concrete example addresses for a
similar/sibling game on the same board family. If the target game's own
boot-code disassembly performs hardware writes at those *same literal
addresses*, for the *same documented purpose* (e.g. "$C40001: Miscellaneous
control", "$C43007: mystery write, Shinobi does this too") — even a
"nobody knows what it does" quirk repeating at the identical offset is
strong corroboration — that's confirmation both of the decode format *and*
of a runtime-programmable region's physical base, cheaper than tracing the
memory-mapper's own config-register writes. Confirmed on Golden Axe
(System 16B): MacDonald's notes, written around a *different* game
(Shinobi) on the same board generation, gave the exact I/O region base
(`$C40000`) and the exact same unexplained `$C43007` startup write, letting
a handful of boot-code instructions confirm the 315-5195 mapper's region-7
physical address without locating the actual config-register writes. See
`~/Development/kolbold/docs/goldenaxe/sys16/data-structure.md` § "maincpu"
for the worked example (address table, cited verbatim from both sources).

## A sample/DSP chip's MAME device source is a strong PCM-format oracle when it's a low-level (not high-level) emulation

Check whether the sound chip's `device_sound_interface` implementation is
LLE (runs the real chip's own dumped internal microcode — check the
device source's own header comments) before trusting its low-level
register-read/external-ROM-read function bodies as literal ground truth
for the raw sample data's bit format (signed vs. unsigned, bit width,
byte order); see `~/.claude/agents/game-re-method/
verification-techniques.md`'s "Sample-to-sample delta... discriminates
signed vs. unsigned 8-bit PCM" section for the full technique, including
an empirical cross-check that doesn't depend on reading emulator source
at all. Confirmed on Capcom QSound (`kolbold`, ddsom/ddtod): MAME's
`qsound_device` is LLE (runs the DL-1425's real DSP16A microcode), and its
`dsp_sample_r()` gave the exact raw-byte-to-PCM-sample formula directly.

## Z80 sound CPUs are the norm on this era's boards — and radare2's z80 disassembler needs a specific caveat

Most MAME-driver arcade boards from the CPS1/CPS2/System 16 generation
pair the main CPU with a Z80 running the sound driver (an `audiocpu`
region in `ROM_START`), commonly talking to a dedicated sample/DSP chip
(QSound, OKI MSM6295, YM2151, ...) through a shared-RAM mailbox the main
CPU writes commands into. `radare2 -a z80` disassembles these fine, but
see `~/.claude/agents/game-re-lessons/
r2-z80-relative-branch-raw-operand.md` before trusting any `jr`/`djnz`
instruction's displayed operand as a resolved address — it isn't one.

## A PC-relative displacement scan resolves "what reads this candidate table" on any 68000 arcade board, not just Amiga

`~/.claude/agents/game-re-tooling/amiga.md`'s PC-relative `PEA`/`LEA
d16(PC)` brute-force xref scan (compute effective address = extension
word's own address + signed displacement, for every occurrence of the
opcode) is not Amiga/HUNK-specific — it's a generic 68000 addressing-mode
fact, and it generalizes cleanly to MAME-driver 68000 boards (System 16,
CPS1/CPS2, etc.) that have no relocation table at all. For `LEA
(d16,PC),An` specifically the opcode words are `0x41FA`/`0x43FA`/
`0x45FA`/`0x47FA`/`0x49FA`/`0x4BFA`/`0x4DFA`/`0x4FFA` (one per destination
address register `A0`-`A7`), each followed by a 16-bit signed
displacement; `PEA (d16,PC)` adds `0x487A`. A flat scan of every
2-byte-aligned word in the ROM image for these opcodes, filtered to hits
whose computed effective address lands in a candidate range, finds every
real reference in one pass — no disassembly needed for the search itself.

Confirmed on Golden Axe (System 16B, `kolbold`): a prior pass had
hypothesized a ~72-byte, ASCII-punctuation-shaped blob (sitting right
after a confirmed table) was an ASCII→tile-index font-remap table, based
on byte-pattern resemblance alone (no traced consumer). Running this scan
against the blob's address range found **no** hits — but scanning the
*8 bytes immediately before it* found 3 real `LEA(pc),An` references,
resolving to a completely different, fully-disassemblable consumer: a
boot-time RAM-block-clear parameter header (`[destOffset][unused]
[outerCount-1][innerCount-1]`) that only ever reads those 8 bytes, never
the punctuation-shaped blob after it. The byte-pattern hypothesis wasn't
just unconfirmed — it was mis-scoped: the "table" being pattern-matched
against was never the whole thing a real consumer read; the confirmed
consumer's actual input was a much smaller adjacent range. **Lesson:**
when a candidate table is hypothesized purely from how its bytes look
(not from a traced reader), run the displacement scan across a **range
wider than the guessed table** — including bytes immediately before and
after it — since the real boundary the code actually reads may not
coincide with where the byte-pattern reasoning drew the line.

## Driver source's `INPUT_PORTS_START`/`PORT_DIPNAME` is a free oracle for a work-RAM value's real-world MEANING, not just the container's layout

Every other technique in this file uses driver source to identify
*container/ROM layout* (which file is which region, how bytes are
copied). The same source also settles what a disassembled **work-RAM
value computed from an I/O port read** actually means in-game, with zero
further tracing: match the disassembled bitmask against the driver's own
`map(port, port).portr("DSWn")` + that port's `PORT_DIPNAME(mask, ...)`
block. A byte-exact mask match confirms both the port's identity (which
DIP bank) and the value's real-world semantics (what each bit pattern
means, e.g. difficulty rank, lives count, coinage) in one step, and often
confirms a companion data table's *semantic direction* for free (a table
selected by "Difficulty" should escalate with difficulty — check that it
does).

Confirmed on Black Tiger (`kolbold`): a disassembled `((~in(0x04)) &
0x1c) >> 2` computation (feeding an index into an otherwise-unexplained
16-record shop-price table) was confirmed byte-exact as literally the
"Difficulty" DIP switch by finding `blktiger.cpp`'s `nomcu_main_io_map`
maps I/O port `0x04` to `"DSW1"`, and DSW1's own `PORT_DIPNAME( 0x1c,
0x0c, DEF_STR( Difficulty ) )` uses the identical `0x1c` mask — settling
the register's identity and its 0-7 value's real meaning (0=Easiest,
7=Hardest, after the code's own invert+shift) with no schematic tracing
and no emulator, and confirming the shop table's prices correctly
escalate with difficulty (the expected direction, not an arbitrary
correlation).

## A driver's own source-commented "unverified guess" table can be confirmed structurally against real ROM/PROM bytes with zero disassembly

Several MAME drivers ship a hand-tuned software table with a comment
admitting it wasn't derived from real hardware (a priority/palette/
timing table "compiled by looking at the game... not derived from a
PROM/ROM so it could be wrong"). Before treating such a table as
permanently unverifiable, check whether the SAME board ships a
small hardware ROM/PROM whose role the driver's own hardware notes
(silkscreen removal notes, schematic references) plausibly assign to the
exact same function — then compare raw byte VALUES directly, no
disassembly or emulation needed:

1. Dump the candidate PROM/ROM's raw bytes and histogram them. A 4-bit
   bipolar PROM's real value SET should be small (a genuine lookup/
   priority table rarely exceeds the number of distinct outputs the
   driver's guessed table itself uses) — an exact value-set match (e.g.
   both use exactly `{0,1,2,3}`) is a strong first filter before any
   further analysis.
2. Collapse both the PROM's address space and the driver's guessed
   table's index space to the SAME granularity (the PROM's real
   addressable resolution is usually coarser than the software index —
   check for constant-value runs/step-function bins rather than assuming
   1:1 addressing) and compare which entries are non-zero/notable and in
   what relative order.
3. A real hardware nibble's specific VALUES don't need to match the
   driver's internal labels verbatim — MAME's own `tileinfo.group`/
   similar indices are often an arbitrary internal render-order
   convention, not a literal copy of a real signal. What must match is
   the STRUCTURE: which inputs get distinguished treatment, how many
   distinct non-zero tiers exist, and in what boundary positions —
   including an exact match on the byte-count/entry-count FRACTION each
   tier occupies (a strong, cheap invariant: two independently-produced
   sources — a real fused PCB PROM vs. a MAME author's manual guess —
   agreeing on tier-size fractions to 3 decimal places is not chance).

Confirmed on Black Tiger (`kolbold`): `bd02.9j` (a Signetics 82S129, one
of 4 otherwise-uncharacterized bipolar PROMs on the board) collapses to
an EXACT structural match — same 3 non-zero bins, same 5 all-zero bins,
identical 0.125/0.125/0.125/0.625 byte-count fractions — against
`blktiger.cpp`'s own hand-guessed 16-entry bg-tile priority
`split_table`, whose source comment explicitly flags it as "a guess...
not derived from a PROM so it could be wrong." This is the same class of
result as Golden Axe's real resistor-ladder DAC data and Knights of the
Round's real boot-time palette table elsewhere in this project (see the
`kolbold` corpus entry) — a driver's own admitted guess turning out to be
independently confirmable (or, in principle, refutable) from the
target's own shipped ROM bytes, no external oracle needed.

## See also

`~/.claude/agents/game-re-lessons/cps2-decrypt-input-must-be-raw-rom-bytes.md`
and `~/.claude/agents/game-re-lessons/cps2-gfx-needs-extra-unshuffle-pass.md`
for CPS2-specific traps found via this workflow (both plausibly generalize
to other MAME-driver families that do similar loader-vs-cipher or
loader-vs-gfx-decode byte-order tricks).
