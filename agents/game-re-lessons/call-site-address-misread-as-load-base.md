# A doc's "X loads Y at address Z" list may give the call site, not Y's own load base — and a prologue at file offset 0 can't tell you which

**When it bites:** an overlay or relocatable blob's "confirmed" load base traces back to a doc's prose list ("caller loads overlay Y at Z") or to a prologue at file offset 0, rather than to an address-independent consistency check. Also: several static techniques (jal census, pointer census, `lui` pair census, Ghidra) all agree on a negative while searching for addresses derived from that same base.

In "X loads Y" lists, the cited address is often the `jal` *inside the caller*. If most entries say "at 0x…" and one gives only a bare address, assume that one uses the same convention, not a different kind of fact. A valid `addiu sp,sp,-N` at file offset 0 **doesn't depend on position**: it looks identical whatever address the blob is loaded at, so it confirms no base. With a wrong base, every downstream census searches addresses off by the same constant delta, producing several hardened negatives that seem to reinforce each other but are really one wrong number.

**Check / fix:** audit the **weakest-provenance premise first** (where did this base number come from?) before trying yet another search technique. Pin the base three independent ways, using only address arithmetic:
1. Trace the resident overlay-loader primitive to the literal destination it decompresses every overlay to.
2. Re-read the original cited instruction itself, not the doc's paraphrase of it.
3. Run an address-independent consistency check on the blob: a large fraction of its internal `jal` targets should land on its own `addiu sp,sp,-N` prologues at the candidate base, and its `lui` immediate census should overwhelmingly point into its own candidate range.

**Canonical example:** Valkyrie Profile 1 (PSX, `valkyrie`). The list read "slot 1490 (battle, jal 0x800105b0 at 0x80042e24)" and, on the next line, "slot 4794 (0x8005e8c4)". The second was also a caller-side `jal` address, but a later session took it as slot 4794's load base and "confirmed" it with the offset-0 prologue. A resource loader's `jal` target then appeared to land mid-body of an unrelated sibling-overlay function. A `ghidra-disasm` escalation called it a hardened negative ("not co-resident at these static addresses"), and two TODO rows closed as "needs a live trace". Every census was off by the same `0x2f0a0`. All three checks above agreed on the real base without any new semantic hypothesis.

Related but distinct: `wrong-file-checked-before-doubting-cited-address.md` (right citation, checked against the wrong file) and `boot-upload-blob-delta-not-driver-wide.md` (a correct delta applied beyond its valid scope; here the delta was wrong from the first derivation).
