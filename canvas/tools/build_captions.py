"""Build WebVTT captions from word-timestamped transcripts of the edited videos.

    python -I canvas/tools/build_captions.py [stem ...]

Reads  canvas/media/interviews/transcripts_edited/<stem>.json  (transcribe.py --captions)
       canvas/media/interviews/caption_fixes.yml   {global: {from: to}, <stem>: {from: to}}
Writes canvas/media/interviews/captions/<stem>.vtt and validates every file.

Fixes match whole-word sequences case-insensitively, ignoring punctuation, and keep
the timing of the words they replace. Filler words (um, uh, ...) are dropped.
Cues: at most 2 lines of 42 characters, 1-7 seconds, broken at sentence ends or pauses.
"""
import json
import re
import sys
from pathlib import Path

import yaml

MEDIA = Path(__file__).resolve().parents[1] / "media" / "interviews"
FILLERS = {"um", "uh", "uhm", "umm", "erm", "hmm", "mm", "mhm", "ah"}
LINE, MAX_CHARS, MAX_DUR, MIN_DUR, GAP = 42, 84, 7.0, 1.0, 0.8


def norm(w: str) -> str:
    return re.sub(r"[^\w'-]", "", w.lower())


MAX_WORD = 2.0
ABBREV = {"dr.", "mr.", "mrs.", "ms.", "prof.", "st.", "vs.", "e.g.", "i.e.", "etc.", "no."}


def sentence_end(word: str) -> bool:
    return bool(re.search(r"[.?!]$", word)) and word.lower() not in ABBREV


def original_segments(stem):
    """Unconditioned transcript of the ORIGINAL video, mapped onto the edited
    timeline through cuts.yml (words inside a cut are dropped, later ones shifted)."""
    spec = yaml.safe_load((MEDIA / "cuts.yml").read_text(encoding="utf-8")) or {}
    cuts = sorted((c["start"], c["end"]) for c in (spec.get(stem) or {}).get("cuts") or [])
    d = json.loads((MEDIA / "transcripts_original" / f"{stem}.json").read_text(encoding="utf-8"))
    segs = []
    for s in d["segments"]:
        ws = []
        for w in s["words"]:
            mid = (w["start"] + w["end"]) / 2
            if not w["word"].strip() or any(a <= mid < b for a, b in cuts):
                continue
            shift = sum(b - a for a, b in cuts if b <= mid)
            ws.append({"start": w["start"] - shift, "end": w["end"] - shift,
                       "word": w["word"].strip()})
        if ws:
            segs.append(ws)
    return segs


def similarity(a, b):
    from collections import Counter
    ca, cb = Counter(norm(w["word"]) for w in a), Counter(norm(w["word"]) for w in b)
    if not ca or not cb:
        return 0.0
    return sum((ca & cb).values()) / max(sum(ca.values()), sum(cb.values()))


def cross_checked(stem, new):
    """Keep the punctuated caption-pass words only where they agree with the
    original pass; elsewhere (hallucination, drift) use the original words.
    New words falling in no original segment (silence) are dropped."""
    segs = original_segments(stem)
    bounds = [(segs[i][-1]["end"] + segs[i + 1][0]["start"]) / 2 for i in range(len(segs) - 1)]
    buckets = [[] for _ in segs]
    j = 0
    for w in new:
        mid = (w["start"] + w["end"]) / 2
        while j < len(bounds) and mid >= bounds[j]:
            j += 1
        if segs[j][0]["start"] - 1.0 <= mid <= segs[j][-1]["end"] + 1.0:
            buckets[j].append(w)
    out, replaced = [], 0
    for seg, got in zip(segs, buckets):
        if similarity(seg, got) >= 0.6:
            out.extend(got)
        else:
            out.extend(dict(w) for w in seg)
            replaced += 1
    return out, replaced, len(segs)


def load_words(stem):
    d = json.loads((MEDIA / "transcripts_edited" / f"{stem}.json").read_text(encoding="utf-8"))
    raw = [{"start": w["start"], "end": w["end"], "word": w["word"].strip()}
           for s in d["segments"] for w in s["words"] if w["word"].strip()]
    raw, replaced, total = cross_checked(stem, raw)
    print(f"  {stem}: {replaced}/{total} segments taken from the original pass")
    words = []
    for w in raw:
        if True:
            start, end = w["start"], w["end"]
            if end - start > MAX_WORD:  # Whisper stretches words across pauses
                start = end - MAX_WORD
            if words and start < words[-1]["end"]:
                start = words[-1]["end"]
            end = max(end, start + 0.05)
            words.append({"start": start, "end": end, "word": w["word"].strip()})
    return words


