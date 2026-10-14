"""Per-frame metrics from a PPSSPP frame dump (Phase 2 frame-data oracle).

PPSSPP "File > Record > Dump frames" (menu id 40165, FFV1 = 40166) writes one video frame
per *emulated* vblank, so frame indices are game-time exact even when the emulator runs
slower than real time while encoding. This script turns such a dump into a per-frame table:

    frame  motion  fire  fire_cx  fire_cy

- motion: mean abs grey-level delta vs the previous frame inside --crop (Kratos region).
          Baseline (idle + rain) is ~1.5-2.5; an animation start shows as a sustained rise.
- fire:   count of "Blades of Athena trail" pixels (hot orange) below the HUD band, at
          480x272. A swing's visible trail window = fire above --fire-threshold.

Then `--segments` prints contiguous trail windows. Interpretation (startup/active/recovery)
is still done by a human against a contact sheet -- see
context/artifacts/2026-10-15/phase2-blades-framedata-FINAL.md.

Stdlib only; needs ffmpeg on PATH or --ffmpeg. Runs on the user's own dump; no game data
is stored in the repo.
"""
import argparse
import shutil
import subprocess
import sys

W, H = 480, 272          # analysis resolution (PSP native)
HUD_BAND = 70            # rows excluded from the fire count (health/magic HUD, top-left)


def frames(ffmpeg, src, vf, fmt, size):
    p = subprocess.Popen([ffmpeg, "-v", "error", "-i", src, "-vf", vf, "-f", "rawvideo",
                          "-pix_fmt", fmt, "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(size)
        if len(b) < size:
            break
        yield b
    p.wait()


def is_fire(r, g, b):
    return r > 190 and 60 < g < 210 and b < 110 and r - b > 120


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "ffmpeg")
    ap.add_argument("--crop", default="480:300:240:200",
                    help="ffmpeg crop w:h:x:y (source 960x544) around Kratos for the motion metric")
    ap.add_argument("--fire-threshold", type=int, default=70)
    ap.add_argument("--segments", action="store_true", help="print trail windows instead of the table")
    a = ap.parse_args()

    mw, mh = 240, 136
    motion = []
    prev = None
    for b in frames(a.ffmpeg, a.video, f"crop={a.crop},scale={mw}:{mh},format=gray", "gray", mw * mh):
        motion.append(sum(abs(x - y) for x, y in zip(b, prev)) / (mw * mh) if prev else 0.0)
        prev = b

    fire = []
    for b in frames(a.ffmpeg, a.video, f"scale={W}:{H}", "rgb24", W * H * 3):
        n = sx = sy = 0
        for y in range(HUD_BAND, H):
            row = y * W * 3
            for x in range(W):
                i = row + x * 3
                if is_fire(b[i], b[i + 1], b[i + 2]):
                    n += 1; sx += x; sy += y
        fire.append((n, sx // n if n else -1, sy // n if n else -1))

    if a.segments:
        start = last = None
        for i, (n, _, _) in enumerate(fire):
            if n >= a.fire_threshold:
                if start is None:
                    start = i
                last = i
            elif start is not None and i - last > 1:
                print(f"{start}-{last} ({last - start + 1}f)")
                start = None
        if start is not None:
            print(f"{start}-{last} ({last - start + 1}f)")
        return

    out = sys.stdout
    out.write("frame\tmotion\tfire\tfire_cx\tfire_cy\n")
    for i, (m, (n, cx, cy)) in enumerate(zip(motion, fire)):
        out.write(f"{i}\t{m:.2f}\t{n}\t{cx}\t{cy}\n")


if __name__ == "__main__":
    main()
