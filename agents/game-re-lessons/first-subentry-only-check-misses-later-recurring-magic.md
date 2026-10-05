# "Not this format" from checking only the first sub-entry after a shared header is incomplete, not wrong — resync-scan the whole buffer for the marker before ruling it out

**When it bites:** a container's root header is confirmed (shared magic,
fixed-size header), the *first* sub-entry immediately after that header is
inspected and its type tag doesn't match the target format's marker
(e.g. it's some other, already-identified sub-resource instead) — and
that single check gets written up as "this container doesn't hold format
X after all." Also: a community reference tool for the exact game exists
and its own dump script uses a scan loop rather than a single fixed-offset
read, and that detail was skimmed past rather than ported.

## What went wrong

Fire Emblem: Three Houses' `.ktsl2asbin` voice-line archive (`chimera`
project) shares its 64-byte root header shape with the already-solved
`.ktsl2stbin` BGM/voice container (same `"KTSR"` magic). An earlier pass
read the *first* sub-entry immediately following that header, found its
`sectionType` was `0x368C88BD` — a fixed-224-byte-record event/cue command
table, a real and different sub-resource — and concluded the whole 265-
entry family "isn't audio at all," a conclusion two independent checks
(no `0x15F4D409` KTSS marker at that position, 0 literal `"KTSS"` bytes in
a substring scan) both agreed with. Both checks were real and both were
insufficient: they only ever examined the first position/looked for one
specific byte string, never walked the rest of the buffer.

The actual fix came from cloning the game's own community tooling
(`niltwill/fe3h-modding-tools`) and reading its `ktsl2asbin-dump.py`: it
scans the *whole* buffer from the header's end, 4 bytes at a time,
matching a *different* `sectionType` constant (`0x70CBCCC5`,
"`INFO2_SECTION_ID`") — resyncing past any 4-byte word that doesn't match
by simply advancing 4 bytes, and past any word that does match by the
matched entry's own declared size. Applying that exact scan to real game
data found 14,886 matching entries across 263 of the 265 files — the
command-table entries the earlier pass found were real, but coexist
*in the same file*, interleaved, with many more entries of a wholly
different type carrying the actual embedded audio.

## The fix

Before writing up "container X doesn't hold format Y" from a single-
position or single-magic check: if there's a shared root/entry-header
convention already confirmed for a sibling format in the same family
(same outer magic, same header size), the family's per-entry markers may
recur many times per file at unpredictable offsets, not just once
immediately after the header. Resync-scan the *entire* decompressed
buffer for the target marker at whatever alignment the format uses (4-byte
words are common), don't stop at the first hit (or first miss). If a
community tool for the exact game exists, check whether its own
extraction script does a fixed-offset read or a scan loop — the loop shape
itself is often the whole insight, cheaper to port than to re-derive.

This is a different failure mode from
`shallow-magic-scan-undercounts-sibling-magic-corpus.md` (that one is
about missing a *different* sibling magic byte pattern entirely); here the
right marker was known and even present in the file, just past the one
position actually checked.
