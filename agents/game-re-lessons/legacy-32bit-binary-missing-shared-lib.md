# A prebuilt 32-bit RE tool binary with a missing/obsolete shared lib is usually a 1-minute fix, not a real blocker

**When it bites:** a community reverse-engineering tool ships a prebuilt Linux
binary that fails to launch with `error while loading shared libraries:
lib*.so.N: cannot open shared object file`, especially when the missing
library is 32-bit-only or an obsolete soname (`libpng12.so.0`, a bare
`libSDL2-2.0.so.0` with no matching distro package) — before writing off the
tool as "not packaged for this environment" and falling back to a slower
from-scratch approach.

Confirmed on Gildor's UModel/UEViewer (`umodel`, a prebuilt 32-bit ELF
committed directly in the project's own repo) on a 64-bit CachyOS/Arch
desktop: it needed `libpng12.so.0` (soname retired industry-wide well over a
decade ago, no distro ships it even via multilib) and `libSDL2-2.0.so.0`
(present as 64-bit only; no 32-bit build available prebuilt). Both built
from source as 32-bit shared libraries in well under a minute combined,
using nothing but a working multilib `gcc -m32` and the ordinary 32-bit
X11/Mesa/ALSA runtime libraries a Steam/Proton gaming setup already has
installed (`lib32-libx11`, `lib32-libxext`, `lib32-libxrandr`,
`lib32-libxcursor`, `lib32-libxfixes`, `lib32-libxi`, `lib32-libxinerama`,
`lib32-libxss`, `lib32-libxkbcommon`, `lib32-mesa` — all of which a
CachyOS/Arch multilib gaming rig had pre-installed): `./configure
--host=i686-pc-linux-gnu CFLAGS="-m32 ..." LDFLAGS="-m32 -L/usr/lib32"` then
`make`, for both libpng 1.2.59 and SDL2 2.28.5 (with `--disable-pipewire` to
dodge a header-version mismatch between the system's newer 64-bit pipewire
dev headers and SDL 2.28's pipewire backend — every other SDL backend is
`dlopen`'d at runtime, not link-time, so disabling one compile-time backend
has no effect on runtime capability). Set `LD_LIBRARY_PATH` to the two
freshly-built `.so` directories and the binary launched and worked
perfectly. No root/sudo needed — everything builds and runs from a user-
writable cache directory. Wrap this in a small idempotent setup script
(clone/download once, build once, skip on rebuild) rather than solving it
by hand each session.

**The generalizable move**: before concluding a prebuilt tool "isn't
packaged for this environment" or planning a slower from-scratch
reimplementation to route around it, run `ldd` on the binary, and for each
`=> not found` line, check whether it's a small, self-contained library
(image codec, audio/windowing shim) buildable from public source in
isolation — it usually is, and the isolated build is a few minutes at most
even when the *whole* tool's own build system (GUI toolkit, full SDK) would
be a much bigger undertaking to reproduce.

Related: `romhacking-community-tools-first.md` (search for the tool at all
before assuming you need to hand-derive the format) — this lesson is what
to do *after* you've found the right tool and it merely won't launch.

## A full-RELRO/`BIND_NOW`-linked binary needs every imported symbol resolved at load time, even ones it never calls in your usage mode

Don't assume a library dependency is "optional in headless mode" just
because the functionality it backs (a GUI toolkit, in `umodel`'s case) is
never exercised by the CLI flags you're using. Check with `readelf -d
<binary> | grep -i bind_now`: if `BIND_NOW`/`FLAGS_1: NOW` is set, the
dynamic linker resolves *every* symbol the binary imports from *every*
`DT_NEEDED` library at process start — not lazily, on first call — so a
stub/dummy replacement library that only defines the symbols your usage
path happens to reach will still fail to load. Confirmed on `umodel`: its
`-export`/`-list`/`-pkginfo`/`-dump` CLI commands never touch SDL2 at
runtime (no window, no GL context, no display needed), but the binary
still requires a real, fully-symbol-complete `libSDL2-2.0.so.0` to be
present and loadable — building the *real* library (see above) was
therefore the only viable fix; a hand-written stub `.so` exporting a
handful of the "obviously needed" symbols would not have worked.
