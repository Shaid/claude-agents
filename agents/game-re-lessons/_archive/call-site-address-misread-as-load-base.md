# A doc's "X loads Y at address Z" list may give the call site, not Y's own load base — and a prologue at file offset 0 can't tell you which

**When it bites:** a "confirmed" base/load-address for a relocatable or
overlaid binary blob traces back to a doc's prose list of "caller loads and
runs overlay Y at address Z" rather than to an address-*independent*
internal-consistency check — especially when the same list annotates *other*
entries explicitly as call sites (`slot 1490 (battle, jal 0x800105b0 at
0x80042e24)`) while the entry in question gives only a bare address with no
"at" clause (`slot 4794 (0x8005e8c4)`). That's a strong tell it's the same
call-site convention, silently unlabeled, not a different kind of fact — the
list's author was citing where each overlay gets *invoked from*, and one
entry's citation looks different only because its wording dropped the "at"
clause, not because it's measuring something else. Also bites when several
independent-looking static techniques (direct-call census, raw-pointer
census, register-pair-construction census, even a full disassembler/
decompiler escalation) all agree on the same negative — that agreement is
not independent corroboration if every technique searched for the same
address, and that address was never independently re-derived.

Confirmed on Valkyrie Profile 1 (PSX, `valkyrie`): a session investigating
who calls a resource-loader function found the loader's own `jal` target
landing mid-body of an unrelated function in a sibling overlay — a
`ghidra-disasm` escalation confirmed this in detail and called it a hardened
negative ("the two overlays are not co-resident at these exact static
addresses, or some other mechanism is reached"). Two full TODO rows closed
as "needs a live trace/emulation." The real bug: an earlier session's doc
entry, "slot 4794 (0x8005e8c4)," was the address of the `jal` instruction
*inside the caller* that loads and runs slot 4794 — exactly the same
citation shape the very next line up in the same list used with an explicit
"at" clause for a different overlay. A later session had read it as slot
4794's own load base instead, and "confirmed" that misreading by checking
that a valid `addiu sp,sp,-N` prologue sat at file offset 0 under that
base — which proves nothing, since **a prologue at file offset 0 is
position-independent**: it looks identical no matter what runtime address
that byte is eventually loaded to. Every downstream census (jal-target
scans, raw pointer-value scans, `lui`+`addiu`/`ori` register-pair
construction, and the full `ghidra-disasm` pass) then searched for
addresses that were all off by the same constant delta (the wrong base
minus the real one, `0x2f0a0` here) — producing several *mutually
reinforcing-looking* hardened negatives that were really one wrong number
propagated through every technique.

The fix that actually cracked it: audit the **weakest-provenance premise
first** — where did this base number really come from in the docs? — rather
than trying yet another search technique on top of the same address. Once
that was suspected, the real base was pinned three independent ways before
reading a single new instruction: (1) trace the actual runtime
overlay-loader primitive (in the main executable, or the equivalent
resident loader) to see what literal destination address it decompresses
*every* overlay to — the ground-truth answer, straight from the loader's
own code; (2) re-read the ORIGINAL citation's own instruction directly,
rather than trusting the doc's paraphrase of it; (3) a data-only,
address-independent internal-consistency check on the blob itself — do a
large fraction of the file's own internal `jal` targets land on the file's
own internal `addiu sp,sp,-N` function prologues at this candidate base
(not just one), and does the file's own `lui` immediate census
overwhelmingly reference its own candidate address range rather than
some other one? All three agreed independently and none needed a single
new hypothesis about game semantics — only address arithmetic.

**Fix, generalized:** before trusting *any* "confirmed by its own
file-offset-0 prologue" claim for a relocatable/overlaid blob's load base,
check that the prologue check is actually address-dependent (it isn't, on
its own — see above) and that the base's real provenance is an
address-independent internal-consistency measurement (the file's own `jal`
targets landing on its own prologues; the file's own `lui` census pointing
at its own range), not a citation copied from a doc's prose list of "caller
loads overlay at address." When a doc lists several "X loads Y at address
Z" entries and most spell out an explicit call-site annotation while one
doesn't, assume the unlabeled one uses the identical convention rather than
treating its lack of annotation as evidence it means something different.
Related but distinct: `wrong-file-checked-before-doubting-cited-address.md`
covers re-verifying a citation against the *wrong file* when the citation
itself was right all along; this file covers the citation's *address*
itself carrying the wrong role (call site vs. load base) from the start.
`boot-upload-blob-delta-not-driver-wide.md` covers a *correctly-derived*
delta applied past its valid scope; this file covers a delta that was wrong
from its very first derivation.
