# Two sibling titles failing the same check identically may fail for unrelated reasons

**When it bites:** the same decode/resolution attempt returns the same
negative result (0 hits, 0% resolved, a structural check failing) across
two or more sibling titles in an engine family — especially the oldest and
newest revisions — and the natural next step is writing one shared
explanation ("this engine revision doesn't support the mechanism") instead
of independently tracing each title's own failure.

An identical symptom across sibling titles is not evidence of an identical
cause. Confirmed on the SSI Gold Box engine (`crawl` project): both Pool of
Radiance (1988, the earliest Amiga port) and Pools of Darkness (1991, the
latest) resolved **zero** levels' ECL wallset-slot bindings statically — the
same 0/N symptom, on titles already known to differ structurally elsewhere
(container format, a GEO header prefix byte). Tracing each independently
(disassembling from every header entry point, running the reachability
walker, and checking every reached call's operand kind) found two
completely different, unrelated reasons: Pool of Radiance's header fields
mostly point to addresses *outside* that level's own ECL block at all (a
structural/addressing difference — 3 of 5 header entry points aren't valid
addresses into the buffer for this revision), while Pools of Darkness's
header fields are all valid and its calls ARE reached, but every one uses a
memory-dereferenced (runtime-computed) operand rather than a literal (a
semantic/behavioral difference — this revision computes the id at runtime
instead of hardcoding it). Writing up "PoR and Pools don't support static
wallset resolution" as one shared fact would have been true in outcome but
wrong in mechanism, and would have missed that PoR's failure is partially
addressable (2 of its 5 entry points ARE valid) while Pools' genuinely
isn't (its whole reachable call surface is dynamic).

**Fix:** when a check fails identically on N sibling titles, trace each
title's own failure to its own root cause before writing a shared
explanation — even when the titles are already known to share almost
everything else. A single sentence covering all of them is only honest if
the underlying mechanism is provably the same; otherwise it hides which
titles have partial paths still worth pursuing (like PoR's 2 valid header
fields here) behind an appearance of total, uniform failure.
