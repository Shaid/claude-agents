# Zero-`filesz` program-header reservations are a free census of every module the game can load

**When it bites:** a whole subsystem's code (combat, AI, a minigame) is
absent from the main executable *and* from every module you have extracted,
the loader is known or suspected to be overlay-based, and you do not yet
know how many modules are still missing, how big they are, or where they
live — so the next step looks like another blind container hunt.

An overlay-linked executable usually keeps one program header **per
overlay**, with `filesz = 0` (nothing to load from the file) and
`memsz` = the overlay's real size at its fixed slot `vaddr`. The segment
table is therefore a complete, authoritative list of every module the binary
can ever page in — present even when the overlay's disc file has not been
located, is encrypted, or is buried in an opaque archive. It is metadata the
linker had to emit and nobody thought to strip.

**Check / fix:** `readelf -lW` the executable (`objdump -p`, or the
platform's equivalent segment dump for PE/XBE/DOL/NSO) and tabulate
`(vaddr, memsz)` for every zero-`filesz` entry. Then read it three ways:

- **Count.** The number of reservations bounds the module population; a
  loader doc claiming "a handful of overlays" against 366 reservations is
  wrong about the architecture, not just incomplete.
- **Group by `vaddr`.** Several reservations sharing one slot address are
  *mutually exclusive* overlays swapped into the same window — that grouping
  is the real module taxonomy, and it is free.
- **Match `memsz` against decoded lengths** of every disc file you can
  already decompress. The unmatched remainder is exactly the missing set,
  now with a known size for each member — which turns "find the battle code"
  into a sized lookup and lets you *rule out* candidate containers by size
  alone, without decoding them.
- **Do contiguity arithmetic.** `slot + size == next slot` means those
  reservations form one contiguous image loaded together, not independent
  modules. Size classes are semantic too: one 1.7 MB reservation and 337
  small ones are not the same kind of code.

**Canonical example:** Valkyrie Profile 2 (PS2, `valkyrie`). Battle logic
was missing from the ELF and from every extracted module.
`readelf -lW` showed **366** `PT_LOAD`s. Slot `0x35ec00` held three
reservations — two matched known decoded disc files, the third
(60,288 B) matched nothing — and `0x35ec00 + 0xeb80 = 0x36d780`,
`+ 0x1a6800 = 0x513f80`, the base of a further 337 small unmatched
reservations. That bounded the "missing battle image" to one concretely
sized target and eliminated several candidate containers on size, before any
of them was decoded. Written up in
`docs/valkyrieprofile2/ps2/battle-logic.md` § 13.5.

Sibling traps: `amiga-overlay-segment-defeats-resident-only-trace.md`
(a resident-only trace can't see overlay code at all) and
`overlay-census-blind-to-region-embedded-code-modules.md` (not every code
module gets a reservation — ones embedded inside data containers don't, so
the reservation table is a lower bound on modules, an exact list only of
*linked* overlays).

**History:** 1 recorded instance (`valkyrie`).
