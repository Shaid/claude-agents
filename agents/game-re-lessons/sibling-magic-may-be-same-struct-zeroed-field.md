# A sibling-magic variant may be the identical struct with one component zeroed, not a new pixel/compression fork

**When it bites:** a format family has two closely-related magics (e.g.
`TIM2`/`CLT2`, `IMG2`/`IMG3`, a base tag plus a one-letter-different
sibling), the sibling is rare (often exactly one instance in a whole
corpus, too few to diff a second sample against), and the natural
assumption is "this must be a pixel-format or compression variant of the
base format" — before you've actually parsed the sibling's header fields
against the base format's *own* documented struct layout.

Confirmed on Chaos Legion (PS2): `CLT2` (1 instance in the whole game, next
to 2,468 `TIM2` textures) was carried as "structurally TIM2-shaped, pixel/
compression delta unknown" purely because a second sample to diff against
was never found — a real, reasonable-sounding blocker that made the format
look unsolvable without more data. It wasn't a variant at all: parsing
`CLT2`'s own picture-header fields against the *public, unmodified* TIM2
picture-header spec decoded cleanly, with `image_size=0` and
`header_size(48) + clut_size(1024) + image_size(0) == total_size(1072)`
holding exactly — i.e. `CLT2` is literally "CLUT2," the *exact same* TIM2
struct with the image component zeroed out, used as a standalone/shared
external palette resource. No pixel-format delta exists to find; the
"need a second sample to diff" plan was solving the wrong problem.

**Fix: before assuming a magic sibling implies a new encoding, try parsing
it against the base format's own published/already-confirmed struct
layout directly, field by field** — a genuine variant will produce
nonsensical field values (out-of-range dimensions, negative sizes,
inconsistent size-chain arithmetic); a "same struct, different role"
sibling will decode to *sensible*, self-consistent values with one or more
components legitimately at zero. This is cheaper than waiting for a second
sample that may not exist (as here — an exhaustive whole-disc magic scan
confirmed there genuinely was only one `CLT2` in the entire game), and the
byte-exact size-chain arithmetic (`sum of sub-fields == declared total`)
is itself sufficient confirmation without needing a second instance at
all.
