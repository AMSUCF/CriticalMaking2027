from __future__ import annotations

import time
import uuid
from pathlib import Path

import requests


class _MultipartFile:
    """A multipart/form-data body that streams one file from disk.

    requests sends an object with __len__ and read() as a streamed body with
    a Content-Length header, so an 850 MB interview is never held in memory.
    """

    CHUNK = 1024 * 1024

    def __init__(self, fields: dict, path: Path, filename: str, content_type: str):
        self.boundary = uuid.uuid4().hex
        b = self.boundary
        head = b"".join(
            f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
            for k, v in fields.items())
        safe = filename.replace('"', "%22")
        head += (f'--{b}\r\nContent-Disposition: form-data; name="file"; '
                 f'filename="{safe}"\r\nContent-Type: {content_type}\r\n\r\n').encode()
        self._parts = [head, None, f"\r\n--{b}--\r\n".encode()]
        self._path = path
        self._size = path.stat().st_size
        self._len = len(head) + self._size + len(self._parts[2])
        self._idx, self._buf, self._fh = 0, b"", None

    @property
    def content_type(self) -> str:
        return f"multipart/form-data; boundary={self.boundary}"

    def __len__(self) -> int:
        return self._len

    def read(self, n: int = -1) -> bytes:
        n = self.CHUNK if n is None or n < 0 else n
        out = b""
        while len(out) < n and self._idx < 3:
            if self._idx == 1:
                if self._fh is None:
                    self._fh = open(self._path, "rb")
                data = self._fh.read(n - len(out))
                if data:
                    out += data
                    continue
                self._fh.close()
                self._idx += 1
                continue
            if not self._buf:
                self._buf = self._parts[self._idx]
            take, self._buf = self._buf[: n - len(out)], self._buf[n - len(out):]
            out += take
            if not self._buf:
                self._idx += 1
        return out

    def __iter__(self):
        while True:
            chunk = self.read(self.CHUNK)
            if not chunk:
                return
            yield chunk


def _form(prefix: str, value, out: list) -> list:
    """Flatten nested dicts into Rails-style form fields: a[b][c]=v."""
    if isinstance(value, dict):
        for k, v in value.items():
            _form(f"{prefix}[{k}]" if prefix else str(k), v, out)
    elif isinstance(value, bool):
        out.append((prefix, "1" if value else "0"))
    else:
        out.append((prefix, str(value)))
    return out


def rubric_criteria(criteria: list[dict]) -> dict:
    """course.yml criteria -> Canvas's indexed criteria hash, each with a
    full-marks and a no-marks rating."""
    out = {}
    for i, c in enumerate(criteria):
        pts = c["points"]
        out[str(i)] = {
            "description": c["description"],
            "long_description": c.get("long", ""),
            "points": pts,
            "ratings": {"0": {"description": "Full Marks", "points": pts},
                        "1": {"description": "No Marks", "points": 0}},
        }
    return out


