# A shared-RAM byte with only reads and zero writers in the main CPU's own code is being supplied by an unemulated coprocessor — stub it, don't chase it further statically

**When it bites:** a CPU-emulation boot harness (Method §5 / the
program-scale case in `cpu-emulation-boot-harness.md`) hangs in a
`btst`/`tst`+conditional-branch spin-loop on a work-RAM (or shared-RAM)
address, on a board with a companion coprocessor/MCU/DSP you have chosen
not to emulate.

## The technique

Before assuming the spin condition is reachable some other way (a missed
boot-sequence step, a wrong memory-map base, a timing issue), run an
exhaustive whole-ROM byte-pattern scan for that address's literal
extension-word encoding (radare2 `/x <addr_hex>` across the assembled
program image — cheap, seconds, and structurally can't miss an occurrence
regardless of the disassembler's own code/data classification, unlike an
`aaa`-auto-analysis-scoped search). Classify every hit as a read
(`btst`/`tst`/`move <addr>,Dn`/`cmpi #imm,<addr>`) or a write
(`move Dn,<addr>`/`clr`/an immediate store). If **100% of hits are reads**,
that is strong, cheap, structural evidence the value is written by
something outside the emulated CPU's own instruction stream — a
protection MCU, a sound/DSP coprocessor, or any companion chip sharing the
RAM — not a bug in your harness or a step you haven't found yet.

## The fix

Force the harness's memory-read callback to return a plausible constant
for that specific address (all bits set to satisfy a `btst`-based
"ready"/"done" poll; or, if the spin-loop compares against **literal
constants visible in the comparison instruction itself** — e.g. a
hardcoded checksum-verification loop — return those exact literal values).
Label the stub clearly as an artificial workaround, not a coprocessor
emulation: everything it unblocks downstream is still the main CPU's own
real code executing for real, just not gated by a real coprocessor
response, so exact per-frame *timing* is not hardware-accurate even though
the *code path* is.

## Confirmed

Golden Axe (Sega System 16B, i8751-protected board, `kolbold`): a Musashi
68000 harness booting `maincpu.bin` from reset hung inside the very first
VBLANK/IRQ4 handler, self-masked so no further interrupt could break it,
spin-waiting on work-RAM byte `$EC96`. A `/x ec96` scan found exactly 12
occurrences in the whole 512 KB ROM, all reads. Stubbing it to `0xFF`
unblocked execution, which then hit a **second, structurally identical**
blocker — a 4-word hardcoded-checksum compare (`$ECD8`/`$ECDA`/`$ECDC`/
`$ECDE` against literal constants) with the same all-reads signature.
Stubbing both let the harness reach real steady-state execution and
dynamically confirm a separate static-disassembly finding (the sprite
template-pool writer) byte-for-byte. See
`~/Development/kolbold/docs/goldenaxe/sys16/data-structure.md` § 6 for the
full worked example. This is the CPU-emulation-harness-specific case of
the general root-vs-shape distinction in
`negative-from-addressing-root-not-shapes.md` — here the "negative" (no
writer exists in the CPU you're emulating) is the useful, load-bearing
result, not a dead end.
