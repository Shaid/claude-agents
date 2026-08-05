# A wildcard/glob invocation of a batch CLI tool can abort its entire run on the first file it can't parse

**When it bites:** running any batch/directory-wide extraction tool (a
community asset extractor, a decompiler, a repackager) with a wildcard or
"process everything in this directory" argument against a large, unvetted
corpus, and the whole run dies partway through on one bad file — even
though the same tool handles a single, explicitly-named file from the same
directory just fine.

Confirmed on Gildor's `umodel` (UE3 asset extractor) against Drakengard
3's 3,238-file `COOKEDPS3/` package directory: `umodel -export -png -ps3
-path=<dir> -out=<out> '*'` aborted outright the first time it reached a
package with a corrupt/unsupported compressed stream (`*** ERROR: zlib
uncompress(...) returned -5`), having exported nothing at all up to that
point despite having already spent time "loading" (i.e., opening and
parsing the name table of) every alphabetically-earlier matching file. The
crash happens during the tool's own **eager pre-scan**: resolving a
wildcard or class filter requires opening and indexing every matching file
up front, before any export begins, so one bad file poisons the whole
batch. Confirmed by direct contrast: invoking the identical tool against
the identical directory with an **exact, non-wildcard filename** does not
trigger this pre-scan at all — only the one requested file is opened,
regardless of how many other files (including the bad one) are sitting in
the same directory.

**The fix**: when a corpus hasn't been individually vetted for
tool-compatibility, never pass a wildcard/glob covering the whole corpus to
a batch tool in one invocation. Enumerate the target files yourself
(a plain directory listing) and invoke the tool once per file (or once per
small, independently-retriable shard), catching and logging each
invocation's failure without letting it abort the others. This does cost
real per-invocation overhead (process startup, and often a full directory
re-scan every single call — confirmed ~0.3-0.4 sec/file here, dominated by
the tool re-listing the same 3,238-entry directory on every launch) but
that's a bounded, budgetable cost, cheaply offset by running several
invocations concurrently (a simple bounded worker-pool — the invocations
are process-startup/IO-bound, not CPU-bound, so real parallelism pays off).
The alternative — losing 100% of a multi-thousand-file run's output because
of one bad file discovered near the end — is strictly worse.

Related: `optional-per-record-compression.md` (a different shape of the
same underlying caution — a minority of "failures" in a healthy corpus
often isn't what it looks like) and
`all-zero-stub-file-inflates-failure-count.md` (what to do once you have a
real per-file failure list — classify it before reporting a raw success
rate).
