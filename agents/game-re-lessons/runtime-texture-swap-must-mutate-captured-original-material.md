# A runtime texture swap on a loaded glTF model must mutate the ORIGINAL material object in place, not replace it — or a render-mode toggle silently reverts it

**When it bites:** building a runtime "swap this mesh's baseColor texture"
feature (a per-character recolor, a palette override, any post-load
material patch) on top of a glTF viewer/engine that also offers render-mode
toggles (wireframe/flat-shaded/point-cloud/"textured") which restore a
captured "original material" when switching back to textured mode — using
the seer framework's shared `@seer-project/engine-3d` package specifically,
or any similarly-shaped glTF viewer abstraction.

## What happened (and didn't go wrong, because of this)

`@seer-project/engine-3d`'s `toModel3D()` (`gltf.ts`) captures each mesh's
material into `model.repr.originalMaterials`, a `Map<Mesh, Material>` keyed
by the material **object reference** at load time — not a deep clone or
snapshot of its properties. `render-modes.ts`'s `'textured'` mode restore
path later does `child.material = model.repr.originalMaterials.get(child)`,
reinstating whatever object is stored there.

Building a class-body palette-variant recolor for Fire Emblem: Three
Houses (`chimera`) needed to override a loaded `Model3D`'s baseColor
texture at runtime, after `loadGltfModel()` already ran (so
`originalMaterials` was already populated). The correct approach — proven
to work with zero changes to the shared `engine-3d` package — was to
traverse `model.object`'s meshes and do `material.map = newTexture;
material.needsUpdate = true` **on the SAME material object already in the
map**, rather than constructing and assigning a brand-new
`MeshStandardMaterial` instance to `mesh.material`. Because the map stores
an object reference, mutating that object's `.map` in place means a later
render-mode toggle back to `'textured'` restores an object whose `.map` is
already the swapped texture — the recolor survives automatically. Had a
new material object been assigned instead, the map would still point at
the OLD (pre-swap) material, and toggling render modes would silently
revert the visible recolor with no error, no warning, and no obvious cause
short of tracing through `render-modes.ts`'s restore logic.

## The fix / rule

When patching a loaded `Model3D`'s appearance at runtime in a system with
a "capture original material, restore on mode toggle" convention: always
mutate the material object already referenced by that capture, never
replace `mesh.material` with a new object. Dispose the OLD texture (not
the material) to avoid a GPU memory leak, and set `needsUpdate = true` on
both the texture and the material so the renderer picks up the change.

## Generalization

Any host code sitting on top of a shared 3D-asset abstraction that keeps
its own "restore-to-original" bookkeeping by object reference (not by deep
value) has this trap for ANY runtime patch to that same asset — not just
texture swaps. Before writing a runtime override, check whether the
abstraction captures "original" state by reference or by value; a
by-reference capture requires in-place mutation for the patch to survive
whatever restore path consumes that capture later.
