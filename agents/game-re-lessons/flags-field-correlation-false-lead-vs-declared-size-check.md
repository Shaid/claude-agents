# A plausible-looking flags/bitfield correlation with corruption is a red herring — check the container's own declared size against the real file size directly first

**When it bites:** hunting for what distinguishes truncated/corrupted files
from healthy ones in a self-describing container corpus, and an unusual
value in some OTHER field (a flags/bitfield byte, a version tag, anything
that isn't itself a size/length) appears to correlate with the files you
already suspect are damaged — before building a corruption detector around
that field, check the much more direct and boring signal: does the
container's own declared total size equal the real file's byte length.

## What happened

Confirmed on the SSI Gold Box "GLIB" container family (`crawl` project,
`tools/shared/goldbox-glib.ts`): while triaging which of 72 real `.GLB`/
`.TLB` files across three sibling titles (Curse of the Azure Bonds, Secret
of the Silver Blades, Pools of Darkness) were truncated floppy-dump damage,
an early hypothesis formed that a container's `flags` field taking an
unexpected value (`0x0500`/`0x0501` instead of the usual `0`/`1`) marked the
corrupted files — the values genuinely did show up disproportionately among
files already suspected bad, which made the correlation look real.

It was refuted by a single clean counter-example: Secret of the Silver
Blades' own `DISK1/8X8D.TLB` has nested sub-containers with `flags=0x0500`
that decode perfectly cleanly — self-consistent offset tables, clean
tile-group divisions dividing evenly by 8, no corruption symptoms at all.
The flags value was a real, legitimate content-type/nesting-depth signal
completely unrelated to file health.

The actual, sufficient, and much simpler discriminator was already sitting
in every container's own header: `container.totalSize !== actualFileLength`.
Checked across the full 72-file, three-title corpus, this single direct
comparison had zero false positives and zero false negatives — every file
where it held was confirmed truncated by a second, independent check (the
same base filename decoding cleanly in a different disk image of the same
title), and every file where it didn't hold decoded with fully
self-consistent internal offsets.

## The fix / general rule

When looking for a corruption/truncation signal in a self-describing
container format, **check the container's own declared total size against
the real file's byte length before looking at anything else** — it's the
cheapest possible test and, for any format that stores its own total size
at all, it's definitionally the ground-truth signal (a container can only
honestly declare a size it actually has). Don't let a superficial
correlation in an unrelated field (flags, version, a content-type tag)
substitute for this direct check, even when the correlation looks
convincing in a small sample — one clean counter-example anywhere in the
corpus is enough to refute it, and that counter-example is worth actively
looking for (test the flag value against every file that decodes cleanly,
not just the files already suspected bad) before committing to it as the
detector.
