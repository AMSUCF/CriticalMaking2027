"""Deploy ENG 6819 Critical Making to Canvas from the Jekyll course site.

Run from canvas/. See README.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import sys
from datetime import date, datetime, time
from pathlib import Path

import frontmatter
import yaml
from dotenv import load_dotenv

import assets
from converter import (TZ, apply_canvas_style, due_at_utc, extract_readings, load_week,
                       lock_at_utc, render_html, split_section, unlock_at_utc)

STATE_FILE = Path(".state.json")
WELCOME_TITLE = "Welcome! (Read this first!)"

# an uploaded Canvas video embed, hand-placed on a live readings page —
# deploys keep it in place of the placeholder paragraph
# (Canvas's editor may leave it inside the placeholder's <em>)
VIDEO_EMBED_RE = re.compile(
    r'<p>(?:<(?:em|strong|span)[^>]*>)*<iframe[^>]*data-media-type="video"'
    r'.*?</iframe>(?:</(?:em|strong|span)>)*</p>', re.DOTALL)


def now_et() -> datetime:
    return datetime.now(TZ)


def is_live(start_date: date, now: datetime | None = None) -> bool:
    """A module is live from midnight ET on its start date.

    Live content is frozen: students are already working in it, so deploys
    leave it alone unless --force is passed.
    """
    now = now or now_et()
    return datetime.combine(start_date, time(0, 0), tzinfo=TZ) <= now


def av_is_live(av: dict, now: datetime | None = None) -> bool:
    """Activity Verification freezes once its open date has passed."""
    return bool(av.get("open")) and is_live(av["open"], now)


def week_label(module: str) -> str:
    return module.split(":")[0].strip()


def group_key(stem: str, cfg: dict) -> str:
    """Week One (introductions) and the extras (the final reflection) count
    as Course Requirements; every other week is a Making Exercise."""
    if stem == cfg["weeks"][0] or stem in (cfg.get("extra") or []):
        return "other"
    return "exercises"


def plan_week(stem: str, root: Path, cfg: dict, syllabus_md: str = "", media=None,
              course_path: str = "/courses/COURSE", api_base: str | None = None) -> dict:
    """Everything one week deploys, rendered; no Canvas calls."""
    path = root / f"{stem}.md"
    doc = load_week(path)
    c = doc.canvas
    site = cfg["site_base"]
    src_dir = posixpath.dirname(stem)
    kind = c.get("type", "discussion")
    page_md, graded_md = split_section(
        doc.body, "Submission" if kind == "assignment" else "Discussion")
    label = week_label(c["module"])
    title = doc.meta.get("title") or c["module"]

    # the Canvas-only readings page: syllabus readings, reading PDFs, interview
    readings_html = placeholder = ""
    guest = None
    if stem in cfg["weeks"]:
        readings_md = extract_readings(syllabus_md, label) if syllabus_md else ""
        syl_dir = posixpath.dirname(cfg.get("syllabus_file", "index.md"))
        parts = []
        if readings_md:
            parts.append(render_html(f"## Readings\n\n{readings_md}", site, syl_dir))
        pdfs = media.pdfs(stem) if media else []
        parts.append(assets.pdf_links_html(pdfs, course_path, api_base))
        iv = assets.interview(cfg, c.get("interview"))
        if iv:
            guest = iv["guest"]
            vid = media.video_id(c["interview"]) if media else None
            parts.append(f"<h2>Featured Interview: {guest}</h2>")
            if vid is not None:
                parts.append(assets.video_embed_html(vid, guest))
            else:
                placeholder = assets.video_placeholder_html(guest)
                parts.append(placeholder)
        body = "".join(p for p in parts if p)
        readings_html = apply_canvas_style(body) if body else ""

    graded_title = c.get("discussion_title") or (
        f"Exercise Discussion: {c['module']}" if kind == "discussion" else title)
    return {
        "stem": stem,
        "name": Path(stem).name,
        "module": c["module"],
        "label": label,
        "title": title,
        "kind": kind,
        "week_start": c["week_start"],
        "points": int(c["points"]),
        "extra_credit": bool(c.get("extra_credit", False)),
        "group": group_key(stem, cfg),
        "rubric": bool(c.get("rubric", False)),
        "interview": c.get("interview"),
        "guest": guest,
        "due_at": due_at_utc(c["due"]),
        "unlock_at": unlock_at_utc(c["week_start"]),
        # `close:` (a date) keeps a week open past the usual late window
        "lock_at": (due_at_utc(c["close"]) if c.get("close")
                    else due_at_utc(c["due"]) if c.get("hard_close")
                    else lock_at_utc(c["due"])),
        "readings_title": f"{label}: Readings + Interview",
        "readings_html": readings_html,
        "readings_placeholder": placeholder,
        "has_graded": bool(c.get("discussion", True)) and bool(graded_md),
        "graded_title": graded_title,
        "page_html": apply_canvas_style(render_html(page_md, site, src_dir)),
        "graded_html": apply_canvas_style(render_html(graded_md, site, src_dir))
        if graded_md else "",
    }


def module_order(cfg: dict) -> list[str]:
    """Stems and break-module names in course order (module positions)."""
    order = list(cfg["weeks"]) + list(cfg.get("extra") or [])
    for b in cfg.get("breaks") or []:
        after = b.get("after")
        i = order.index(after) + 1 if after in order else len(order)
        order.insert(i, b["module"])
    return order


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    text = STATE_FILE.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _course_root(cfg: dict) -> Path:
    # the course files live one directory above canvas/ when run in place,
    # or in cwd when tests fabricate a flat layout
    for base in (Path("."), Path("..")):
        if (base / cfg["syllabus_file"]).exists():
            return base
    raise SystemExit(f"{cfg['syllabus_file']} not found in . or ..: run deploy.py "
                     f"from canvas/")


ENV_KEYS = ("CANVAS_API_URL", "CANVAS_API_TOKEN", "CANVAS_COURSE_ID")


def _load_env() -> None:
    env = Path.cwd() / ".env"
    load_dotenv(env)
    lacking = [k for k in ENV_KEYS if not os.environ.get(k)]
    if lacking:
        where = env if env.exists() else f"{env} (there is no such file)"
        raise SystemExit(f"{', '.join(lacking)} not set: put "
                         f"{'it' if len(lacking) == 1 else 'them'} in {where}")


def _resolve_stem(name: str, cfg: dict) -> str:
    """--week accepts a full stem (exercises/one_selfie) or its last part."""
    stems = cfg["weeks"] + (cfg.get("extra") or [])
    if name in stems:
        return name
    hits = [s for s in stems if Path(s).name == name]
    if len(hits) == 1:
        return hits[0]
    raise SystemExit(f"--week {name}: not in course.yml weeks/extra")


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str)
                          .encode("utf-8")).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--week")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--simple-syllabus", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="also redeploy modules (and Activity Verification) that "
                         "have already opened")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(Path("course.yml").read_text(encoding="utf-8"))
    cfg.setdefault("extra", [])
    root = _course_root(cfg)

    if args.simple_syllabus:
        from simple_syllabus import build_package
        out = build_package(root / cfg["syllabus_file"], Path("preview"), cfg["site_base"])
        print(f"simple syllabus package: {out}")
        return 0

    if args.all:
        stems = cfg["weeks"] + cfg["extra"]
    elif args.week:
        stems = [_resolve_stem(args.week, cfg)]
    else:
        ap.error("pass --all or --week NAME")

    syl_path = root / cfg["syllabus_file"]
    syllabus_md = frontmatter.load(str(syl_path)).content

    present = []
    for s in stems:
        if (root / f"{s}.md").exists():
            present.append(s)
        else:
            print(f"[missing] {s}.md not found; skipped")
    docs, bad = {}, []
    for s in present:
        try:
            docs[s] = load_week(root / f"{s}.md").canvas
        except ValueError as e:
            bad.append(str(e))
    if bad:
        raise SystemExit("fix the front matter first:\n  " + "\n  ".join(bad))
    keys = {s: docs[s].get("interview") for s in present}
    starts = {s: docs[s]["week_start"] for s in present}

    # freeze check: anything students can already see is left alone
    now = now_et()
    if not args.force:
        for s in present:
            if is_live(starts[s], now):
                print(f"[frozen] {s} opened {starts[s]} and is live; not redeployed "
                      f"(pass --force to override)")
        present = [s for s in present if not is_live(starts[s], now)]
        if not present and not args.all:
            return 1

    breaks = []
    if args.all:
        for b in cfg.get("breaks") or []:
            if is_live(b["week_start"], now) and not args.force:
                print(f"[frozen] {b['module']} opened {b['week_start']}; not redeployed")
            else:
                breaks.append(b)
    positions = {name: i + 1 for i, name in enumerate(module_order(cfg))}
    av = cfg.get("activity_verification")
    welcome_md = None
    if cfg.get("welcome_file") and cfg["weeks"][0] in present:
        wpath = root / cfg["welcome_file"]
        if wpath.exists():
            welcome_md = frontmatter.load(str(wpath)).content
        else:
            print(f"[missing] {cfg['welcome_file']} not found; no Welcome page")

    if args.dry_run:
        media = assets.Media(cfg, Path("."))
        media.sync(present, keys)
        plans = [plan_week(s, root, cfg, syllabus_md, media) for s in present]
        prev = Path("preview")
        prev.mkdir(exist_ok=True)
        for p in plans:
            (prev / f"{p['name']}.html").write_text(p["page_html"], encoding="utf-8")
            extras = []
            if p["readings_html"]:
                (prev / f"{p['name']}-readings.html").write_text(
                    p["readings_html"], encoding="utf-8")
                extras.append("readings")
            if p["has_graded"]:
                (prev / f"{p['name']}-{p['kind']}.html").write_text(
                    p["graded_html"], encoding="utf-8")
            print(f"[dry-run] module '{p['module']}' | opens {p['unlock_at']} | "
                  f"page{''.join(' + ' + e for e in extras)} | {p['kind']} "
                  f"'{p['graded_title']}' {0 if p['extra_credit'] else p['points']}pts "
                  f"[{cfg['assignment_groups'][p['group']]}] "
                  f"due {p['due_at']} locks {p['lock_at']}"
                  + (" [rubric]" if p["rubric"] else "")
                  + (" [extra credit]" if p["extra_credit"] else ""))
            if p["stem"] == cfg["weeks"][0] and welcome_md is not None:
                (prev / "welcome.html").write_text(
                    apply_canvas_style(render_html(welcome_md, cfg["site_base"])),
                    encoding="utf-8")
                print(f"[dry-run]   + page '{WELCOME_TITLE}' (first item)")
            if av and p["stem"] == av.get("module_of"):
                note = ("frozen" if av_is_live(av, now) and not args.force else
                        f"{av['points']}pts due {due_at_utc(av['due'])}")
                print(f"[dry-run]   + assignment '{av['name']}' {note}")
        for b in breaks:
            print(f"[dry-run] break module '{b['module']}' | opens "
                  f"{unlock_at_utc(b['week_start'])} | text: {b['text']}")
        if args.all:
            (prev / "syllabus.html").write_text(
                apply_canvas_style(render_html(syllabus_md, cfg["site_base"])),
                encoding="utf-8")
            print("[dry-run] Syllabus page")
            if cfg.get("course_image") and media.course_image(cfg["course_image"]):
                print(f"[dry-run] course image: {cfg['course_image']}")
        return 0

    _load_env()
    import requests
    from canvas_client import CanvasClient
    client = CanvasClient(os.environ["CANVAS_API_URL"], os.environ["CANVAS_API_TOKEN"],
                          os.environ["CANVAS_COURSE_ID"])
    try:
        info = client.course_info()
    except requests.HTTPError as e:
        code = getattr(e.response, "status_code", None)
        hint = ("; Canvas token rejected (expired?); put a fresh CANVAS_API_TOKEN "
                "in .env" if code == 401
                else "; no such course: check CANVAS_COURSE_ID in .env" if code == 404
                else "")
        raise SystemExit(f"could not read the Canvas course (HTTP {code}){hint}")
    print(f"deploying to: {info.get('name')} ({info.get('course_code')})")
    want = cfg.get("expect_course_code")
    if want and str(want) not in (info.get("course_code") or ""):
        raise SystemExit(f"course_code {info.get('course_code')!r} does not contain "
                         f"{str(want)!r}; wrong CANVAS_COURSE_ID?")

    course_path = f"/courses/{os.environ['CANVAS_COURSE_ID']}"
    api_base = os.environ["CANVAS_API_URL"].rstrip("/") + "/api/v1"
    state = _load_state()
    try:
        media = assets.Media(cfg, Path("."), client, state)
        try:
            media.sync(present, keys)
        except requests.HTTPError as e:
            raise SystemExit(f"media upload failed: {e}")
        plans = [plan_week(s, root, cfg, syllabus_md, media, course_path, api_base)
                 for s in present]
        _deploy(client, cfg, args, state, plans, breaks, positions, welcome_md,
                syllabus_md, now)
        if args.all and cfg.get("course_image"):
            try:
                fid = media.course_image(cfg["course_image"])
                if fid is not None and state.get("course_image_id") != fid:
                    client.set_course_image(fid)
                    state["course_image_id"] = fid
                    print("deployed: course image")
            except requests.HTTPError as e:
                raise SystemExit(f"deploy failed at 'course image': {e}")
    finally:
        _save_state(state)
    return 0


def _deploy(client, cfg, args, state, plans, breaks, positions, welcome_md,
            syllabus_md, now) -> None:
    import requests
    groups = {}

    def group_id(key):
        if key not in groups:
            groups[key] = client.upsert_assignment_group(cfg["assignment_groups"][key])
        return groups[key]

    def page(title, html, known):
        return client.upsert_page(title, html, args.publish, known_url=known)

    av = cfg.get("activity_verification")
    by_stem = {p["stem"]: p for p in plans}
    break_by_name = {b["module"]: b for b in breaks}
    for name in module_order(cfg):
        try:
            if name in break_by_name:
                b = break_by_name[name]
                known = state.setdefault("breaks", {}).get(name)
                mid = client.upsert_module(name, unlock_at=unlock_at_utc(b["week_start"]),
                                           published=args.publish or None,
                                           known_id=known, position=positions[name])
                state["breaks"][name] = mid
                client.add_to_module(mid, "SubHeader", b["text"], position=1)
                print(f"deployed: {name}")
                continue
            p = by_stem.get(name)
            if p is None:
                continue
            st = state.setdefault(p["stem"], {})
            module_id = client.upsert_module(p["module"], unlock_at=p["unlock_at"],
                                             published=args.publish or None,
                                             known_id=st.get("module_id"),
                                             position=positions[p["stem"]])
            st["module_id"] = module_id
            pos = 1
            if p["stem"] == cfg["weeks"][0] and welcome_md is not None:
                state["welcome_url"] = page(
                    WELCOME_TITLE,
                    apply_canvas_style(render_html(welcome_md, cfg["site_base"])),
                    state.get("welcome_url"))
                client.add_to_module(module_id, "Page", state["welcome_url"], pos)
                pos += 1
            if p["readings_html"]:
                _deploy_readings(client, p, st, page)
                client.add_to_module(module_id, "Page", st["readings_url"], pos)
                pos += 1
            st["page_url"] = page(p["title"], p["page_html"], st.get("page_url"))
            client.add_to_module(module_id, "Page", st["page_url"], pos)
            pos += 1
            if p["has_graded"]:
                points = 0 if p["extra_credit"] else p["points"]
                gid = group_id(p["group"])
                if p["kind"] == "assignment":
                    aid = client.upsert_assignment(
                        p["graded_title"], points, p["due_at"], gid,
                        ["online_url", "online_upload"], args.publish,
                        known_id=st.get("assignment_id"), unlock_at=p["unlock_at"],
                        lock_at=p["lock_at"], description=p["graded_html"])
                    st["assignment_id"] = aid
                    client.add_to_module(module_id, "Assignment", aid, pos)
                else:
                    topic = client.upsert_discussion(
                        p["graded_title"], p["graded_html"], points, p["due_at"], gid,
                        args.publish, known_id=st.get("discussion_id"),
                        unlock_at=p["unlock_at"], lock_at=p["lock_at"])
                    st["discussion_id"] = topic["id"]
                    if topic.get("assignment_id"):
                        st["assignment_id"] = topic["assignment_id"]
                    client.add_to_module(module_id, "Discussion", topic["id"], pos)
                pos += 1
                if p["rubric"]:
                    _attach_rubric(client, cfg, state, st, p)
            if av and p["stem"] == av.get("module_of"):
                if av_is_live(av, now) and not args.force:
                    print(f"[frozen] {av['name']} opened {av['open']} and is live; "
                          f"not updated")
                    if state.get("activity_verification_id"):
                        client.add_to_module(module_id, "Assignment",
                                             state["activity_verification_id"], pos)
                else:
                    state["activity_verification_id"] = client.upsert_assignment(
                        av["name"], av["points"], due_at_utc(av["due"]), group_id("other"),
                        ["online_text_entry"], args.publish,
                        known_id=state.get("activity_verification_id"),
                        unlock_at=unlock_at_utc(av["open"]) if av.get("open") else None,
                        lock_at=lock_at_utc(av["due"]))
                    client.add_to_module(module_id, "Assignment",
                                         state["activity_verification_id"], pos)
                pos += 1
            print(f"deployed: {p['module']}")
        except requests.HTTPError as e:
            raise SystemExit(f"deploy failed at '{name}': {e}")

    if args.all:
        try:
            state["syllabus_url"] = page(
                "Syllabus", apply_canvas_style(render_html(syllabus_md, cfg["site_base"])),
                state.get("syllabus_url"))
        except requests.HTTPError as e:
            raise SystemExit(f"deploy failed at 'Syllabus': {e}")
        print("deployed: Syllabus page")


def _deploy_readings(client, p, st, page) -> bool:
    """Upsert the readings page, keeping a hand-uploaded interview video in
    place of the placeholder. False if the page was left as it is."""
    html = p["readings_html"]
    known = st.get("readings_url") or client.find_page(p["readings_title"])
    if p["readings_placeholder"] and known:
        live = client.get_page_body(known)
        video = VIDEO_EMBED_RE.search(live) if live else None
        if video:
            html = html.replace(p["readings_placeholder"], video.group(0))
            print(f"  [kept] {p['readings_title']}: hand-uploaded interview video")
        elif live and 'data-media-type="video"' in live:
            # a video we can't lift out cleanly: never wipe it
            print(f"  [kept] {p['readings_title']}: live video embed not in the "
                  "expected spot; page left as is")
            st["readings_url"] = known
            return False
    st["readings_url"] = page(p["readings_title"], html, known)
    return True


def _attach_rubric(client, cfg, state, st, p) -> None:
    """Create the course rubric once (its id kept in state), then associate
    it with this week's assignment for grading."""
    import requests
    aid = st.get("assignment_id")
    rcfg = cfg.get("rubric")
    if not rcfg:
        print(f"  [rubric] {p['stem']} asks for a rubric but course.yml has none")
        return
    if not aid:
        print(f"  [rubric] no assignment id for {p['graded_title']}; rubric not attached")
        return
    title, criteria = rcfg["title"], rcfg["criteria"]
    sha = _sha(rcfg)
    use = not p["extra_credit"]   # a 0-point extra credit can't be graded by it
    total = sum(c["points"] for c in criteria)
    if use and total != p["points"]:
        print(f"  [rubric] {title} totals {total} but {p['graded_title']} is worth "
              f"{p['points']}; Canvas will set the points to the rubric total")
    rs = state.get("rubric") or {}
    if not rs.get("id"):
        found = client.find_rubric(title)
        if found is None:
            rid, assoc = client.create_rubric(title, criteria, aid, use)
            state["rubric"] = {"id": rid, "sha256": sha}
            st["rubric_association_id"] = assoc
            print(f"  rubric: created '{title}' ({rid})")
            return
        rs = state["rubric"] = {"id": found, "sha256": None}
    try:
        assoc = client.associate_rubric(rs["id"], aid, known_id=st.get("rubric_association_id"),
                                        use_for_grading=use)
    except requests.HTTPError as e:
        if st.get("rubric_association_id") is None or \
                getattr(e.response, "status_code", None) != 404:
            raise
        assoc = client.associate_rubric(rs["id"], aid, use_for_grading=use)
    st["rubric_association_id"] = assoc
    if rs.get("sha256") != sha:
        rs["id"] = client.update_rubric(rs["id"], title, criteria, association_id=assoc)
        rs["sha256"] = sha
        print(f"  rubric: updated '{title}'")


if __name__ == "__main__":
    sys.exit(main())
