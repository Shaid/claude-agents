# Decompiling UE1/UE2/UE3 UnrealScript bytecode via EliotVU/Unreal-Library (UELib)

Confirmed on Drakengard 3 (PS3, `flower` project) — the real answer to the
gap `unreal-engine3-umodel.md` leaves open: umodel can *confirm*
`Class`/`Function`/`State` bytecode exists and quantify it (`-list`), but
cannot decompile it back to readable source at all. **UELib
(`https://github.com/EliotVU/Unreal-Library`) can, cleanly, for real
console-cooked content — with two real fixes most licensee titles will
also need.** Full verification methodology and evidence:
`docs/drakengard3/ps3/data-structure.md` §24 in the `flower` project.

## No GUI/Wine/Mono needed — UELib ships its own headless CLI

**UE Explorer** (the canonical decompiler this engine family gets pointed
at) is a Windows/.NET WinForms app, but its entire decompile engine lives in
a separate dependency, UELib, which is itself a normal cross-platform .NET
library (`netstandard2.0;netstandard2.1;net10.0` multi-target) with **its
own separate CLI project** (`CLI/` in the repo — `UnrealLoader.LoadPackage`
+ `obj decompile <objectPath>`). Don't assume "canonical tool is a Windows
GUI app" means Wine/Mono/GUI-automation is the way in — check the
dependency's own repo structure first; the actual decompile logic is
routinely separable from a GUI-only reference tool. UELib is also actively
developed (real commits within the current week as of this writing, not an
abandoned UDK-era artifact) — don't assume "made for the UDK era" implies
stale/unmaintained without checking commit history.

A local, no-root .NET SDK (Microsoft's own `dotnet-install.sh`, which
installs to a user-writable directory) is sufficient to build both UELib
itself and a driver against it — no system-level install needed, matching
the no-root-tooling pattern used elsewhere in this project family (e.g.
`ancient` for compression, `amitools`).

## Fix 1: `UnrealPackage.CookerPlatform` must be forced to `Console` before any object deserializes

UELib's own platform auto-detection (`UnrealPackage.SetupBuild`)
recognizes "this package is console-cooked" only via a **fixed directory-
name allowlist** (`CookedPC`, `CookedPCConsole`, `CookedPCServer`,
`CookedXenon`, `CookedIPhone`) plus per-title `[Build(version,
licenseeVersion, ...)]` attribute matches for titles UELib's authors have
specifically added. A licensee's own directory-naming convention (`COOKEDPS3`
for Drakengard 3) and a `LicenseeVersion=0` package (no per-title match)
both fall through this detection silently — no error, no warning. Without
the fix, `UStruct.Deserialize()` reads editor-only fields
(`ScriptText`/`CppText`/`Line`/`TextPos`) a real console-cooked package
never wrote, misaligning every subsequent field read a few bytes later
(symptom: an `InvalidCastException` reading an unrelated field type several
reads downstream of the actual wrong branch — the failure surfaces well
past its cause, same shape as `masking-bug-pairs.md`/other
delayed-symptom lessons).

**Fix**: `pkg.CookerPlatform = BuildPlatform.Console;` right after
`UnrealLoader.LoadPackage()` returns, before `InitializePackage(...)` or
any object deserialize. `CookerPlatform`'s own field doc comment in UELib's
source already states this exact scenario verbatim — read the vendored
source's doc comments, not just its README/`--help`, before assuming a
config gap needs a workaround rather than an already-documented flag.

## Fix 2: cross-package native-function-table merge, with a real ordering trap

A licensee's own gameplay-script package (e.g. `SQEX03GAME.XXX`) typically
declares thousands of `Function`s but **zero native ones** — the actual
native/operator declarations (comparison/arithmetic operators, `VSize`,
string `Concat`, the `foreach` actor-iterator native, etc.) live in the
separately-cooked core-engine packages the title also ships alongside it
(`Core.XXX`/`Engine.XXX`/`GameFramework.XXX` or platform-renamed
equivalents — check the same directory as the gameplay package). Skipping
this doesn't error, it silently degrades: every native/operator call in
decompiled output renders as an opaque `__NFUN_<index>__` placeholder
instead of its real name.

