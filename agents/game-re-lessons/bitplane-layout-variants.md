# Sequential-planar vs row-interleaved vs plane-major bitplanes

**When it bites:** a planar bitmap decode "matches the documented format" but the rendered image is garbage or scrambled.

All three layouts "match the documented format" on paper; only one actually
renders correctly for a given file. Test the layouts empirically before
concluding the data itself is corrupt or misidentified.
