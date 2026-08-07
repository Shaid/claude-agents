# A "lazily built" factory inside a vendored library can actually be eager and permanently cached — config assigned after the first use is silently ignored

**When it bites:** driving a vendored decompiler/parser library that exposes
a mutable per-context configuration field (a symbol table, native-function
table, format-flag override, encoding table) meant to be set once before
use — especially when your plan is "load everything, then assign
configuration, then process objects." If a config field's effect on the
first few objects processed matches the *default/empty* behavior even
though you assigned real data to it beforehand, suspect this before
anything else.

Confirmed on Drakengard 3 (PS3, UE3, `flower` project) driving
EliotVU/Unreal-Library (UELib) to decompile UnrealScript bytecode.
`UnrealPackage.NTLPackage` (a native-function-name lookup table) needs to be
assigned before decompiling — its own naming and the surrounding library
code's shape (`Branch.GetTokenFactory(Package)`, called from
`UStruct.GetTokenFactory()`) strongly imply it's read lazily, on first
actual `.Decompile()` call. It is not: `UByteCodeDecompiler`'s *constructor*
— itself invoked from deep inside `UStruct.Deserialize()`, i.e. triggered by
the **first `.BeginDeserializing()`/`Load()` call on any Function/State
in that package**, not by any decompile call — eagerly calls
`container.GetTokenFactory()`, and `EngineBranch.GetTokenFactory` caches its
result **forever** per-package-instance
(`if (_TokenFactory != null) return _TokenFactory;`). A driver that loaded
all 4 needed packages first, then assigned the merged native table to all of
them, then began decompiling, still produced 100% unresolved
placeholders — because a native-token-harvesting pass had *already* called
`BeginDeserializing()` on every function in the target package (to read an
unrelated field, `NativeToken`, off each) before the table assignment,
which was enough to lock in an empty-table factory permanently. The fix was
strict ordering: harvest from the *other* packages only, assign the merged
table to the target package, and only *then* touch anything belonging to
the target package for the first time.

**Fix:** when a vendored library's docs/field-comments say "assign this
before use" but the surrounding code shape suggests laziness, don't trust
the shape — trace what the *first* deserialize/parse call on the target
object actually does, specifically whether it constructs any
helper/decoder/factory object in its own constructor (not just its
declared method body) that reads the config field at that moment. If a
config field lives on a shared context object (a package/session/document),
audit *every* prior touch of that same context for anything that could
trigger the eager path — including diagnostic/scanning code you wrote
yourself that happens to deserialize objects for an unrelated reason before
you meant to "really" start.
