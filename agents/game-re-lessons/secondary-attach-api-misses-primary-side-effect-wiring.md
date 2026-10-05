# A session/viewer's secondary "attach another object" method can silently skip the primary method's side-effect wiring

**When it bites:** a stateful session/viewer abstraction (a `MeshSession`,
render-graph controller, or similar) has one original "set the content"
entry point plus a later-added second entry point for compositing extra
content alongside it (e.g. `setModel()` for the main model, `addModel()`
added afterward for a second piece — a head onto a body, an attachment onto
a base mesh). A toggle that visibly and correctly affects content added via
the ORIGINAL entry point (render mode, shading, texture filter, smoothing)
silently does nothing for content added via the SECOND entry point, with no
error, no warning, no crash — the added object renders, just never responds
to any appearance change.

Confirmed on Fire Emblem: Three Houses' composited body+head character
picker (`@seer-project/engine-3d`'s `MeshSession`, `chimera` project):
`setModel()` wired every appearance-refresh function
(`refreshAppearance`/`refreshPolish`/`applyTextureFilter`) to the one
`model` reference it held. `addModel()`, added later specifically so a
second GLB (a head) could be composited alongside the primary one (a body)
in the same scene, only pushed the new object into the Three.js scene graph
— it was never wired into any of those refresh functions at all. The head
rendered correctly at first load, but toggling wireframe/normals-debug/
smooth-shading/anisotropic-filtering affected only the body; the head
stayed fully textured and lit regardless of the selected mode. This went
unnoticed through several sessions of building the compositing feature
because "does the head render" was the only check performed — nobody
toggled a render mode while a composited head was on screen.

**The fix:** replace the single `model` reference with an internal
`trackedModels: Model3D[]` array that BOTH `setModel()` and `addModel()`
push into, then loop every appearance-refresh function over the whole
array instead of the one reference. This is a shared-package fix, not a
host-side workaround, and other consumers of `addModel()` get the fix
automatically once shipped — but see the companion lesson
`per-call-cache-clear-breaks-under-per-item-loop-conversion.md` for a real
regression this exact refactor can introduce if a per-model refresh
function was written assuming it only ever runs once per refresh cycle.

**Generalizable premise-trap:** when a stateful session/viewer abstraction
grows a second "attach content" entry point alongside its original one,
audit EVERY side-effect-wiring hook the original entry point has — not just
whether the new method visibly adds the object to the scene. Grep the
original method's body for every function/array/cache it registers the
model into, and check the new method registers into each of the same ones.
A new entry point added later, under time pressure, for a narrower use case
("just add this second mesh") is very likely to have only gotten the
visible-add part ported.
