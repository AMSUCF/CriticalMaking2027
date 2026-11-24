# ENG 6819: Critical Making in Digital Humanities (Spring 2027)

Course site for ENG 6819 at UCF, taught by Dr. Anastasia Salter. The same Markdown feeds two outputs:

- **GitHub Pages** (public): <https://anastasiasalter.net/CriticalMaking2027>. Plain Jekyll with no remote theme. The quilt look (taken from the instructor's selfie quilt: sunflower, violet, raspberry and lilac fabrics on muslin, a cutting-mat contents list, sewing-button bullets) lives in `_layouts/default.html` and `assets/css/style.scss`. A small script in the layout wraps each `### Week …` heading and its lists into a "quilt block", so keep that heading pattern. Light and dark ("lamplight") themes follow the reader's system setting, with a toggle.
- **Webcourses (Canvas)**: pushed by the deployer in `canvas/`, which is adapted from HumanitiesAI's. Canvas also gets the **Canvas-only** material, which never goes on the public site:
  - the 12 featured-guest interview videos, with their captions;
  - the copyrighted reading PDFs.

## Layout

| Path | What it is |
|---|---|
| `index.md` | Syllabus and weekly schedule. Each week's readings and its `#### Explore` list become that week's Canvas "Readings + Interview" page. |
| `welcome.md` | The Canvas Welcome page, the first item in Week One. |
| `exercises/*.md` | One page per week. Each has a `canvas:` front-matter block (dates, points, discussion title, interview key). The text after `### Discussion` (or `### Submission` in the reflection) becomes the graded discussion or assignment prompt. |
| `exercises/materials/` | Demo files linked from the exercises (Twine, Tracery, RiTa, remixes). |
| `img/` | Images used by the exercise pages. |
| `canvas/` | The deployer, `course.yml`, tests and the deployer README (`canvas/README.md`). |
| `canvas/tools/` | One-off media tools: IMSCC extraction, transcription, OCR redaction, cutting, caption building. |
| `canvas/media/` | **Gitignored.** Interview originals, edited videos and captions, reading PDFs, cut lists. This folder is the only copy of the media. Back it up, and never commit it. |

## Spring 2027 calendar (UCF, Session 1)

- Classes begin Mon Jan 11. MLK Day is Mon Jan 18.
- Spring Break is Mar 15–21.
- The withdrawal deadline is Fri Apr 2.
- Classes end Mon Apr 26, and finals run Apr 28 – May 4.
- Modules open Mondays. Work is due Sundays at 11:59 PM ET, with a one-week no-penalty grace period.
- Activity Verification is due Fri Jan 15. The Final Reflection, and the last day for late work, is Sun May 2.

## Deploying to Canvas

See `canvas/README.md`. In short, from the `canvas/` folder:

```
..\.venv\Scripts\python deploy.py --all --dry-run     # previews in canvas/preview/
..\.venv\Scripts\python deploy.py --all               # creates everything unpublished
..\.venv\Scripts\python deploy.py --all --publish     # once reviewed; ALWAYS keep --publish from then on
```

`canvas/.env` holds `CANVAS_API_URL`, `CANVAS_API_TOKEN` and `CANVAS_COURSE_ID` for the Spring 2027 shell.

## Interview media pipeline

The interviews were recorded in Spring 2026 and edited for reuse in 2027. Every step runs from the repo root using the media venv (`python -m venv .venv-media`, then `pip install faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" rapidocr-onnxruntime opencv-python-headless pyyaml`):

1. `canvas/tools/extract_imscc.py`: pull the originals, the 2026 captions and the PDFs out of a Canvas export.
2. `canvas/tools/transcribe.py`: transcribe with word timestamps using faster-whisper large-v3.
3. `canvas/media/interviews/cuts.yml`: list the passages to remove (year- or semester-specific remarks) and any on-screen redactions. `canvas/tools/find_text.py` finds on-screen text by OCR.
4. `canvas/tools/cut.py`: write `canvas/media/interviews/edited/*.mp4`.
5. `canvas/tools/build_captions.py`: re-transcribe the edited videos and write the corrected `canvas/media/interviews/captions/*.vtt`.

**The Week Nine guest is Quinn Daedal.** Their name changed after the interview was recorded. The former name was cut from the audio, and the on-screen Zoom label and shared pages were redacted. Use only "Quinn Daedal" in every course material.

## Yearly rollover checklist

- Update the dates in every exercise's `canvas:` front matter, the prose dates in `index.md` (schedule headers, Contents anchors, grading table), the dates in `welcome.md`, and the `activity_verification` and `breaks` dates in `canvas/course.yml`.
- Grep for the old year.
- Re-check the interviews for new year-specific remarks if any were re-recorded.
- Set the new course ID in `canvas/.env`, delete `canvas/.state.json`, then dry-run.
