import json
from pathlib import Path

import pytest
import requests

import assets
import deploy

SITE = "https://x.y/CM"


def _cfg(canvas):
    import yaml
    return yaml.safe_load((canvas / "course.yml").read_text(encoding="utf-8"))


class FakeMedia:
    def __init__(self, pdfs=None, videos=None):
        self._p, self._v = pdfs or {}, videos or {}
    def pdfs(self, stem): return self._p.get(stem, [])
    def video_id(self, key): return self._v.get(key)


def _plan(canvas, stem, media=None, **kw):
    return deploy.plan_week(stem, canvas.parent, _cfg(canvas),
                            (canvas.parent / "index.md").read_text(encoding="utf-8"),
                            media, **kw)


# --- planning ----------------------------------------------------------------------

def test_plan_week_path_stem_links_and_dates(course):
    p = _plan(course, "exercises/one_selfie")
    assert p["stem"] == "exercises/one_selfie" and p["name"] == "one_selfie"
    assert p["module"] == "Week Two: Selfie" and p["label"] == "Week Two"
    assert p["title"] == "Making Exercise One: Selfie"
    assert p["graded_title"] == 'Making Exercise One: "Selfie"'
    assert p["kind"] == "discussion" and p["has_graded"] and p["rubric"]
    assert p["group"] == "exercises" and p["points"] == 7
    assert p["due_at"] == "2027-01-25T04:59:00Z"
    assert p["unlock_at"] == "2027-01-18T05:00:00Z"
    assert p["lock_at"] == "2027-02-01T04:59:00Z"          # one week late window
    html = p["page_html"]
    assert f'src="{SITE}/img/original.jpg"' in html        # ../img from exercises/
    assert f'href="{SITE}/exercises/two_comic"' in html     # extensionless sibling
    assert f'href="{SITE}/index.html#weekly-schedule"' in html
    assert 'href="#the-selfie-prompt"' in html and 'href="https://example.org/x"' in html
    assert "border-top: 6px solid #0b7a75" in html
    assert "Share approximately five images" in p["graded_html"]
    assert "Share approximately" not in html


def test_plan_week_default_discussion_title_and_group(course):
    p = _plan(course, "exercises/two_comic")
    assert p["graded_title"] == "Exercise Discussion: Week Three: Comic"
    intro = _plan(course, "exercises/introductions")
    assert intro["group"] == "other" and intro["graded_title"] == "Introductions"


def test_plan_week_type_assignment(course):
    p = _plan(course, "exercises/reflection")
    assert p["kind"] == "assignment" and p["group"] == "other"
    assert p["graded_title"] == "Final Reflection"
    assert "Upload a document" in p["graded_html"]
    assert "Upload a document" not in p["page_html"]
    assert p["lock_at"] == p["due_at"] == "2027-05-03T03:59:00Z"   # hard_close
    assert p["readings_html"] == ""                     # extras get no readings page


def test_plan_week_close_date_and_dst(course):
    md = course.parent / "exercises" / "two_comic.md"
    md.write_text(md.read_text(encoding="utf-8").replace(
        "  due: 2027-01-31\n", "  due: 2027-03-14\n  close: 2027-03-21\n"), encoding="utf-8")
    p = _plan(course, "exercises/two_comic")
    assert p["due_at"] == "2027-03-15T03:59:00Z"        # spring-forward Sunday
    assert p["lock_at"] == "2027-03-22T03:59:00Z"


def test_plan_week_extra_credit(course):
    md = course.parent / "exercises" / "two_comic.md"
    md.write_text(md.read_text(encoding="utf-8").replace(
        "  rubric: true\n", "  rubric: true\n  extra_credit: true\n"), encoding="utf-8")
    assert _plan(course, "exercises/two_comic")["extra_credit"] is True


