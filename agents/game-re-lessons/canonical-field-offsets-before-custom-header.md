# Readable text near a file's start may be a known format's own field, not a custom prefix

**When it bites:** you see plausible plaintext/ASCII near the top of a file,
before what looks like the "real" magic further in, and you're about to
conclude the file has a nonstandard/custom header wrapping a known format.

Jungle Strike AGA's `music` file appeared to open with a block of plaintext
cue strings (`"pos 0 - anim bit"`, `"pos 5 - breifing"`...) before a `M.K.`
(ProTracker MOD) magic found deeper in the file — looked like a custom
cue-point header bolted onto a MOD. In fact `M.K.` was at exactly file offset
1080, the **canonical** location for a standard 31-sample ProTracker module
(20-byte title + 31×30-byte sample headers + 1+1+128 order bytes = 1080)
starting at absolute offset 0 — there was no prefix at all. The "cue
strings" were the MOD's own standard 22-byte sample-name fields
(`20 + i*30`), which trackers never validate and composers/devs freely
repurpose for arbitrary text (here: animation cue labels, and a composer
credit tucked into the 31st, otherwise-unused, sample slot).

Before concluding a header is custom: check whether the visible strings land
exactly on a well-known format's own named/comment fields at their canonical
offsets (tracker sample/instrument names, IFF chunk names, resource-fork
comment fields, etc.) — read the format's field table first. This is the
audio/text-metadata sibling of `palette-storage-quirks.md`'s "check the
format's own conventions before assuming something is missing or custom."

**Second confirmed case, same project, same specific magic.** Desert
Strike (Amiga)'s 5 "named audio cue" chunks (`docs/desertstrike/amiga/
data-structure.md`) had been logged in an earlier pass's paths-tried table
as "not a ProTracker M.K. module (no such magic found)" — a `DMCA`-family
member was assumed instead. Re-deriving from scratch found `M.K.` present
at exactly file offset 1080, the same canonical location as the `music`
case above; the earlier pass had stopped at the file's leading
"custom-looking" fields (the cue title, "death"/"winlevel"/..., followed by
repurposed sample-name fields carrying real instrument names) without
searching the rest of the file for the real magic. **Generalizes beyond
this specific format:** a paths-tried table's "no such magic found" row
deserves a fresh, from-scratch magic search (not a re-read of the old
note) before being trusted as settled — especially when the "no magic"
verdict followed directly after describing what looked like a custom
header, since that's exactly the shape of this trap.
