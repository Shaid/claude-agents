# A `lui`/`addiu`-`lw`-`sw` address pair with a negative low half reconstructs to one page below the `lui` immediate's literal value

**When it bites:** reconstructing a MIPS (PS1/PS2/N64/PSP; PowerPC `lis`/`addi` likewise) address from `lui HI` + `addiu`/`lw`/`sw LO`, especially by eye. Also: writing a `lui`+`addiu`/`ori` scanner for "who constructs address T" and trusting a 0-hit result. Also: a doc cites a hex address for a global, and investigating that exact value as new structure goes nowhere.

`addiu`/`lw`/`sw` sign-extend their 16-bit immediate. When the target's low half is `>= 0x8000`, the compiler emits `lui HI+1` and a negative `LO`, so naive `HI:LO` concatenation lands exactly `0x10000` high. `ori` is the exception: it zero-extends, so it always pairs with the raw `lui HI`.

**Check / fix:**
- Never concatenate hex digits. Compute `((HI << 16) + signExtend16(LO)) >>> 0` in a script for any address you will cite, search for, or compare.
- **Scanners:** split `T` into `HI = T >>> 16`, `LO = T & 0xffff`, and generate the high-half candidate *per second-instruction type*: `addiu`/`lw`/`sw` → `LO >= 0x8000 ? HI+1 : HI`; `ori` → `HI` always. Reusing the corrected `HI` for `ori` silently misses every `ori` pair with bit 15 set — the scanner runs clean and reports a confident 0.
- **Citations:** when a cited address (even your own prior round's prose) leads nowhere, re-derive it from the call site's actual immediate-load bytes, then grep the docs for the re-derived value — it may be an already-documented structure (`doc-self-cross-reference-before-fresh-disassembly.md`).

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`): `lui $at,0x8005` / `sw …,-0x4780($at)` was transcribed as `0x8005b880`; the real target is `0x80050000 - 0x4780 = 0x8004b880`. This caused an address bug in the field engine's `P`/`charTable`/`varBase`/`bitBlock` globals, fixed by computing with a sign-extend helper instead of eyeballing.

**Variants (`valkyrie` VP1 PSX):**
- *Transcription drift* — round 25 described a "FIFO" at `*(0x8007f1e4)+0xfc`; re-disassembly gave `lui $v1,0x8008; lw $v1,-0xe14($v1)` = `0x8007f1ec`, the documented `ctx` global, whose `+0xfc` is the already-documented expression-stack pointer.
- *Half-coverage scanner* — a whole-disc sweep for `0x8002fa9c` (low half `0xfa9c`) checked only `lui 0x8003` before both `addiu` and `ori`, so it could never match `lui 0x8002 / ori 0xfa9c`. Fixing it still found nothing for this target (the real bug was a wrong base: `sub-overlay-base-is-parent-base-plus-size.md`), but the negative had been untrustworthy.

**History:** 3 recorded instances (valkyrie) — full log in `_archive/lui-addiu-negative-low-half-borrows-from-high-half.md`.
