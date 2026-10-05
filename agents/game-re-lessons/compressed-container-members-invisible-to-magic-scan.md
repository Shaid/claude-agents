# Compressed container members carry no magic, so a magic-byte scan's coverage and absence results are both invalid until checked against the container's directory

**When it bites:** a corpus was discovered by scanning container bytes for a
content magic (`_M1G`, `GT1G`, `KTSR`, ...) rather than by walking the
container's own directory — and now you're about to (a) publish a coverage
figure, (b) write up an *absence* ("format X / asset Y does not exist
anywhere in this extraction"), or (c) act on an apparent ceiling in the data
("the biggest skeleton here is 124 bones"). Bites hardest when a project doc
carries a note like *"the wrapper doesn't need reverse-engineering — the
magic scan finds every embedded resource"*.

A magic scan can only find resources stored **uncompressed**. If the
container compresses members — commonly per-member and optionally, decided
at build time — the compressed ones contain no recognizable magic anywhere
in their bytes. The scan does not fail, warn, or return zero; it returns a
plausible, self-consistent, *fractional* corpus. Every downstream number
computed from it is quietly scaled down, and any negative conclusion drawn
inside it is unsound no matter how thoroughly it was argued.

## What happened

FE Warriors: Three Hopes (Switch, `chimera`). Every asset stage discovered
its data by scanning the 1,417 `.fdata` package files for a content magic.
A prior pass then investigated "which skeleton do the unresolved animation
tracks need?", searched the resulting mesh corpus exhaustively, and closed
the item with a well-evidenced negative: 172 non-playable skeletons, all
≤10 bones, deduping to **13** distinct `boneIndices` signatures, none of
which resolved more than 0.07% of the unresolved tracks — therefore "no
second skeleton exists anywhere in the currently-extracted romfs; it would
need an update/DLC archive." That pass even re-verified all 1,770 romfs
files were extracted (true, and irrelevant).

Decoding the container's own directory (Koei Tecmo RDB, `_DRK0000` /
`IDRK0000`) instead showed **54.5% of the game's 166,571 resources are
zlib-compressed inside the very files the scan had already walked**:

| | Magic scan saw | Directory lists | Compressed |
|---|---|---|---|
| G1M models | 198 files' worth (~945) | **6,923** | 5,978 |
| distinct skeleton topologies | 13 | **211** | — |
| largest skeleton | 124 bones | **236 bones** | — |
| animation clips | 1,675 | **5,152** | 3,032 |
| audio resource *types* | 1 | **2** (243 compressed banks, 421 MB, never extracted) | — |

The 236-bone rig — a strict superset of the 124-bone playable one — was in
the base game the whole time, and took the briefed problem from 88.35% to
**100.00%** track resolution. The prior pass's search was rigorous; its
*medium* was wrong. Nothing it could have done inside a magic scan would
have found the answer.

## The cheap test

Before trusting any coverage figure or absence claim from a magic scan:
**find the container's directory and compare its resource count for that
type against the scan's hit count.** If they disagree, the scan is the
problem. Two supporting moves:

- A resource directory usually names types by an opaque type-ID rather than
  a magic. Sample ~25 records per type, decompressing as needed, and read
  the leading 4 bytes — in this corpus every one of 33 types was 100%
  homogeneous in its payload magic, which named them all in one pass and
  also settled a *separate* long-standing absence question (an SFX
  container confirmed absent because no such type exists — a far stronger
  proof than a byte scan, because it does not depend on storage form).
- The compression is usually already-known: here it was chunked zlib
  (`u32 compressedLength` + one member, ≤0x4000 each), the same scheme the
  publisher used in two other containers this project had already solved.

## Relationship to the neighbouring lessons

`shallow-magic-scan-undercounts-sibling-magic-corpus.md` covers two other
mechanisms by which a scan undercounts (a sibling magic differing by one
byte; alignment/false-positive logic skipping real hits) and reaches the
same remedy — prefer a directory walk for any corpus-sizing claim. This is
the third and most severe mechanism, because unlike those two it cannot be
defeated by searching harder: the bytes are not in the file in the form
being searched for. `magic-scan-can-substitute-for-container-reverse-
engineering.md` describes when scanning is a legitimate shortcut, and has
been corrected in light of this. `optional-per-record-compression.md` is
the same underlying container behaviour seen from the other side — there
the compressed minority is *found* but decodes as garbage; here it is never
found at all.
