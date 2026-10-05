# A container-detector's hardcoded tag/magic offset, derived from an early partial corpus, silently skips every real instance outside it — no error, not even a parse failure

**When it bites:** a pipeline's own detector function for a container/chunk
format hardcodes the byte offset (or size) of a leading header before a magic
tag — derived from a "corpus-wide constant, N/N entries" table in the docs —
and a task later asks whether that container's true population is bigger
than documented, or a fresh full-archive census by decompressed size/entropy
turns up a large cluster of plausible-looking content the existing pipeline
never touched at all.

Confirmed on Fire Emblem: Three Houses (Switch, `chimera`)'s `.kldm`/
`MDLK0001` container. An earlier pass's own leading-header table was
explicitly "re-derived against the full 29-entry `.kldm` corpus" and
declared the tag's own offset (`0x74`) a corpus-wide constant — true of
that 29-entry sample, silently false of the rest. `detectKldmChainStart`
hardcoded `bytes.slice(0x74, 0x74+8)`. A fresh full-DATA0-archive magic scan
(searching every non-empty entry's first KT_GZ block for the literal
`"MDLK0001"` bytes, not trusting any assumed offset) found **189** real
hits at **five** different tag offsets (0, 48, 76, 92, 116) spanning a much
wider index range than the documented one — 155 previously-undiscovered
entries, all silently skipped by the fixed-offset check with **zero**
errors or warnings, since `detectKldmChainStart` just returned `null` and
the caller moved on to the next entry as if the format simply didn't apply
there. Decoding the newly-found entries through the *already-existing,
unmodified* chain-walker (`parseG1MChain`) worked immediately once given
the right start offset — the container/codec itself had been fully solved
all along; only the *detector's offset assumption* was wrong. Worse: even
inside the already-documented 29-entry index range, one entry (the single
LARGEST hit in the entire 31,160-entry archive) used a different offset
than the other 29 and was *also* silently skipped — proving that even a
"re-derived against the full corpus" claim can be wrong if "the full
corpus" was itself an unverified assumption about a range boundary.

**This is a different trap than a stored field being misread as constant**
(`self-describing-length-field-mistaken-for-corpus-constant.md`) or a decoder
whose field *width* was never exercised by a first small corpus
(`format-field-width-unexercised-by-first-corpus.md`, `small-sample-probe-
undercounts-dominant-subformat.md`) — those fail loudly-ish (a bad stride, a
truncated value) on the first out-of-range record they hit. A hardcoded
detector *offset* fails silently and totally: every instance outside the
sampled offset is never even attempted, with no parse error to notice,
because the detector's job is exactly "decide whether this format applies
here at all," and a wrong offset makes it say "no" cleanly for real hits.

**The generalizable fix**: when a detector locates a magic/tag by scanning
a *fixed* offset rather than searching a bounded window for the literal
bytes, treat that as a standing risk, not settled — especially right after
a "confirmed, N/N, 0 deviations" table was built from anything less than a
freshly re-run full-corpus scan. Re-verify by scanning for the tag itself
(bounded window, e.g. the first 256-512 bytes) across the *whole* archive
before trusting a fixed-offset detector's negative results, particularly
when a separate signal (unusually large decompressed sizes in an
"unclassified" bucket) already suggests more content exists than the
detector reports.
