# A per-object subprocess export can log an error yet still leave a real, truncated/zero-byte output file behind — validate the artifact before parsing it

**When it bites:** a pipeline shells out to an external per-object/
per-package export tool (a community asset extractor, umodel, a
decompiler) in a loop, and a downstream step parses each exported file
with fixed-offset binary reads (a header/signature check via
`readUInt32BE` at a known offset) without first validating the file's own
size/magic.

Confirmed on Drakengard 3 (PS3, `flower` project): umodel's own per-object
export failed mid-read for one texture (`Reading TD_..._ILCA mip level 0
... from TEXTURES_....TFC`, logged as an ordinary per-object error the
pipeline already tolerates) — but still created a real, **zero-byte**
`.png` file at the expected output path rather than no file at all. A
downstream `readPngDimensions` helper, written assuming any file that
exists is a complete PNG, called `buffer.readUInt32BE(16)` on the 0-byte
buffer and threw a raw `ERR_BUFFER_OUT_OF_BOUNDS` — an uncaught,
opaque native error that crashed the *entire* batch (hundreds of
already-successful promotions lost), not a clean, attributable failure
for the one bad file. The real content wasn't even lost: a sibling
package's own promotion of the exact same texture object (cooked-seekfree
packaging duplicates shared dependencies per-package) was a healthy,
full-size file — the crash was purely a downstream robustness gap, not a
missing-data problem.

**The fix, two layers**: (1) the low-level reader itself validates a
minimum size and the real magic/signature bytes before touching any fixed
offset, throwing a clear, catchable `Error` naming the file and its actual
byte count instead of letting a native bounds exception escape — this
makes the failure mode debuggable from the error message alone, whether or
not layer (2) below exists. (2) the calling loop wraps the read (and any
other per-file promotion step) in a try/catch, skipping and logging the
one bad file rather than aborting the batch — the same resilience
convention a mature pipeline already applies to malformed JSON/glTF output
from a partially-failed export; extend it to *every* per-file artifact a
subprocess tool writes, not just the ones a prior failure already taught
you to distrust. Add a regression test with a real zero-byte/wrong-magic
fixture, not just the happy-path case, so this class of crash can't
silently regress.

Related: `wildcard-batch-tool-aborts-on-first-bad-file.md` (a different
shape of "an external batch tool's partial-failure behavior needs
explicit handling, not an assumption of atomicity") and
`all-zero-stub-file-inflates-failure-count.md` (validate a *source* file's
content before trusting a decode failure at face value — this lesson is
the mirror case, validating a tool's *output* artifact instead).
