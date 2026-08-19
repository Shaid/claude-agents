# Leftover version-control metadata on a shipped disc marks an accidental plaintext dev-asset oracle

**When it bites:** surveying a commercial disc/package tree beyond the
files an explicit task brief names, and an unexpected loose-file directory
turns up alongside the normal packed/compiled game data — especially one
containing files literally named `CVS`, `.cvsignore`, `.svn`, or `.git`.

Shipped commercial discs occasionally include an accidental leftover
developer working-copy checkout — a build/QA machine's source-control
checkout got copied into the disc image instead of (or alongside) the
properly packed release data. The tell is unambiguous and cheap to check:
literal version-control metadata files (CVS's `Root`/`Repository`/`Entries`,
SVN's `.svn/`, git's `.git/`) sitting in a directory that otherwise looks
like ordinary game data. When present, treat the accompanying loose files
as a **plaintext ground-truth oracle**, not just incidental clutter to
skip past — they are frequently the human-authored *source* that an
already-reverse-engineered but semantically opaque binary/compiled sibling
format was built from, and can name fields, structures, or hierarchies a
binary-only investigation had to leave as unlabeled indices.

Confirmed on Zone of the Enders: The 2nd Runner's PS3 "HD Collection"
build. Two of 95 `ZoE2/stage/<name>/` directories (`init/`, `ca01/`) shipped
a full loose asset tree instead of the normal tiny pointer file, and a
sibling `ZoE2/stage/CVS/` directory contained real CVS metadata
(`CVS/Root` = `/home/atg/ZoE2/cvs`, `CVS/Repository` =
`.../cvs/zoe2/cdrom.img/stage`) — proving the tree was a developer's
pre-`STAGE.DAT`-packing working copy, shipped by mistake. Inside it, a
plaintext `.atr` file (`-- jehuty Model Tree List --`) named the real bone
hierarchy (`SKL_HIP`, `SKL_BELLY`, `SKL_CHEST`, ...) and per-bone
skinning-envelope lists in human-readable form — directly relevant to an
already-confirmed-but-unnamed binary "skeleton region" (i16 records + a
16-byte bone table + hundreds of opaque per-node u16 index lists) the
sibling PS2 platform's investigation had already located but could not
label. A `.tex` file in the same tree also independently re-derived (on
completely different, uncompressed bytes) the exact `{magic, c2, off,
size}` chunk-record grammar and `hi16*0x10+lo16` offset formula the PS2
investigation had confirmed for its compiled/encrypted model container —
cross-validating that format for free.

**Fix:** when surveying a disc/package tree, grep/`find` for
`CVS`/`.svn`/`.git` directory names as a matter of course, not only when a
task brief calls one out — the search costs one `find` command and the
payoff (a plaintext oracle for an already-solved-but-unnamed binary format)
can be disproportionate to that cost.
