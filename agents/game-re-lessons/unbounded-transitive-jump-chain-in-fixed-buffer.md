# A resource's real transitive jump-chain reachability can vastly exceed a fixed-size target buffer, even under a documented "small per-instance" convention

**When it bites:** placing a resource's full reachable content (following
every internal unconditional jump/goto to its real target, not just a
linear scan) into a fixed-size real-hardware buffer (console work RAM,
ARAM, a decompression window) as part of a boot/load harness, when a
project's own docs cite a "typically small, bounded per-instance" size
convention for that resource family (often sourced from an authoring-tool
limit, not a proven hard driver limit).

Following every real jump target transitively is the *correct* thing to
do — an unconditional jump in a sequential-execution format really is a
continuation of that same execution path, not optional content. But
"correct to follow" and "bounded in size" are independent properties: a
resource can legitimately be composed as a **one-way chain through several
widely-separated regions of a much larger shared data pool** (e.g. reusing
common intro/outro/verse material across many sibling resources) rather
than a compact, self-contained blob. Each individual jump target decodes
cleanly, in-range, with zero desync artifacts — there is no decode bug to
find — the chain's total *distinct byte count* may even stay modest while
its *address span* (min-to-max touched offset) balloons far past any small
documented convention. Confirmed on FFVI (SNES)'s AKAOSNES V4 sequence
data: a full transitive walk of one song's own `GOTO` chain spanned tens
of kilobytes of real file-offset distance — each jump target confirmed
clean and in-range against an already-validated event decoder — dwarfing
both the ~4KB "per-song" convention cited in the project's own docs (itself
sourced from a composer-tool limit, explicitly caveated there as unproven
against real driver data) and the 64KB target hardware buffer.

**Fix:** don't assume a documented small-resource convention bounds real
transitive reachability — measure it directly on real data before sizing
a fixed placement scheme. If a literal address-preserving placement (needed
when the consuming code re-derives addresses via its own base+delta
relocation, see `harness-prerelocation-collides-with-drivers-own-
relocation.md`) can't fit the real span, consider a packed/compacted
placement instead (assign each visited unique region a fresh, sequential
target address, tracked in a lookup map) — this preserves exact reachable
*content* and every jump's real *target* while using only as much buffer
space as bytes actually visited, at the cost of not being byte-address-
identical to whatever the real system's own transfer mechanism would
produce. Also budget for the case where even the packed span will not fit
comfortably (a session may still choose to truncate with a documented,
graceful fallback — e.g. redirecting a beyond-budget jump target to a
synthetic "end" stub — rather than crashing or silently mis-executing).
