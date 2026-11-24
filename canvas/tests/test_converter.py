import textwrap
from datetime import date

import pytest
from converter import (
    ACCENT_COLOR, ACCENT_LABEL, apply_canvas_style, due_at_utc, extract_readings,
    kramdown_id, load_week, lock_at_utc, render_html, split_discussion, split_section,
    unlock_at_utc,
)

SITE = "https://anastasiasalter.net/CriticalMaking2027"


def test_load_week_parses_canvas_block(tmp_path):
    f = tmp_path / "one_selfie.md"
    f.write_text(textwrap.dedent("""\
        ---
        title: "Making Exercise One: Selfie"
        canvas:
          module: "Week Two: Selfie"
          week_start: 2027-01-18
          due: 2027-01-24
          points: 7
          discussion: true
        ---
        # Week Two
        """), encoding="utf-8")
    doc = load_week(f)
    assert doc.canvas["points"] == 7
    assert doc.meta["title"] == "Making Exercise One: Selfie"
    assert doc.body.startswith("# Week Two")


def test_load_week_rejects_missing_keys(tmp_path):
    f = tmp_path / "bad.md"
    f.write_text("---\ncanvas:\n  module: X\n---\nbody", encoding="utf-8")
    with pytest.raises(ValueError, match="due"):
        load_week(f)


def test_load_week_needs_no_unit_and_rejects_bad_type(tmp_path):
    f = tmp_path / "x.md"
    base = ("---\ncanvas:\n  module: M\n  week_start: 2027-01-18\n  due: 2027-01-24\n"
            "  points: 7\n")
    f.write_text(base + "---\nbody", encoding="utf-8")
    assert load_week(f).canvas["module"] == "M"
    f.write_text(base + "  type: quiz\n---\nbody", encoding="utf-8")
    with pytest.raises(ValueError, match="type"):
        load_week(f)


