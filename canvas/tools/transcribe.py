"""Transcribe interview videos with faster-whisper (word timestamps).

    python -I canvas/tools/transcribe.py <in_dir> <out_dir> [stem ...]

For each <stem>.mp4 writes <out_dir>/<stem>.json (segments + words) and
<out_dir>/<stem>.txt (one timestamped segment per line, for reading/review).
"""
import json
import os
import sys
from pathlib import Path


def _add_cuda_dlls() -> None:
    """Expose pip-installed nvidia-cublas/cudnn DLLs (Windows) to ctranslate2."""
    try:
        import nvidia
    except ImportError:
        return
    for root in nvidia.__path__:
        for bin_dir in Path(root).glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]


_add_cuda_dlls()
from faster_whisper import WhisperModel  # noqa: E402

GLOSSARY = (
    "Critical making interview for ENG 6819 at UCF with Anastasia Salter. "
    "Guests: Anne Sullivan, Erin Kathleen Bahl, Lyle Skains, Lai-Tze Fan, Dan Cox, "
    "Chloe Milligan, Kavi Duvvoori, Quinn Daedal, Leonardo Flores, Zach Whalen, "
    "Lee Skallerup Bessette, Nikki Fragala Barnes. Texts and Technology, "
    "digital humanities, electronic literature, ELO, Twine, Harlowe, Bitsy, "
    "Tracery, Voyant, p5.js, OpenProcessing, Claude, ChatGPT, Unflattening, "
    "Sousanis, Kairos, Hyperrhiz, The Digital Review, Data-Sitters Club, "
    "NaNoGenMo, Emily Johnson, Fulcrum."
)


def stamp(t: float) -> str:
    m, s = divmod(t, 60)
    h, m = divmod(int(m), 60)
    return f"{h:d}:{m:02d}:{s:05.2f}"


def decode(path: Path):
    """16 kHz mono float32 via ffmpeg (avoids PyAV version issues)."""
    import subprocess
    import numpy as np
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
         "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def load_model():
    try:
        return WhisperModel("large-v3", device="cuda", compute_type="float16")
    except Exception as e:  # missing cuDNN etc.
        print(f"cuda unavailable ({e}); falling back to cpu int8", flush=True)
        return WhisperModel("large-v3", device="cpu", compute_type="int8")


HOTWORDS = ("Salter Sullivan Bahl Skains Lai-Tze Fan Cox Milligan Duvvoori Daedal "
            "Flores Whalen Skallerup Bessette Fragala Barnes Twine Harlowe Bitsy "
            "Tracery Voyant p5.js OpenProcessing Claude Kairos Sousanis")


def main(in_dir: str, out_dir: str, stems: list[str]) -> None:
    # --captions: carry context between windows (keeps punctuation/casing) and
    # hint names on every window; used for the final caption pass.
    captions = "--captions" in stems
    stems = [s for s in stems if s != "--captions"]
    src, out = Path(in_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = [src / f"{s}.mp4" for s in stems] if stems else sorted(src.glob("*.mp4"))
    model = load_model()
    for f in files:
        # (hotwords caused hallucinated glossary runs; build_captions.py also
        # cross-checks every segment against the unconditioned original pass)
        extra = ({"condition_on_previous_text": True, "repetition_penalty": 1.1,
                  "no_repeat_ngram_size": 4, "hallucination_silence_threshold": 2.0,
                  "compression_ratio_threshold": 2.2}
                 if captions else {"condition_on_previous_text": False})
        segments, info = model.transcribe(
            decode(f), language="en", word_timestamps=True, vad_filter=True,
            initial_prompt=GLOSSARY, **extra)
        segs = []
        for s in segments:
            segs.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                         "words": [{"start": w.start, "end": w.end, "word": w.word}
                                   for w in (s.words or [])]})
        (out / f"{f.stem}.json").write_text(
            json.dumps({"duration": info.duration, "segments": segs}, indent=1),
            encoding="utf-8")
        (out / f"{f.stem}.txt").write_text(
            "\n".join(f"[{stamp(s['start'])} - {stamp(s['end'])}] {s['text']}"
                      for s in segs), encoding="utf-8")
        print(f"{f.stem}: {len(segs)} segments", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
