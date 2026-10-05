# A shared decode function's current behavior can be another platform's cross-check oracle, not just legacy code

**When it bites:** you've confirmed a shared decode-library function
(`src/assets/formats/*.ts` in the seer architecture, or its equivalent) is
wrong for the game/platform you're fixing, and the function is also
imported — unchanged, same signature — by a *sibling* platform's pipeline
(a different port of the same game, or an unrelated game sharing the
engine family). Before mutating that function's behavior in place, check
what the sibling caller actually does with its output.

The seer architecture deliberately shares format-decoder code across every
platform/game that needs it (`docs/architecture-overview.md` §7's "Shared
Format Decoder Library"). This is usually safe to fix in place — but a
sibling caller sometimes depends on the function's *current, possibly
still-unconfirmed-elsewhere* behavior as its own verification tool: e.g. a
DOS/VGA port's pipeline decoding its own sprite bank under the same plain
model the Amiga side used, specifically so it can do a bit-for-bit
cross-platform comparison against the Amiga decode as evidence the two
ports share tile geometry. Mutating the shared function's semantics to fix
the Amiga side would silently invalidate that comparison's premise for the
sibling caller too — not a compile error, not a test failure necessarily
(if the sibling has no test pinning the old behavior), just a quietly
wrong cross-check the next person trusts.

Confirmed on PowerMonger: `sprite-bank.ts`'s `decodeSpriteBank` (plain
N-bitplane row-interleaved index) was confirmed wrong for the Amiga side's
SPRITE16/24/32/8. banks (masked 4bpp is correct). But
`tools/powermongerdosvga/build-assets.ts` imports that exact function and
config shape to decode the DOS/VGA port's own `SPRITE08/16/32.EGA` banks,
and its own header comment documents a deliberate bit-for-bit comparison
against the Amiga decode under this same plain model as evidence the two
ports share tile geometry. Mutating `decodeSpriteBank` itself (changing its
output shape or bit semantics) would have silently broken that already-
shipped comparison's premise. Fix: left `decodeSpriteBank`/`SpriteBankConfig`
byte-for-byte unchanged (still correct for the Amiga side's own TEXTURES,
which genuinely has no mask plane), and added a new, separate
`decodeMaskedSpriteBank` alongside it for the corrected banks — zero risk
to the DOS/VGA pipeline, verified by actually re-running it after the
change.

**Fix:** before changing a shared decoder's behavior, `grep` the whole
project (not just the game/platform you're fixing) for every importer of
that function/type — across `tools/<other-platform>/`, not just `src/`.
If a sibling importer's own doc comments or code describe using the
function's *current* output as a cross-check/oracle (not just "decodes our
data"), treat that as a second, independent consumer contract: add a new
function alongside the old one for the corrected behavior rather than
mutating the shared one, and re-run the sibling's own pipeline afterward to
confirm it's unaffected — don't just trust that its tests (if any) would
have caught a semantic drift.
