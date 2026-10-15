#!/usr/bin/env python3
"""Capture a GoS animation as consecutive PPSSPP GE frame dumps (one dump per rendered frame).

Talks to PPSSPP's WebSocket debugger directly (the MCP round-trip is too slow to keep up).
PPSSPP stalls emulation while it serializes a dump, so back-to-back requests at FULL speed return
consecutive rendered frames (2026-10-15: the 30-vblank isolated □1 spans ~15 dumps -> GoS renders
at 30 fps, 1 dump = 2 vblanks; poses change smoothly dump to dump).

Each dump is then decoded with gedump.py; the skinned, posed Kratos mesh of every frame is the
animation itself (blades and chains included) — no skeleton retargeting needed.

Usage:
    python tools/rip/capture_anim.py --ws ws://127.0.0.1:PORT/debugger --out <dir>
        --frames 60 [--press square@0,square@12,...]

--press: button@dumpIndex — the button is pressed (2 emulated frames) right before dump N.
Outputs <out>/f0000.ppdmp ... and <out>/capture.json (wall times, sizes, sha1 per dump).
Dumps contain game data: keep <out> OUTSIDE the repo (e.g. C:\\mods\\model\\...).
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import time
from pathlib import Path

import websockets


async def call(ws, event: str, **params):
    msg = {"event": event, "ticket": f"t{time.monotonic_ns()}", **params}
    await ws.send(json.dumps(msg))
    while True:
        r = json.loads(await ws.recv())
        if r.get("ticket") == msg["ticket"] or (r.get("event") == event and "ticket" not in r):
            if r.get("event") == "error":
                raise RuntimeError(r)
            return r
        if r.get("event") == "error" and r.get("ticket") == msg["ticket"]:
            raise RuntimeError(r)


def parse_presses(spec: str) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for item in filter(None, (s.strip() for s in spec.split(","))):
        btn, _, idx = item.partition("@")
        out.setdefault(int(idx), []).append(btn)
    return out


async def main_async(args) -> None:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    presses = parse_presses(args.press)
    log = []
    async with websockets.connect(args.ws, max_size=None) as ws:
        for i in range(args.frames):
            for btn in presses.get(i, []):
                await call(ws, "input.buttons.press", button=btn, duration=args.press_frames)
            t0 = time.time()
            r = await call(ws, "gpu.record.dump")
            uri = r.get("uri", "")
            data = base64.b64decode(uri.split(",", 1)[1]) if "," in uri else b""
            p = out / f"f{i:04d}.ppdmp"
            p.write_bytes(data)
            log.append({"i": i, "t": t0, "dt": round(time.time() - t0, 3), "size": len(data),
                        "sha1": hashlib.sha1(data).hexdigest()[:12], "pressed": presses.get(i, [])})
            print(f"{i:4d} {len(data):8d} B  {log[-1]['dt']:.2f}s  {log[-1]['pressed']}", flush=True)
    (out / "capture.json").write_text(json.dumps(log, indent=1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ws", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--press", default="")
    ap.add_argument("--press-frames", type=int, default=2)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
