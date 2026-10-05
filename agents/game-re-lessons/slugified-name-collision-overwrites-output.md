# A filename slugified from a human-readable label can silently collide

**When it bites:** a pipeline derives output filenames or manifest keys from labels, basenames, "extension-stripped" names, or coarse category + fallback names (`se_waveform_0`) instead of a guaranteed-unique id. Also: several pipeline steps derive names from the same source key, or an upsert-by-name manifest merge exists anywhere downstream.

The symptom is always the same and always quiet. The second write overwrites the first, or the manifest upsert drops an entry. Nothing errors and every surviving file looks valid, but it holds the wrong content or the count is short. The root causes differ:
- Labels that differ only by punctuation or case normalise to one slug.
- Two pipeline steps (texture and mesh) derive the same name from one source entry, and each step's local `usedNames` set can't see the other's.
- A basename-only key throws away the directory that made it unique.
- Stripping an "extension" that is really a sequence number (`.002`…`.016`).
- A coarse group label combined with a generic per-item fallback index, repeated across hundreds of source files.

**Check / fix:**
- Build the guaranteed-unique discriminator into the name: an index or id, the asset *type* suffix (`_mesh`/`_texture`) when several steps share a source key, the full relative path with separators replaced (`__`), the full basename with dots replaced rather than truncated, or the source file's own stem (`se_enemy103000_v_waveform_0`). Keep coarse labels as separate `group` fields.
- Assert uniqueness after generation and fail loudly: `len(set(output_paths)) == len(entries)`. Run it across steps, not per step.
- Before trusting a naming scheme at corpus scale, run a dedup check over the real listing: `find … | xargs -n1 basename | sort | uniq -d`.
- Strip an extension only after the corpus confirms it is a shared format suffix, not a numeric or ordinal value unique per file.
- Reconcile counts exactly: compare the pipeline's reported count with the files on disk and with the final manifest entries per category, including after adding a whole new asset type. A clean exit proves nothing.

**Canonical example:** Dragon's Crown (PS3, `vanille`, `tools/shared/acb-music.ts`). About 211 CRI ACB banks produced tracks named `${group}_${t.name}`. All 203 `se_*.acb` banks fell back to `waveform_N`, so they collided across banks with different audio. Stdout reported "12281 tracks", but `manifest.json` held 6421, a nonzero and plausible-looking wrong count with no error.

**Variants:**
- Per-character recolour sheets (project not named in the log): `"GANDALF"` and `"GANDALF'"` both became `gandalf`, and two "Southrons" groups both became `southrons`. Caught by the `len(set(...))` check. The fix was to add the `SAS` index.
- NieR:Automata (`flower`, `build-assets.ts`): `wd1/g10722.dtt` holds a texture and a mesh, both named by `slugName()`. The manifest count didn't grow after a new asset type was added.
- Fire Emblem: Engage (`chimera`, `extract_unity_meshes.py`): a `Path.stem` key over 24,755 bundles had 1,685 duplicate basenames (`bg.bundle`, `acc.bundle` per category). It was caught proactively with `uniq -d`.
- Reunion (Amiga AGA, `methanoid`): `.replace(/\.[^.]+$/,'')` collapsed `ATVEZETO.002–.016` and `RESOUNDS.001–.079`. The pipeline claimed 277 images, there were 264 on disk, and 1 WAV instead of 80.

**History:** 5 recorded instances (recolour-sheet script, flower, chimera, methanoid, vanille): full log in `_archive/slugified-name-collision-overwrites-output.md`.
