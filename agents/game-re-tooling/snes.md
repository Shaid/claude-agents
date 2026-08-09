# Tooling — SNES / Super Famicom (65816, LoROM/HiROM, SPC700)

`Read` this when working on an SNES/Super Famicom target. Covers ROM header
conventions, radare2's native SNES support and its sharp edge, and a
JRPG-era text-encoding shortcut worth trying before assuming a custom
tile-indexed glyph system.

## Reference: fullsnes.txt

`fullsnes.txt` (same directory as this file) is Martin Korth's (nocash,
author of no$sns) exhaustive SNES hardware reference — every PPU/DMA/APU
register, memory map, timing, and CPU-quirk documented in detail, extracted
from no$sns v1.6. Check it **before** re-deriving register semantics from
scratch via byte-pattern census (e.g. "what does DMA channel N's control
byte `$43x0` bit 7 mean", "what's the exact CGRAM/VRAM port read-increment
behaviour") — most of what a census/disassembly pass has to painstakingly
infer session-by-session on this project is already written down here.
Canonical source: `https://problemkaputt.de/fullsnes.txt` (re-fetch if this
copy goes stale — no version/date header is embedded in the file itself).

## ROM header and memory map

- **Copier-header check first.** Some dumps have a 512-byte copier header
  prepended. Test by size: a clean dump's byte length is evenly divisible
  by the platform's bank size (`0x8000` for LoROM); if stripping 512 bytes
  would *break* that divisibility while keeping it intact does not, the
  file has no copier header. Confirm by checking the internal header parses
  and its checksum validates (below) at the un-adjusted offset.
- **LoROM header location and offset math:** the internal header lives at
  file offset `0x7FC0` (= CPU address `$00:FFC0` — LoROM maps bank `$00`'s
  CPU window `$8000`-`$FFFF` 1:1 onto file offset `0x0000`-`0x7FFF`).
  General LoROM file-offset↔CPU-address conversion: for file offset `o`,
  `bank = floor(o / 0x8000)`, `addr = 0x8000 + (o mod 0x8000)`, CPU address
  = `bank:addr`. Banks `$80`-`$FF` are hardware mirrors of `$00`-`$7F` — the
  same physical byte is addressable as either `$1E:8A4A` or `$9E:8A4A`;
  disassembly/code may cite either form for the same bytes.
- **A file offset `>= 0x8000` is never bank `$00` — re-run the formula at
  every citation, don't eyeball a disassembler's raw-offset label as the
  CPU address.** Crossing file offset `0x8000` is a **bank rollover** in
  CPU-address space (`bank = floor(o/0x8000)` increments), not a
  continuation of bank `$00`'s address range — straight-line 65816
  execution can't cross it either, since a bank's addressable window ends
  at `$FFFF` and doesn't auto-carry into the next bank without an explicit
  far jump/call. A throwaway linear disassembler that labels its output
  with the raw file offset (e.g. `"008060:"`) looks, at a glance, exactly
  like a CPU-address-with-bank-`$00` label — nothing about the string
  distinguishes them. Confirmed on Wizardry 6 (SNES): a doc cited file
  offset `0x8060` as "CPU `$00:8060`-ish" for two sessions running (the
  second session reproduced the first's error rather than catching it),
  when the formula gives bank `$01`. The mistake also caused a *routine*
  misattribution: code actually reached via a separate task/coroutine
  call, not inline in the boot sequence the mislabeled bank made it look
  like it belonged to (see the coroutine-scheduler note below). Caught
  only when unrelated work needed to trace *how* that code was reached,
  which forced a bank recheck. Treat this as a mandatory sanity check on
  every offset citation that sits near or past a `0x8000`-aligned
  boundary, even ones already sitting in a "confirmed" doc section —
  confirmed-looking prose can carry a bank error forward indefinitely
  without anyone re-deriving it.
- **Checksum sanity check:** the header's checksum (2 bytes) and its
  bitwise complement (2 bytes, stored separately) must XOR to `0xFFFF`.
  Use this to confirm you've found the real header at the right offset
  before trusting any other field, especially after a copier-header
  strip/no-strip decision.
- **The declared ROM-size byte legitimately disagrees with the real file
  size — this is normal, not a truncated dump.** The size field only
  encodes powers of two (`size_KB = 2^value`); a cartridge whose true size
  isn't itself a power-of-two number of Mbit (e.g. 24 Mbit — `3 * 2^3`, not
  a power of two) has no exact code to declare and rounds *up* to the next
  representable one (32 Mbit here). Cross-check against an independent
  source (a ROM database, a websearch of the cartridge's known capacity)
  if in doubt — the *file size* is ground truth, not the header field.

## A community rip *definition's* address fields are still unmapped CPU addresses

When a reference project's format info comes as structured data (a JSON rip
definition, a table dump) rather than disassembly, its address fields are
still **LoROM/HiROM CPU addresses that need the platform mapping formula
applied** — even when a given value is small enough to look like it could
already be a plausible raw file offset. This is an easy trap specifically
*because* the data-driven case looks like it should need no address-space
reasoning at all (unlike reading disassembly, where the CPU-vs-file
distinction is always front of mind). Confirmed on FFIV (SNES, `ceres`
project, LoROM): `everything8215/ff4`'s `vanilla/ff4-en-rip.json` declares
each table's location as a `range` field, e.g. `"0x0FA710-0x0FA763"` for
the character-names table — small enough to be mistaken for a literal file
offset. Reading the ROM at that raw value produced 100% garbage for every
table tried; running the *same* value through the ordinary LoROM formula
(`((addr & 0xFF0000) >> 1) + (addr & 0x7FFF)`) gave `0x07A710`, which
decoded 14/14 real character names byte-exact on the very next attempt.
**Always run every address field taken from a reference project's data
(not just its prose or disassembly) through the platform's mapping formula
unconditionally, never conditionally on whether the raw value "looks like"
it could already be a file offset.**

## radare2 native SNES support

- radare2 (recent builds, confirmed working in 6.1.9) has a native `snes`
  bin+asm plugin: `r2 -a snes <file>` auto-detects `format=sfc,
  arch=snes`, parses the LoROM/HiROM header, and sets up virtual
  addressing so CPU addresses can be used directly (`pd @ 0x8000` reads
  file offset `0x0000` for a LoROM image with no copier header) — no
  manual bank/offset translation needed for simple reads.
- **Sharp edge, read before trusting any disassembly output:** the linear
  disassembler does not track the 65816's M/X accumulator/index-width
  flags (set by `REP`/`SEP`), so any 8-bit-immediate instruction stretch
  gets mis-decoded until a later flag change happens to resync it by luck.
  This is *not* a minor cosmetic issue — it silently produces
  plausible-looking wrong instructions, not an error. See
  `r2-snes-flag-width-blind.md` for the concrete example and the fix
  (hand-verify against raw bytes across any mode-switch boundary,
  especially right after RESET). The recommended fix — a small throwaway
  flag-aware linear 65816 disassembler script — has now paid off cleanly
  on two separate projects/ROMs (Urban Strike SNES, Wizardry 6 SNES):
  both times it decoded a known-good hand-verified instruction sequence
  byte-exact on the first try and was then trusted for the rest of the
  session's disassembly with no further hand-verification needed.
- **On a HiROM image, don't trust the plugin's virtual addressing beyond
  the header window without checking first.** Confirmed on FFVI (SNES,
  `~/Development/ceres`, pure HiROM+FastROM, no copier header): `r2 -a
  snes` correctly auto-detected the format and `hexdump`/`disassemble` at
  CPU address `0xFFC0` (the internal header) returned real, correct bytes
  — but the *identical* tool calls at `0xC50000` (a real HiROM bank
  address, `bank $C5`, known-good via the project's own
  `hiRomToFileOffset()` formula and independently confirmed by direct
  Python byte reads) and even at raw file offset `0x50000` both silently
  returned all-`0xFF` (unmapped memory), with no error — a linear
  "disassembly" of unmapped space renders as plausible-looking garbage
  instructions, not an obvious failure. One working address (the header)
  is not evidence the plugin's bank mapping is correct in general for a
  HiROM file; test at least one more address deep in a bank you already
  know the true content of (a checksum-validated header field is right at
  the LoROM/HiROM boundary and may be special-cased) before trusting any
  further reads. When it fails, don't debug the plugin — read raw bytes
  directly (Python/Node, or the project's own file-offset helper) instead;
  this is strictly reliable and was already the working method for
  everything else in that project.

## Finding a graphics loader without a DMA register census

The DMA-register byte-pattern census (`STA $420B`/`$4342`/`$4345` etc. —
see `verification-techniques.md`) is the first thing to try, but it only
finds resources that get DMA'd tile-by-tile with an easily-censused
register pattern. Some resources are staged into WRAM by a **plain CPU
block-move (`MVN`, opcode `0x54`) instead** — a flat, uncompressed
ROM→WRAM copy with no DMA registers touched at all, invisible to a DMA
census. If the DMA census stalls, try this instead: byte-scan the whole
ROM for opcode `0x54` and filter to operand pairs where **exactly one**
bank byte is `$7E`/`$7F` (WRAM) and the other looks like a plausible ROM
bank — this surfaces "load resource from ROM into WRAM" call sites
directly, false positives and all (raw byte scans without instruction-
boundary validation will hit some), letting you skip straight to
disassembling the surrounding code. Cracked Wizardry 6 SNES's face-
portrait bank this way after the DMA-census/VRAM-upload-loop path
stalled (the tile data turned out to be plain, uncompressed bytes staged
via `MVN`, not DMA'd from a decompression buffer).

**When censusing long-addressing instructions (`LDA long` `0xAF`, `LDA
long,X` `0xBF`, `JSL` `0x22`) for code cross-references to a candidate
data region, filter out any hit whose 16-bit address portion is `<
0x8000`.** For LoROM banks `$00`-`$3F`/`$80`-`$BF`, CPU addresses below
`$8000` map to the WRAM mirror / hardware-register space (`$0000`-`$1FFF`
WRAM, `$2000`-`$5FFF` registers, `$6000`-`$7FFF` expansion), not the
banked ROM window (`$8000`-`$FFFF`) — a raw byte scan without this check
will report such a "hit" as landing at some ROM file offset when the
instruction (if it's even real and not a misaligned false positive) can't
actually be referencing ROM data there at all. This single filter reduced
937 raw hits down to 31 candidates on Wizardry 6 (SNES) — a ~30x noise
reduction — when censusing for references into a candidate data table.
Combine with the mirror-bank normalization (`bank & 0x7f`) already needed
to compare `$80`-`$FF`-bank hits against `$00`-`$7F`-bank ones.
**Caveat found later the same project**: this filter cuts false
positives but does nothing for false negatives, and in this exact case
the real consumer wasn't among the 31 — it used `DBR`-relative indexed
addressing (bank set separately via `PHB`/`PLB`, then a short `LDA
table,X`) whose encoded table-base operand legitimately sits just under
`0x8000` because the index is pre-scaled, invisible to *any*
long-addressing-opcode census regardless of the filter. See
`indexed-table-base-below-valid-rom-window.md` before trusting a "few
hits after filtering" result as proof of a small candidate set.

**MVN operand byte order isn't safe to assume — disambiguate it
empirically per binary.** The two operand bytes after the opcode are one
source bank, one destination bank, but which is which is easy to get
backwards from memory. Don't guess: for a bank pair like `$7F`/`$85`
(one WRAM, one ROM), only one reading is physically sensible (`ROM →
WRAM`; the reverse would mean writing to ROM, which does nothing) — use
that to fix the order for the rest of the session. Confirmed for
Wizardry 6 SNES: first operand byte after the opcode = destination bank,
second = source bank (i.e. assembler mnemonic order `MVN dbank,sbank`
matches byte-stream order directly, no reversal). Once one concrete
`MVN`-shaped call site is found this way, its source-address register
(always `X`, never `Y` — `Y` is always the MVN destination pointer,
fixed CPU behaviour, not operand-dependent) can be traced backward a few
instructions to find the resource directory/table feeding it.

## `TCS` immediately followed by `RTS` is a coroutine resume primitive, not a bug or obfuscation

If a small helper function's body is essentially `STX <slot-index-save>;
LDA <table>,X; TCS; RTS` (load a 16-bit value from a per-slot table into
the stack pointer via `TCS`, then immediately `RTS`), don't file it as "a
non-obvious indirection, semantics unresolved" — it's the **resume** half
of a classic 65816/6502-family cooperative round-robin task scheduler.
`TCS` repoints the hardware stack at the slot's saved location; the `RTS`
that follows pulls its return address from *there* instead of the real
call stack, i.e. it resumes whatever address was stored 1 byte past the
slot (SAS/6502-family `RTS` semantics: pulls the address and adds 1).
Look for a paired **yield** primitive nearby (`TSC` to save the *current*
stack pointer back into the same per-slot table, then restore a fixed
kernel stack-pointer constant, then `RTS`) and a fixed-size table of task
slots initialized once at boot (a "set task entry" helper that stores
`entry_address − 1` per slot, provable by checking an idle/no-op task:
its stored value resumes execution one byte later than the store, which
only makes sense under `RTS`'s "+1" semantics). Confirmed on Wizardry 6
(SNES): this exact shape was mistaken for an unresolved indirection
across two sessions before a fresh look recognized it — once identified,
it explained the ROM's every-frame "spin loop" (NMI simply resumes the
next task each frame; there is no separate "main loop" to find, the
scheduler *is* the main loop) and immediately named the boot/opening
task's own entry point as the top-down starting point for tracing
title-screen/opening-sequence code.

## Text encoding — check half-width katakana before assuming a custom scheme

For a Japan-only SNES-era JRPG with no known font/text documentation,
**check whether short in-game strings (monster/item/spell names, menu
terms) are plain single-byte half-width katakana before assuming a fully
custom tile-indexed glyph system is needed.** Half-width katakana is a
standard single-byte range within Shift-JIS/CP932 (`0xA1`-`0xDF`, JIS X
0201 kana block), decodable with Python's stock `cp932` codec directly. For
a from-scratch TypeScript/JavaScript port (Node has no built-in CP932
decoder), the flat 63-entry lookup table below reproduces it exactly,
indexed from `0xA1`:

```
｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ
```
(`0xA5` = `･`, commonly used as a word separator in multi-word
transliterations, e.g. `"GIANT RAT"` → `ｼﾞｬｲｱﾝﾄ･ﾗｯﾄ`.)

Half-width katakana is dramatically simpler than a full double-byte
kanji font/tile-index system and self-confirms cheaply: if a candidate
byte range decodes with zero garbage/out-of-range bytes and every
resulting string is a legible, grammatically-plausible word, that's strong
evidence you've found the real encoding without needing a traced reader at
all (cracked Wizardry 6 SNES's entire monster-name table this way — 102/102
clean decodes, zero garbage). Don't extend this confidence to *full*
double-byte kanji text on the strength of a byte-range check alone, though:
a blind whole-ROM scan for valid-looking double-byte CP932 sequences (lead
byte `0x81`-`0x9F`/`0xE0`-`0xFC`, trail byte `0x40`-`0x7E`/`0x80`-`0xFC`)
produces mostly false positives from ordinary graphics/tilemap data that
happens to fall in-range — that broader case needs a traced string-table
boundary or reader before it's trustworthy, unlike the self-confirming
half-width-katakana case above.

## Static recompilation (native-port stretch goal)

See the "Recompilation landscape" table in `game-re.md` — `docs/snes-recomp.md`
in `seer` is the platform's entry there.
