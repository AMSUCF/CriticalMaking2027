import json
from urllib.parse import parse_qsl

import pytest
import requests
import responses
from canvas_client import CanvasClient, _MultipartFile

API = "https://canvas.test"
COURSE = f"{API}/api/v1/courses/42"


def c42(**kw):
    return CanvasClient(API, "tok", "42", **kw)


def sent(call):
    return json.loads(call.request.body)


def form(call):
    return dict(parse_qsl(call.request.body, keep_blank_values=True))


# --- modules, pages, discussions, assignments --------------------------------------

@responses.activate
def test_upsert_module_finds_existing():
    responses.get(f"{COURSE}/modules", json=[{"id": 7, "name": "Week Two: Selfie"}])
    responses.put(f"{COURSE}/modules/7", json={"id": 7})
    assert c42().upsert_module("Week Two: Selfie") == 7


@responses.activate
def test_upsert_module_creates_with_unlock_and_position():
    responses.get(f"{COURSE}/modules", json=[])
    rsp = responses.post(f"{COURSE}/modules", json={"id": 9})
    assert c42().upsert_module("Week Ten: Spring Break", unlock_at="2027-03-15T04:00:00Z",
                               position=11) == 9
    assert sent(rsp.calls[0])["module"] == {"name": "Week Ten: Spring Break",
                                            "unlock_at": "2027-03-15T04:00:00Z",
                                            "position": 11}


@responses.activate
def test_upsert_module_known_id_skips_lookup():
    responses.put(f"{COURSE}/modules/7", json={"id": 7})
    assert c42().upsert_module("M", known_id=7, published=True) == 7
    assert len(responses.calls) == 1


@responses.activate
def test_upsert_discussion_creates_graded_and_returns_topic():
    responses.get(f"{COURSE}/discussion_topics", json=[])
    rsp = responses.post(f"{COURSE}/discussion_topics", json={"id": 43, "assignment_id": 99})
    topic = c42().upsert_discussion("T", "<p>m</p>", 7, "2027-01-25T04:59:00Z", 5,
                                    unlock_at="2027-01-18T05:00:00Z",
                                    lock_at="2027-02-01T04:59:00Z")
    assert topic == {"id": 43, "assignment_id": 99}
    body = sent(rsp.calls[0])
    assert body["assignment"] == {"points_possible": 7, "due_at": "2027-01-25T04:59:00Z",
                                  "assignment_group_id": 5,
                                  "unlock_at": "2027-01-18T05:00:00Z",
                                  "lock_at": "2027-02-01T04:59:00Z"}
    assert body["published"] is False


@responses.activate
def test_upsert_discussion_matches_exact_title():
    responses.get(f"{COURSE}/discussion_topics",
                  json=[{"id": 1, "title": "T2"}, {"id": 2, "title": "T"}])
    responses.put(f"{COURSE}/discussion_topics/2", json={"id": 2, "assignment_id": 5})
    assert c42().upsert_discussion("T", "m", 7, None, 5)["id"] == 2


@responses.activate
def test_upsert_assignment_creates_with_description():
    responses.get(f"{COURSE}/assignments", json=[])
    rsp = responses.post(f"{COURSE}/assignments", json={"id": 44})
    assert c42().upsert_assignment("Final Reflection", 10, "2027-05-03T03:59:00Z", 5,
                                   ["online_url", "online_upload"],
                                   description="<p>Up.</p>") == 44
    a = sent(rsp.calls[0])["assignment"]
    assert a["submission_types"] == ["online_url", "online_upload"]
    assert a["description"] == "<p>Up.</p>" and a["published"] is False


@responses.activate
def test_upsert_assignment_updates_known_id():
    responses.put(f"{COURSE}/assignments/42", json={"id": 42})
    assert c42().upsert_assignment("Activity Verification", 3, None, 5,
                                   ["online_text_entry"], known_id=42) == 42


