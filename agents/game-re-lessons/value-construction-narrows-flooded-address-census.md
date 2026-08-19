# A global flagged "too many xrefs to trace" can still be narrow if you search for how the TARGET VALUE is built, not the target address

**When it bites:** a global word/field is documented (or discovered) as
having dozens-to-hundreds of load/store sites — too many to read one by
one — and the actual question is "which of these sites sets/tests one
specific bit or narrow value", not "what touches this field at all".

Searching every access to an *address* doesn't scale once a field is
genuinely hot (loop counters, generic flag words, anything read every
frame). But the specific *value* you care about — one bit, or a small
constant — is usually much rarer to construct than the address is to
touch, and on a fixed-width RISC ISA (MIPS, ARM, PowerPC, SH-2, ...) a
value that doesn't fit a single immediate has to be assembled through a
small, greppable set of instruction shapes. A single 32-bit-address-space-
aligned bit (`1 << 16` through `1 << 31`) is the cheapest case: it equals
exactly one `lui $reg, N` (upper-half load, no `ori` needed), so grepping
the *whole binary* for that one specific `lui` immediate collapses however
many raw address hits there were down to a handful of real candidates —
one of which is normally the actual write/test site.

Confirmed on Valkyrie Profile (PSX): a global flag word had roughly 180
raw `sw`/`lw` hits to its displacement across one overlay + the resident
exe (matching the project doc's own prior note that it had "hundreds of
xrefs"), making a by-address read hopeless. The two bits the question
actually depended on (`0x00080000`, `0x00100000`) are each a bare `lui`
half with no `ori` required. Grepping for `lui $reg, 0x8` / `lui $reg,
0x10` across the same binaries returned **15 total hits**, and exactly one
was a real write to the target address — an instant, tractable answer to
a question the by-address approach could never have finished.

**Fix:** before giving up on (or brute-force-reading) a flooded address
census, ask whether the specific value you need is itself hard to build —
a multi-instruction immediate, a shifted single bit, a magic constant, a
known enum value — and search for *that* construction pattern across the
whole binary instead of the address. This routinely turns an intractable
by-address search into a short, enumerable candidate list, even when the
address itself really does have hundreds of legitimate, unrelated touches.
