# `@seer-project/engine-3d` consumers need their own `@types/three` devDependency

**When it bites:** wiring `@seer-project/engine-3d` (or importing `three`
directly) into a project for the first time — `npx tsc --noEmit` fails with
`Could not find a declaration file for module 'three'` even though `three`
itself installs and resolves fine at runtime, and even though
`@seer-project/engine-3d`'s own `package.json` lists `three` as a
dependency.

Some modern `three` npm releases (confirmed on `0.185.1`) don't bundle
their own `.d.ts` files or a `"types"` field in `package.json` — TypeScript
support is expected to come from the separate `@types/three` package. Since
`@seer-project/engine-3d` only lists `@types/three` as a **devDependency**
(needed to build the package itself, not exposed transitively to
consumers) and `three` as a **peerDependency**, a project that adds
`@seer-project/engine-3d` + `three` to its own `package.json` and runs
`npm install` gets a project that runs correctly in the browser but fails
`tsc` — nothing in the dependency chain pulls in `@types/three`
automatically.

**The fix**: add `@types/three` (matching the version range engine-3d's own
`package.json` devDependencies pins) as a `devDependency` of the consuming
project directly, then `npm install` — confirmed this alone was sufficient
to make `npx tsc --noEmit` clean with no other changes (Valkyrie Profile
project, wiring engine-3d's polygon + glTF paths into both a PSX and a PS2
viewer).
