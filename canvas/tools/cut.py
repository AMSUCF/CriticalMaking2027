"""Apply time cuts and on-screen redactions to interview videos.

    python -I canvas/tools/cut.py [stem ...]

Reads canvas/media/interviews/cuts.yml:

    daedal:
      cuts:                       # removed from the video (original timeline, seconds)
        - {start: 61.2, end: 74.9, reason: "...", excerpt: "..."}
      redact: edits/daedal_blur.json   # optional, from find_text.py
      label: {box: [x, y, w, h], text: "Quinn Daedal", start: 0, end: 300}  # optional list

Redactions (on the original timeline, before cutting):
  * `redact` regions are Gaussian-blurred while visible;
  * `label` entries cover a Zoom name label with a dark box and redraw `text` in it.
Then cut segments are dropped with select/aselect (frame-accurate re-encode).
Stems with no cuts and no redactions are copied unchanged.
Writes interviews/edited/<stem>.mp4 and records durations in cuts_applied.json.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

MEDIA = Path(__file__).resolve().parents[1] / "media" / "interviews"
FONT = "C\\:/Windows/Fonts/arialbd.ttf"


def duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def between(spans) -> str:
    return "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in spans)


def video_filter(redact, labels) -> str:
    chain, cur, n = [], "[0:v]", 0
    for r in redact:
        x, y, w, h = r["box"]
        sigma = max(10, h // 2)
        chain.append(f"{cur}split[m{n}][c{n}]")
        chain.append(f"[c{n}]crop={w}:{h}:{x}:{y},gblur=sigma={sigma}:steps=3[b{n}]")
        chain.append(f"[m{n}][b{n}]overlay={x}:{y}:"
                     f"enable='between(t,{r['start']:.3f},{r['end']:.3f})'[v{n}]")
        cur, n = f"[v{n}]", n + 1
    for lab in labels:
        x, y, w, h = lab["box"]
        en = f"between(t,{lab.get('start', 0):.3f},{lab.get('end', 1e9):.3f})"
        size = max(10, int(h * 0.62))
        chain.append(f"{cur}drawbox=x={x}:y={y}:w={w}:h={h}:color=0x1f1f1f:t=fill:"
                     f"enable='{en}',drawtext=fontfile='{FONT}':text='{lab['text']}':"
                     f"fontcolor=white:fontsize={size}:x={x + 6}:y={y}+({h}-th)/2:"
                     f"enable='{en}'[v{n}]")
        cur, n = f"[v{n}]", n + 1
    return ";".join(chain), cur


def probe_video(p: Path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,avg_frame_rate", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout.strip()
    w, h, rate = out.split(",")[:3]
    num, den = rate.split("/")
    return int(w), int(h), float(num) / float(den)


def label_image(lab):
    """Dark box with white text, rendered once with Pillow (BGR array)."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    x, y, w, h = lab["box"]
    img = Image.new("RGB", (w, h), (31, 31, 31))
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", max(10, int(h * 0.55)))
    draw = ImageDraw.Draw(img)
    top = (h - (font.getbbox(lab["text"])[3] - font.getbbox(lab["text"])[1])) // 2
    draw.text((8, top - font.getbbox(lab["text"])[1]), lab["text"], font=font, fill=(255, 255, 255))
    return np.array(img)[:, :, ::-1].copy()


def redact_pass(src: Path, dst: Path, redact, labels) -> None:
    """Frame-by-frame redaction (only active regions are touched), audio copied."""
    import cv2
    import numpy as np
    w, h, fps = probe_video(src)
    rate = f"{fps:.6f}"
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-an", "-fps_mode", "cfr",
                            "-r", rate, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{w}x{h}", "-r", rate, "-i", "-", "-i", str(src),
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "fast",
                            "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "copy", str(dst)],
                           stdin=subprocess.PIPE)
    imgs = [label_image(lab) for lab in labels]
    size, i = w * h * 3, 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()
        t = i / fps
        for r in redact:
            if r["start"] <= t <= r["end"]:
                x, y, bw, bh = r["box"]
                x2, y2 = min(w, x + bw), min(h, y + bh)
                roi = frame[y:y2, x:x2]
                if roi.size:
                    sigma = r.get("sigma") or max(12, bh // 2)  # large areas: set sigma
                    roi = cv2.GaussianBlur(roi, (0, 0), sigma)
                    frame[y:y2, x:x2] = cv2.GaussianBlur(roi, (0, 0), sigma)
        for lab, img in zip(labels, imgs):
            if lab.get("start", 0) <= t <= lab.get("end", 1e9):
                x, y, bw, bh = lab["box"]
                frame[y:y + bh, x:x + bw] = img[: h - y, : w - x]
        enc.stdin.write(frame.tobytes())
        i += 1
    enc.stdin.close()
    dec.wait()
    if enc.wait() != 0:
        raise SystemExit(f"encode failed for {dst}")


def process(stem: str, spec: dict) -> dict:
    src = MEDIA / "originals" / f"{stem}.mp4"
    dst = MEDIA / "edited" / f"{stem}.mp4"
    dst.parent.mkdir(parents=True, exist_ok=True)
    cuts = [(c["start"], c["end"]) for c in spec.get("cuts") or []]
    redact = json.loads((MEDIA / spec["redact"]).read_text()) if spec.get("redact") else []
    redact += spec.get("redact_inline") or []  # hand-placed blur regions
    labels = spec.get("label") or []
    if isinstance(labels, dict):
        labels = [labels]
    before = duration(src)
    if not cuts and not redact and not labels:
        shutil.copy2(src, dst)
    else:
        if redact or labels:
            redacted = MEDIA / "edited" / f"{stem}.redacted.mp4"
            redact_pass(src, redacted, redact, labels)
            src, redact, labels = redacted, [], []
        parts, vout = video_filter(redact, labels)
        graph = [parts] if parts else []
        if cuts:
            keep = f"not({between(cuts)})"
            graph.append(f"{vout}select='{keep}',setpts=N/FRAME_RATE/TB[vo]")
            graph.append(f"[0:a]aselect='{keep}',asetpts=N/SR/TB[ao]")
            vmap, amap = "[vo]", "[ao]"
        else:
            vmap, amap = vout, "0:a"
            if vout == "[0:v]":
                vmap = "0:v"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src)]
        if graph:
            cmd += ["-filter_complex", ";".join(graph)]
        cmd += ["-map", vmap, "-map", amap, "-c:v", "libx264", "-preset", "fast",
                "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                "-movflags", "+faststart", str(dst)]
        subprocess.run(cmd, check=True)
    after = duration(dst)
    removed = sum(e - s for s, e in cuts)
    print(f"{stem:10} {before:8.1f}s -> {after:8.1f}s  (cut {removed:.1f}s, "
          f"{len(redact)} blurs, {len(labels)} labels)", flush=True)
    return {"before": before, "after": after, "cut_seconds": removed,
            "cuts": len(cuts), "blurs": len(redact), "labels": len(labels)}


def main(stems):
    spec = yaml.safe_load((MEDIA / "cuts.yml").read_text(encoding="utf-8")) or {}
    log_path = MEDIA / "cuts_applied.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    for stem in stems or sorted(p.stem for p in (MEDIA / "originals").glob("*.mp4")):
        log[stem] = process(stem, spec.get(stem) or {})
        log_path.write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
