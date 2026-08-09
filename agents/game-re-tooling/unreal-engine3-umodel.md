# Unreal Engine 3 via umodel (Gildor's UModel/UEViewer): what its CLI can and can't do, and how to get animation anyway

Confirmed on Drakengard 3 (PS3, `flower` project) — umodel already solves
UE3 package parsing/mesh/texture export well (see `game-re-corpora/
flower.md`); this file is about the parts of umodel's *own* source that
matter once a project needs more than static geometry/textures.

## `-export -gltf` (the CLI batch path) cannot embed animation data — ever, no flag combination fixes it

This is a real, deliberate limitation in umodel itself, not a bug to route
around blindly — confirmed by reading the vendored source
(`Exporters/ExportGLTF.cpp`, `Viewers/SkelMeshViewer.cpp`,
`UmodelTool/Main.cpp`, `UmodelTool/UmodelCommands.cpp`), not assumed from
CLI help text or a header comment:

- `ExportGLTF.cpp`'s `ExportAnimations()` is a real, complete glTF-animation
  writer — it only runs if `CSkeletalMesh::Anim` (a runtime field, default
  `NULL`) is set to a resolved `CAnimSet`.
- The **only** code that ever sets `Mesh->Anim` is
  `CSkelMeshViewer::Export()` in `Viewers/SkelMeshViewer.cpp`, gated
  `#if RENDERING` — i.e. it only runs inside the **interactive GUI viewer**
  (`-view` mode), never from a batch export.
- The actual CLI batch export entrypoint, `ExportObjects()`
  (`UmodelTool/UmodelCommands.cpp`), calls `ExportObject()` directly for
  every loaded object and **never constructs a `CSkelMeshViewer`** — so
  `Mesh->Anim` stays `NULL` for anything run via `-export`, regardless of
  `-gltf`, `-anim=<name>`, or any other flag.
- Confirming this is deliberate, not an oversight:
  `UmodelTool/Main.cpp`'s `CallExportAnimation()` has an explicit branch —
  when export format is glTF and the object being exported is directly an
  `AnimSet`/`UAnimSet` — that does nothing but
  `appPrintf("ERROR: glTF animation could be exported from mesh viewer
  only.\n")`.

**Don't burn time trying `-anim=`/`-notex`/class-filter combinations to
force glTF animation out of a batch `-export` run — it structurally cannot
happen.** The two real options are: (a) drive the interactive GUI viewer
via some kind of X11/input automation harness to reach the only working
code path (fragile, not attempted — the option below is simpler and was
sufficient), or (b) decode umodel's own **`.psa`** export instead (see
below) and re-derive the transform + bone-matching logic yourself.

## Workaround: decode umodel's own `.psa` (ActorX) export headlessly, then re-derive the glTF transform

umodel's *default* (non-`-gltf`) skeletal-mesh export format is `.psa`
(ActorX) — `CallExportAnimation()`'s default/`psk` branch calls
`ExportPsa()` unconditionally, with **no `RENDERING` gate at all**, so it
works fine in a headless batch `-export` run. If a project already runs a
plain (non-`-gltf`) whole-package export pass (e.g. to get texture PNGs),
every `AnimSet` object in the corpus already has a `.psa` sitting in the
staging directory for free — no extra umodel invocations needed.

`.psa`'s binary layout (chunked: `ANIMHEAD`/`BONENAMES`/`ANIMINFO`/
`ANIMKEYS`/`SCALEKEYS`, all little-endian, sequence-major/frame-major/
bone-minor key ordering) is documented byte-exact in
`Exporters/Psk.h`/`Exporters/ExportPsk.cpp`'s `DoExportPsa()` — read those
directly rather than reverse-engineering the format from a sample file;
this is a widely-used legacy Unreal interchange format, not
project-specific, so a from-scratch parser built against the real writer
source generalizes to any future UE1/UE2/UE3 project using umodel.

