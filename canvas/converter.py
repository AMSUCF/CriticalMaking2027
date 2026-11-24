from __future__ import annotations

import html as _html
import posixpath
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import frontmatter
from markdown_it import MarkdownIt

# one accent band for every Canvas page this course deploys, in the site's
# quilt fabrics (assets/css/style.scss). Canvas strips <style> and web fonts,
# so the band uses inline colours and borders only.
ACCENT_COLOR = "#4b2e83"   # violet
PILL_COLOR = "#f4c430"     # sunflower
STITCH_COLOR = "#c2185b"   # raspberry
ACCENT_LABEL = "Critical Making"

REQUIRED_KEYS = ("module", "week_start", "due", "points")

_md = MarkdownIt("commonmark", {"html": True}).enable("table")


@dataclass
class WeekDoc:
    path: Path
    meta: dict
    canvas: dict
    body: str


def load_week(path) -> WeekDoc:
    post = frontmatter.load(str(path))
    canvas = post.metadata.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError(f"{path}: missing 'canvas' front matter block")
    missing = [k for k in REQUIRED_KEYS if k not in canvas]
    if missing:
        raise ValueError(f"{path}: canvas block missing {', '.join(missing)}")
    kind = canvas.get("type", "discussion")
    if kind not in ("discussion", "assignment"):
        raise ValueError(f"{path}: canvas type must be 'discussion' or 'assignment', "
                         f"not '{kind}'")
    return WeekDoc(Path(path), post.metadata, canvas, post.content)


def kramdown_id(text: str) -> str:
    """Jekyll/kramdown auto_ids, so syllabus TOC links work in Canvas."""
    t = re.sub(r"^[^a-zA-Z]+", "", text)
    t = re.sub(r"[^a-zA-Z0-9 -]", "", t)
    return t.replace(" ", "-").lower()


_HEADING_RE = re.compile(r"<h([1-6])>(.*?)</h\1>", re.DOTALL)


def _add_heading_ids(html: str) -> str:
    def add(m):
        plain = _html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
        return f'<h{m.group(1)} id="{kramdown_id(plain)}">{m.group(2)}</h{m.group(1)}>'
    return _HEADING_RE.sub(add, html)


def _rewrite(html: str, site_base: str, src_dir: str = "") -> str:
    """Point every relative href/src at the public site.

    Relative paths resolve against `src_dir`, the source file's directory
    relative to the repo root ("" for index.md, "exercises" for exercise
    pages), so `../img/x.png` in exercises/one_selfie.md becomes
    `{site_base}/img/x.png`. `.md` links become `.html`; extensionless
    links (Jekyll permalinks) are kept extensionless.
    """
    base = site_base.rstrip("/")

    def fix(m):
        attr, url = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:|tel:|#|data:|//|/)", url):
            return m.group(0)
        path, sep, rest = _split_suffix(url)
        if not path:           # "?x" or "#x" alone: same page; leave it
            return m.group(0)
        path = re.sub(r"\.md$", ".html", path)
        joined = posixpath.normpath(posixpath.join(src_dir, path))
        if path.endswith("/") and not joined.endswith("/"):
            joined += "/"
        joined = "" if joined in (".", "./") else joined
        return f'{attr}="{base}/{joined}{sep}{rest}"'

    return re.sub(r'(href|src|poster)="([^"]+)"', fix, html)


def _split_suffix(url: str) -> tuple[str, str, str]:
    """('path', '?' or '#' or '', 'remainder')"""
    m = re.search(r"[?#]", url)
    if not m:
        return url, "", ""
    return url[: m.start()], url[m.start()], url[m.start() + 1:]


def render_html(md_text: str, site_base: str, src_dir: str = "") -> str:
    return _rewrite(_add_heading_ids(_md.render(md_text)), site_base, src_dir)


TZ = ZoneInfo("America/New_York")
# bullets that belong elsewhere in the Canvas module, not on the readings page
_SKIP_BULLET_RE = re.compile(
    r"^-\s+(?:\*\*)?\[?(?:\*\*)?\s*(Featured Guest|(Optional |Extra Credit )?Making Exercise)")


def extract_readings(syllabus_md: str, week_label: str) -> str:
    """Pull a week's readings from the syllabus Weekly Schedule.

    Finds the `### {week_label}: ...` heading and returns its markdown up to
    the next `###` heading (a `#### Explore` sub-list is kept), minus the
    Featured Guest and Making Exercise bullets; "" if the heading isn't found.
    """
    m = re.search(
        rf"^###\s+{re.escape(week_label)}[:\s][^\n]*\n(.*?)(?=^###\s|\Z)",
        syllabus_md, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    kept, skipping = [], False
    for line in m.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            skipping = bool(_SKIP_BULLET_RE.match(stripped))
            if not skipping:
                kept.append(line)
        elif not stripped:
            skipping = False  # blank line ends any bullet continuation
            kept.append(line)
        elif not skipping:
            kept.append(line)
    out = "\n".join(kept).strip()
    # a section reduced to nothing but a heading (or a rule) has no readings
    if not re.sub(r"^(#+.*|-{3,}|\*{3,})$", "", out, flags=re.MULTILINE).strip():
        return ""
    return out


def split_section(md_text: str, heading: str = "Discussion") -> tuple[str, str]:
    """(page part, after part) split at a `### {heading}` line."""
    m = re.compile(rf"^### {re.escape(heading)}[ \t]*$", re.MULTILINE).search(md_text)
    if not m:
        return md_text.strip(), ""
    return md_text[: m.start()].strip(), md_text[m.end():].strip()


def split_discussion(md_text: str) -> tuple[str, str]:
    return split_section(md_text, "Discussion")


def due_at_utc(due_date) -> str:
    dt = datetime.combine(due_date, time(23, 59), tzinfo=TZ)
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def unlock_at_utc(start_date) -> str:
    """Module/assignment opens at midnight ET on its start date."""
    dt = datetime.combine(start_date, time(0, 0), tzinfo=TZ)
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def lock_at_utc(due_date, grace_days: int = 7, grace_hours: int | None = None) -> str:
    """Hard close after the due date: grace_hours if given, else grace_days."""
    due = datetime.combine(due_date, time(23, 59), tzinfo=TZ)
    dt = due + (timedelta(hours=grace_hours) if grace_hours is not None
                else timedelta(days=grace_days))
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def apply_canvas_style(html: str) -> str:
    band = (
        f'<div style="border-top: 6px solid {ACCENT_COLOR}; '
        f'border-bottom: 2px dashed {STITCH_COLOR}; padding: 12px 0 10px 0; '
        f'margin-bottom: 16px;"><span style="display: inline-block; '
        f'padding: 2px 12px; border-radius: 9999px; background: {PILL_COLOR}; '
        f'color: {ACCENT_COLOR}; border: 2px solid {ACCENT_COLOR}; '
        f'font-size: 12px; font-weight: bold; letter-spacing: 1px; '
        f'text-transform: uppercase;">{ACCENT_LABEL}</span></div>'
    )
    return band + html
