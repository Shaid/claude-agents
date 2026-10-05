# When a field's own confirmed writer makes the crashing value structurally impossible, stop hunting for another writer — the referring pointer's identity is wrong

**When it bites:** a crash or bad-value investigation has already found and
fully confirmed the *one* writer of the field holding the bad value (a
disassembly-verified store, cross-checked against an independent invariant
so it isn't in doubt), and that writer provably cannot produce the observed
value — yet the investigation keeps searching for a *different* writer, a
missed code path, or a stale-cache explanation for why the field ended up
wrong.

Confirmed on Fire Emblem: Three Houses (Switch, `chimera`): a crash read
`*( *(unitObj+0x28) + 0x68 )` as the literal integer `1` and dereferenced it
as a pointer. Two full sessions searched the entire executable for "what
writes `1` (or writes anything) into offset `0x68` of the object at
`unitObj+0x28`" via byte-pattern/window scans — a reasonable-looking plan,
since the field's role (a resource-slot registry pointer) was already
solidly established from its confirmed consumer. Both came up empty on the
real question, because there is no such writer: the field's one true writer
(found by a differently-shaped census — filtering `str x?,[x?,#0x68]` sites
by a *sibling* store to `+0xC0` on the same base, which is a much smaller,
more selective net than searching `+0x68` alone) stores a **self-pointer**
into an embedded sub-object at object-construction time, cross-confirmed by
an independent zero-deviation structural check (the constructor's own
resource-registration call uses byte-identical arguments to the crash's own
call). A field whose only writer stores `this + constant` can never hold a
small literal like `1` for a real instance of that class — full stop, no
alternate code path needed to explain it.

**The resolving move was to stop treating the field as buggy and instead
prove the *referring pointer* — `unitObj` itself — was never really an
instance of the expected class.** Tracing `unitObj` backward through the
crash's own call stack (register-by-register, frame by frame) found it was
fetched out of a 512-entry table by an **unvalidated, model-data-driven
index** computed with no bounds check — while a structurally identical
computation 250 bytes away, in a sibling code path, *does* range-check the
same quantity and skips out-of-range entries. A negative or out-of-range
index reads a stray qword from elsewhere in (or past) the table, which
survives a bare null check and gets treated as if it were a real object of
the expected class. Its "`+0x68` field" is then just whatever unrelated data
happens to sit at that byte offset of whatever the stray qword actually
points at — the specific value `1` needs no dedicated writer at all once
`unitObj`'s own identity is wrong.

**General shape, applicable beyond this one bug:** when field `F` of object
`O` holds a value that `F`'s own fully-confirmed, invariant-preserving
writer(s) cannot produce, do not keep searching for a missing writer of `F`
— the addressing chain that produced the reference to `O` is the more
likely fault. Redirect the investigation to **how `O`'s pointer/reference
itself was obtained** (an array/table index with no bounds check, a cast
from a differently-typed handle, a stale/freed pointer reused after a
`free`), and look specifically for a nearby sibling code path that performs
the identical lookup *with* a validation step the crashing path lacks —
engines frequently duplicate a lookup (a fast/unchecked draw-time path next
to a slower/checked bucketing or validation pass) exactly because the
validated version was written first and the unchecked one trusts it too
much.

This is a different failure mode from `negative-from-addressing-root-not-
shapes.md` (which is about *negative* claims — "nothing reads/writes this" —
built from an incomplete search). This lesson is about a *positive*,
already-confirmed write chain: the writer is real, singular, and fully
understood, and the mistake is continuing to distrust or search around it
instead of trusting the invariant it proves and moving the search one level
up the reference chain.