The real trap: `UnrealPackage.NTLPackage` (the native-token-table field)
must be assigned to a package **before the very first deserialize of
anything belonging to that package**, not merely "before you call
Decompile()" — see
`~/.claude/agents/game-re-lessons/eager-factory-caches-before-late-config-assignment.md`
for the exact mechanism (a constructor deep inside the deserialize path
eagerly builds and permanently caches the token factory the first time
*anything* in the package is touched, including an unrelated diagnostic
scan). Load the core-engine packages first, harvest their native tokens
(scanning every `UFunction` for `NativeToken != 0`, building a
`NativeTableItem` per hit — UELib's own `NativeTableItem(UFunction)`
constructor does this), merge, then load the gameplay package **last** and
assign the merged table immediately, before touching any of its own
objects.

## Verification: use umodel's own `-list` counts as a cross-check

If `unreal-engine3-umodel.md`'s `-list`-based UnrealScript-vs-native census
was already run on the target (it should be — that's the cheap first
step), UELib's own parsed `Names`/`Exports`/`Imports`/`PackageVersion`
counts, filtered by object-path prefix to the licensee's own namespace
(excluding re-exported Core/Engine helper objects that also appear in the
gameplay package's own export table), should match umodel's independently-
derived `Function`/`Class` counts **exactly** — two independent UE3 package
parsers agreeing byte-for-byte is strong, cheap, zero-new-oracle evidence
the decode is genuinely correct, not just "didn't crash." Confirmed on
Drakengard 3: 6,752 functions and 1,155 classes, exact match both ways.

## A batch success-rate needs more than "did it throw"

See
`~/.claude/agents/game-re-lessons/vendored-decompiler-swallows-per-token-exceptions.md`
— UELib's own `ByteCodeDecompiler` catches per-token/per-statement
exceptions internally (`LibServices.LogService.SilentException`) and
returns a best-effort partial string rather than propagating. Install a
custom `ILogService` that counts these instead of the default
print-and-continue before trusting a full-corpus "0 errors" figure; on
Drakengard 3 this found 5/6,752 functions and 1/1,155 classes with a
partial internal glitch that a bare try/catch around `.Decompile()` alone
would have missed entirely (all narrow, well-isolated UELib formatting
bugs — a duplicated-switch tail-nest bug, an editor-only
`filtereditoronly` block, an inline-enum formatting bug — not
addressing/dataflow corruption; the surrounding real logic stayed intact
and readable in every case).

## UELib's generic tagged-property machinery reads *any* UObject instance, not just Class defaultproperties — Level/Actor/Component data included

`UObject.Deserialize()` calls the same generic property loop
(`DeserializeProperties()`/`UDefaultProperty`) that decompiles a `Class`'s
`defaultproperties` block for **any** object with a non-zero class index —
and the base `UObject.Decompile()` (distinct from `UClass`/`UFunction`'s
own script-decompile override) produces a generic `begin object
name=... class=... <properties> end object` T3D-style dump for any
instance. This means a placed `Actor`'s subobject (e.g. a Level/Map
package's `StaticMeshComponent`, carrying a real `StaticMesh` reference
and a `Materials[]` per-instance override array) reads out with **zero new
parser code** — `pkg.FindObjectByGroup("SomeComponentName")` (no dotted
group prefix needed for a top-level export),
`obj.BeginDeserializing()`, then either `obj.Decompile()` for a quick
free-text dump or iterate `obj.Properties` directly for structured
extraction. No native-token-table merge is needed for this (that's only
for `Function`/`State` *bytecode* — plain property data has none), so
this path is simpler to set up than the `decompile`/`scan-all` Class/
Function path this file otherwise documents.

