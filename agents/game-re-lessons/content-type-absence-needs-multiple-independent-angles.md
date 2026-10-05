# "Does content-type X exist anywhere in this corpus" needs several structurally-different search angles agreeing, not one

**When it bites:** you're about to write a load-bearing "X doesn't exist in this game" negative, about a whole category (FMV, a cut feature, an asset class the user insists is there), from one empty search. Also: the corpus is a pre-extracted dump (Switch RomFS, ISO), where the extraction itself may have silently dropped files or whole NSPs.

Every search technique is blind to some hiding places, and each technique is blind to different ones. An empty result rules out only what that one technique could have seen. A negative is strong only when orthogonal angles agree, and only over a corpus you've confirmed is complete.

**Check / fix — run these angles, with the cheapest first:**
0. **Is the corpus complete?** Compare the extraction tool's own listing (`hactool --listromfs`) file count against the extracted tree. Then `find data -iname '*.nsp'` and check which NSPs and NCAs the pipeline actually processed. A largest-NSP/largest-NCA-only extractor silently skips DLC. Switch DLC NSPs need `--titlekey` but no `--basenca`.
1. **Size-outlier hunt** against the content type's typical size (FMV is tens of MB or more). This misses content stored small or split into pieces.
2. **Exhaustive full-content magic scan** of every byte, after decoding every known compression or encryption layer, including dedicated passes over oversized files. This misses still-undecoded codecs, and short hits need falsifying (`short-magic-hit-in-high-entropy-region-needs-falsification.md`).
3. **Name/keyword census** of filenames, directories, and leaf names inside partially solved containers (`movie`, `cutscene`, `fmv`, `trailer`, format conventions like `.2DV`). This misses content with no self-describing name.
4. **Structural shape argument** for the most likely region. For example, real video is one monolithic stream per clip, while real-time cutscenes are many small typed files. This gives positive evidence for the alternative.

In the write-up, state which axis each angle covers and why the others can't defeat it. A second magic scan at a different offset is not a second angle. Name any remaining gap explicitly (boot executable, encrypted DLC).

**Canonical example:** NieR (PS3, `flower`). A user-disputed "where's the FMV" question was closed by angles 1–4 across the whole decrypted base-game set. The candidate region, a cutscene-staging directory holding 56% of the corpus, was built entirely from small per-scene meshes, keyframe tracks, effects, captions, and scripts, which is real-time shape rather than video.

**Variants:**
- FE Warriors (Switch, `chimera`): a four-angle "audio confirmed absent" verdict shipped in the docs, but the tree held 2,227 of the 6,440 files the RomFS declared, and whole directories (`nx/sound`, `nx/voice`, `nx/ui`…) had been dropped. This is why angle 0 runs first, unconditionally.
- FE: Three Houses (Switch, `chimera`): the audio files were listed by `--listromfs` but missing on disk. Also, 2 of 12 DLC NSPs, never fed to `hactool`, held real undocumented 3D content (`DATA0/1.bin`).

**History:** 4 recorded instances (`flower`, `chimera` ×3). Full log in `_archive/content-type-absence-needs-multiple-independent-angles.md`.