class CanvasClient:
    # seconds to wait between media-track attempts while Canvas builds the
    # media object for a freshly uploaded video
    caption_retry_delays = (5, 15, 30)

    def __init__(self, base_url: str, token: str, course_id: str, session=None,
                 sleep=time.sleep):
        self.root = f"{base_url.rstrip('/')}/api/v1"
        self.course_id = str(course_id)
        self.course = f"{self.root}/courses/{course_id}"
        self.s = session or requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"
        self.sleep = sleep

    def _get_all(self, url: str, **params) -> list:
        out, params = [], {"per_page": 100, **params}
        while url:
            r = self.s.get(url, params=params)
            r.raise_for_status()
            out.extend(r.json())
            url = r.links.get("next", {}).get("url")
            params = {}
        return out

    def _post(self, url: str, payload: dict) -> dict:
        r = self.s.post(url, json=payload)
        r.raise_for_status()
        return r.json()

    def _put(self, url: str, payload: dict) -> dict:
        r = self.s.put(url, json=payload)
        r.raise_for_status()
        return r.json()

    # --- modules, pages, discussions, assignments ---------------------------

    def upsert_module(self, name: str, unlock_at: str | None = None,
                      published: bool | None = None,
                      known_id: int | None = None,
                      position: int | None = None) -> int:
        payload = {"module": {"name": name}}
        if unlock_at is not None:
            payload["module"]["unlock_at"] = unlock_at
        if published is not None:
            payload["module"]["published"] = published
        if position is not None:
            payload["module"]["position"] = position
        if known_id is not None:
            return self._put(f"{self.course}/modules/{known_id}", payload)["id"]
        for m in self._get_all(f"{self.course}/modules"):
            if m["name"] == name:
                return self._put(f"{self.course}/modules/{m['id']}", payload)["id"]
        return self._post(f"{self.course}/modules", payload)["id"]

    def upsert_page(self, title: str, body: str, published: bool = False,
                    known_url: str | None = None) -> str:
        payload = {"wiki_page": {"title": title, "body": body, "published": published}}
        if known_url is not None:
            return self._put(f"{self.course}/pages/{known_url}", payload)["url"]
        for p in self._get_all(f"{self.course}/pages", search_term=title):
            if p["title"] == title:
                return self._put(f"{self.course}/pages/{p['url']}", payload)["url"]
        return self._post(f"{self.course}/pages", payload)["url"]

    def find_page(self, title: str) -> str | None:
        """The url slug of the page titled exactly `title`, else None."""
        for p in self._get_all(f"{self.course}/pages", search_term=title):
            if p["title"] == title:
                return p["url"]
        return None

    def get_page_body(self, url: str) -> str | None:
        r = self.s.get(f"{self.course}/pages/{url}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json().get("body") or ""

    def upsert_assignment_group(self, name: str) -> int:
        for g in self._get_all(f"{self.course}/assignment_groups"):
            if g["name"] == name:
                return g["id"]
        return self._post(f"{self.course}/assignment_groups", {"name": name})["id"]

    def upsert_discussion(self, title: str, message: str, points: int,
                          due_at: str | None, assignment_group_id: int,
                          published: bool = False,
                          known_id: int | None = None,
                          unlock_at: str | None = None,
                          lock_at: str | None = None) -> dict:
        """Create or update a graded discussion; returns the topic JSON
        (`id`, and `assignment_id` for the rubric)."""
        assignment = {"points_possible": points, "due_at": due_at,
                      "assignment_group_id": assignment_group_id}
        if unlock_at is not None:
            assignment["unlock_at"] = unlock_at
        if lock_at is not None:
            assignment["lock_at"] = lock_at
        payload = {
            "title": title, "message": message, "published": published,
            "assignment": assignment,
        }
        if known_id is None:
            for d in self._get_all(f"{self.course}/discussion_topics"):
                if d["title"] == title:
                    known_id = d["id"]
                    break
        if known_id is not None:
            return self._put(f"{self.course}/discussion_topics/{known_id}", payload)
        return self._post(f"{self.course}/discussion_topics", payload)

    def upsert_assignment(self, name: str, points: int, due_at: str | None,
                          assignment_group_id: int,
                          submission_types: list[str],
                          published: bool = False,
                          known_id: int | None = None,
                          unlock_at: str | None = None,
                          lock_at: str | None = None,
                          description: str | None = None) -> int:
        payload = {
            "assignment": {
                "name": name, "points_possible": points, "due_at": due_at,
                "assignment_group_id": assignment_group_id,
                "submission_types": submission_types, "published": published,
            }
        }
        if unlock_at is not None:
            payload["assignment"]["unlock_at"] = unlock_at
        if lock_at is not None:
            payload["assignment"]["lock_at"] = lock_at
        if description is not None:
            payload["assignment"]["description"] = description
        if known_id is None:
            for a in self._get_all(f"{self.course}/assignments"):
                if a["name"] == name:
                    known_id = a["id"]
                    break
        if known_id is not None:
            return self._put(f"{self.course}/assignments/{known_id}", payload)["id"]
        return self._post(f"{self.course}/assignments", payload)["id"]

    def add_to_module(self, module_id: int, item_type: str, ref,
                      position: int | None = None) -> None:
        """Put an item in a module at `position` (an item already there is
        moved to it). For a SubHeader, `ref` is its text."""
        items = self._get_all(f"{self.course}/modules/{module_id}/items")
        if item_type == "Page":
            found = next((i for i in items if i.get("page_url") == ref), None)
            item = {"type": "Page", "page_url": ref}
        elif item_type == "SubHeader":
            found = next((i for i in items
                          if i["type"] == "SubHeader" and i.get("title") == ref), None)
            item = {"type": "SubHeader", "title": ref}
        else:
            found = next((i for i in items
                          if i.get("content_id") == ref and i["type"] == item_type), None)
            item = {"type": item_type, "content_id": ref}
        if found is not None:
            if position is not None and found.get("position") != position:
                self._put(f"{self.course}/modules/{module_id}/items/{found['id']}",
                          {"module_item": {"position": position}})
            return
        if position is not None:
            item["position"] = position
        self._post(f"{self.course}/modules/{module_id}/items", {"module_item": item})

    def course_info(self) -> dict:
        r = self.s.get(self.course)
        r.raise_for_status()
        return r.json()

    def set_course_image(self, file_id) -> dict:
        """Dashboard card image: an uploaded course file's id."""
        return self._put(self.course, {"course": {"image_id": file_id}})

    # --- files and media ----------------------------------------------------

    def upload_file(self, path, folder: str, content_type: str) -> dict:
        """Canvas three-step upload; replaces a same-named file in `folder`.
        The file is streamed from disk, never read whole into memory."""
        path = Path(path)
        size = path.stat().st_size
        pre = self._post(f"{self.course}/files", {
            "name": path.name, "size": size, "content_type": content_type,
            "parent_folder_path": folder, "on_duplicate": "overwrite"})
        body = _MultipartFile(pre.get("upload_params") or {}, path, path.name, content_type)
        # step 2 goes to the storage host, which must not get our token
        r = requests.post(pre["upload_url"], data=body,
                          headers={"Content-Type": body.content_type},
                          allow_redirects=False)
        if r.is_redirect:
            r = self.s.get(r.headers["Location"])
        r.raise_for_status()
        out = r.json()
        if "id" not in out and out.get("location"):
            out = self.s.get(out["location"]).json()
        return out

    def set_media_tracks(self, attachment_id, tracks: list[dict]) -> list:
        """Replace an uploaded video's caption tracks.

        PUT /api/v1/media_attachments/:attachment_id/media_tracks with a JSON
        array of {locale, content, kind}. Canvas answers 401/404 (or 5xx)
        until it has built the video's media object, so this retries on
        `caption_retry_delays` and re-raises the last error if it never
        succeeds.
        """
        url = f"{self.root}/media_attachments/{attachment_id}/media_tracks"
        delays = list(self.caption_retry_delays)
        while True:
            r = self.s.put(url, json=tracks, params={"include[]": "content"})
            try:
                r.raise_for_status()
                return r.json()
            except requests.HTTPError:
                if not delays:
                    raise
                self.sleep(delays.pop(0))

    # --- rubrics ------------------------------------------------------------
    # Rubric calls are form-encoded, as Canvas's own UI sends them: Rails
    # reads rubric_association[use_for_grading] as the string "1".

    def _form_send(self, method: str, url: str, fields: list) -> dict:
        r = self.s.request(method, url, data=fields)
        r.raise_for_status()
        return r.json()

    def find_rubric(self, title: str) -> int | None:
        for rb in self._get_all(f"{self.course}/rubrics"):
            if rb.get("title") == title:
                return rb["id"]
        return None

    def create_rubric(self, title: str, criteria: list[dict], assignment_id: int,
                      use_for_grading: bool = True) -> tuple[int, int]:
        """POST /courses/:id/rubrics, associated with `assignment_id` for
        grading. Returns (rubric id, rubric association id)."""
        fields = _form("rubric", {"title": title, "free_form_criterion_comments": False,
                                  "criteria": rubric_criteria(criteria)}, [])
        fields += _form("rubric_association", {
            "association_id": assignment_id, "association_type": "Assignment",
            "use_for_grading": use_for_grading, "purpose": "grading"}, [])
        fields.append(("skip_updating_points_possible", "true"))
        out = self._form_send("POST", f"{self.course}/rubrics", fields)
        return out["rubric"]["id"], (out.get("rubric_association") or {}).get("id")

    def update_rubric(self, rubric_id: int, title: str, criteria: list[dict],
                      association_id: int | None = None) -> int:
        """PUT /courses/:id/rubrics/:id (criteria are replaced whole).
        Returns the rubric id Canvas reports (it may copy a rubric that
        can't be edited in place)."""
        fields = _form("rubric", {"title": title, "free_form_criterion_comments": False,
                                  "criteria": rubric_criteria(criteria)}, [])
        if association_id is not None:
            fields.append(("rubric_association_id", str(association_id)))
        fields.append(("skip_updating_points_possible", "true"))
        out = self._form_send("PUT", f"{self.course}/rubrics/{rubric_id}", fields)
        return (out.get("rubric") or {}).get("id", rubric_id)

    def associate_rubric(self, rubric_id: int, assignment_id: int,
                         known_id: int | None = None,
                         use_for_grading: bool = True) -> int:
        """Attach the rubric to an assignment for grading: POST (or, for a
        known association, PUT) /courses/:id/rubric_associations."""
        fields = _form("rubric_association", {
            "rubric_id": rubric_id, "association_id": assignment_id,
            "association_type": "Assignment", "use_for_grading": use_for_grading,
            "purpose": "grading"}, [])
        if known_id is not None:
            out = self._form_send("PUT", f"{self.course}/rubric_associations/{known_id}",
                                  fields)
        else:
            out = self._form_send("POST", f"{self.course}/rubric_associations", fields)
        assoc = out.get("rubric_association", out)
        return assoc["id"]
