"""Find on-screen text in a video with OCR and emit blur regions.

    python -I canvas/tools/find_text.py <video.mp4> <regex> <out.json> [--fps 1]

Samples frames at --fps, OCRs each, and records every text box whose text matches
<regex> (case-insensitive). Adjacent detections of the same region are merged into
intervals padded by one sample period on each side, written as
[{"start": s, "end": e, "box": [x, y, w, h], "text": "..."}] for blur.py.
"""
import json
import re
import subprocess
import sys

import numpy as np
from rapidocr_onnxruntime import RapidOCR


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True).stdout.strip()
    w, h = (int(v) for v in out.split(",")[:2])
    return w, h


def frames(path, fps, w, h):
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps}",
         "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    size = w * h * 3
    i = 0
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield i / fps, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        i += 1
    proc.wait()


def overlaps(a, b, slack=12):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax > bx + bw + slack or bx > ax + aw + slack or
                ay > by + bh + slack or by > ay + ah + slack)


def main(path, pattern, out, fps=1.0):
    rx = re.compile(pattern, re.I)
    w, h = probe(path)
    ocr = RapidOCR()
    hits = []
    prev_small, prev_result = None, None
    for t, img in frames(path, fps, w, h):
        # reuse the last OCR result when the frame is essentially unchanged
        small = img[::8, ::8].astype(np.int16)
        if prev_small is not None and np.abs(small - prev_small).mean() < 1.5:
            result = prev_result
        else:
            result, _ = ocr(img)
            prev_small, prev_result = small, result
        for box, text, _score in result or []:
            if rx.search(text.replace(" ", "")) or rx.search(text):
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x, y = int(min(xs)), int(min(ys))
                hits.append((t, [x, y, int(max(xs)) - x, int(max(ys)) - y], text))
        if int(t) % 120 == 0:
            print(f"{t:7.0f}s  hits so far: {len(hits)}", flush=True)
    period = 1.0 / fps
    regions = []
    for t, box, text in hits:
        for r in regions:
            if overlaps(r["box"], box) and t - r["end"] <= 2 * period + 1e-6:
                r["end"] = t
                x = min(r["box"][0], box[0]); y = min(r["box"][1], box[1])
                x2 = max(r["box"][0] + r["box"][2], box[0] + box[2])
                y2 = max(r["box"][1] + r["box"][3], box[1] + box[3])
                r["box"] = [x, y, x2 - x, y2 - y]
                break
        else:
            regions.append({"start": t, "end": t, "box": box, "text": text})
    for r in regions:  # pad in time and space
        r["start"] = max(0.0, r["start"] - period)
        r["end"] = r["end"] + period
        x, y, bw, bh = r["box"]
        r["box"] = [max(0, x - 6), max(0, y - 4), bw + 12, bh + 8]
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(regions, fh, indent=1)
    print(f"{len(hits)} hits -> {len(regions)} regions -> {out}")


if __name__ == "__main__":
    args = sys.argv[1:]
    fps = 1.0
    if "--fps" in args:
        i = args.index("--fps")
        fps = float(args[i + 1])
        del args[i:i + 2]
    main(*args, fps=fps)