**Critical trap**: `.psa`'s own coordinate convention (`ExportPsk.cpp`'s
`MIRROR_MESH` block: negate `Position.Y`, negate `Orientation.Y` and
`Orientation.W`) is **not** the same convention umodel's glTF mesh exporter
uses for bind-pose bones (`ExportGLTF.cpp`'s `TransformPosition`/
`TransformRotation`: swap Y/Z, scale cm→m, plus a root-bone-only quaternion
conjugate). To drive an already-promoted glTF mesh's skeleton with
`.psa`-decoded keys, first **undo** the PSA mirror to recover the raw
UE3-space value, **then** apply the glTF transform — applying only one of
the two, or the wrong one, produces plausible-looking-but-wrong motion
(not an obvious garbage/NaN failure) since both transforms are
"reasonable-looking" coordinate flips on their own.

## Placed-Actor transforms: two real "legs," and `FRotator`→quaternion needs the root-bone parity fix, not a plain swap

Reading a placed `Actor`/`StaticMeshActor`'s real world transform (e.g. to
assemble a Level's placements into one real scene — via the generic
tagged-property reads a UELib-style driver already gives you, see
`unreal-engine3-uelib.md`) surfaces two things not obvious from the SDK
alone, confirmed on Drakengard 3 (`flower` project,
`docs/drakengard3/ps3/data-structure.md` §28):

- **Two different objects can carry the real transform, depending on the
  placement mechanism** — an ordinary placed Actor carries it on the Actor
  itself (`Location`/`Rotation`/`DrawScale`/`DrawScale3D`); a batched-
  placement actor (e.g. `StaticMeshCollectionActor`) instead leaves the
  Actor at identity and puts each sub-component's own real transform on
  the *component* (`Translation`/`Rotation`/`Scale`/`Scale3D` — a
  `SceneComponent`'s relative-transform fields, different property names
  for the same conceptual data). A real corpus scan found these two shapes
  are mutually exclusive per placement (never both real) but composing both
  legs unconditionally (parent-Actor · child-Component TRS) handles either
  shape with no branching needed.
- **`FRotator` (`Pitch`/`Yaw`/`Roll`, 65536 units/turn) → quaternion**:
  transcribe umodel's own `RotatorToAxis`/`Euler2Vecs`
  (`Unreal/UnrealMesh/UnMathTools.h`, `Core/Math3D.cpp`) rather than
  reverse-engineering it — but two things aren't obvious from reading the
  source alone, only from numeric verification: (1) `RotatorToAxis`'s three
  output vectors are the local→world matrix's **columns**, not rows
  (`CAxis::UnTransformVector`'s own `dst = src.x*v0 + src.y*v1 + src.z*v2`
  confirms this) — using them as rows instead silently builds a quaternion
  that rotates the wrong direction; and (2) a **freshly-derived** rotation
  quaternion built this way needs the same "root bone" parity fix
  `ExportGLTF.cpp` applies only to skeleton bone index 0 (negate the
  swapped quaternion's X/Y/Z, keep W) when converting to glTF space — the
  *plain* Y/Z swap non-root bones use is not sufficient here, because that
  plain-swap correctness for non-root bones relies on umodel's own
  `BoneCoords`/`UnTransformCoords` parent-chain accumulation mechanism,
  which a standalone placement transform never participates in. Verify by
  composing a transform two independent ways (rotate-then-convert vs.
  convert-then-apply-to-already-converted-local-data) and checking they
  agree to floating-point precision — they only will with the root-style
  conjugate; the plain swap gives errors of several centimeters per test
  case that look like "close but not quite right" rather than an obvious
  failure.

## AnimSet ↔ SkeletalMesh association: bone-name overlap, not a reference — and don't trust filename conventions

UE3 has **no direct serialized reference** from an `AnimSet` to the
`SkeletalMesh` it animates, or vice versa. umodel's own
`ExportAnimations()` resolves this at runtime purely by comparing bone
names (`stricmp`, case-insensitive) between the mesh's `RefSkeleton` and
the AnimSet's `TrackBoneNames` — reuse that exact algorithm offline: index
every discovered AnimSet's bone-name list (cheap — a header-only `.psa`
parse, no need to read the bulk key data), then for a given mesh, pick the
AnimSet with the highest bone-name-overlap ratio.

