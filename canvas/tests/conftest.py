import shutil
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "course"


def make_media(canvas: Path) -> None:
    """Small stand-ins for the Canvas-only media (bahl's video and
    not_here.pdf are deliberately absent)."""
    files = {
        "media/interviews/edited/sullivan.mp4": b"\x00\x00\x00\x18ftypmp42" + b"v" * 4096,
        "media/interviews/captions/sullivan.vtt": "WEBVTT\n\n00:00.000 --> 00:01.000\nHello\n",
        "media/pdfs/RattoCriticalMaking.pdf": b"%PDF-1.4 ratto",
        "media/pdfs/00_Provacations.pdf": b"%PDF-1.4 provocations",
        "media/pdfs/01_Selfie.pdf": b"%PDF-1.4 selfie",
    }
    for rel, data in files.items():
        p = canvas / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            p.write_text(data, encoding="utf-8")
        else:
            p.write_bytes(data)


@pytest.fixture
def course(tmp_path, monkeypatch):
    """A copy of tests/fixtures/course with media; cwd is its canvas/ dir,
    and "now" is well before the term so nothing is frozen."""
    import deploy
    root = tmp_path / "course"
    shutil.copytree(FIXTURE, root)
    canvas = root / "canvas"
    make_media(canvas)
    monkeypatch.chdir(canvas)
    monkeypatch.setattr(deploy, "now_et",
                        lambda: deploy.datetime(2026, 12, 1, 12, 0, tzinfo=deploy.TZ))
    return canvas
