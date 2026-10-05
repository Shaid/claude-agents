# A census for carry-chain opcodes (68k `addx`/`roxl`/`roxr`, or the equivalent on other CPUs) is a near-specific locator for hand-written bit-stream readers

**When it bites:** hunting for a custom compression/decompression routine
(or any hand-written variable-length bit-stream reader/writer) in
disassembly, and a general "look for an unpacking loop" reading pass over
the plausible code region has already been tried and come up empty or
ambiguous.

## What went wrong (and what worked)

Reunion (Amiga OCS/ECS floppy, `methanoid`): a `re-codebreaker` escalation
needed to locate two in-house LZ77 decompressors inside `Main.exe`'s CODE
hunk. A prior session had already read through the plausible region
looking for a recognizable unpack loop and found nothing conclusive. A
targeted census for the 68000's carry-propagating shift/rotate/add-with-
extend family — `roxl`/`roxr` (rotate through carry, the standard idiom
for shifting a "next bit" out of a multi-word bit accumulator) and `addx`
(add with extend, used to chain a multi-word arithmetic/shift operation
across register boundaries) — found **both** decompressors' bit-reader
cores in one pass, at addresses the earlier general read had walked past.

The reason this opcode family is such a strong locator: ordinary
data-movement and arithmetic code essentially never needs the carry flag
to persist meaning across instructions (`roxl`/`roxr`/`addx` are the *only*
68000 opcodes whose defined behavior depends on the incoming X/carry bit
from a *previous* instruction). A hand-written bit-stream reader is
essentially the only code shape that legitimately needs this — pulling one
bit at a time out of a word via `lsr`/`roxr` and testing the bit that fell
into the carry flag, or synthesizing a "sentinel" bit via `addx` to detect
when an accumulator has been fully consumed. A raw byte-pattern census for
these opcodes therefore has an extremely low false-positive rate relative
to its hit rate on genuine bit-stream code.

## Fix

When searching disassembly for a custom bit-level codec (compression,
protection-check, checksum) and a general read-through pass stalls, run an
opcode census specifically for the target CPU's carry-chain family before
trying anything more elaborate:

- 68000/68020: `roxl`, `roxr`, `addx`, `subx`, `negx`
- x86: `adc`, `sbb`, `rcl`, `rcr`
- ARM: instructions with the `S` flag feeding a subsequent `adc`/`sbc`, or
  explicit carry-using shift forms

This generalizes past compression codecs to any hand-written bit-packed
format reader/writer (checksum accumulators, protection-check bit
scramblers, custom RNGs built from shift registers) — the same opcode
family is the tell for all of them, since they share the same underlying
need to carry single-bit state across instruction boundaries.
