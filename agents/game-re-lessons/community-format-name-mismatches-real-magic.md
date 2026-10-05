# A community/doc format name can be flatly wrong about which on-disk magic a game actually ships

**When it bites:** a task brief or an existing project doc names an
undecoded format by a community/fan-tool convention (e.g. "G1A") with its
magic marked unconfirmed, and you're about to hunt for that literal magic
across the corpus before checking whether a same-family, differently-named
sibling format (e.g. "G2A") is what the game actually shipped.

Fire Emblem Warriors (2017) and Fire Emblem: Three Houses both needed
skeletal animation decoded. This project's own docs called the format
"G1A" (following the community's own animation-format template name,
magic `_A1G`), inherited from an earlier pass that never actually looked
for the magic. A corpus-wide raw-byte scan found essentially zero real
`_A1G` hits (one coincidental 4-byte collision inside high-entropy
compressed data, with no plausible ASCII version digits following it —
see `short-magic-hit-in-high-entropy-region-needs-falsification.md`).
Both games instead shipped **G2A** (magic `_A2G`), a newer, structurally
unrelated (bit-packed/quantized) animation format from the *same*
reference-template repo, one file over from the one the docs named.

**The template repo itself was the tell, not a surprise find once looked
at directly**: the same `three-houses-research-team/010-binary-templates`
repo this project already used for G1M/G1T ships *both* `G1A.bt` (old,
plain-float curves) and `G2A.bt` (newer, bit-packed) side by side, with
`G1A.bt`'s own header comment giving no hint that it's superseded. Don't
assume a template repo has exactly one format per "kind" of asset — for
older/newer console generations or games, check for a same-family sibling
template (`G1A`/`G2A`, `G1M`/`G1H`, version-numbered variants) before
committing effort to the one a doc happens to name first.

**The general move**: before hand-deriving a format from a template whose
magic hasn't been confirmed against real bytes, do the raw magic-byte scan
*first* — cheap, and it directly answers "is this even the right format
name" before any decode effort is spent. If the named magic comes back at
or near zero, don't conclude the format is absent; check the same
reference source for a same-family sibling name/version before escalating
or declaring the content type missing (see
`content-type-absence-needs-multiple-independent-angles.md` for the
broader "confirmed absent" discipline this feeds into).