**Real gap to expect**: an `ArrayProperty`'s element type is inferred by
looking up the real class declaration on the object's own `Class` chain —
which fails silently (produces `/* Array type was not detected. */`
instead of real decoded elements) whenever that class is only *imported*,
not *loaded*, in the current session (true by default for any component
class like `Engine.StaticMeshComponent` if you only ever load the one
package containing the instance, which is normal for this generic-
property use case — no reason to load `ENGINE.XXX` too). Fix:
`UnrealConfig.VariableTypes["PropertyName"] = (null, PropertyType.X)` — a
property-name-keyed override dictionary UELib ships for exactly this
"class only imported" scenario (see its own field doc comment). Confirmed
on `StaticMeshComponent.Materials` (→ `PropertyType.ObjectProperty`).

**Real gap #2, multi-element array values are joined into one string, not
one tag per element**: a genuinely dynamic `TArray` property (like
`Materials`) shows up as exactly **one** `UDefaultProperty` tag in
`obj.Properties` (not one per array index) — its `.Value` getter decodes
*every* element internally and joins them with `\r\n` into one combined
string (e.g. `"Materials(0)=Ref0\r\n\tMaterials(1)=Ref1"`). Naively taking
the first/last single-quote across that whole joined string (a first
attempt) silently produces a Frankenstein reference — the first element's
package glued to the last element's object name. Split on newlines first,
then parse each line's own quoted reference independently.

**Real gap #3 (a UELib bug, not a project-specific format issue): two
optional trailing header fields (`AdditionalPackagesToCook`,
`TextureAllocations`) can hang the whole package load** on a title whose
cooker never actually wrote them, despite a version-threshold check that
says they should exist. See
`~/.claude/agents/game-re-lessons/vendored-parser-hang-needs-committed-source-patch.md`
for the full root-cause + the deliberate, committed vendored-source patch
that fixes it (a hard absolute count cap — both a whole-file-relative and
a nearby-offset-relative bound were tried and rejected first, see that
file for why). If your project's `uelib-driver` needs to deserialize
objects from packages your title's own cooker may have skipped these
fields on (in practice: any package outside the small set already proven
clean by an existing Class/Function decompile pass), apply this patch
before trusting a "why is this one file so slow" report to be your own
project's format issue rather than UELib's.

## A second, real UE3 `.XXX`-family compression sub-format ("format B") exists — umodel and hand-derivation may confirm different things

The `.XXX`/`.upk` chunk-compression wrapper most UE3-on-console projects
confirm first (Tag + BlockSize + CompressedTotal + UncompressedTotal +
block table, the whole file wrapped) is only **one** of two real UE3
on-disk sub-formats — confirmed distinct on Drakengard 3, and the
mechanism (`FPackageFileSummary::Serialize3`'s own version-gated field
list) is generic UE3, not title-specific, so expect this on other titles
too. The second ("format B"): the `FPackageFileSummary` header is stored
**plain** (uncompressed, native-endian) at the start of the file: only the
remaining data (name/import/export tables + every object's bytes) is
split into a `CompressedChunks` array (`{uncompressedOffset,
uncompressedSize, compressedOffset, compressedSize}` per entry, each
entry itself shaped like a format-A block-table region) embedded directly
in the header (`Summary.CompressionFlags`/`Summary.CompressedChunks`).
umodel handles both transparently (see `UnPackage.cpp`'s own branch on
`Summary.CompressionFlags`) — which is exactly why a from-scratch/UELib-
facing parser can go a long time only ever having been checked against
one of the two, if its own development sample happened to be narrow (see
`~/.claude/agents/game-re-lessons/single-working-consumer-hides-second-container-subformat.md`).
Byte-exact field order for format B, derived from UEViewer's own
`Unreal/UnrealPackage/UnPackage3.cpp` (not guessed): confirmed at
`docs/drakengard3/ps3/data-structure.md` §27 in the `flower` project,
cross-checked against 5+ real files' `umodel -list`-derived Names/Exports/
Imports/Engine counts, exact match.

**A generic UE3 flag worth knowing regardless of the above**:
`PackageFlags & PKG_ContainsMap` (`0x00020000`) is UE3's own, real,
documented "this package is a Level/Map" signal (see UELib's own
`PackageFlag.ContainsMap`/`UnrealPackage.IsMap()`) — a fast, reliable way
to enumerate every Level/Map package in a corpus from the header alone,
no full decompression or umodel invocation needed per candidate file.
