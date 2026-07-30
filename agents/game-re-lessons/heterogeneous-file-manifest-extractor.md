# Heterogeneous file sets want a manifest-driven extractor

**When it bites:** an extractor's special-case branches keep growing as you add more file types.

The wyrm pattern: per-file config (`type`, `palette: self|donor`, `codec`,
`pixelBase`) driven from a manifest, instead of ever-growing special-case
code in the extractor itself. Reach for this once a second or third
distinct file "shape" shows up in the same game's data set.
