# A "where does this global get set" search can fail because the value is passed by poking a literal operand in the code stream, not a variable

**When it bites:** you've confirmed a routine reads some selector/index from
a fixed global or a `move.w (d16,PC),d0`-style PC-relative literal, searched
every write to that global's absolute address, and found nothing (or too
little) — especially on a period 8/16-bit platform (68k, 6502, Z80) where
RAM was scarce enough that "store the parameter as an immediate operand
right after the routine, poke it before calling" was a normal, deliberate
technique, not an obfuscation trick.

Powermonger (Amiga, `RUN_PROG`): the map-select screen needed to pass a
chosen scenario index into the MAPDATA-record loader. Instead of writing to
a global, its click handler computed the index and executed
`move.w d2, $10CD4` — `$10CD4` is a literal word sitting immediately after
the loader routine's own `rts`, read by the loader via
`move.w $10cd4(pc), d0`. A search for stores to a *global* holding "current
record index" would never find this, because the "variable" is a code-
stream literal with no symbolic identity — its only clue is the `(pc)`-
relative operand at the read site and a raw absolute-address write at the
poke site, which look unrelated unless you notice the write's target
literally falls a few bytes past the read site's own routine.

**Fix:** when a `(d16,PC)`-relative load feeds a value you need to trace
back to its origin, don't just search for stores to a same-named global —
also check whether the literal itself sits inside (or right after) a nearby
routine, and search for absolute-address writes to *that specific address*
regardless of whether it looks like "data." A `move.w #imm, $ADDR.l` where
`$ADDR` equals "some routine's end + N" is the tell. This is a distinct
failure mode from `filename-template-string-may-have-a-second-live-copy.md`
(patched *string* templates) and from ordinary self-modifying opcode
patches (`crack-redirects-io-to-resident-loader-stub.md`) — here the
"parameter" itself has no home outside the instruction stream at all, ever,
by original design.

**A second manifestation, useful in the opposite direction — discovering a
resource *pairing* rather than tracing a value's origin.** A dedicated
"load resource N" fast-path function (a shortcut wrapper around a generic
by-ID loader, installed for one specific, frequently-used resource) can
have its own hardcoded ID operand poked at runtime to temporarily retarget
it at a *different* resource, then restored — directly proving the two
resources are used together in one subsystem, without needing to trace
either resource's consumer code at all. Confirmed on Dune (Amiga, `wyrm`):
`LAB_0BEA` was a known dedicated shortcut for loading `onmap.hsq` (`MOVE.W
#$0026,D0 ; [fall into the generic loader]`); grepping for writes to
`LAB_0BEA+2` (the immediate operand's own address) found a second function
patching it to `attack.hsq`'s catalog ID, calling the shortcut, then
restoring the original value — settling in one grep that the world-map
screen and the attack/combat-icon screen are the same loading subsystem,
something neither resource's own call sites would have suggested in
isolation. **Fix:** when a resource has a dedicated loader shortcut (as
opposed to always going through a generic by-ID dispatcher), grep for
absolute-address writes to `<shortcut label>+N` (the operand's own
address, same technique as the origin-tracing case above) before assuming
the shortcut is single-purpose — a self-patched target is a free,
code-level proof of resource pairing.
