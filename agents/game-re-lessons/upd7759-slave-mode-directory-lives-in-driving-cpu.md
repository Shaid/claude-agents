# A chip's "external-CPU-fed" operating mode moves its ROM-resident conventions into the driving program instead

**When it bites:** you're reverse-engineering a sample/speech/sound chip
that has both a "standalone" (reads its own ROM directly) and a
"slave"/"external-fed" (a driving CPU streams bytes to it one at a time)
operating mode, and you're about to assume the chip's own documented
ROM-resident conventions (a magic header, a start-address directory table)
apply — especially if a directory/header search over the sample ROM comes
up completely empty, or a first-pass decode of the chip's documented byte
grammar (starting at each candidate sample's very first byte) produces
uniformly degenerate/empty output across the entire corpus rather than a
mix of good and bad results.

An external-CPU-fed mode exists specifically so a driving CPU (a Z80 sound
program, a 68000, etc.) can take over addressing and sequencing that the
chip would otherwise do itself from ROM. That means:

1. **The sample directory itself is not in the sample ROM at all** — it's
   data (usually a handful of small parallel tables: start offset, bank/
   page number, maybe a length or gate field) baked into the *driving
   program's* own binary, only recoverable by disassembling that program's
   dequeue/dispatch routine, not by scanning the sample ROM for a magic
   signature.
2. **The driving CPU's streaming handler is typically "dumb"** — it has no
   model of the chip's internal state machine, and just pushes sequential
   bytes on every hardware handshake pulse (DRQ/IRQ/NMI) regardless of what
   internal state the chip is currently in. This means the *first few
   bytes* of every sample's byte range can be **silently consumed and
   discarded** by non-data priming/handshake states in the chip's own
   startup sequence, with **no marker anywhere in the ROM data** explaining
   why — the discard count is an emergent property of the chip's real
   state machine, not something documented at the format level.

Confirmed on Golden Axe (Sega System 16B, `kolbold` project)'s NEC
uPD7759 speech chip: the Z80 sound driver selects **slave mode** once at
boot (a control-port write triggering MAME's `upd775x_device::md_w`'s
mode-select edge), confirmed independently by the complete absence of the
chip's own standalone-mode `nn 5a a5 69 55` + 2-byte-offset-table header
anywhere in the 128 KB sample ROM. The real 20-entry sample directory
(start offset / bank number / an always-zero "gate" field) was found only
by disassembling the Z80 program's sound-command dequeue routine. A first
attempt at decoding samples straight from each directory entry's start
offset (per the chip's documented ADPCM block-header grammar) produced
**zero usable output for every one of the 20 samples** — every "header"
byte at that position was `0xFF`, not a valid grammar tag. Re-deriving
MAME's own `upd775x_device::advance_state()` state machine step-by-step
(which of its post-`STATE_START` priming states actually consume a byte
vs. just discard it) predicted exactly **5** bytes get silently eaten
before the 6th is treated as the real first ADPCM header — confirmed
empirically (all 20 real samples share the literal byte prefix
`FF 00 00 00 00`), and skipping exactly that many bytes made every sample
decode cleanly.

**Fix:** before trusting a chip's documented ROM-resident header/directory
convention, confirm which mode the specific game actually selected (a
boot-time mode-select register write is usually easy to find and trace).
If the mode is external-CPU-fed: (1) look for the directory in the driving
CPU's own program via its command-dispatch/dequeue code, not in the sample
data; (2) if a first-pass decode from each directory entry's raw offset
produces degenerate output across the *whole* corpus (not just one
sample), suspect a fixed-size discard preamble rather than a wrong
directory or wrong codec — re-derive the reference emulator's own state
machine (not just its documented grammar) to find the exact byte count,
and confirm empirically that every real sample shares the same prefix
before trusting the derived count.