@responses.activate
def test_upsert_page_known_url_updates_in_place():
    rsp = responses.put(f"{COURSE}/pages/week-two-readings", json={"url": "week-two-readings"})
    assert c42().upsert_page("Week Two: Readings + Interview", "<p>b</p>", True,
                             known_url="week-two-readings") == "week-two-readings"
    assert sent(rsp.calls[0])["wiki_page"]["published"] is True


@responses.activate
def test_upsert_page_creates_when_missing():
    responses.get(f"{COURSE}/pages", json=[{"title": "Other", "url": "other"}])
    responses.post(f"{COURSE}/pages", json={"url": "syllabus"})
    assert c42().upsert_page("Syllabus", "<p/>") == "syllabus"


@responses.activate
def test_find_page_and_get_page_body():
    responses.get(f"{COURSE}/pages", json=[{"title": "Syllabus", "url": "syllabus"}])
    responses.get(f"{COURSE}/pages/syllabus", json={"body": "<p>x</p>"})
    responses.get(f"{COURSE}/pages/nope", status=404)
    c = c42()
    assert c.find_page("Syllabus") == "syllabus" and c.find_page("Nope") is None
    assert c.get_page_body("syllabus") == "<p>x</p>"
    assert c.get_page_body("nope") is None


@responses.activate
def test_add_to_module_repositions_existing_item():
    responses.get(f"{COURSE}/modules/7/items",
                  json=[{"id": 1, "type": "Page", "page_url": "lec", "position": 2}])
    rsp = responses.put(f"{COURSE}/modules/7/items/1", json={"id": 1})
    c42().add_to_module(7, "Page", "lec", position=1)
    assert sent(rsp.calls[0])["module_item"]["position"] == 1


@responses.activate
def test_add_to_module_skips_put_when_position_matches():
    responses.get(f"{COURSE}/modules/7/items",
                  json=[{"id": 1, "type": "Discussion", "content_id": 5, "position": 3}])
    c42().add_to_module(7, "Discussion", 5, position=3)
    assert len(responses.calls) == 1


@responses.activate
def test_add_to_module_creates_assignment_item():
    responses.get(f"{COURSE}/modules/7/items", json=[])
    rsp = responses.post(f"{COURSE}/modules/7/items", json={"id": 3})
    c42().add_to_module(7, "Assignment", 8, position=4)
    assert sent(rsp.calls[0])["module_item"] == {"type": "Assignment", "content_id": 8,
                                                 "position": 4}


@responses.activate
def test_add_to_module_subheader_matched_by_text():
    responses.get(f"{COURSE}/modules/7/items", json=[])
    rsp = responses.post(f"{COURSE}/modules/7/items", json={"id": 3})
    c42().add_to_module(7, "SubHeader", "Enjoy the break!", position=1)
    assert sent(rsp.calls[0])["module_item"] == {"type": "SubHeader",
                                                 "title": "Enjoy the break!", "position": 1}
    responses.get(f"{COURSE}/modules/8/items",
                  json=[{"id": 4, "type": "SubHeader", "title": "Enjoy the break!",
                         "position": 1}])
    c42().add_to_module(8, "SubHeader", "Enjoy the break!", position=1)
    assert len(responses.calls) == 3          # found: no second POST


@responses.activate
def test_course_info():
    responses.get(COURSE, json={"name": "N", "course_code": "ENG6819"})
    assert c42().course_info()["course_code"] == "ENG6819"


@responses.activate
def test_pagination_follows_link_header():
    responses.get(f"{COURSE}/modules", json=[{"id": 1, "name": "A"}],
                  headers={"Link": f'<{COURSE}/modules?page=2>; rel="next"'})
    responses.get(f"{COURSE}/modules?page=2", json=[{"id": 2, "name": "B"}])
    responses.put(f"{COURSE}/modules/2", json={"id": 2})
    assert c42().upsert_module("B") == 2


# --- uploads ----------------------------------------------------------------------