Don't assume a `<Prefix>_<Character>` filename convention (e.g.
`ANIM_PL00_SF.XXX` "obviously" being the player character's dedicated
animation package) picks the *best* match — confirmed on Drakengard 3 that
scene/cutscene-specific packages (e.g. `BG00_10_M0010_E0030_SP.XXX`,
carrying a dedicated `AS_<scene>_<character>`-named `AnimSet` alongside
that cutscene's own `SkeletalMesh3`) can be a **tighter** bone-name match
(100% overlap) than the "obvious" general-purpose per-character package
(86% overlap, since it also carries prop/weapon bones the specific mesh
variant lacks). Rank candidates by actual bone-overlap ratio, not by
filename plausibility.

## `umodel -list`'s Export table as a fast, zero-new-tooling UnrealScript-vs-native census

For the "is this UE3 licensee title's gameplay logic real UnrealScript
(portable, rehostable on a PC UE3/UDK build) or native C++ (needs
platform-specific binary recompilation)" question that
`~/Development/seer/docs/engine-based-porting.md` poses for every UE3
target — don't guess from package names alone. `umodel -list -<platform>
-path=<dir> <package>.XXX` prints the package's full Export table with
per-object class name and serialized byte size; that's already enough to
answer it quantitatively, no new tooling, no `-export` needed:

- **Count `Class`/`Function`/`State` exports.** A `Function` export's
  serialized size is its parameter/local-property list *plus* its actual
  UnrealScript VM bytecode — hundreds of bytes per function is real
  executable content, not a declaration. Sum the size column across all
  `Function` exports for a package-level "how much real script logic is
  here" number.
- **Check what fraction of `Class` names carry the licensee's own naming
  prefix** vs. generic Epic names. A licensee's actual game-logic package
  scores high on this (confirmed on Drakengard 3: `SQEX03GAME.XXX`,
  1,150/1,155 classes `Sqex03`-prefixed, 6,752 `Function` exports totaling
  3.57MB) — but a UE3 title's `GameFramework.XXX`/`Engine.XXX` packages
  are *also* real, substantial UnrealScript (Drakengard 3:
  98+1,330=1,428 classes, 518+4,817=5,335 functions between the two) while
  scoring **0%** on the prefix test, because they're Epic's own stock
  script content shared by every UE3 title regardless of licensee
  customization — don't mistake "real script" for "this game's own logic"
  without the naming-convention cross-check.
- **A near-empty `Class` (tens of bytes, zero `Function`/`State` children)
  is the native-C++-backed signature**, not a formatting quirk — confirmed
  on a licensed audio-middleware package (Drakengard 3's `SQEXSEAD.XXX`:
  12 classes, 74 bytes each, 0 functions): UnrealScript only sees the
  class's property surface, the actual logic is native.
- **Ordinary content packages (levels, UI, ordinary asset containers)
  legitimately report 0 `Class`/`Function`/`State` exports at all** — this
  is expected, not a tool failure. They *reference* classes from the
  core/framework packages via their Import table rather than declaring
  their own; gameplay-logic script content concentrates in a handful of
  packages, not the whole corpus.

**Real limitation, confirmed empirically, not from `-help` text alone**:
`umodel` can *confirm* UnrealScript content exists and quantify it via
`-list`, but **cannot decompile it back to readable source**. Both direct
routes fail on `Class`/`Function`/`State` objects specifically:
`-dump -<platform> -path=<dir> <package> <object>` returns `WARNING:
Unknown class "Class" for object "..."` / `The specified package(s) has no
supported objects.` (its per-object detail views only cover the object
types it renders — meshes, textures, materials, sounds — not script
introspection), and `-export -uc` (`-uc` = "create unreal script when
possible") silently produces **zero output files** for a `Function`/
`Class` target. This matches `-help`'s own "Supported resources for
export" list (`SkeletalMesh`, `MeshAnimation`, `VertMesh`, `StaticMesh`,
`Texture`, `Sounds`, `ScaleForm`, `FaceFX`, `Sound`) — `Class`/`Function`/
`State` are conspicuously absent. For actual bytecode decompilation, the
real tool is a UnrealScript-aware library like **UE Explorer**/**UELib**
(`EliotVU/Unreal-Library`) — **now solved**, confirmed on this exact
project (flower/Drakengard 3): `game-re-tooling/unreal-engine3-uelib.md`.
