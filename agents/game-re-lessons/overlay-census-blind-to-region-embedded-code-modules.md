# A "corpus-wide" overlay census only covers code the pipeline extracts as a top-level overlay — not code embedded as a region payload inside ordinary data slots

**When it bites:** a corpus-wide static code census (a base-load census, a
literal-immediate scan, an xref search) for a global/struct-field's
writer/reader comes back with a suspiciously narrow result — often "exactly
one file references this at all" — especially when that one file is a
shared/base overlay rather than per-instance level/room content, on an
engine known (or suspected) to embed small native code snippets as payload
regions inside per-level/per-room data containers, not only as TOC-level
overlay files.

## The trap

"Every cached overlay" quietly narrows to "every code file this project's
pipeline currently extracts and caches as a top-level artifact" — which is
not the same set as "every compiled code that exists on the disc." Some
engines give each level/room a tiny bespoke native-code hook (a scripted
camera pan, a background animation, a one-off physics tweak) and ship it
not as its own TOC entry but as one more typed region inside that level's
ordinary data slot, alongside its art/geometry/tables. A census that only
walks the overlay list never looks inside those slots' own sub-region
directories, so it never sees this code at all — and a clean, exhaustive-
looking negative ("occurs in exactly 1 of N cached overlays") is completely
consistent with the real writer sitting in region payload #47 of a data
slot the census never opened.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`): the room-placement "pan X/Y" runtime
fields (`+0x20`/`+0x24` on a scroll-record struct) had no writer under two
independently-built static searches. Both used the confirmed base-load
idiom (`lui reg,0x8008` / `lw reg,-0xf00(reg)`) to find every reference to
the record-array global, and both searched only the project's cached
top-level overlays (`build/cache/valkyrieprofile/codeoverlay_slot*.bin`).
The idiom occurred in exactly one overlay, and every literal `+0x20`/
`+0x24` store candidate nearby resolved to an unrelated struct (GPU
scratchpad, a particle record) — a clean-looking, doubly-confirmed
negative. The real writers were 61 small native-code modules
(`regionType 18`), 268 B to a few KB each, living as **region payloads
inside room data slots 3611-4800** — the exact same slots holding each
room's background art and scroll-record table — loaded contiguously right
after the shared overlay (`moduleBase = overlayBase + overlay.length`).
These modules had never been extracted and disassembled as a set before,
despite the project's own docs already describing their existence and load
address for an unrelated question (a per-room "task table" census). Once
extracted and censused the same way as the overlay, exactly 2 of the 61
modules (the two shipboard rooms) write the pan-Y field with a sine bob;
none writes pan X. A re-oracle escalation found this after both static
passes; the escalation's key move was asking "is 'every cached overlay'
actually every code on the disc, or just every code file the pipeline
currently extracts as a top-level artifact?" and, on getting "the latter,"
walking every data slot's own region directory for embedded `regionType`
values matching known native-code shapes.

## Fix

Before trusting a "no writer/reader found anywhere" verdict from any
overlay-level census on an unfamiliar engine:

1. Check whether the project's own docs (however unrelated the original
   question) already mention per-level/per-room native code modules,
   overlays-within-data, or a "task"/"script" dispatch table whose targets
   turned out to be compiled code rather than bytecode — that's a standing
   signal this architecture exists.
2. If so, extract and disassemble every instance of that embedded-module
   type as its own corpus (dedupe by content hash — many rooms share an
   identical module) and re-run the exact same census over each one,
   loaded at its own real base address (typically `overlayEnd`, or another
   address the engine documents/computes at link time).
3. Only write up the negative once both the shared overlay(s) AND every
   embedded per-instance module have been searched.

This generalizes past PSX/VP1: any "shared base engine + small per-level
native hooks embedded in level data" architecture (a common space-saving
pattern when levels need bespoke one-off behavior but don't justify a full
separate overlay) is at risk of the identical blind spot.