@responses.activate
def test_upload_file_three_step_streams_the_file(tmp_path):
    f = tmp_path / "FAN - ESC masks.pdf"
    f.write_bytes(b"%PDF" + b"x" * 5000)
    responses.post(f"{COURSE}/files", json={"upload_url": "https://up.test/x",
                                            "upload_params": {"key": "k", "acl": "private"}})
    responses.post("https://up.test/x", status=302,
                   headers={"Location": f"{API}/api/v1/files/7/create_success"})
    responses.get(f"{API}/api/v1/files/7/create_success", json={"id": 7})
    assert c42().upload_file(f, "Readings", "application/pdf")["id"] == 7
    pre = sent(responses.calls[0])
    assert pre == {"name": "FAN - ESC masks.pdf", "size": 5004,
                   "content_type": "application/pdf", "parent_folder_path": "Readings",
                   "on_duplicate": "overwrite"}
    up = responses.calls[1].request
    assert "Authorization" not in up.headers       # never send the token to the upload host
    assert up.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    # (responses reads the stream to record it)
    body = up.body if isinstance(up.body, bytes) else up.body.read()
    assert b'name="key"\r\n\r\nk\r\n' in body and b"%PDF" + b"x" * 5000 in body
    assert up.headers["Content-Length"] == str(len(body))


def test_requests_streams_the_multipart_body(tmp_path):
    # requests keeps the object as the body (read in blocks by http.client)
    # and sends a Content-Length, not chunked encoding
    f = tmp_path / "v.mp4"; f.write_bytes(b"v" * 3000)
    body = _MultipartFile({"k": "v"}, f, f.name, "video/mp4")
    prep = requests.Request("POST", "https://up.test/x", data=body,
                            headers={"Content-Type": body.content_type}).prepare()
    assert prep.body is body
    assert prep.headers["Content-Length"] == str(len(body))
    assert "Transfer-Encoding" not in prep.headers


def test_multipart_stream_is_well_formed(tmp_path):
    f = tmp_path / "v.mp4"
    payload = bytes(range(256)) * 9000              # > 2 MB, several chunks
    f.write_bytes(payload)
    body = _MultipartFile({"key": "k", "Policy": "p"}, f, f.name, "video/mp4")
    data = b"".join(iter(lambda: body.read(65536), b""))
    assert len(data) == len(body)
    b = body.boundary.encode()
    assert data.startswith(b"--" + b + b'\r\nContent-Disposition: form-data; name="key"')
    assert b'name="file"; filename="v.mp4"\r\nContent-Type: video/mp4\r\n\r\n' + payload[:10] in data
    assert data.endswith(payload[-10:] + b"\r\n--" + b + b"--\r\n")
    assert payload in data


@responses.activate
def test_upload_file_with_json_success_body(tmp_path):
    f = tmp_path / "a.pdf"; f.write_bytes(b"%PDF")
    responses.post(f"{COURSE}/files", json={"upload_url": "https://up.test/x",
                                            "upload_params": {}})
    responses.post("https://up.test/x", status=201,
                   json={"location": f"{API}/api/v1/files/8"})
    responses.get(f"{API}/api/v1/files/8", json={"id": 8})
    assert c42().upload_file(f, "Readings", "application/pdf")["id"] == 8


# --- media tracks -------------------------------------------------------------------

TRACKS = [{"locale": "en", "content": "WEBVTT\n\n00:00.000 --> 00:01.000\nHi\n",
           "kind": "subtitles"}]


@responses.activate
def test_set_media_tracks_puts_json_array():
    url = f"{API}/api/v1/media_attachments/7/media_tracks"
    responses.put(url, json=[{"id": 1, "locale": "en"}])
    assert c42().set_media_tracks(7, TRACKS) == [{"id": 1, "locale": "en"}]
    req = responses.calls[0].request
    assert json.loads(req.body) == TRACKS
    assert "include%5B%5D=content" in req.url


