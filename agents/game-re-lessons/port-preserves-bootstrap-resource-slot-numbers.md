# A confirmed byte-identical container/codec reuse across a port can also preserve the old platform's exact bootstrap-resource index numbers

**When it bites:** A container/codec format has already been confirmed
byte-identical (or near-identical) between an original platform and a later
remaster/port — same magic, same struct layout, same compression — and you
still need to locate one or more "bootstrap" resources on the new platform
(a font/glyph-order reference chart, a name table, any resource used to
decode everything else). Before spending a session on structural scanning,
entropy census, or disassembly to relocate it.

## What happened

Valkyrie Profile: Lenneth (PSX) and its PSP remaster share a confirmed
byte-identical resource-bundle container (a `{count, field1,
{regionType, regionSize}}` "group directory," reused unmodified inside the
PSP's completely different outer archive, `PSPVAL1.PFS`, vs. PSX's raw
encrypted sector TOC). A prior session had already partially exploited
this: an enemy-stat record type cross-decoded correctly against the
unmodified PSX reader, hitting the exact PSX-confirmed record count
(996), but the records' `nameId` fields didn't resolve to names, because
the two resources that make that possible on PSX — the "reference
alphabet" glyph-order chart (which bootstraps every subset-font text
decode in the game, since every text resource ships its own font with
glyphs numbered by first-use order) and the enemy name table itself —
hadn't been located on PSP.

On PSX, those two resources live at TOC slot 6 and TOC slot 1500. Rather
than re-deriving their PSP locations by any structural means (scanning for
the reference chart's ascending-glyph-order signature, or the name table's
own record shape, across thousands of PFS entries), the fix was to just
**try PFS index 6 and PFS index 1500 directly** — the exact same numbers,
despite `PSPVAL1.PFS` being a wholly different container technology
(ISO9660 + a custom archive with its own directory trailer, vs. PSX's
XOR-encrypted raw sector table). Both hit immediately: PFS index 6 decoded
as a valid reference alphabet, PFS index 1500 as a valid name table, and
together they resolved all 996 enemy names with 0 unresolved ids — cross-
checked against an independently-derived 25-name playable-character roster
(0/25 mismatches) and several real, recognizable enemy names ("Undead
Carcass", "Dragon Servant").

## The general lesson

A confirmed container/codec-level reuse across a port is evidence the
*whole asset pipeline* was carried over with minimal changes — likely
including whatever fixed index/slot numbering scheme the original
authoring tools assigned resources, not just the byte-level format those
resources are stored in. This holds even when the outer container
technology is completely different (the addressing scheme is a property
of the build/authoring pipeline, not of the runtime archive format), and
even though slot semantics don't always transfer (e.g. some slot ranges
between PSX and PSP populate meaningfully different content — always
verify with a decode + plausibility oracle, never trust the number
coincidence alone).

Once you've confirmed a format-level reuse, the very next thing to try —
before any structural re-derivation of a still-missing bootstrap
resource's location — is a direct index probe at the old platform's own
number. It's a single read + decode + plausibility check, and it can
collapse a session's worth of scanning into minutes.

## A second instance: the base game's own higher-level PARSING ALGORITHM can transfer too, not just its resource addresses

Confirmed on the same project, a later session: once PSP's `PSPVAL1.PFS`
index space was already confirmed to alias PSX's TOC-slot numbers 1:1 (the
finding above, now also independently reconfirmed for room backgrounds —
1,118/1,118 PSX rooms render byte-identical from PSP bytes through the
unmodified PSX room compositor), the next open item was VP1's whole
dialogue/menu/item-text corpus (`vp1psp-text-tables`). PSX's own text
extractor pairs a subset-font block with its string-table/scene-script
partner via three rules (an explicit length-prefixed "chain" pointer in
the font's own container header, a directory region-tag convention
`fontTag`/`fontTag+0x100`, and a same-container disc-order-neighbour
fallback) — and that pairing function turned out to be **entirely
format-agnostic**: it operates on an abstract "list of candidate blocks
with an optional container-relative tag" input, with no PSX-specific
container-scanning logic baked into it at all. PSX's *caller* builds that
input via one whole-disc blind byte-magic scan + TOC-offset-containment
test; PSP's own container (`PSPVAL1.PFS`) has no equivalent flat byte
stream to scan the same way. The fix needed **zero changes to the pairing
algorithm itself** — only a thin, container-appropriate adapter (a
blind magic-byte scan scoped to one already-loaded PFS entry's own buffer,
instead of a disc-byte-range read) to produce the same input shape. Result:
1,140 font+text pairs / 37,955 strings recovered on the first pass, verified
byte-exact against PSX's own decode of the identical index number on 8
sampled cases spanning every pairing rule.

**The generalized rule, sharper than "resource addresses transfer":** once
a container/codec-level reuse *and* an index/slot-number correspondence are
both confirmed, check whether the base game's higher-level
resource-*joining* algorithms (pairing two related sub-resources within one
container, resolving a cross-reference, building an index) are themselves
written in a container-agnostic shape — operating on an abstract
block/offset/tag representation rather than hard-coding the old platform's
own whole-file-scan-and-offset-containment convention. If so, the *whole
algorithm* is reusable unmodified; the only real work is writing a thin
per-container-unit adapter for whatever primitive the algorithm used to
build its input (usually just a magic-byte scan or a directory parse). This
generalizes past text-pairing specifically: any "find and join two
independently-located sub-resources sharing one containing unit" routine
in a format-agnostic shape is a candidate for the same free reuse on a
newly-confirmed-compatible sibling container, and is worth checking for
*before* writing a fresh per-container reimplementation from scratch.