def test_readings_page_with_uploaded_video_and_pdfs(course):
    media = FakeMedia(pdfs={"exercises/one_selfie": [{"title": "01_Selfie", "id": 501}]},
                      videos={"sullivan": 777})
    p = _plan(course, "exercises/one_selfie", media, course_path="/courses/42",
              api_base="https://c.t/api/v1")
    html = p["readings_html"]
    assert p["readings_title"] == "Week Two: Readings + Interview"
    assert '<h2 id="readings">Readings</h2>' in html
    assert "Unflattening" in html and "Hello Selfie" in html
    assert "Featured Guest" not in html and "Making Exercise" not in html
    assert "Game Poems" in html                          # #### Explore kept
    assert "Week Three" not in html and "Second Half" not in html
    assert ('<a class="instructure_file_link" title="01_Selfie" '
            'href="/courses/42/files/501?wrap=1" '
            'data-api-endpoint="https://c.t/api/v1/courses/42/files/501" '
            'data-api-returntype="File">01_Selfie</a>') in html
    assert "<h2>Featured Interview: Anne Sullivan</h2>" in html
    embed = ('<p><iframe style="width: 640px; height: 360px; display: inline-block;" '
             'title="Anne Sullivan interview" data-media-type="video" '
             'src="/media_attachments_iframe/777?type=video&amp;embedded=true" '
             'allowfullscreen="allowfullscreen" allow="fullscreen" loading="lazy">'
             '</iframe></p>')
    assert embed in html
    assert deploy.VIDEO_EMBED_RE.search(html).group(0) == embed
    assert p["readings_placeholder"] == ""
    order = [html.index(s) for s in ("Readings", "Reading PDFs", "Featured Interview")]
    assert order == sorted(order)


def test_readings_page_placeholder_without_video(course):
    p = _plan(course, "exercises/two_comic", FakeMedia())
    assert p["readings_placeholder"] == (
        "<p><em>The interview with Erin Kathleen Bahl will be posted here.</em></p>")
    assert p["readings_placeholder"] in p["readings_html"]
    assert "Reading PDFs" not in p["readings_html"]
    assert "<iframe" not in p["readings_html"]


def test_readings_page_skipped_when_nothing_to_show(course):
    idx = course.parent / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8").replace("### Week Three", "### Wk 3"),
                   encoding="utf-8")
    md = course.parent / "exercises" / "two_comic.md"
    md.write_text(md.read_text(encoding="utf-8").replace("  interview: bahl\n", ""),
                  encoding="utf-8")
    assert _plan(course, "exercises/two_comic", FakeMedia())["readings_html"] == ""


def test_unknown_interview_key_is_an_error(course):
    md = course.parent / "exercises" / "two_comic.md"
    md.write_text(md.read_text(encoding="utf-8").replace("bahl", "nobody"), encoding="utf-8")
    with pytest.raises(SystemExit, match="nobody"):
        _plan(course, "exercises/two_comic", FakeMedia())


def test_module_order_puts_break_after_named_stem(course):
    assert deploy.module_order(_cfg(course)) == [
        "exercises/introductions", "exercises/one_selfie", "exercises/two_comic",
        "Week Ten: Spring Break", "exercises/reflection"]


def test_video_embed_regex_matches_iframe_left_inside_placeholder_em():
    live = ('<h2>Featured Interview: X</h2>\n<p><em><iframe style="width: 480px;" '
            'title="Video player for bahl.mp4" data-media-type="video" '
            'src="https://webcourses.ucf.edu/media_attachments_iframe/1?x=1">'
            '</iframe></em></p>\n<p>after</p>')
    m = deploy.VIDEO_EMBED_RE.search(live)
    assert m and m.group(0).startswith("<p><em><iframe")
    assert m.group(0).endswith("</iframe></em></p>") and "after" not in m.group(0)


# --- dry run ---------------------------------------------------------------------------

