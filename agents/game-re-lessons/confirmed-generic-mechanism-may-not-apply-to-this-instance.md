# A disassembly-confirmed, generically-reachable override mechanism can still be the wrong one for the specific object under test

**When it bites:** you've found, via real disassembly, a function that
unconditionally overrides some per-object field (a bias, a flag, a table
index) for *every* object of a given spawn-type/shape that passes through
it — and that function is called from a plausible-sounding site (e.g. a
"spawn companion/NPC" function whose target object shares your target's
class, package, or load address). It's tempting to conclude this is *the*
mechanism governing your specific instance and apply its override
unconditionally.

## What went wrong

Parasite Eve II (PSX, `~/Development/parasite`): resolving TMD model
textures needed each primitive's stored `tpage`/`clut` fields plus a
per-object bias (`TmdObject.field_24`/`field_25`, added at draw time —
`poly->tpage += ws->field_70`). Disassembly found `Gp_PumpTmdStream`
(`src/gameplay/D4.c:498`) unconditionally sets this bias to `(4,6)` for
*any* `TmdObject` with `spawnType==1` that passes through it, and found it
called from a party-companion NPC spawn function (`src/gameplay/3FB8.c:9710`)
whose target object shared Kyle's own overlay load address. That reads as
strong, specific evidence: "Kyle's body uses bias `(4,6)`."

It was wrong. Applying that bias moved every resolved `tpage`/`clut` value
completely outside the range of Kyle's own decoded `.pe2img`/`.pe2clut`
sibling chunks — while the *default* bias `(0,0)` (the plain
`Gp_AttachTmd`/`Gp_AttachTmdFlags` path every object gets unless
overridden) resolved every single primitive to VRAM/CLUT coordinates that
matched the real decoded chunk data byte-for-byte (both texture pages
landed exactly on the file's own two work-entry-table column origins; both
CLUT rows landed exactly inside the file's own decoded CLUT chunk's row
range). The disassembly finding was real — `Gp_PumpTmdStream` genuinely
does this, and genuinely is reachable from *a* Kyle-associated spawn path —
it just isn't the path that creates the specific `TmdObject` this model's
body mesh belongs to (almost certainly a separate HUD/pickup-icon object
sharing the same overlay).

## The fix

Don't stop at "found a function that plausibly does this, called from a
plausibly-related site." When an independent **structural** cross-check is
available — here, "does the resolved address land inside data this same
object/file/package actually decoded" — run it before trusting the
mechanism, and prefer its verdict over the disassembly narrative when they
disagree. Concretely: decode the candidate resolution (with and without
the override) and check whether the result lands inside a real, otherwise-
independently-confirmed region (a decoded VRAM page, a table's declared
row range, an array's declared bounds) — the same "does this address land
in decoded data" check this project's own `disc-io-census-blind-to-
already-loaded-data-consumer.md` and `confirmed-call-target-off-
instruction-boundary.md` lessons use for other purposes. A real override
mechanism failing this check on your specific object is strong evidence it
belongs to a *different* object sharing the same class/package/address
space, not that the check is wrong.

This generalizes past texture-page biases: any per-object override field
(state flags, palette index, animation-block selector) found via a
disassembled setter function needs the same treatment before being applied
project-wide — especially when the setter's only evidence of applicability
is "called from a spawn site whose target *shares an address/package*
with my object," rather than a direct trace from *your specific* object's
own creation call.
