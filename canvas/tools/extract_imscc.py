"""One-off: pull the retained Canvas-only media out of the Spring 2026 export.

Run from the repo root with an isolated interpreter:
    python -I canvas/tools/extract_imscc.py eng6819-26spring-0w60-export.imscc

Writes (all gitignored) to canvas/media/:
    interviews/originals/<stem>.mp4      untouched interview videos
    interviews/captions_2026/<stem>.vtt  the original Canvas caption tracks
    pdfs/<name>.pdf                      Canvas-only reading PDFs
    manifest.json                        sha256 / size / duration of every file
Nothing else from the export is retained (lectures, exercise videos, legacy pages).
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "canvas" / "media"
UM = "web_resources/Uploaded Media/"
WR = "web_resources/"

# stem -> (zip entry, guest). Stems match the exercise files they belong to.
INTERVIEWS = {
    "sullivan":  (UM + "CritMakingSullivan.mp4",   "Anne Sullivan"),
    "skains":    (UM + "CritMakingLyleSkains.mp4", "Lyle Skains"),
    "fan":       (UM + "CritMakingFan.mp4",        "Lai-Tze Fan"),
    "cox":       (UM + "CritMakingDanCox.mp4",     "Dan Cox"),
    "duvvoori":  (UM + "CritMakingDuvvoori.mp4",   "Kavi Duvvoori"),
    # the export's filename predates the guest's name change, so it is located by
    # its exact size instead (see resolve_by_size); use Quinn Daedal everywhere
    "daedal":    ("size:822716685", "Quinn Daedal"),
    "flores":    (WR + "CritMakingFlores.mp4",     "Leonardo Flores"),
    "whalen":    (UM + "CritMakingWhalen_1.mp4",   "Zach Whalen"),
    "bessette":  (UM + "CritMakingLee-2.mp4",      "Lee Skallerup Bessette"),
    "barnes":    (UM + "CritMakingBarnes.mp4",     "Nikki Fragala Barnes"),
}
# captions whose videos are missing from the export
ORPHAN_CAPTIONS = {
    "bahl": WR + "CritMakingBahl.mp4.srt",
    "milligan": WR + "CritMakingMilligan.mp4.srt",
}
PDFS = [WR + n for n in (
    "RattoCriticalMaking.pdf", "HertzMakingCritMaking.pdf",
    "HarrerRadicalJamming.pdf", "DIgnazioKleinFeministData.pdf",
    "LovelessIntro.pdf", "LovelessConclusion.pdf", "FAN - ESC masks.pdf")]
CHAPTER_DIR = WR + "Critical Making Chapters/"


def sha256_stream(fh) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: fh.read(1 << 20), b""):
        h.update(chunk)
    return h.hexdigest()


def copy_entry(z: zipfile.ZipFile, name: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    info = z.getinfo(name)
    if dest.exists() and dest.stat().st_size == info.file_size:
        with open(dest, "rb") as fh:  # already extracted by an earlier run
            return {"source": name, "sha256": sha256_stream(fh),
                    "bytes": info.file_size}
    h = hashlib.sha256()
    with z.open(name) as src, open(dest, "wb") as out:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
            out.write(chunk)
    info = z.getinfo(name)
    if dest.stat().st_size != info.file_size:
        raise SystemExit(f"size mismatch for {name}")
    return {"source": name, "sha256": h.hexdigest(), "bytes": info.file_size}


def resolve_by_size(z: zipfile.ZipFile, size: int) -> str:
    matches = [i.filename for i in z.infolist()
               if i.filename.endswith(".mp4") and i.file_size == size]
    if len(matches) != 1:
        raise SystemExit(f"expected one mp4 of {size} bytes, found {len(matches)}")
    return matches[0]


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True).stdout
    return round(float(out.strip()), 2)


def caption_tracks(z: zipfile.ZipFile) -> dict[str, str]:
    """Map export file href -> VTT text using media_tracks.xml + the manifest."""
    ns = {"m": "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"}
    man = ET.fromstring(z.read("imsmanifest.xml"))
    href = {}
    for res in man.iter():
        if res.tag.endswith("resource") and res.get("href"):
            href[res.get("identifier")] = res.get("href")
    tracks = {}
    mt = ET.fromstring(z.read("course_settings/media_tracks.xml"))
    for media in mt:
        target = href.get(media.get("identifierref"))
        for track in media:
            if target and track.get("locale", "en") == "en":
                tracks[target] = track.text or ""
    return tracks


def main(archive: str) -> None:
    manifest = {"interviews": {}, "orphan_captions": {}, "pdfs": {}}
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        tracks = caption_tracks(z)
        for stem, (entry, guest) in INTERVIEWS.items():
            if entry.startswith("size:"):
                entry = resolve_by_size(z, int(entry[5:]))
            if entry not in names:
                raise SystemExit(f"missing interview entry {entry}")
            dest = MEDIA / "interviews" / "originals" / f"{stem}.mp4"
            rec = copy_entry(z, entry, dest)
            rec["guest"] = guest
            rec["duration_s"] = duration(dest)
            vtt = tracks.get(entry)
            if vtt:
                cap = MEDIA / "interviews" / "captions_2026" / f"{stem}.vtt"
                cap.parent.mkdir(parents=True, exist_ok=True)
                cap.write_text(vtt, encoding="utf-8")
                rec["captions_2026"] = cap.relative_to(MEDIA).as_posix()
            else:
                rec["captions_2026"] = None
            manifest["interviews"][stem] = rec
            print(f"{stem:11} {rec['duration_s']:8.1f}s captions={'yes' if vtt else 'NO'}")
        for stem, entry in ORPHAN_CAPTIONS.items():
            dest = MEDIA / "interviews" / "captions_2026" / f"{stem}.srt"
            manifest["orphan_captions"][stem] = copy_entry(z, entry, dest)
        chapters = sorted(n for n in names
                          if n.startswith(CHAPTER_DIR) and n.endswith(".pdf"))
        for entry in PDFS + chapters:
            dest = MEDIA / "pdfs" / Path(entry).name
            manifest["pdfs"][dest.name] = copy_entry(z, entry, dest)
    (MEDIA / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                         encoding="utf-8")
    print(f"pdfs: {len(manifest['pdfs'])}; manifest written")


if __name__ == "__main__":
    main(sys.argv[1])
