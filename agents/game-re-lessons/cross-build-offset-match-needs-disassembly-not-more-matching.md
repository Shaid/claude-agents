# An exact struct-offset match between two builds of the same game is a lead, not confirmation — only disassembling the candidate settles it

**When it bites:** two different builds/executables of the *same* game (a
public reference disassembly like `fe2.s` vs. this project's own local
binary; a demo vs. retail build; two regional releases) share a numerically
*exact* struct-field offset or bit-test (e.g. both read/write object
`+0x7e`/`+126`, or both test flag bit 5 at the identical byte offset), and
the temptation is to treat that exact numeric agreement as strong enough
evidence on its own to promote the local candidate function's semantic role
(what the reference build's function is documented to do) to confirmed —
especially when the match is precise rather than approximate, which feels
like it should rule out coincidence.

## What went wrong

Frontier: Elite II (`hunter` project, Amiga): the public `fe2.s` reference
disassembly documents `UpdateSystemPhysics`, an orbital-motion updater that
reads/writes a 64-bit phase pair at object `+126` and advances it by a
`+144` orbital increment. This project's own local `.1960` binary has a
handler at `file+0x8402a` that compares an object's 64-bit `+0x7e` (=126
decimal, an exact match) against the global clock and advances a phase pair
by `+0xce`. The offset match was exact, and a second, independently-found
correlation (both builds test the identical object flag bit 5 at offset
`+0x118`/`+280`) reinforced it further — two numeric agreements, not one.
This was documented as a strong "lead," correctly hedged as unconfirmed
pending a caller/signature match, but the hedged framing still shaped every
subsequent hypothesis toward "this is the orbital updater."

Actually disassembling the candidate function's body refuted it. `0x8402a`'s
"due" branch doesn't advance a continuous orbital angle at all — it swaps
the object's live model field to a specific marker/flash model (`0x00ba`,
confirmed via the model table to have a distinct, richer header than its
neighboring ship models — a "special" overlay model, not a mesh in normal
rotation) and sets a state byte. A second, physically adjacent handler at
`file+0x84082` shares the *identical* 16-byte clock-compare prologue but is
the matching restore: it copies the saved former model back and clears the
state. Together they're a **timed set-then-restore marker/flash event** —
a mechanism that happens to reuse the same `+0x7e` timestamp field and
`+0xce`/`+0x118` conventions the orbital module also uses elsewhere in the
same object record, not the orbital module itself. The `+0x118` bit-5 test
is real corroborating evidence that this hunk-9 neighborhood shares object
conventions with the public build's physics code — it just doesn't pin down
*which* function in that neighborhood is the physics updater.

## The fix

Treat an exact cross-build offset/bit-test match the same way the project's
own verification bar treats a "70% shape match": necessary evidence, never
sufficient on its own, no matter how precise the number. The reason it can't
be sufficient is structural, not statistical — the same object-record field
(a timestamp, a flag byte, a scratch offset) is routinely read and written
by *multiple, semantically unrelated* handlers in the same engine (a
scheduler reuses its clock-pair convention for marker events, damage timers,
AI cooldowns, and orbital motion alike), so matching the *field* only
narrows the search to "some handler that touches this field," not to the
one specific handler the reference build names. The only test that actually
discriminates is reading what the candidate function's own body *does* on
each branch (disassemble it, don't just locate it) and checking that
against the reference build's documented behavior shape — an arithmetic
phase/rotation update with no state or model changes, in this case, versus
the model-swap-and-restore the local candidate turned out to be. This is a
sibling of `struct-analogy-needs-pointer-target-census.md` (a shape/field
match needs a corpus-wide pointer-target census, not eyeballing, to become
confirmed) and `cross-disassembly-fingerprint-false-positive.md` (a matched
instruction run between two disassemblies of the *same* binary still needs
a divergence-point check) — the same discipline applied specifically to a
numeric offset/bit-test correlation between two *different* builds of one
game.
