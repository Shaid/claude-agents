# A `lui`/`addiu`-`lw`-`sw` address pair with a negative low half reconstructs to one page below the `lui` immediate's literal value

**When it bites:** hand-reconstructing a MIPS 32-bit address from a split
`lui $rt, HI` followed by an `addiu`/`lw`/`sw ..., LO($rt)` pair, and reading
the address off as `(HI << 16) | LO` or `(HI << 16) + LO` without checking
the sign of `LO` first — especially when transcribing addresses by eye from
a disassembly listing rather than computing them, or when a symbol/global
looks like it's landing one instruction-word-alignment or one page away.
Also when *writing* an automated scanner that searches disassembled bytes
for code constructing one specific target address via `lui`+`addiu`/`ori`
(to find an indirect call site, a jump-table build, or any "does anything
reference constant X" census) and a "0 hits" result is about to be trusted
or escalated — see the Variant below for a distinct failure mode in the
scanner itself, not in a human reading its output
from where every other reference to the "same" symbol lands. Also fires
when a doc's own prose cites a specific hex address for a global/field and
a later round is about to investigate that exact value as new, undocumented
content rather than first re-deriving it from the cited call site's own
`lui`/`addiu` bytes — see the transcription variant below.

## The trap

`addiu`/`lw`/`sw`'s 16-bit immediate is **sign-extended**, not
zero-extended. A compiler emitting a split address for a target whose low
16 bits have the high bit set (i.e. `target & 0xffff >= 0x8000`) cannot
just concatenate `HI:LO` — it must emit `HI + 1` in the `lui` and let the
negative `LO` subtract back down:

```
lui   $at, 0x8005      ; NOT the top half of the real address
addiu $t0, $at, -0x4780
```

Read naively as `(0x8005 << 16) | 0xb880` this looks like `0x8005b880`. It
is actually `0x8005b880 - 0x8005b880`... worked correctly: `(0x8005 << 16) +
(-0x4780) = 0x80050000 - 0x4780 = 0x8004b880` — one full page (`0x10000`)
below the naive reading, because the assembler pre-incremented the `lui`'s
immediate to compensate for the `addiu`'s sign-extension. Whenever `LO`'s
top bit is set, the true high half is `HI - 1`, not `HI`.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`): a `lui $at,0x8005` / `sw ...,-0x4780($at)`
pair was transcribed by eye as targeting `0x8005b880` and was the root
cause of a real address-typo bug in an early pass over the field engine's
`P`/`charTable`/`varBase`/`bitBlock` globals — the correct target is
`0x8004b880`. The error was caught and fixed by re-deriving the address
programmatically (sign-extend the 16-bit immediate, then add) instead of
concatenating hex digits by eye, and the same hand-decoding discipline
(`fields()`/sign-extend helpers, never eyeballing a `lui`/`addiu` pair) was
then used in every subsequent independent-verification script this session.

## Fix

Never concatenate a `lui` immediate with an `addiu`/`lw`/`sw` immediate as
hex digits. Always compute `((HI << 16) + signExtend16(LO)) >>> 0` (or the
equivalent in whatever language is doing the reconstruction), and prefer a
tiny script over manual arithmetic for any address that will be cited,
searched for, or compared against another source — this is exactly the
kind of one-line-looks-right arithmetic that survives a manual read-through
and only surfaces when an independent script or a cross-reference disagrees
by exactly `0x10000`. Not PSX-specific: identical for any MIPS target
(PS2, N64, PSP) and for any other ISA that splits addresses into a
sign-extended low half plus a high half (e.g. PowerPC's `lis`/`addi`).

## Variant: a round's own address citation, once written into prose, can drift by a few bytes and get trusted by a later round without re-derivation

The case above is a wrong *computation*. The same "never trust a
transcribed hex address, always recompute from the instruction bytes"
discipline also has to cover a wrong *transcription* of an address that was
never miscomputed at all — just mistyped once into prose and then
propagated as ground truth.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 26 of the
`vp1psx-scene-script-opcodes` campaign: round 25's own write-up described a
function as reading a "small FIFO queue" at `*(0x8007f1e4)+0xfc`. Round 26,
re-disassembling the exact cited call site from scratch instead of trusting
that citation, found `lui $v1,0x8008; lw $v1,-0xe14($v1)` — computing to
`0x8007f1ec`, eight bytes off from round 25's own prose. `0x8007f1ec` is
`ctx`, the project's own extensively pre-documented interpreter/field-
context global, and `+0xfc` on it is that struct's own already-documented
**expression-stack pointer** — not a bespoke FIFO at all. Trusting the
mistyped address at face value would have sent the investigation hunting
for a phantom, undocumented queue structure that doesn't exist, instead of
landing immediately on a mechanism already fully solved under a different
name.

**Fix:** when a doc cites a specific hex address for a global/field a
mechanism reads or writes — including your own project's own prior round's
prose, not just an external reference — and investigating that exact
address as a distinct, new structure goes nowhere (a doc-wide grep for it
turns up nothing, "it should be new/undocumented" leads to a dead end),
re-derive the address computationally from the actual `lui`/`addiu` (or
platform-equivalent immediate-load) bytes at the cited call site before
spending more effort on it. A citation lifted from prose — even prose one
account's own prior round wrote — is not primary evidence; the instruction
bytes are. Pair this with `doc-self-cross-reference-before-fresh-
disassembly.md`: a freshly re-derived address is always worth a fresh grep,
since it may resolve straight to an already-fully-documented structure the
wrong address gave no hint of.

## Variant: an automated `lui`+`addiu`/`ori` address-construction *scanner* silently covers only half the encoding space

The trap above is about a human (or a citation) misreading one specific
instruction pair. A related but distinct trap hits code that *searches* for
such pairs: a script hunting "does anything construct target address `T`
via `lui`+`addiu`/`ori` ahead of an indirect `jalr`" needs the *low* half's
sign to pick the *high* half candidate, and `addiu` and `ori` disagree on
it. Split `T` into `HI = T >>> 16` and `LO = T & 0xffff`:

- If `LO`'s bit 15 is set (`LO >= 0x8000`), a sign-extending `addiu` needs
  `lui $r, HI+1` — the `+1` pre-compensates for the negative `LO` it will
  add.
- `ori` never sign-extends (it's a plain bitwise OR into a register whose
  low 16 bits are zero right after `lui`), so it always needs the *raw*
  `lui $r, HI` — **never** `HI+1` — regardless of `LO`'s sign.

A scanner that checks both `addiu` and `ori` as the second instruction but
uses the *same* (sign-corrected) `HI` for both will never find a real
`lui $r,HI / ori $r,$r,LO` pair whenever `LO >= 0x8000` — exactly the
common case, since compilers pick `ori` over `addiu` specifically when they
don't need arithmetic sign extension. The scanner still runs clean, reports
a confident "0 hits," and looks like a stronger negative than it is,
because nothing about its output signals the gap — there's no exception, no
partial match, just silence on the one encoding it structurally cannot see.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): four rounds of an
increasingly rigorous "who calls this function" search culminated in a
whole-disc `lui`+`addiu`/`ori` sweep that checked only `lui $reg,0x8003`
(the sign-corrected high half for the target `0x8002fa9c`, whose low half
`0xfa9c` has bit 15 set) before both `addiu` and `ori` — silently unable to
ever match a `lui $reg,0x8002 / ori $reg,$reg,0xfa9c` pair even though one
existed to find. Adding the missing `HI` case closed the coverage gap (and
still found nothing for THIS specific target — the real bug turned out to
be an unrelated wrong base address, `sub-overlay-base-is-parent-base-plus-
size.md` — but the scanner gap was real and worth fixing on its own before
trusting the negative that led to the escalation which found it).

**Fix:** when writing (or reviewing) any `lui`+`addiu`/`ori` address-
construction scanner, check the target's low16 for bit 15 and generate
*two* high-half candidates independently per second-instruction type:
`{addiu: LO>=0x8000 ? HI+1 : HI}` and `{ori: HI}` always. Don't reuse one
"corrected" high half for both instruction forms.
