# Two independently-named pointers may be the same object — confirm identity via a handler that already touches known content through one of them

**When it bites:** two structures have been independently named and
documented from different angles (e.g. a bytecode/script interpreter's own
"context" pointer, found by tracing the VM's dispatch loop; and a
persistent, save-carried state block, found by tracing gameplay-counter
reads/writes) in the same overlay/module, and it's tempting to either
assume they're unrelated or to leave "are these the same object?" as an
open question needing a fresh trace from scratch.

Confirmed on Valkyrie Profile (PSX, `valkyrie`), 4th pass on
`vp1psx-slot4807-sacred-phase`: the field overlay's scene-script VM has a
documented interpreter context pointer `ctx = *(0x8007F1EC)` (from
`scene-script-vm.md`, derived by tracing the VM's dispatch loop). The same
overlay separately has an already-known opcode handler at `0x8007107C`
documented only as "`P[0x388] += arg`" (an adjuster for the persistent Seal
Rating counter, `P` being the overlay's resident save-state block reached
via its own, differently-discovered pointer in other overlays). Rather than
hunt for a fresh, independent trace of `P`'s pointer in this specific
overlay, re-disassembling `0x8007107C` itself settled it in one step: its
base-register load is `lui $v1,0x8008; lw $v1,-0xe14($v1)` — i.e.
`*(0x8007F1EC)`, byte-identical to the documented `ctx` address. Since this
handler is independently known (from a different investigation) to write a
real `P`-block field through that base, `ctx` and `P` are provably the same
object for this overlay, with no new tracing needed beyond reading one
already-cited handler's raw operand bytes. It also explained an
architectural puzzle for free: this overlay never compiled a general
`GetFlag`/`SetFlag`-shaped accessor, because it never needed a separate `P`
pointer at all — the interpreter's own context register already was one.

**The general technique:** when two pointers/structures are suspected to be
the same object, don't reach first for a fresh independent trace of either
one's provenance. Check whether any *already-documented* handler touches
known content (a specific struct field, a specific opcode's effect) through
one of the two pointers, then re-disassemble just that handler's base-load
instruction and compare its literal address against the other pointer's
already-documented value. A byte-exact match is a one-step identity proof,
reusing work two earlier, unrelated investigations already did — cheaper
than re-deriving either pointer's origin from scratch, and it can retroactively
explain why a search for a *second* mechanism (here, a general flag
accessor) came back empty: there was only ever one object to route through.

See `docs/valkyrieprofile/psx/data-structure.md` § 20.28-20.29 and
`tools/valkyrieprofile/probe-sacred-phase-worldmap-states8-13.ts` (Section G)
for the worked example.
