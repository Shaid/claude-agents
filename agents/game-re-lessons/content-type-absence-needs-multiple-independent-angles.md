# "Does content-type X exist anywhere in this corpus" needs several structurally-different search angles agreeing, not one

**When it bites:** the task is to conclusively confirm or rule out whether
a whole *category* of content exists anywhere in a game's data (pre-
rendered video/FMV, a cut feature, a whole asset class the user is
confident must be present) — as opposed to decoding a format you already
know is there. A single search technique coming back empty is tempting to
report as "not present," but one empty search only rules out the one way
that technique could have found the thing.

**Each search technique is structurally blind to some ways the content
could hide, and a different technique is blind to different ways.** A
magic-byte scan misses content wrapped in an undecoded compression/
encryption layer it can't see through. A file-size histogram misses
content stored in many small pieces rather than one big file. A directory/
extension survey misses content sitting inside an already-catalogued
container under an unexpected sub-name. None of these alone is a strong
negative; agreement across several *orthogonal* techniques is.

**The four-angle combination that worked** (NieR, 2010, PS3, `flower`
project — conclusively ruled out any pre-rendered video/FMV in the whole
decrypted base-game data set, a real user-disputed question, not a routine
non-finding):

1. **Size-outlier hunt.** The target content type has a known typical size
   profile (FMV clips are typically tens of MB+) — sort every corpus entry
   by size and check whether anything of that scale exists outside
   already-explained categories. Catches "ships as one big standalone
   file," misses anything smaller or split into pieces.
2. **Exhaustive full-content magic-byte scan** — not a sample, not just
   file headers. Every already-known compression/encryption layer gets
   decoded first so the scan sees real content, not compressed noise; every
   byte of every entry gets searched, including a dedicated pass over any
   files too large to decode/hold entirely in memory at once. Catches
   "ships with a recognizable container signature somewhere in a file,"
   misses content wrapped in a *still-undecoded* codec (see
   `short-magic-hit-in-high-entropy-region-needs-falsification.md` for the
   false-positive risk this angle carries) or referenced only by name.
3. **Leaf-name/keyword census inside already-partially-solved container
   formats**, plus a corpus-wide filename/directory keyword search for the
   content type's own vocabulary (`movie`, `cutscene`, `fmv`, `trailer`,
   and any format-specific naming convention already seen, like a `.2DV`
   extension literally decoding to "2D Video"). Catches "referenced by name
   even if not yet format-decoded," misses content with no self-describing
   name at all.
4. **A structural "shape" argument for the single most-likely-candidate
   content region**, independent of any byte search. Real pre-rendered
   video is architecturally *one big monolithic stream per clip*; the
   NieR case's most-likely region (a per-scene cutscene-staging directory,
   56% of the whole corpus) instead showed *every single scene* built from
   many small, independently-typed files (character meshes, per-camera-cut
   keyframe tracks, particle effects, captions, scripts) — the opposite
   shape, and itself real positive evidence for "this is rendered in real
   time," not just an absence of evidence for video. This angle catches
   what the byte-level angles structurally cannot: content that would be
   *architecturally* wrong for the format even if a byte scan somehow
   missed a signature.
5. **Cross-check the extraction tool's own archive/container listing
   against what's actually on disk**, when the corpus is a pre-extracted
   dump (a Switch NCA's RomFS, a PS-family ISO, any packed-then-unpacked
   source). A full-content magic-byte scan (angle 2) can only find what
   was actually extracted — it is structurally blind to files the
   extraction step silently dropped. Confirmed on Fire Emblem: Three
   Houses (Switch, `chimera` project): a corpus-wide scan of every
   decompressed entry in the game's main archive found zero bytes of the
   audio container's inner magic, even though 265 entries shared its
   *outer* magic (an internal type-tag field distinguished them as an
   unrelated sub-resource, not audio data at all). The real audio files
   were loose romfs files that were
   **present in the NCA's own RomFS table** (`hactool --listromfs` listed
   them) but silently absent from the already-extracted dump on disk —
   a prior extraction pass had dropped them without error. Re-running the
   extraction tool's own directory-listing mode (no re-extraction needed)
   caught this in seconds; angles 1-4 above, applied only to the
   already-extracted tree, could never have found it, because the content
   genuinely wasn't there yet.

   **This recurred on a second game in the same project** — Fire Emblem
   Warriors (2017), same `chimera` project, same `extract-romfs.ts`
   pipeline. A full four-angle negative (extension census, corpus-wide
   magic scan including the container's own `KTSR` tag, `ffprobe` on every
   cutscene movie, and an NCA content-type audit) had been accepted as
   "confirmed absent" and shipped in the project's docs — every one of
   those four checks really was correct *for the 2,227-file tree it
   scanned*, but that tree was missing 4,213 of the 6,440 files the
   Program NCA's own RomFS table declared, including the entire
   `nx/sound`/`nx/voice` audio directories (plus, unrelated to audio,
   `nx/ui`, `nx/stage`, `nx/shader`, and part of `nx/movie` — the drop was
   directory-wholesale, not audio-specific). A single `hactool
   --listromfs` file-count comparison against the extracted tree's own
   file count (6,440 vs. 2,227) would have caught this in seconds, before
   spending any effort on the four content-level angles at all. **Two
   occurrences in one project elevates this from "worth checking" to "run
   this comparison first, unconditionally, before trusting any
   'confirmed absent' verdict built on a Switch (or any pre-extracted-
   dump-based) romfs corpus"** — it's now the cheapest angle of the five
   and should be angle 0, not angle 5.

**Fix:** before writing a load-bearing "content type X does not exist"
negative, run enough of these four angles that each plausible hiding place
is covered by at least one, and make sure the angles are genuinely
orthogonal (a second magic-byte scan at a different offset doesn't count as
a second angle). State explicitly, in the write-up, which axis each angle
covers and why it can't be defeated by the others' blind spots — that's
what makes the negative resistant to "well, did you check X" follow-up,
rather than a single empty search dressed up as a conclusion. If a genuine
gap remains after all angles agree (e.g., a boot executable or an encrypted
DLC pack outside the searched data set), name it explicitly as the one
place the negative doesn't reach, rather than letting the overall
conclusion imply a completeness it doesn't have.
