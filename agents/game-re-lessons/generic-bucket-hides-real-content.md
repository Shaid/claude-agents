# A large "misc"/"other"/"uncategorized" bucket is a classifier gap, not a verdict on the content

**When it bites:** a name-keyword (or otherwise metadata-light) classifier
sorts an archive's entries into a handful of named buckets plus a catch-all
`misc`/`other`/`uncategorized`, and that catch-all ends up holding a large
fraction of the archive — especially a majority.

A classifier that only looks at one field (typically an entry's name
string) will dump *everything lacking that field* into the catch-all
regardless of what the content actually is — an empty or missing name says
nothing about whether the entry is genuinely miscellaneous. If the archive
format's own directory carries other per-entry metadata beyond the name
(dimensions, a type/flags byte, a data-size field), try grouping the
unclassified remainder by *that* before accepting "misc" as the final
answer. A real semantic category very often shares a structural property
even when it has no name — e.g. every instance of one icon set being
authored at the same pixel dimensions — so grouping the catch-all by any
other available field and rendering each group together can reveal coherent
real content with zero code-tracing.

Worked example (Black Crypt, `crawl` project, DOS `clipper.clp` archive): an
existing extractor bucketed 751 images by name-keyword matching into
`dungeon`/`monsters`/`ui`/`items`, and sent every entry with an empty or
purely-numeric name to `misc` — 505 of 751 (67%), reported without further
comment across multiple sessions. Grouping just that 505-entry bucket by
each entry's own `(width, height)` — a field the archive's directory
already stores for every image, name or no name — showed each size cluster
was visually one coherent, real category: 180 entries at one size were
weapon/armor/potion/jewelry icons (the same visual language as the 48
already-*named* `items` entries, just missing name strings), another 73 at
a different size were spell-effect icons, 19 more were chest-armor icons
(briefly mislabeled "heraldry/shield-crest emblems" on a first, too-quick
pass — corrected once someone actually looked closely: same
breastplate/chainmail visual language as the other armor, just bigger).
272 of 505 "miscellaneous" entries turned out to be perfectly ordinary,
classifiable content the whole time — the metadata to sort them was sitting
unused in the same directory record the classifier was already reading. The
armor/heraldry mislabel is its own small lesson nested inside this one: even
after clearing the "is this real content" bar, a quick eyeball of a whole
same-dimension cluster can still misname *what kind* of real content it is —
worth a second look specifically at whether a "decorative/emblem" guess is
actually just a bigger or more ornate instance of a category you already
have (here: armor), rather than a genuinely distinct one.

Rule of thumb: the bigger the catch-all bucket (especially over ~30-40% of
the archive), the stronger the prior that it's an artifact of the
classifier's blind spot rather than a true statement about the content.