def test_load_week_rejects_file_without_canvas_block(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("# just markdown\n", encoding="utf-8")
    with pytest.raises(ValueError, match="canvas"):
        load_week(f)


# --- link rewriting ------------------------------------------------------------

def test_root_page_links_resolve_against_site_root():
    html = render_html("[wk2](exercises/two_comic) [r](exercises/reflection.md) "
                       "![e](img/x.png)", SITE)
    assert f'href="{SITE}/exercises/two_comic"' in html          # extensionless kept
    assert f'href="{SITE}/exercises/reflection.html"' in html     # .md -> .html
    assert f'src="{SITE}/img/x.png"' in html


def test_exercise_page_links_resolve_against_their_directory():
    md = ("![o](../img/original.jpg) [c](two_comic) [s](../index.md#weekly-schedule) "
          "[m](materials/kit.zip) [d](./three_gifs.md?x=1)")
    html = render_html(md, SITE, "exercises")
    assert f'src="{SITE}/img/original.jpg"' in html
    assert f'href="{SITE}/exercises/two_comic"' in html
    assert f'href="{SITE}/index.html#weekly-schedule"' in html
    assert f'href="{SITE}/exercises/materials/kit.zip"' in html
    assert f'href="{SITE}/exercises/three_gifs.html?x=1"' in html


def test_render_leaves_absolute_anchor_and_canvas_links():
    html = render_html("[a](https://claude.ai) [b](#discussion) [c](mailto:a@b.c) "
                       "[d](/courses/1/files/2)", SITE, "exercises")
    assert 'href="https://claude.ai"' in html
    assert 'href="#discussion"' in html
    assert 'href="mailto:a@b.c"' in html
    assert 'href="/courses/1/files/2"' in html


def test_parent_traversal_above_site_root_is_kept():
    html = render_html("[up](../other/page.md)", "https://x.y")
    assert 'href="https://x.y/../other/page.html"' in html


def test_render_adds_heading_ids():
    assert '<h2 id="ai-use-policy">AI Use Policy</h2>' in render_html("## AI Use Policy",
                                                                       "https://x.y")


def test_kramdown_id_matches_jekyll_toc():
    assert (kramdown_id("Week Two: Selfie (Monday, January 18)")
            == "week-two-selfie-monday-january-18")
    assert kramdown_id("AI Use Policy") == "ai-use-policy"


# --- splitting and readings ------------------------------------------------------

def test_split_discussion():
    page, disc = split_discussion("intro\n\n### Discussion\n\nQ1?\nQ2?")
    assert page == "intro" and disc == "Q1?\nQ2?"


def test_split_without_marker_returns_empty():
    assert split_discussion("intro only") == ("intro only", "")


def test_split_submission():
    page, sub = split_section("intro\n\n### Discussion\n\nnot me\n\n### Submission\n\nUp.",
                              "Submission")
    assert "not me" in page and sub == "Up."


SYLLABUS = textwrap.dedent("""\
    ## Weekly Schedule

    ### Week One: Provocations (Monday, January 11)

    - Ratto (PDF)
    - **Due: Activity Verification (Friday, January 15)**

    ### Week Two: Selfie (Monday, January 18)

    - *Unflattening* - First Half
    - **Featured Guest: Anne Sullivan**
    - **[Making Exercise One: "Selfie"](exercises/one_selfie)**

    #### Explore

    - [*Game Poems*](https://www.gamepoems.com/)

    ### Week Ten: Spring Break (March 15 - 21)

    ### Week Eleven: Generation (Monday, March 22)

    - Mollick
    - **[Optional Making Exercise Thirteen: Tools](exercises/thirteen_tools)**
    """)


def test_extract_readings_skips_guest_and_exercise_bullets_keeps_explore():
    out = extract_readings(SYLLABUS, "Week Two")
    assert "Unflattening" in out
    assert "Featured Guest" not in out and "Making Exercise" not in out
    assert "#### Explore" in out and "Game Poems" in out
    assert "Ratto" not in out and "Mollick" not in out


def test_extract_readings_other_weeks():
    assert "Ratto" in extract_readings(SYLLABUS, "Week One")
    assert "Week Eleven" not in extract_readings(SYLLABUS, "Week One")
    eleven = extract_readings(SYLLABUS, "Week Eleven")
    assert "Mollick" in eleven and "Optional" not in eleven
    assert extract_readings(SYLLABUS, "Week Ten") == ""     # the break: no readings
    assert extract_readings(SYLLABUS, "Week Nine") == ""    # no such heading


# --- dates (America/New_York) -----------------------------------------------------

def test_due_at_utc_2027_dates_and_dst():
    assert due_at_utc(date(2027, 1, 24)) == "2027-01-25T04:59:00Z"     # EST
    # Sunday March 14 2027 is the spring-forward day: 23:59 EDT = 03:59Z
    assert due_at_utc(date(2027, 3, 14)) == "2027-03-15T03:59:00Z"
    assert due_at_utc(date(2027, 3, 21)) == "2027-03-22T03:59:00Z"     # a close date


def test_unlock_at_utc_midnight_et():
    assert unlock_at_utc(date(2027, 1, 18)) == "2027-01-18T05:00:00Z"
    assert unlock_at_utc(date(2027, 3, 15)) == "2027-03-15T04:00:00Z"


def test_lock_at_utc_one_week_grace_across_dst():
    assert lock_at_utc(date(2027, 1, 24)) == "2027-02-01T04:59:00Z"
    # due Sun Mar 7 (EST) -> locks Sun Mar 14 23:59 EDT
    assert lock_at_utc(date(2027, 3, 7)) == "2027-03-15T03:59:00Z"
    assert lock_at_utc(date(2027, 1, 24), grace_hours=24) == "2027-01-26T04:59:00Z"


def test_apply_canvas_style_band():
    out = apply_canvas_style("<p>x</p>")
    assert f"border-top: 6px solid {ACCENT_COLOR}" in out
    assert f">{ACCENT_LABEL}</span>" in out
    assert out.endswith("<p>x</p>")