def test_dry_run_writes_previews_without_network_or_env(course, monkeypatch, capsys):
    for k in deploy.ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(requests.Session, "request",
                        lambda *a, **k: pytest.fail("network call on a dry run"))
    assert deploy.main(["--all", "--dry-run"]) == 0
    prev = course / "preview"
    for name in ("introductions.html", "introductions-readings.html",
                 "introductions-discussion.html", "one_selfie.html",
                 "one_selfie-readings.html", "one_selfie-discussion.html",
                 "two_comic-readings.html", "reflection.html", "reflection-assignment.html",
                 "welcome.html", "syllabus.html"):
        assert (prev / name).exists(), name
    assert not (prev / "reflection-readings.html").exists()
    out = capsys.readouterr().out
    assert "[dry-run] module 'Week Two: Selfie' | opens 2027-01-18T05:00:00Z" in out
    assert "[Making Exercises] due 2027-01-25T04:59:00Z" in out and "[rubric]" in out
    assert "assignment 'Final Reflection' 10pts [Course Requirements]" in out
    assert "+ page 'Welcome! (Read this first!)'" in out
    assert "+ assignment 'Activity Verification' 3pts due 2027-01-16T04:59:00Z" in out
    assert ("[dry-run] break module 'Week Ten: Spring Break' | opens 2027-03-15T04:00:00Z"
            in out)
    # missing media: warned, never fatal
    assert "[missing media] media/interviews/edited/bahl.mp4 not found (video)" in out
    assert "[missing media] media/pdfs/not_here.pdf not found (pdf)" in out
    readings = (prev / "one_selfie-readings.html").read_text(encoding="utf-8")
    assert "/media_attachments_iframe/FILE-sullivan.mp4" in readings
    assert "/courses/COURSE/files/FILE-01_Selfie.pdf?wrap=1" in readings
    assert "not_here" not in readings
    intro = (prev / "introductions-readings.html").read_text(encoding="utf-8")
    assert ">Provocations for Making</a>" in intro and ">RattoCriticalMaking</a>" in intro
    assert "Activity Verification" in intro            # the syllabus Due bullet stays
    syl = (prev / "syllabus.html").read_text(encoding="utf-8")
    assert f'href="{SITE}/exercises/one_selfie"' in syl
    welcome = (prev / "welcome.html").read_text(encoding="utf-8")
    assert f'href="{SITE}/exercises/introductions"' in welcome
    assert not (course / ".state.json").exists()


def test_dry_run_week_accepts_short_name(course, capsys):
    assert deploy.main(["--week", "two_comic", "--dry-run"]) == 0
    assert (course / "preview" / "two_comic.html").exists()
    assert not (course / "preview" / "syllabus.html").exists()
    with pytest.raises(SystemExit, match="not in course.yml"):
        deploy.main(["--week", "nope", "--dry-run"])


