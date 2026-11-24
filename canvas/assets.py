"""Canvas-only media: interview videos (+ captions) and reading PDFs.

These files are never committed (canvas/media/ is gitignored) and never go
on the public site; they are uploaded to Canvas Files and linked or
embedded on each week's "Readings + Interview" page. Paths in course.yml
are relative to canvas/ (the directory deploy.py runs in).
"""
from __future__ import annotations

import hashlib
import html as _html
from pathlib import Path

FOLDERS = {"video": "Interviews", "pdf": "Readings"}
TYPES = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime",
         ".webm": "video/webm", ".pdf": "application/pdf"}


def sha256_file(path: Path) -> str:
    """Streamed: videos run to ~850 MB."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_entries(cfg, stem) -> list[dict]:
    """[{file, title}] for a stem's PDFs; a plain path's title is its stem."""
    out = []
    for e in (cfg.get("pdfs") or {}).get(stem) or []:
        if isinstance(e, dict):
            out.append({"file": e["file"], "title": e.get("title") or Path(e["file"]).stem})
        else:
            out.append({"file": e, "title": Path(e).stem})
    return out


def interview(cfg, key) -> dict | None:
    if not key:
        return None
    iv = (cfg.get("interviews") or {}).get(key)
    if iv is None:
        raise SystemExit(f"interview '{key}' is not in course.yml interviews")
    return iv


def pdf_links_html(pdfs: list[dict], course_path: str, api_base: str | None) -> str:
    """pdfs: [{title, id}] with Canvas file ids."""
    if not pdfs:
        return ""
    items = []
    for p in pdfs:
        href = f"{course_path}/files/{p['id']}"
        api = (f' data-api-endpoint="{api_base}{href}" data-api-returntype="File"'
               if api_base else "")
        items.append(f'<li><a class="instructure_file_link" title="{_html.escape(p["title"])}" '
                     f'href="{href}?wrap=1"{api}>{_html.escape(p["title"])}</a></li>')
    return "<h2>Reading PDFs</h2><ul>" + "".join(items) + "</ul>"


def video_embed_html(file_id, guest: str) -> str:
    """The iframe Canvas's rich content editor inserts for an uploaded video
    (canvas-lms packages/canvas-rce .../fileTypeUtils.ts mediaPlayerURLFromFile)."""
    return (f'<p><iframe style="width: 640px; height: 360px; display: inline-block;" '
            f'title="{_html.escape(guest)} interview" data-media-type="video" '
            f'src="/media_attachments_iframe/{file_id}?type=video&amp;embedded=true" '
            f'allowfullscreen="allowfullscreen" allow="fullscreen" loading="lazy">'
            f'</iframe></p>')


def video_placeholder_html(guest: str) -> str:
    return f"<p><em>The interview with {_html.escape(guest)} will be posted here.</em></p>"


def _warn_missing(rel, what):
    fallback = ("the placeholder is used" if what == "video"
                else "no captions uploaded" if what == "captions"
                else "left off the readings page")
    print(f"[missing media] {rel} not found ({what}); {fallback}")


class Media:
    """Resolves (dry run) or uploads (live) the media for the stems being
    deployed. `pdfs(stem)` and `video_id(key)` answer for the planner."""

    def __init__(self, cfg, base: Path, client=None, state=None):
        self.cfg, self.base, self.client = cfg, Path(base), client
        self.state = state if state is not None else {}
        self.files = self.state.setdefault("files", {}) if client else {}
        self._pdfs, self._videos = {}, {}
        self._pending_captions = []

    @property
    def live(self) -> bool:
        return self.client is not None

    # --- planning answers ---------------------------------------------------
    def pdfs(self, stem) -> list[dict]:
        return self._pdfs.get(stem, [])

    def video_id(self, key):
        return self._videos.get(key)

    # --- sync ---------------------------------------------------------------
    def sync(self, stems, interview_keys: dict) -> None:
        """stems: the stems being deployed; interview_keys: stem -> key."""
        for stem in stems:
            got = []
            for e in pdf_entries(self.cfg, stem):
                fid = self._file(e["file"], "pdf")
                if fid is not None:
                    got.append({"title": e["title"], "id": fid})
            self._pdfs[stem] = got
        for stem in stems:
            key = interview_keys.get(stem)
            iv = interview(self.cfg, key)
            if not iv or not iv.get("video"):
                continue
            fid = self._file(iv["video"], "video")
            if fid is None:
                continue
            self._videos[key] = fid
            if iv.get("captions"):
                self._pending_captions.append((key, fid, iv["captions"]))
        # captions last: Canvas needs time after an upload to build each
        # video's media object, and the other uploads buy some of it
        for key, fid, rel in self._pending_captions:
            self._captions(key, fid, rel)

    def _file(self, rel, kind):
        path = self.base / rel
        if not path.is_file():
            _warn_missing(rel, kind)
            return None
        if not self.live:
            return f"FILE-{path.name}"
        st = path.stat()
        rec = self.files.get(rel)
        if rec and rec.get("size") == st.st_size and rec.get("mtime") == st.st_mtime:
            sha = rec["sha256"]      # unchanged since we last hashed it
        else:
            sha = sha256_file(path)
        if rec and rec.get("sha256") == sha:
            rec.update(size=st.st_size, mtime=st.st_mtime)
            return rec["id"]
        ctype = TYPES.get(path.suffix.lower(), "application/octet-stream")
        print(f"uploading: {rel} ({st.st_size // (1024 * 1024)} MB)")
        out = self.client.upload_file(path, FOLDERS[kind], ctype)
        self.files[rel] = {"id": out["id"], "sha256": sha,
                           "size": st.st_size, "mtime": st.st_mtime}
        print(f"uploaded: {rel} -> file {out['id']}")
        return out["id"]

    def _captions(self, key, video_id, rel):
        path = self.base / rel
        if not path.is_file():
            _warn_missing(rel, "captions")
            return
        if not self.live:
            return
        import requests
        caps = self.state.setdefault("captions", {})
        text = path.read_text(encoding="utf-8-sig")
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        rec = caps.get(key) or {}
        if (rec.get("status") == "done" and rec.get("attachment_id") == video_id
                and rec.get("sha256") == sha):
            return
        try:
            self.client.set_media_tracks(
                video_id, [{"locale": "en", "content": text, "kind": "subtitles"}])
        except requests.HTTPError as e:
            caps[key] = {"attachment_id": video_id, "sha256": sha, "status": "pending"}
            print(f"[captions pending] {rel}: Canvas has not finished processing video "
                  f"{video_id} ({e}); the next deploy will retry")
            return
        caps[key] = {"attachment_id": video_id, "sha256": sha, "status": "done"}
        print(f"captions: {rel} -> video {video_id}")
