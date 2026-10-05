# A per-entry resumability guard using "ANY sub-item already exists" instead of "ALL" permanently orphans a partially-emitted multi-item container

**When it bites:** a resumable extraction pipeline processes a container
entry that can yield more than one output item (a multi-texture archive
record, a multi-frame sprite, any "one source blob -> N output files"
step), and its resume-from-disk skip check is `items.some(i =>
existsSync(outputPathFor(i)))` — true if *any* sibling item's output
already exists — rather than requiring *all* of them.

## What went wrong

Confirmed on Fire Emblem: Three Houses (`chimera`)'s texture pipeline
(`build-assets.ts`). A DATA0 entry can be a multi-texture G1T container
(e.g. one 1024x1024 + one 512x512 texture in the same entry). The main
loop's resumability check was:

```js
const anyExisting = g1t.textures.some((t) =>
  existsSync(resolve(outDir, `${name}_${t.index}.png`)),
);
if (anyExisting) { doneSet.add(i); continue; }
```

On an earlier run, one of an entry's two textures decoded and got skipped
by an unrelated flatness-heuristic false positive (see
`sparse-sample-flatness-heuristic-false-negative-on-real-content.md`)
while its sibling texture succeeded and was written to disk. On every
subsequent run, `anyExisting` saw the sibling's PNG, marked the WHOLE
entry done, and `continue`d past it — permanently skipping the per-texture
loop that would have retried (and, after the flatness bug was fixed,
correctly emitted) the missing texture. Fixing the flatness bug alone did
**not** fix this: 5 entries stayed stuck with only their smaller texture
ever emitted until this guard was separately corrected. A disk census
found the gap (`_0.png` present for 1,134/1,152 expected entries at first,
then only 1,129/1,134 after the flatness fix — 5 short, all two-texture
entries missing exactly their larger texture).

## The fix

Change `.some()` to `.every()` — require every sub-item's expected output
to already exist before skipping the whole entry. For the common single-
item-per-entry case the two predicates are identical, so this is a strict
completeness fix with zero behavior change for the bulk of a corpus; it
only changes behavior (correctly) for entries with more than one output
item and partial prior success.

## Generalization

Any "does this container's output already exist" resumability check that
short-circuits on a single representative sub-item, rather than checking
every expected sub-item, has this trap whenever a container can yield more
than one output and a *different* per-item filter (a flatness heuristic, an
unsupported-format catch block, a size cap) can plausibly reject some
sibling items while accepting others. Prefer per-item existence checks
(each item independently decides whether to (re-)run) over one shortcut
check per container, or explicitly require ALL expected items when a single
combined check is kept for performance.