def test_missing_exercise_file_is_skipped_with_warning(course, capsys):
    (course.parent / "exercises" / "two_comic.md").unlink()
    assert deploy.main(["--all", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "[missing] exercises/two_comic.md not found; skipped" in out
    assert "[dry-run] module 'Week Two: Selfie'" in out


def test_exercise_without_canvas_block_is_a_clean_error(course):
    (course.parent / "exercises" / "two_comic.md").write_text("# no front matter\n",
                                                               encoding="utf-8")
    with pytest.raises(SystemExit, match="two_comic.md: missing 'canvas'"):
        deploy.main(["--all", "--dry-run"])


def test_simple_syllabus_cli_writes_preview(course):
    assert deploy.main(["--simple-syllabus"]) == 0
    html = (course / "preview" / "simple_syllabus.html").read_text(encoding="utf-8")
    assert 'data-component="Weekly Schedule"' in html
    assert f'href="{SITE}/exercises/one_selfie"' in html


# --- live deploys against a fake Canvas -------------------------------------------------

def _slug(title):
    return "".join(ch for ch in title.lower().replace(" ", "-") if ch.isalnum() or ch in "-+")


class FakeCanvas:
    """Records every call. `bodies` holds what live pages contain;
    `track_errors` HTTP failures for set_media_tracks."""
    def __init__(self, code="ENG6819-0W60", bodies=None, track_errors=0):
        self.calls, self.code = [], code
        self.bodies = dict(bodies or {})
        self.sent = {}
        self.track_errors = track_errors
        self.next_id = 100
    def _id(self):
        self.next_id += 1
        return self.next_id
    def of(self, kind): return [c for c in self.calls if c[0] == kind]
    def course_info(self): return {"name": "Critical Making", "course_code": self.code}
    def upsert_assignment_group(self, name):
        self.calls.append(("group", name)); return {"Making Exercises": 1}.get(name, 2)
    def upsert_module(self, name, unlock_at=None, published=None, known_id=None, position=None):
        self.calls.append(("module", name, position, unlock_at, published, known_id))
        return known_id or 10 + len(self.of("module"))
    def upsert_page(self, title, body, published=False, known_url=None):
        self.calls.append(("page", title, published, known_url)); self.sent[title] = body
        url = known_url or _slug(title); self.bodies[url] = body
        return url
    def find_page(self, title):
        return _slug(title) if _slug(title) in self.bodies else None
    def get_page_body(self, url): return self.bodies.get(url)
    def upsert_discussion(self, title, message, points, due_at, group, published=False,
                          known_id=None, unlock_at=None, lock_at=None):
        self.calls.append(("discussion", title, points, group, known_id))
        self.sent[title] = message
        tid = known_id or self._id()
        return {"id": tid, "assignment_id": tid + 1000}
    def upsert_assignment(self, name, points, due_at, group, types, published=False,
                          known_id=None, unlock_at=None, lock_at=None, description=None):
        self.calls.append(("assignment", name, points, group, tuple(types), known_id))
        self.sent[name] = description
        return known_id or self._id()
    def add_to_module(self, module_id, kind, ref, position=None):
        self.calls.append(("item", module_id, kind, ref, position))
    def upload_file(self, path, folder, ctype):
        self.calls.append(("upload", path.name, folder, ctype)); return {"id": self._id()}
    def set_media_tracks(self, attachment_id, tracks):
        self.calls.append(("tracks", attachment_id, tracks[0]["locale"], tracks[0]["kind"]))
        if self.track_errors:
            self.track_errors -= 1
            r = requests.Response(); r.status_code = 401
            raise requests.HTTPError("401 Unauthorized", response=r)
        return [{"id": 1}]
    def find_rubric(self, title):
        self.calls.append(("find-rubric", title)); return None
    def create_rubric(self, title, criteria, assignment_id, use_for_grading=True):
        self.calls.append(("create-rubric", title, assignment_id, use_for_grading))
        return 31, 61
    def associate_rubric(self, rubric_id, assignment_id, known_id=None, use_for_grading=True):
        self.calls.append(("associate", rubric_id, assignment_id, known_id, use_for_grading))
        return known_id or 62
    def update_rubric(self, rubric_id, title, criteria, association_id=None):
        self.calls.append(("update-rubric", rubric_id, association_id)); return rubric_id


def _live(monkeypatch, canvas, fake, state=None):
    for k, v in {"CANVAS_API_URL": "https://c.t", "CANVAS_API_TOKEN": "t",
                 "CANVAS_COURSE_ID": "42"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(deploy, "load_dotenv", lambda *a, **k: None)
    if state is not None:
        (canvas / ".state.json").write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr("canvas_client.CanvasClient", lambda *a: fake)
    return fake


def _state(canvas):
    return json.loads((canvas / ".state.json").read_text(encoding="utf-8"))


def _items(fake, module_id):
    return [(c[2], c[3], c[4]) for c in fake.of("item") if c[1] == module_id]


def test_live_full_deploy(course, monkeypatch, capsys):
    fake = _live(monkeypatch, course, FakeCanvas())
    assert deploy.main(["--all"]) == 0
    out = capsys.readouterr().out
    assert "deploying to: Critical Making (ENG6819-0W60)" in out
    # modules in course order, with positions and ET midnight unlocks
    mods = [(c[1], c[2], c[3]) for c in fake.of("module")]
    assert mods == [("Week One: Provocations", 1, "2027-01-11T05:00:00Z"),
                    ("Week Two: Selfie", 2, "2027-01-18T05:00:00Z"),
                    ("Week Three: Comic", 3, "2027-01-25T05:00:00Z"),
                    ("Week Ten: Spring Break", 4, "2027-03-15T04:00:00Z"),
                    ("Final Reflection", 5, "2027-04-26T04:00:00Z")]
    st = _state(course)
    intro = st["exercises/introductions"]
    # week one: welcome, readings, page, discussion, Activity Verification
    assert _items(fake, intro["module_id"]) == [
        ("Page", st["welcome_url"], 1), ("Page", intro["readings_url"], 2),
        ("Page", intro["page_url"], 3), ("Discussion", intro["discussion_id"], 4),
        ("Assignment", st["activity_verification_id"], 5)]
    av = [c for c in fake.of("assignment") if c[1] == "Activity Verification"]
    assert av == [("assignment", "Activity Verification", 3, 2, ("online_text_entry",), None)]
    assert ("discussion", "Introductions", 7, 2, None) in fake.calls      # Course Requirements
    selfie = st["exercises/one_selfie"]
    assert _items(fake, selfie["module_id"]) == [
        ("Page", selfie["readings_url"], 1), ("Page", selfie["page_url"], 2),
        ("Discussion", selfie["discussion_id"], 3)]
    assert ("discussion", 'Making Exercise One: "Selfie"', 7, 1, None) in fake.calls
    # break module: a single SubHeader
    brk = st["breaks"]["Week Ten: Spring Break"]
    assert _items(fake, brk) == [("SubHeader",
                                  "Enjoy the break! No readings or exercises this week.", 1)]
    # reflection: an assignment with url/upload submissions in Course Requirements
    refl = st["exercises/reflection"]
    assert ("assignment", "Final Reflection", 10, 2, ("online_url", "online_upload"),
            None) in fake.calls
    assert "Upload a document" in fake.sent["Final Reflection"]
    assert _items(fake, refl["module_id"])[-1] == ("Assignment", refl["assignment_id"], 2)
    # media: uploads to the right folders, captions on the uploaded video
    ups = sorted((c[1], c[2], c[3]) for c in fake.of("upload"))
    assert ups == [("00_Provacations.pdf", "Readings", "application/pdf"),
                   ("01_Selfie.pdf", "Readings", "application/pdf"),
                   ("RattoCriticalMaking.pdf", "Readings", "application/pdf"),
                   ("sullivan.mp4", "Interviews", "video/mp4")]
    vid = st["files"]["media/interviews/edited/sullivan.mp4"]["id"]
    assert fake.of("tracks") == [("tracks", vid, "en", "subtitles")]
    assert st["captions"]["sullivan"]["status"] == "done"
    readings = fake.sent["Week Two: Readings + Interview"]
    assert f"/media_attachments_iframe/{vid}?type=video&amp;embedded=true" in readings
    pdf = st["files"]["media/pdfs/01_Selfie.pdf"]["id"]
    assert f'href="/courses/42/files/{pdf}?wrap=1"' in readings
    # bahl's video is missing: placeholder, deploy continues
    assert "will be posted here" in fake.sent["Week Three: Readings + Interview"]
    assert "[missing media] media/interviews/edited/bahl.mp4" in out
    # rubric: created once with the first exercise, associated with the second
    assert fake.of("create-rubric") == [
        ("create-rubric", "Making Exercise Rubric", selfie["assignment_id"], True)]
    comic = st["exercises/two_comic"]
    assert fake.of("associate") == [("associate", 31, comic["assignment_id"], None, True)]
    assert st["rubric"]["id"] == 31
    assert selfie["rubric_association_id"] == 61 and comic["rubric_association_id"] == 62
    assert not fake.of("update-rubric")
    # syllabus and welcome pages
    assert "Syllabus" in fake.sent and st["syllabus_url"] == "syllabus"
    assert all(c[2] is False for c in fake.of("page"))          # unpublished by default


def test_live_publish_publishes_everything(course, monkeypatch):
    fake = _live(monkeypatch, course, FakeCanvas())
    assert deploy.main(["--all", "--publish"]) == 0
    assert all(c[2] is True for c in fake.of("page"))
    assert all(c[4] is True for c in fake.of("module"))


def test_second_run_reuses_ids_and_skips_unchanged_uploads(course, monkeypatch):
    _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--all"])
    first = _state(course)
    fake = _live(monkeypatch, course, FakeCanvas(bodies={}))
    assert deploy.main(["--all"]) == 0
    assert not fake.of("upload")                                # same sha256
    assert not fake.of("tracks")                                # captions done
    assert not fake.of("create-rubric") and not fake.of("find-rubric")
    selfie = first["exercises/one_selfie"]
    assert ("associate", 31, selfie["assignment_id"], 61, True) in fake.calls
    assert [c[5] for c in fake.of("module")] == [
        first[s]["module_id"] for s in ("exercises/introductions", "exercises/one_selfie",
                                        "exercises/two_comic")] + [
        first["breaks"]["Week Ten: Spring Break"], first["exercises/reflection"]["module_id"]]
    assert ("discussion", 'Making Exercise One: "Selfie"', 7, 1,
            selfie["discussion_id"]) in fake.calls


def test_changed_file_is_reuploaded_and_captions_redone(course, monkeypatch):
    _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--week", "one_selfie"])
    old = _state(course)["files"]["media/interviews/edited/sullivan.mp4"]["id"]
    (course / "media/interviews/edited/sullivan.mp4").write_bytes(b"a new cut")
    fake = _live(monkeypatch, course, FakeCanvas())
    assert deploy.main(["--week", "one_selfie"]) == 0
    assert [c[1] for c in fake.of("upload")] == ["sullivan.mp4"]
    new = _state(course)["files"]["media/interviews/edited/sullivan.mp4"]["id"]
    assert new != old and fake.of("tracks") == [("tracks", new, "en", "subtitles")]


def test_unchanged_size_and_mtime_skip_hashing(course, monkeypatch):
    _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--week", "one_selfie"])
    monkeypatch.setattr(assets, "sha256_file", lambda p: pytest.fail(f"hashed {p}"))
    fake = _live(monkeypatch, course, FakeCanvas())
    assert deploy.main(["--week", "one_selfie"]) == 0
    assert not fake.of("upload")


def test_captions_pending_then_retried(course, monkeypatch, capsys):
    fake = _live(monkeypatch, course, FakeCanvas(track_errors=1))
    assert deploy.main(["--week", "one_selfie"]) == 0          # never fatal
    st = _state(course)
    assert st["captions"]["sullivan"]["status"] == "pending"
    assert "[captions pending] media/interviews/captions/sullivan.vtt" in capsys.readouterr().out
    fake = _live(monkeypatch, course, FakeCanvas())
    assert deploy.main(["--week", "one_selfie"]) == 0
    assert len(fake.of("tracks")) == 1 and not fake.of("upload")
    assert _state(course)["captions"]["sullivan"]["status"] == "done"


def test_hand_uploaded_video_replaces_placeholder(course, monkeypatch, capsys):
    hand = ('<p><em><iframe style="width: 480px;" title="Video player for bahl.mp4" '
            'data-media-type="video" src="/media_attachments_iframe/900?type=video">'
            '</iframe></em></p>')
    live = "<h2>Featured Interview: Erin Kathleen Bahl</h2>" + hand + "<p>x</p>"
    state = {"exercises/two_comic": {"readings_url": "wk3-readings"}}
    fake = _live(monkeypatch, course, FakeCanvas(bodies={"wk3-readings": live}), state)
    assert deploy.main(["--week", "two_comic"]) == 0
    body = fake.sent["Week Three: Readings + Interview"]
    assert hand in body and "will be posted here" not in body
    assert ("page", "Week Three: Readings + Interview", False, "wk3-readings") in fake.calls
    assert "[kept] Week Three: Readings + Interview: hand-uploaded" in capsys.readouterr().out


def test_hand_uploaded_video_found_by_title_when_state_lost(course, monkeypatch):
    hand = ('<p><iframe data-media-type="video" src="/media_attachments_iframe/900">'
            '</iframe></p>')
    slug = _slug("Week Three: Readings + Interview")
    fake = _live(monkeypatch, course, FakeCanvas(bodies={slug: hand}))
    assert deploy.main(["--week", "two_comic"]) == 0
    assert hand in fake.sent["Week Three: Readings + Interview"]


def test_unrecognised_live_video_leaves_page_alone(course, monkeypatch, capsys):
    odd = '<div><iframe data-media-type="video" src="/media_attachments_iframe/9"></iframe></div>'
    state = {"exercises/two_comic": {"readings_url": "wk3-readings"}}
    fake = _live(monkeypatch, course, FakeCanvas(bodies={"wk3-readings": odd}), state)
    assert deploy.main(["--week", "two_comic"]) == 0
    assert "Week Three: Readings + Interview" not in fake.sent
    assert "page left as is" in capsys.readouterr().out
    # still in the module
    assert ("Page", "wk3-readings", 1) in _items(fake, _state(course)["exercises/two_comic"]
                                                  ["module_id"])


def test_uploaded_video_overrides_hand_upload(course, monkeypatch):
    hand = ('<p><iframe data-media-type="video" src="/media_attachments_iframe/900">'
            '</iframe></p>')
    state = {"exercises/one_selfie": {"readings_url": "wk2"}}
    fake = _live(monkeypatch, course, FakeCanvas(bodies={"wk2": hand}), state)
    deploy.main(["--week", "one_selfie"])
    body = fake.sent["Week Two: Readings + Interview"]
    assert "media_attachments_iframe/900" not in body and 'title="Anne Sullivan interview"' in body


def test_rubric_change_updates_rubric(course, monkeypatch):
    _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--week", "one_selfie"])
    yml = course / "course.yml"
    yml.write_text(yml.read_text(encoding="utf-8").replace("Two replies.", "Two replies!"),
                   encoding="utf-8")
    fake = _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--week", "one_selfie"])
    assert fake.of("update-rubric") == [("update-rubric", 31, 61)]
    fake = _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--week", "one_selfie"])
    assert not fake.of("update-rubric")


def test_existing_rubric_found_by_title_is_reused(course, monkeypatch):
    class Found(FakeCanvas):
        def find_rubric(self, title):
            self.calls.append(("find-rubric", title)); return 77
    fake = _live(monkeypatch, course, Found())
    deploy.main(["--week", "one_selfie"])
    assert not fake.of("create-rubric")
    assert fake.of("associate")[0][1] == 77
    assert fake.of("update-rubric") == [("update-rubric", 77, 62)]   # brought up to date


def test_rubric_not_graded_on_extra_credit(course, monkeypatch, capsys):
    md = course.parent / "exercises" / "two_comic.md"
    md.write_text(md.read_text(encoding="utf-8").replace(
        "  rubric: true\n", "  rubric: true\n  extra_credit: true\n"), encoding="utf-8")
    fake = _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--week", "two_comic"])
    assert fake.of("discussion")[0][2] == 0                 # points sent as 0
    assert fake.of("create-rubric")[0][3] is False


def test_rubric_points_mismatch_is_reported(course, monkeypatch, capsys):
    md = course.parent / "exercises" / "two_comic.md"
    md.write_text(md.read_text(encoding="utf-8").replace("points: 7", "points: 9"),
                  encoding="utf-8")
    _live(monkeypatch, course, FakeCanvas())
    deploy.main(["--week", "two_comic"])
    assert "totals 7 but Exercise Discussion: Week Three: Comic is worth 9" in \
        capsys.readouterr().out


def test_stale_rubric_association_is_recreated(course, monkeypatch):
    class Gone(FakeCanvas):
        def associate_rubric(self, rubric_id, assignment_id, known_id=None,
                             use_for_grading=True):
            if known_id:
                r = requests.Response(); r.status_code = 404
                raise requests.HTTPError("404", response=r)
            return super().associate_rubric(rubric_id, assignment_id, None, use_for_grading)
    state = {"rubric": {"id": 31, "sha256": deploy._sha(_cfg(course)["rubric"])},
             "exercises/two_comic": {"rubric_association_id": 5}}
    _live(monkeypatch, course, Gone(), state)
    assert deploy.main(["--week", "two_comic"]) == 0
    assert _state(course)["exercises/two_comic"]["rubric_association_id"] == 62


def test_activity_verification_frozen_but_kept_in_module(course, monkeypatch, capsys):
    monkeypatch.setattr(deploy, "now_et",
                        lambda: deploy.datetime(2027, 1, 11, 9, tzinfo=deploy.TZ))
    state = {"activity_verification_id": 55}
    fake = _live(monkeypatch, course, FakeCanvas(), state)
    assert deploy.main(["--week", "introductions", "--force"]) == 0
    # --force covers both the module and the AV
    assert [c for c in fake.of("assignment") if c[1] == "Activity Verification"]
    fake = _live(monkeypatch, course, FakeCanvas())
    monkeypatch.setattr(deploy, "av_is_live", lambda av, now=None: True)
    monkeypatch.setattr(deploy, "is_live", lambda d, now=None: False)
    assert deploy.main(["--week", "introductions"]) == 0
    assert not [c for c in fake.of("assignment") if c[1] == "Activity Verification"]
    mid = _state(course)["exercises/introductions"]["module_id"]
    assert ("Assignment", 55, 5) in _items(fake, mid)
    assert "[frozen] Activity Verification" in capsys.readouterr().out


def test_missing_welcome_file_is_a_warning(course, monkeypatch, capsys):
    (course.parent / "welcome.md").unlink()
    fake = _live(monkeypatch, course, FakeCanvas())
    assert deploy.main(["--week", "introductions"]) == 0
    assert "[missing] welcome.md not found" in capsys.readouterr().out
    assert "Welcome! (Read this first!)" not in fake.sent
    mid = _state(course)["exercises/introductions"]["module_id"]
    assert _items(fake, mid)[0][2] == 1 and _items(fake, mid)[0][0] == "Page"


def test_state_saved_when_deploy_fails_midway(course, monkeypatch):
    class Boom(FakeCanvas):
        def upsert_page(self, title, *a, **k):
            if title == "Making Exercise Two: Comic":
                r = requests.Response(); r.status_code = 500
                raise requests.HTTPError("500 Server Error", response=r)
            return super().upsert_page(title, *a, **k)
    _live(monkeypatch, course, Boom())
    with pytest.raises(SystemExit, match="deploy failed at 'exercises/two_comic'"):
        deploy.main(["--all"])
    st = _state(course)
    assert st["exercises/one_selfie"]["discussion_id"]
    assert st["exercises/two_comic"]["module_id"]
    assert "media/pdfs/01_Selfie.pdf" in st["files"]


def test_course_guard_aborts_on_wrong_course(course, monkeypatch):
    yml = course / "course.yml"
    yml.write_text(yml.read_text(encoding="utf-8") + "expect_course_code: '6819'\n",
                   encoding="utf-8")
    fake = _live(monkeypatch, course, FakeCanvas(code="ENG6806"))
    with pytest.raises(SystemExit, match="6819"):
        deploy.main(["--all"])
    assert fake.calls == []


@pytest.mark.parametrize("status, hint", [(401, "fresh CANVAS_API_TOKEN"), (403, "HTTP 403"),
                                          (404, "check CANVAS_COURSE_ID in .env")])
def test_course_info_http_error_is_a_clean_exit(course, monkeypatch, status, hint):
    class Rejected(FakeCanvas):
        def course_info(self):
            r = requests.Response(); r.status_code = status
            raise requests.HTTPError(f"{status} Client Error", response=r)
    _live(monkeypatch, course, Rejected())
    with pytest.raises(SystemExit, match=hint):
        deploy.main(["--week", "one_selfie"])


def test_missing_env_is_a_clean_exit_naming_the_env_path(course, monkeypatch):
    calls = []
    monkeypatch.setattr(deploy, "load_dotenv", lambda *a, **k: calls.append(a))
    for k in deploy.ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(SystemExit) as e:
        deploy.main(["--week", "one_selfie"])
    assert str(course / ".env") in str(e.value) and "CANVAS_API_URL" in str(e.value)
    assert calls and Path(calls[0][0]) == course / ".env"
