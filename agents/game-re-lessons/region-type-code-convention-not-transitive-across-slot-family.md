# A confirmed "region type N = code" convention for one container family doesn't automatically hold for a sibling slot family in the same project

**When it bites:** a self-describing container format (a group/region
directory tagging each sub-block with a type id) has an already-confirmed
"type N = raw executable code" convention from one part of the project, and
you're about to assume that same type id marks the code region in a
*different* family of slots using the identical container shape, without
independently checking.

Valkyrie Profile 1 (PSX): this project's group-directory container
(`u32 count; u32 field1; {u32 regionType; u32 regionSize}[]`, tiling a TOC
slot's decompressed payload) had `regionType 4` established as "raw MIPS
code" from earlier work on other slots. Applied uncritically to a family of
menu sub-overlay slots, this produced group-directory-derived "code region"
files that were actually too small to contain cited executable addresses at
all. The real code for that slot family lives in `regionType 18` instead —
a type id this project's general convention would have called something
else (header/text-ish, by the numbering's rough association elsewhere).
`regionType 4` in these particular slots turned out to hold something else
entirely (undetermined this pass, but conspicuously *larger* than the real
code region, ruling out "just padding").

**Fix, generalized:** a region/chunk/type tag confirmed to mean one thing
for one family of containers in a project is a *hypothesis*, not a
transferable fact, when applied to a structurally-similar but distinct
family (different TOC slot range, different subsystem, different original
source file on the developer's side) using the same outer container shape.
Re-verify which type id actually holds code (or whichever content class
you need) per family — e.g. by disassembling the region and checking for
plausible instruction density/control flow, or by locating one independently
cited real address and testing which type/region it falls inside — rather
than inheriting the mapping. This is a sibling case to
`header-field-role-not-transitive-across-sibling-format.md` (inner payload
header fields don't transfer across sibling formats sharing an outer
container) at one level up: here it's a *type discriminant's meaning*, not
a header field's position, that fails to transfer.
