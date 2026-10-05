# A resource id stored in a strided record field and carried to the loader inside a callback object is invisible to literal, `base+K`, and consecutive-value scans — all four at once

**When it bites:** an exhaustive static search for who loads a resource-id
family (a range of archive/TOC slots the game visibly displays) has run
every value-shaped search — bare immediates, `addiu rt,rs,K` base+index
forms, `lui`/use pairs, and a "≥3 consecutive in-range `u16`/`u32` values"
table scan — over the *whole* code corpus and returned a clean 0/0/0, and
the write-up is drifting toward "no static consumer; must be a not-yet-cached
overlay, a data-computed index, or needs live capture."

Valkyrie Profile (PSX, `valkyrie`), TOC slots 4772-4793 (22 full-screen art
plates). Two sessions built a "hardened, exhaustive negative": four searches
over 1,530 nested code sub-blocks + 8 top-level overlays + both boot
executables, on both discs, 0 hits, every survivor hand-disassembled. All
four negatives were *true*. The consumer was in TOC slot 1 — one of the 8
overlays that corpus had decoded in full — and took a fifth shape none of
the four could see:

- the slot numbers sit at `+14` of a **16-byte-stride per-character
  descriptor table** in the overlay's data (`0x8005ff90`, 35 records), so no
  two in-range values are ever adjacent and a consecutive-run scan sees
  nothing;
- the code reads the field with the PSX GCC indexed idiom
  `lui $at,0x8006 ; addu $at,$at,$v0 ; lh $v0,-114($at)` (`$v0 = idx << 4`):
  no immediate equals a slot, no `addiu K` lands in the range, and a plain
  `lui`+first-use pair search *breaks on the `addu`* (the register is
  rewritten before its use);
- the value is then stored into a **task object's `+0x10` field**, and the
  function that hands `obj+0x10` to `resourceSize`/`seek`/`read` is a
  callback installed by `lui`/`addiu` address materialisation into `obj+0` —
  invisible to any `jal`-target census of the loader primitives.

**Fix — three cheap search shapes, in this order:**

1. **Strided-record scan** over every decoded block: for every stride
   4..64 and every 2-byte phase, count consecutive records whose `u16` at
   that phase is in range; keep runs of ≥4 with ≥3 distinct values; reject
   runs that are monotone or share one residue mod 4 (those are the low
   halves of a `u32` address table marching through the range). Found the
   real table at stride 16 on the first try, on PSX and — as an independent
   second-compiler oracle — in the PSP remaster's `Title_master.prx`, which
   carried the identical 25 slot numbers in identical order at a different
   address (see `cross-platform-decode-oracles.md`).
2. **`lui`/use pair search that permits exactly one `addu X,X,idx`** between
   the `lui` and the use (still breaking on any other write to `X`). This is
   what finds the table's readers; a pair search that stops at the first
   write to the `lui` register returns only unrelated `0x8006xxxx` globals.
3. **Follow the struct field, not the immediate:** from the reader, trace
   the value into whatever object field it is stored in, then census *that
   field's* readers in every function installed as a callback (raw pointers
   to prologues, `lui`/`addiu` materialisations stored into `obj+0`) — the
   loader call is in one of them.

Sibling lessons: `data-table-stores-prepacked-value-code-census-misses-it.md`
(a *code* census misses a value that only exists in data — here the data
census was run too, and still missed it because of the stride) and
`negative-from-addressing-root-not-shapes.md` (a shape-based negative is only
as complete as its shape list — this is the concrete shape that list keeps
lacking). The one-line diagnosis: every search assumed the id would appear as
an immediate or beside its siblings; it appears only as a field inside a
strided record and travels to the loader inside a callback object.
