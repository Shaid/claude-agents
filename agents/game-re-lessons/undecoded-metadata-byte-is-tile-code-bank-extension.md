# An "undecoded, not priority-related" per-record byte can be the tile-code's own bank-extension bits

**When it bites:** a sprite/tile-composite decode renders plausible,
non-degenerate, coherently-positioned, non-garbage content that still
doesn't semantically match the expected subject (a "boss" that renders as
an unrelated character, a "vehicle" that renders as terrain) — especially
right after fixing one real bug (a wrong raster order, a wrong palette)
made the render look like it should finally be trustworthy — and a
structurally-adjacent header/flag byte in the same record was previously
documented as undecoded or only partially decoded ("priority/z-order, not
decoded further", "unknown flags", "combined with some other field into
something not traced").

## What went wrong

D&D: Shadows over Mystara (CPS2, `kolbold`): this game's HARDWARE sprite
table already had a confirmed, documented tile-code extension mechanism —
CPS2's OBJ_BASE builder steals 2 spare bits from the sprite's own Y-position
word (`code = word2 + ((word1 & 0x6000) << 3)`), stretching the addressable
tile-code space 4x beyond the raw 16-bit code field. That mechanism was
already fully solved and shipped for the *hardware* record layer.

A completely separate, *software*-level sprite-definition blob format (an
internal "keyframe → composite tile list" structure built by the game's own
animation VM before it ever reaches OBJ_BASE) had its own per-blob `flag`
byte, documented as "combined with the object's own priority byte into a
priority/z value baked into the X/Y word — not decoded further." Two full
investigation passes rendered composites from this blob format using only
the blob's raw 16-bit `code` field, ignoring `flag` entirely. Both passes
produced real, structurally sound, non-degenerate, plausibly-positioned
tile art — just from the WRONG one of the tile atlas's 3 available
0x10000-tile-code-wide banks (an unrelated humanoid character sheet
instead of the dragon's own art), because a stale palette/raster-order bug
in the first pass, and a *different*, still-live bug (the ignored `flag`
byte) in the second "corrected" pass, both happened to decode to plausible
tile shapes rather than visible garbage. The second pass's own render was
confident enough to be reported as a *confirmed negative* ("this is not a
dragon") rather than "possible decoder bug" — exactly the failure mode
this file exists to prevent.

The real mechanism: `flag`'s low 2 bits are the blob's own tile-code BANK
selector (`realCode = blobCode + (flag & 3) * 0x10000`) — found by tracing
the OBJ_BASE-record-*building* code's own `ror.l #3` instruction, which
packs `flag` into bits 13-15 of the packed hardware X/Y longword, the
*exact same bits* MAME's `cps2_render_sprites()` reads back as the
already-documented Y-bit hardware extension above. It's the identical
mechanism at a different layer — the software blob format re-derives the
hardware's own bit-packing scheme for the same reason (needing more than
16 bits of tile-code space), and the "not decoded further" byte was simply
never traced through the record-*building* code, only assumed irrelevant
because a render without it didn't visibly error.

## Fix

When a per-record byte is "not decoded, assumed priority/z/flags" and a
tile-code field from the same record renders plausible-but-semantically-
wrong content, don't accept the render as a confirmed negative — trace
what the record-**building** code (not the record-*reading*/render code)
does with that specific byte before trusting the result. If the platform
already has a confirmed hardware tile-code-extension mechanism elsewhere
(bits stolen from an unrelated field to widen an addressable code space),
check first whether the undecoded byte is the *software* side of the exact
same trick — this is a common, recurring hardware idiom (packing extra
address bits into spare positions of an otherwise-full word), not a
one-off. A cheap sanity check that would have caught this earlier: does
the tile atlas's total byte count divide evenly into N discrete
`0x10000`-code-wide (or similarly round) banks? If so, and a "confirmed"
render's codes cluster entirely within one such bank while a structurally
similar sibling asset's codes live in a different bank, that's a strong
tell the render is reading the wrong bank rather than reading correct-but-
uninteresting content.

See also `attribute-word-spare-bits-hold-game-logic-metadata.md` (a
related but distinct case — HARDWARE-unread spare bits repurposed for game
*logic*, not a code-bank extension) and
`shared-tile-bank-page-selector-is-per-record-not-uniform.md` (a
confirmed page-selector byte applied from the wrong sibling record, vs.
this file's case of a selector byte whose role was never identified at
all).