def apply_fixes(words, fixes):
    rules = sorted(((k.split(), v) for k, v in fixes.items()), key=lambda r: -len(r[0]))
    out, i = [], 0
    while i < len(words):
        for src, dst in rules:
            n = len(src)
            seg = words[i:i + n]
            if len(seg) == n and [norm(w["word"]) for w in seg] == [norm(s) for s in src]:
                tail = re.search(r"[^\w'-]+$", seg[-1]["word"])
                tail = tail.group(0) if tail else ""
                text = dst if dst.endswith(tail) else dst + tail
                out.append({"start": seg[0]["start"], "end": seg[-1]["end"], "word": text})
                i += n
                break
        else:
            out.append(words[i])
            i += 1
    return out


def clean(words):
    kept = []
    for w in words:
        # "non" + "-english", "it" + "'s", "D" + "&D", "3" + ".0"
        if kept and re.match(r"^([-'’&]\w|\.\d)", w["word"]):
            kept[-1]["word"] += w["word"]
            kept[-1]["end"] = w["end"]
            continue
        if norm(w["word"]) in FILLERS:
            # carry trailing punctuation onto the previous word
            tail = re.search(r"[.?!]$", w["word"])
            if tail and kept and not re.search(r"[.?!,]$", kept[-1]["word"]):
                kept[-1]["word"] += tail.group(0)
            continue
        if w["word"] == "i":
            w["word"] = "I"
        w["word"] = re.sub(r"^i'", "I'", w["word"])
        kept.append(w)
    sentence_start = True
    for w in kept:  # sentence casing
        if sentence_start and w["word"][:1].islower() and "@" not in w["word"]:
            w["word"] = w["word"][0].upper() + w["word"][1:]
        sentence_start = sentence_end(w["word"])
    return kept


def cues_from(words):
    cues, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["word"] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        dur = cur[-1]["end"] - cur[0]["start"]
        ends_sentence = sentence_end(w["word"])
        too_long = nxt and (not fits(text + " " + nxt["word"])
                            or nxt["end"] - cur[0]["start"] > MAX_DUR)
        pause = nxt and nxt["start"] - w["end"] > GAP
        if (nxt is None or too_long or pause
                or (ends_sentence and len(text) >= 30)):
            cues.append(cur)
            cur = []
    return cues


def fits(text):
    try:
        wrap(text)
        return True
    except ValueError:
        return False


def wrap(text):
    if len(text) <= LINE:
        return text
    words = text.split()
    best, best_score = None, None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        if len(a) <= LINE and len(b) <= LINE:
            score = abs(len(a) - len(b))
            if best_score is None or score < best_score:
                best, best_score = (a, b), score
    if best is None:
        raise ValueError(f"cannot wrap: {text}")
    return "\n".join(best)


def stamp(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def build(stem, fixes):
    words = clean(apply_fixes(load_words(stem), fixes))
    groups = cues_from(words)
    out = ["WEBVTT", ""]
    timed = []
    for g in groups:
        timed.append([g[0]["start"], g[-1]["end"], " ".join(w["word"] for w in g)])
    for i, c in enumerate(timed):  # monotonic, minimum and maximum duration
        if i and c[0] < timed[i - 1][1]:
            c[0] = timed[i - 1][1]
        c[1] = min(max(c[1], c[0] + 0.3), c[0] + MAX_DUR)
        limit = timed[i + 1][0] if i + 1 < len(timed) else c[1] + MIN_DUR
        if c[1] - c[0] < MIN_DUR:
            c[1] = max(c[1], min(c[0] + MIN_DUR, limit))
    for n, (s, e, text) in enumerate(timed, 1):
        out += [str(n), f"{stamp(s)} --> {stamp(e)}", wrap(text), ""]
    dest = MEDIA / "captions" / f"{stem}.vtt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out), encoding="utf-8")
    return dest


def validate(path):
    problems, last_end = [], 0.0
    blocks = path.read_text(encoding="utf-8").strip().split("\n\n")[1:]
    for b in blocks:
        lines = b.split("\n")
        s, e = (sum(float(x) * 60 ** (2 - i) for i, x in enumerate(p.split(":")))
                for p in lines[1].split(" --> "))
        text = lines[2:]
        if s < last_end - 1e-6:
            problems.append(f"overlap at cue {lines[0]}")
        if e <= s:
            problems.append(f"non-positive duration at cue {lines[0]}")
        if e - s > MAX_DUR + 0.5:
            problems.append(f"long cue {lines[0]} ({e - s:.1f}s)")
        if len(text) > 2 or any(len(t) > LINE for t in text):
            problems.append(f"layout at cue {lines[0]}")
        last_end = e
    return len(blocks), problems


def main(stems):
    fixes_all = yaml.safe_load((MEDIA / "caption_fixes.yml").read_text(encoding="utf-8")) or {}
    stems = stems or sorted(p.stem for p in (MEDIA / "transcripts_edited").glob("*.json"))
    bad = False
    for stem in stems:
        fixes = {**(fixes_all.get("global") or {}), **(fixes_all.get(stem) or {})}
        path = build(stem, fixes)
        n, problems = validate(path)
        bad |= bool(problems)
        print(f"{stem:10} {n:5d} cues  {'OK' if not problems else problems[:5]}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
