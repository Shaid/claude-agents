# A relocated base pointer plus an instruction displacement can put a call target nowhere in the file at all

**When it bites:** an exhaustive literal/value census for a call target on a
relocatable executable format (Amiga HUNK, PE, ELF PIE, any format with a
load-time relocation table) comes back completely empty — not just under a
plain absolute-address search, but also under every jump-table/indirect
form already known to exist elsewhere in the same binary — especially when
another indirection mechanism in the same binary (a per-object vtable, a
type-dispatch table) is the leading hypothesis for "how is this reached"
but hasn't itself been directly confirmed to touch the target.

## What went wrong

On Reunion (Amiga OCS/ECS, `methanoid`), a copy-protection re-arm routine
at `Main.exe` file offset `0x65A0` was known to be real, executable,
non-dead code (its own body was fully disassembled and characterized), but
its caller could not be found. A prior session ran an exhaustive
instruction-level census — `JSR abs.L`, `JSR (d16,PC)`, `BSR.W`, `BSR.S`,
`JSR abs.W` — plus a raw byte search for the address as stored DATA (a
function-pointer table entry), all negative, and concluded the routine was
"reached via an indirect per-object-type vtable dispatch." A follow-up
session extended the search further still: raw 16-bit *and* 32-bit
whole-file byte search for the address in either its absolute or
hunk-relative form (still zero), a sweep of the SAME 16-bit
PC-relative-displacement jump-table idiom the binary was independently
confirmed to use in 3 other places (zero), and a sweep of `PEA
(d16,PC)`/`PEA abs.L`/`PEA abs.W` (an anti-debug vector-install idiom this
project has hit in sibling games) — also zero. All of this was real,
methodologically sound, and still came back empty, because none of it was
looking in the right place.

The real caller (found by a `re-codebreaker` escalation) was:

```
lea $64cc.l,A2      ; a RELOC32-carrying absolute-long operand
jsr ($18,A2)        ; -> hunk1Base + $64CC + $18 = hunk1 + $64E4 = the real routine
```

The `lea` operand deliberately loads an address **24 bytes before** the
real routine — landing inside an adjacent `$FEFE`-filled filler run, not on
the routine itself — and the `jsr (d16,An)` displacement makes up the
difference at the CPU-instruction level, entirely at runtime, after the
loader's relocation fixup has patched the `lea`'s operand. The routine's
real address (in either its absolute or hunk-relative spelling) therefore
**never appears anywhere in the file, in any width, under any addressing
form** — not because the search technique was wrong, but because the value
being searched for genuinely does not exist as a stored constant. It is
reconstructed by arithmetic (relocated base + fixed displacement) that a
byte-value census is structurally blind to by definition.

This project's own already-solved `1AM`/`2AM` compression codec (same
binary, unrelated subsystem) hit the identical *shape* of false negative
for a different reason: a dispatcher that should distinguish two 3-byte
magic strings (`"1AM"`/`"2AM"`) actually compares only a 16-bit half of
each, so a full-string literal search for either magic finds zero hits
even though the dispatch is real and correct. Two independent instances of
"the census found nothing because the real comparison/construction is
narrower or more indirect than what was searched for" inside one binary.

## The fix

- When a call-target census across every direct and already-known-indirect
  form comes back completely empty on a relocatable format, **the reloc
  table itself is a stronger and cheaper search space than one more
  byte-value sweep.** Parse every `HUNK_RELOC32` (or platform-equivalent)
  entry and ask directly: does any entry's *patched* value, once resolved
  (`hunkBase + storedOperand`), land anywhere near the target — including
  offset by a small displacement, not just exactly on it? Any absolute-long
  reference to code in a relocated hunk MUST carry a reloc entry to be
  fixed up at load, so a reloc-table walk is a completeness proof, not
  just a resolution aid for operands you already suspect are relocated.
- Concretely: census every **indirect-displacement call site**
  (`JSR/JMP/PEA (d16,An)` — a register-plus-small-offset call, not a bare
  `JSR (An)`) and pair each one with the nearest preceding
  **reloc-validated** `LEA $abs.l,An`/`LEA $abs.w,An` load into the SAME
  register within the same routine. Resolve `base + displacement` for
  every such pair and check whether any equals the target. This is a
  different, and here decisive, census shape from either "does the target
  appear as a literal" or "does the target appear as a jump-table entry."
- A deliberately-chosen base that lands just outside the routine (in
  padding, in a neighboring routine, anywhere but the routine's own start)
  is a strong tell of intentional obfuscation against exactly this kind of
  literal search — expect it specifically in copy-protection/anti-debug
  code, which has an incentive to defeat naive disassembly and cross-
  reference tooling.
- Don't let "no direct census hit + a nearby indirect-dispatch mechanism
  exists elsewhere in the binary" default to "must be that mechanism." In
  this case the leading vtable hypothesis was wrong — directly
  disassembling the suspected vtable resolver showed it resolved object
  IDENTITY (a pool-slot address), not a per-type handler function pointer,
  and the real answer was a completely different, simpler mechanism found
  by widening the search space rather than deepening the existing lead.
