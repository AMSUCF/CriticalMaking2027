# Canvas Deployer

Deploys ENG 6819 Critical Making in Digital Humanities (Spring 2027) to Canvas
(Webcourses) from this repository. The public Jekyll site
(<https://anastasiasalter.net/CriticalMaking2027>) stays the source of truth
for the syllabus (`index.md`) and the exercise pages (`exercises/*.md`); the
deployer turns them into Canvas modules, pages, graded discussions and
assignments, and adds the Canvas-only material — interview videos and reading
PDFs — that is never committed or put on the public site.

Adapted from the HumanitiesAI deployer: same upsert-by-id/title design, same
freeze rules, same dry-run previews.

## Setup

From the **repository root**:

```
python -m venv .venv
.venv\Scripts\pip install -r canvas/requirements.txt
copy canvas\.env.example canvas\.env
```

(`.venv-media`, if present, belongs to the media tools in `canvas/tools/`;
the deployer only uses `.venv`.)

Edit `canvas/.env`:

```
CANVAS_API_URL=https://webcourses.ucf.edu
CANVAS_API_TOKEN=paste-token-here
CANVAS_COURSE_ID=000000
```

Token: Webcourses **Account → Settings → Approved Integrations → + New Access
Token** (Canvas shows it once). `CANVAS_COURSE_ID` is the number in the course
URL. The token is sent as a Bearer header to Canvas only; it is never sent to
the file-storage host during uploads. `canvas/.env` is gitignored — never
commit it.

Run everything **from `canvas/`**:

```
cd canvas
..\.venv\Scripts\python deploy.py --all --dry-run
```

## Flags

| Flag | Effect |
| --- | --- |
| `--all` | Every stem in `weeks` + `extra`, the break modules, the Syllabus page, and (with Week One) the Welcome page and Activity Verification. |
| `--week NAME` | One week: a full stem (`exercises/one_selfie`) or its last part (`one_selfie`). |
| `--dry-run` | No Canvas calls and no credentials needed. Writes `preview/*.html` (`one_selfie.html`, `one_selfie-readings.html`, `one_selfie-discussion.html`, `reflection-assignment.html`, `welcome.html`, `syllabus.html`) and prints a one-line summary per module. Missing media is reported; uploaded-file ids show as `FILE-<name>`. |
| `--publish` | Create/update everything as **published** (default: unpublished). |
| `--force` | Also redeploy modules (and Activity Verification, and break modules) that have already opened. Without it, live content is frozen (below). |
| `--simple-syllabus` | Write `preview/simple_syllabus.html`: `index.md` split into `## ` sections for pasting into Simple Syllabus. |

## What gets deployed

For each stem, a module (unlocks at 00:00 ET on `week_start`) containing, in
order:

1. *(first week only)* the page **Welcome! (Read this first!)** from
   `welcome.md` at the repo root (skipped with a warning if missing);
2. **"{Week X}: Readings + Interview"** — a Canvas-only page with
   `## Readings` (that week's bullets from `index.md`), **Reading PDFs**
   (links to the uploaded PDFs) and **Featured Interview: {guest}** (the
   uploaded video, or a placeholder). Only for stems in `weeks`, and skipped
   when a week has no readings, PDFs, or interview;
3. the exercise page, titled `"Overview: " + title` (front matter `title`) so it is
   not confused with the discussion or assignment that carries the bare title;
4. the graded discussion — or, for `type: assignment`, an assignment taking a
   URL or upload — with the Making Exercise rubric if `rubric: true`;
5. *(the `activity_verification.module_of` stem only)* the Activity
   Verification assignment (text entry).

Week One (the first stem in `weeks`) and the `extra` stems (the final
reflection) go in the **Course Requirements** assignment group, with Activity
Verification; every other week goes in **Making Exercises**.

A **break** module (e.g. Week Ten: Spring Break) has an unlock date and a
single text header, and sits after the stem named in `after`.

Module positions follow course order (`weeks` + `extra`, breaks inserted), so
deployed modules take positions 1..N; put any hand-made modules after them.
`--all` also writes a **Syllabus** page (not in a module) from `index.md`.

Due dates are 23:59 America/New_York; unlocks 00:00. Discussions lock one
week after the due date unless `close:` or `hard_close:` says otherwise.

## Exercise front matter

Each `exercises/*.md` file listed in `course.yml` needs a `canvas:` block:

```yaml
---
title: "Making Exercise One: Selfie"
canvas:
  module: "Week Two: Selfie"          # module name; week label = text before ':' ("Week Two")
  week_start: 2027-01-18
  due: 2027-01-24
  points: 7
  discussion: true                     # default true; false = no graded item
  discussion_title: 'Making Exercise One: "Selfie"'   # optional
  type: discussion                     # or "assignment"; default discussion
  extra_credit: false                  # true -> points sent as 0
  close: 2027-03-21                    # optional explicit lock date
  hard_close: false                    # lock at the due date
  rubric: true                         # attach the Making Exercise rubric
  interview: sullivan                  # optional key into course.yml interviews
---
```

Required: `module`, `week_start`, `due`, `points`. The graded item's title is
`discussion_title`, else `"Exercise Discussion: " + module` for a discussion
or the page `title` for an assignment.

The body is split at a line that is exactly `### Discussion` (or
`### Submission` for `type: assignment`): everything above is the Canvas
page, everything below is the discussion prompt / assignment description. With
no such line there is no graded item.

Links: relative links resolve against the file's own folder and point at the
public site — `../img/x.png` in `exercises/one_selfie.md` becomes
`{site_base}/img/x.png`, `two_comic` becomes `{site_base}/exercises/two_comic`,
`foo.md` becomes `foo.html`. Absolute URLs, `#anchors` and `/…` paths are left
alone.

A listed exercise file that doesn't exist yet is skipped with a `[missing]`
line; one without a valid `canvas:` block stops the run (all such files are
listed at once).

### What the deployer reads from `index.md`

- Week headings must be `### {Week label}: …` — e.g.
  `### Week Two: Selfie (Monday, January 18)` — where the week label is the
  part of the module name before `:`. The readings run to the next `###`
  heading; a `#### Explore` sub-list is kept.
- Bullets starting `**Featured Guest:` or `**[Making Exercise …` (also
  `Optional Making Exercise`) are left off the readings page; everything else
  is kept.
- A week whose heading is missing simply gets no `## Readings` section.

## course.yml keys

| Key | Meaning |
| --- | --- |
| `site_base` | Public site URL that relative links point to. |
| `syllabus_file` | `index.md` (repo root). |
| `welcome_file` | Repo-root markdown deployed as "Welcome! (Read this first!)", first item of the first week. |
| `assignment_groups` | `{exercises: Making Exercises, other: Course Requirements}`. |
| `weeks` | Stems in order (`exercises/introductions`, …). Each gets a readings page. |
| `extra` | Stems after the weeks (`exercises/reflection`); no readings page. |
| `breaks` | `{module, week_start, after, text}` per break module. |
| `activity_verification` | `{name, points, open, due, module_of}`. |
| `rubric` | `{title, criteria: [{description, long, points}]}`; each criterion gets Full Marks / No Marks ratings. |
| `interviews` | `key: {guest, video, captions}`; paths relative to `canvas/`, `null` if none. |
| `pdfs` | `stem: [path, …]`; a path, or `{file, title}` for custom link text (default: file name without extension). |
| `expect_course_code` | Optional: abort unless the Canvas course code contains this string. |
| `course_image` | Dashboard card image, relative to `canvas/`. With `--all` it is uploaded to **Files → Course Image** (only when its SHA-256 changes) and set as the course image. |

The course image (`course_image.png`, 1048×584, four times Canvas's 262×146
card) is the site header's quilt panel without its label, rendered from
`tools/course_image.html`:

```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --hide-scrollbars ^
  --window-size=1048,584 --screenshot=%CD%\course_image.png tools\course_image.html
```

Every page the deployer writes starts with a band in the same quilt fabrics
(violet binding, a sunflower "Critical Making" label, a raspberry stitch
line), set in `converter.py`. Canvas strips stylesheets and web fonts, so
the band uses inline colours and borders only.

## Media workflow (Canvas-only)

Interview videos, captions and reading PDFs live under `canvas/media/`, which
is **gitignored** — they are never committed and never go on the public site.

- PDFs upload to Canvas **Files → Readings**; videos to **Files →
  Interviews**, using Canvas's three-step upload, streamed from disk (the
  100–850 MB videos are never loaded into memory).
- `.state.json["files"]` records `{id, sha256, size, mtime}` per file. A file
  whose SHA-256 is unchanged is not re-uploaded (size + mtime unchanged means
  it isn't even re-hashed). Re-exporting a video uploads it again, replacing
  the same-named file.
- An uploaded video is embedded the way Canvas's editor does it:
  `<iframe … data-media-type="video" src="/media_attachments_iframe/{file_id}?type=video&amp;embedded=true" …>`.
- Captions (`.vtt`, or `.srt`) are attached with
  `PUT /api/v1/media_attachments/{file_id}/media_tracks` (locale `en`, kind
  `subtitles`) after all uploads. Canvas needs time to process a new video
  first, so the call is retried (5 s, 15 s, 30 s); if Canvas still isn't
  ready the run prints `[captions pending]`, records it in `.state.json`, and
  carries on — the next deploy retries. If captions stay pending, add them by
  hand in the Canvas video player.

**Missing media never fails a run.** A configured PDF that doesn't exist is
left off the page; a missing video (or `video: null`) gets the placeholder
*"The interview with {guest} will be posted here."* — dry run and live alike,
with a `[missing media]` line.

### Hand-uploading an interview (fallback)

If a video can't go through the deployer (e.g. it isn't ready yet), embed it
by hand: open that week's **Readings + Interview** page in Canvas, replace the
placeholder with the video (Upload/Record Media or Course Media), and save.
Later deploys keep that embed in place of the placeholder (they match
`VIDEO_EMBED_RE`, also when Canvas's editor leaves it inside the
placeholder's `<em>`). If a video embed is found somewhere unexpected, the
page is left untouched (`[kept] … page left as is`). Once the file is in
`canvas/media/` and configured, the deployer's own upload replaces the hand
embed.

## Deploy order

1. **Dry run.** `deploy.py --all --dry-run`; read the summary and skim
   `preview/`.
2. **Deploy unpublished.** `deploy.py --all` — creates everything,
   unpublished, and uploads the media (the first run takes a while).
3. **Review in Canvas** (modules, pages, videos, captions, rubric, dates).
4. **Publish.** `deploy.py --all --publish`.

**Every later redeploy must also pass `--publish`** (e.g.
`deploy.py --week one_selfie --publish`): a run without it sends
`published: false` and pulls the redeployed pages, discussions and
assignments back to unpublished.

## Live content is frozen

A module is live from 00:00 ET on its `week_start`; live modules are skipped
with a `[frozen]` line (`--week` on a live week exits non-zero). Activity
Verification freezes at its `open` date and break modules at their
`week_start`. The Syllabus page is always updated by `--all`. Use `--force`
(ideally with `--week`) for a deliberate fix to something live.

## The state file

`canvas/.state.json` (gitignored) holds the Canvas ids per stem
(`module_id`, `readings_url`, `page_url`, `discussion_id`, `assignment_id`,
`rubric_association_id`), plus `welcome_url`, `syllabus_url`,
`activity_verification_id`, `breaks`, `rubric` (`id`, criteria hash),
`files` and `captions`. It is written at the end of every live run, even one
that fails part-way. Without it, every upsert falls back to matching by exact
title, so deleting it is safe but re-uploads all media (the file hashes are
lost) — back it up rather than delete it.

The rubric is created once (with the first exercise that asks for it) and
then associated with each exercise's assignment for grading. Editing the
rubric in `course.yml` updates it in Canvas on the next deploy. Its total
should equal the exercise points: if not, Canvas sets the points to the
rubric total (the deployer warns). Extra-credit exercises get the rubric
without using it for grading.

## Tests

```
.venv\Scripts\python -m pytest canvas
```

from the repo root. The suite uses `responses` and fake clients only — no
network — and its own fixture course in `canvas/tests/fixtures/course/`, so it
doesn't depend on the real `index.md` or exercises.

## Troubleshooting

- **401** — token missing/expired: make a new one and update `canvas/.env`.
- **404** — wrong `CANVAS_COURSE_ID`, or no access to the course.
- **Failed part-way** — rerun; every write is an idempotent upsert.
- **`zoneinfo` errors on Windows** — reinstall requirements (`tzdata`).
