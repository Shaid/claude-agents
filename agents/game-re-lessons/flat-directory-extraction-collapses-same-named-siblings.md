# A flat single-directory extractor silently drops files when the source has same-named siblings in different subdirectories

**When it bites:** a disc/archive extractor writes every file into one flat
output directory keyed by filename alone (no subdirectory structure
preserved), and the source container's own directory/FST declares more
entries than end up on disk — especially when a published extraction count
("N files extracted") is quoted from the extractor's own FST/directory
enumeration rather than a post-extraction `ls | wc -l` on the actual output.

Confirmed on Muramasa: The Demon Blade (Wii, `vanille`): `tools/muramasa/
extract.py` walks the disc's FST (2,736 entries) and writes each file's
*basename* into one shared `build/cache/muramasa/data/` directory,
discarding the FST's real subdirectory path. The FST itself declares 642
`.mbs` model files, but only 621 physical files exist in the extracted
output — 21 basenames recur across different source subdirectories (e.g.
a character's default and battle-variant model sharing a stem across two
folders) and each later write silently overwrites the earlier one on the
same filename. The project's own `docs/muramasa/wii/data-structure.md`
inventory table (which counts FST entries, not files on disk) reported the
FST's 642 and was technically correct for what it measured, but did not
surface the on-disk shortfall — the discrepancy only turned up when a
downstream pipeline stage (`tools/shared/muramasa-models.ts`) diffed its own
processed-file count against the FST-derived expectation.

**The fix, generalized:** for any extractor that flattens a hierarchical
container into one directory, cross-check the FST/directory's declared
entry count for each extension against `ls build/cache/.../*.ext | wc -l`
on the real output before trusting either number as "the corpus size." A
mismatch means real content is being silently shadowed by same-named
siblings, not that the container's own directory is wrong. The proper fix
is to preserve subdirectory structure in the extractor (or otherwise
disambiguate colliding basenames) — treating the smaller on-disk count as
"the corpus" understates real content and any downstream coverage
percentage computed against it will look better than it is.
