# Directory entries sharing a data offset can be aliases

**When it bites:** a frame-splitting theory for a sprite/image directory is producing an implausibly large frame count.

Two directory entries sharing a data offset can be aliases (e.g. a
normal/mirrored pair of one image), not sub-frames to split apart. A
plausible even-height frame-splitting theory once produced 495 phantom
"frames" from 204 real sprites. Verify with a structural invariant before
splitting anything.
