# A shared tile/font bank's page selector is per-record, not uniform across similar records

**When it bites:** a shared tile/font ROM is confirmed to hold multiple
selectable "pages" or sub-alphabets, gated by a per-record attribute/config
byte (not by the tile-code bytes themselves) — and a batch of several
similar short records (e.g. inline icon graphics, alternate-style text
lines) is about to be rendered/decoded using ONE record's already-known
selector value applied to all of them.

## What went wrong

Black Tiger's (arcade, `kolbold`) `chars` font ROM is addressed as
`tileCode = rawByte + page*256`, where `page` comes from 3 bits of a
per-line attribute byte (`(attr & 0xe0) >> 5`) — confirmed from MAME's
`get_tx_tile_info` source. The main NPC dialogue text uses one fixed
attribute (`0x93`, page 4) for every real line. A handful of short 2-6
byte "control segments" elsewhere in the same dialogue block — each with
its OWN 4-byte record header carrying its OWN attribute byte (`0xae`,
`0x2c`, `0xaf`, `0x20`, all different from `0x93` and from each other) —
had been flagged as "almost certainly a portrait/icon selector, not traced
to a consumer."

The first attempt to actually render these reused the uniform page-4 offset
the main dialogue text used (since that was the already-confirmed, in-hand
value) rather than each segment's own real attribute byte, and got
meaningless 2-letter garbage ("CD", "ST") — plausible enough to look like a
genuine (if unexplained) finding, and would have been reported as "still
unexplained content" if not double-checked. Re-rendering with each
segment's OWN attribute byte (page 1 or page 5, not page 4) produced real,
coherent small icon/kanji graphics instead.

## The fix

When a shared tile/font bank's page/bank selection is confirmed to be a
per-record field (not a global constant), always pull the SPECIFIC
record's own selector value before rendering its tile-code bytes — never
reuse a sibling or "the usual" record's selector, even for records that
look structurally identical and sit right next to each other in the same
container. The failure mode is silent: a wrong-but-different page still
often decodes to *something* plausible-shaped (letters, not visual noise),
which reads as a real (if unexplained) result rather than an obvious
decode error, and can send the investigation down the wrong path (e.g.
mistaking real icon/graphic content for meaningless placeholder letters).