@responses.activate
def test_set_media_tracks_retries_until_media_object_exists():
    url = f"{API}/api/v1/media_attachments/7/media_tracks"
    responses.put(url, status=401, json={"status": "unauthorized"})
    responses.put(url, status=404)
    responses.put(url, json=[{"id": 1}])
    waits = []
    assert c42(sleep=waits.append).set_media_tracks(7, TRACKS) == [{"id": 1}]
    assert waits == [5, 15]


@responses.activate
def test_set_media_tracks_gives_up_after_retries():
    url = f"{API}/api/v1/media_attachments/7/media_tracks"
    for _ in range(4):
        responses.put(url, status=401)
    waits = []
    with pytest.raises(requests.HTTPError):
        c42(sleep=waits.append).set_media_tracks(7, TRACKS)
    assert waits == [5, 15, 30] and len(responses.calls) == 4


# --- rubrics ----------------------------------------------------------------------

CRITERIA = [{"description": "Process documentation", "long": "Five images.", "points": 3},
            {"description": "Peer responses", "points": 2}]


@responses.activate
def test_create_rubric_associates_for_grading():
    rsp = responses.post(f"{COURSE}/rubrics",
                         json={"rubric": {"id": 31}, "rubric_association": {"id": 61}})
    assert c42().create_rubric("Making Exercise Rubric", CRITERIA, 99) == (31, 61)
    f = form(rsp.calls[0])
    assert f["rubric[title]"] == "Making Exercise Rubric"
    assert f["rubric[criteria][0][description]"] == "Process documentation"
    assert f["rubric[criteria][0][long_description]"] == "Five images."
    assert f["rubric[criteria][0][points]"] == "3"
    assert f["rubric[criteria][0][ratings][0][points]"] == "3"
    assert f["rubric[criteria][0][ratings][1][points]"] == "0"
    assert f["rubric[criteria][1][long_description]"] == ""
    assert f["rubric_association[association_id]"] == "99"
    assert f["rubric_association[association_type]"] == "Assignment"
    assert f["rubric_association[use_for_grading]"] == "1"
    assert f["rubric_association[purpose]"] == "grading"
    assert f["skip_updating_points_possible"] == "true"


@responses.activate
def test_associate_rubric_post_then_put_known():
    post = responses.post(f"{COURSE}/rubric_associations",
                          json={"rubric": {"id": 31}, "rubric_association": {"id": 62}})
    put = responses.put(f"{COURSE}/rubric_associations/62",
                        json={"rubric": {"id": 31}, "rubric_association": {"id": 62}})
    assert c42().associate_rubric(31, 100) == 62
    assert c42().associate_rubric(31, 100, known_id=62, use_for_grading=False) == 62
    f = form(post.calls[0])
    assert f == {"rubric_association[rubric_id]": "31",
                 "rubric_association[association_id]": "100",
                 "rubric_association[association_type]": "Assignment",
                 "rubric_association[use_for_grading]": "1",
                 "rubric_association[purpose]": "grading"}
    assert form(put.calls[0])["rubric_association[use_for_grading]"] == "0"


@responses.activate
def test_update_rubric_and_find_rubric():
    rsp = responses.put(f"{COURSE}/rubrics/31", json={"rubric": {"id": 31}})
    responses.get(f"{COURSE}/rubrics", json=[{"id": 31, "title": "Making Exercise Rubric"}])
    assert c42().update_rubric(31, "Making Exercise Rubric", CRITERIA, association_id=62) == 31
    assert form(rsp.calls[0])["rubric_association_id"] == "62"
    assert c42().find_rubric("Making Exercise Rubric") == 31
    assert c42().find_rubric("Other") is None


@responses.activate
def test_set_course_image_puts_image_id():
    responses.put(COURSE, json={"id": 42, "image_id": "55"})
    c42().set_course_image(55)
    assert sent(responses.calls[0]) == {"course": {"image_id": 55}}
