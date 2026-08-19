# radare2's SNES/65816 disassembler doesn't track M/X flag width — and even your own flag-aware disassembler needs the *right* entry state, not a project-wide default

**When it bites:** About to trust a raw radare2 linear disassembly of a
65816/SNES binary — especially right after a `RESET` handler or any other
code that starts in 8-bit emulation-mode width, before the first
`REP`/`SEP`. **Also** bites when calling your *own* hand-rolled flag-aware
disassembler (the fix below) on a function you're jumping straight to,
rather than one you've traced there linearly from a known-good start —
seeding it with a "usual" M/X default instead of the state a real,
upstream instruction sequence actually leaves the CPU in reproduces the
exact same silent failure mode this file describes for r2, just caused by
your own wrong assumption instead of a tool limitation.

radare2 6.1.9 ships a native `snes` bin+asm plugin (`format=sfc,
arch=snes`) that correctly parses the LoROM/HiROM header and sets up
virtual addressing (CPU addresses like `$00:8000` map straight to file
offsets, no manual translation needed for reads). But its **linear
disassembler does not track the 65816's M/X accumulator/index-width
flags**, which `REP #$xx`/`SEP #$xx` toggle at runtime and which change
whether `LDA #imm`/`LDX #imm`/etc. are 2 or 3 bytes. Emulation-mode code
(the only mode the CPU can be in at power-on, before the first mode
switch) defaults to 8-bit A/X/Y; r2 appears to assume 16-bit immediates
from the very first instruction, so any 8-bit-immediate instruction run
gets mis-decoded (wrong operand byte count) and every subsequent
instruction in that span is garbage — until a later `REP`/`SEP` happens to
land the byte-counting back in sync by luck.

Concrete example (Wizardry 6 SNES, file offset `0x800F`): the real code,
hand-verified against raw bytes, is
```
a9 01          LDA #$01        ; 8-bit immediate — M=1, emulation-mode default
8d 0d 42       STA $420D       ; MEMSEL
5c 18 80 80    JML $808018
```
(9 bytes, landing exactly on `$8018` where a `REP #$30` follows). r2's own
output for the same span instead shows `lda #0x8d01`, `ora 0x5c42`, `clc`,
`bra 0x007f98` — plausible-looking but entirely wrong instructions, only
resynchronizing at the `REP #$30` that follows.

**Fix:** don't trust r2 (or `rasm2`) SNES output verbatim across a
mode-switch boundary — same gap in both, since `rasm2` is a stateless
one-shot disassembler with no flag tracking either. For more than a
handful of instructions, hand-verifying byte-by-byte doesn't scale — write
a small **flag-aware linear 65816 disassembler** instead (a ~250-line
throwaway Python script is enough, not committed — it's a probe tool):
decode each opcode's fixed operand length from a lookup table, special-case
only the opcodes whose operand width depends on the *current* M
(accumulator) or X (index) flag (`LDA`/`STA`/`ADC`/`CMP`/etc. immediate
forms depend on M; `LDX`/`LDY`/`CPX`/`CPY` immediate forms depend on X),
and update the tracked M/X state whenever a `SEP`/`REP` instruction is
decoded (`SEP` sets bits, `REP` clears them; bit `0x20` = M, bit `0x10` =
X). Seed the initial M/X state from context (power-on/emulation-mode
default is 8-bit/8-bit for both) and walk linearly from a known-good start
address — this only resyncs correctly across straight-line code with no
computed jumps, which is normal for tracing one function at a time. This
turned a multi-hour manual byte-count exercise into an instant, reliable
disassembly for Urban Strike SNES's boot trace and its compression-codec
routine (confirmed byte-exact against the game's own DMA register writes
afterward — see `game-re-corpora/strike.md`'s SNES section). Once past a
`REP #$30`/`SEP #$20` in genuinely known territory you're on stable ground
until the next mode switch — same caveat applies there too. Treat any
committed linear r2/rasm2 dump of SNES code as a *starting point*, not as
ground truth, the same way IRA's `-preproc` output needs checking on Amiga
(see `game-re-tooling/amiga.md`) — this is the 65816 equivalent of that
trap, but caused by flag-tracking rather than code/data classification.

**The entry-state trap, once you have your own flag-aware disassembler.**
M/X width is not a single project-wide constant — different call contexts
genuinely run with different flags at entry, because nothing forces every
function in a ROM to be reached with the same M/X the boot sequence
happens to use. Confirmed on Urban Strike SNES: an entire bank (`$A8`,
containing the game's actual tile/graphics upload code) was disassembled
with `X=1` (8-bit index, a reasonable-looking default carried over from
elsewhere) when the real calling context leaves `X=0` (16-bit index) at
entry — one instruction (`A0 00 00 B7`) decodes as `LDY #$00 / BRK #$B7`
at `X=1` but as `LDY #$0000 / LDA [$20],Y` at `X=0`, and every instruction
after it in that bank was consequently garbage. This produced a fully
plausible, internally-consistent-looking disassembly that supported a
wrong conclusion ("no resource dispatch exists") for an entire session,
because nothing about the mis-decoded output looked broken — same
signature as the r2 case above, just self-inflicted. **Fix:** never seed a
flag-aware disassembler's M/X state from a "usual" default when jumping
directly to a function — trace linearly from the actual call site (or the
nearest upstream `REP`/`SEP` you've confirmed executes on the path that
reaches this code) and carry the resulting state forward. If you can't
trace back to a confirmed entry state, treat the disassembly as
provisional and look for an independent sanity check (a structural
invariant, a known-good instruction shape) before trusting it for more
than a few instructions.
