# A register-immediate-load + block-copy pair finds palette writes a boot-loop scan misses

**When it bites:** a targeted scan for a boot-time COPY LOOP into a known
palette-RAM address range comes back negative (no loop found, or only a
false-positive data table), on a CPU family with no single instruction that
stores a 16-bit immediate directly to an absolute address (Z80, 6502, and
most 8-bit-era CPUs — unlike 68000's `move.w #$rgb,paletteAddr`).

## The trap

The "individual, scattered immediate-value write instructions" technique
that cracked palette data on 68000-family targets (ddsom, Golden Axe) doesn't
port literally to Z80: Z80 has no `LD (nn),#imm16` opcode. The naive
translation — grep for `LD A,#imm8` immediately followed by `LD (nn),A` — is
a real, valid idiom, but it's not the ONLY one, and on many games it isn't
even the primary one. A negative "no boot loop found" result is often
reported as "no static palette source exists" when in fact the real
mechanism is neither a loop nor scattered single-byte immediates.

## The fix

Search for a THIRD idiom: a register-immediate ADDRESS load (`LD DE,
<paletteAddr>` — not a color value, an address) immediately or shortly
followed by a block-copy instruction (`LDIR`) reading from a ROM source
pointer. This is a small, non-looping (or lightly-indexed) block move, not a
"copy the whole palette in one big loop" boot routine, which is why a
loop-shaped search misses it entirely. Concretely: disassemble each ROM
region *linearly from a verified-good code start* (not arbitrary byte
offsets — misaligned windows produce incoherent garbage that looks like a
negative result but is really a disassembly-alignment artifact), then grep
for `ld de, <addr-in-palette-range>` and check whether a `ld bc, N` + `ldir`
follows within a few instructions. Distinguish it from unrelated pointer
setup (`ld de, addr` used for something else entirely) by requiring the
paired block-copy — that filter alone dropped ~85% of raw hits as noise on
Black Tiger (`kolbold`).

## Confirmed instance

Black Tiger (Capcom, 1987, `kolbold`): a prior session's `LD (0xd800/dc00
...),A` boot-loop scan found only a false-positive data table and concluded
"palette RAM has no static ROM-backed initial content." A follow-up session
found 3 real `ld de,<paletteAddr>`+`ldir` sites this way — 5 real SPRITES-
group0 color variants, 6 real TILES background "scene" variants, and a real
12-frame color-cycle fade animation — all thematically coherent, non-noise
data. Re-rendering the sprite/tile atlases with the recovered colors turned
flat-grey geometry into an immediately recognizable colored cast, a
decisive (not marginal) visual confirmation.

## Generalization

The underlying principle transfers past palette data and past Z80: whenever
a "search for the obvious idiom" (a loop, or a single-instruction immediate
store) comes back negative on a CPU/format lacking that exact idiom, ask
what the SAME semantic operation (bulk-write N bytes to a known destination
from a ROM source) looks like in that CPU's actual instruction set before
concluding the data doesn't exist statically.
