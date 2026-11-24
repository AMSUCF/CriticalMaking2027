# CriticalMaking2027: notes for Claude

- **Two outputs from one source.**
  - GitHub Pages (Jekyll; `index.md`, `exercises/`, `welcome.md`).
  - Canvas, via `canvas/deploy.py`.
  - Read `README.md` and `canvas/README.md` before changing either.
- **Canvas-only material.** The interview videos, their captions and the reading PDFs live only in the gitignored `canvas/media/`. Never commit them, link them from the site, or embed videos in site pages.
- **No lecture or demo videos.** Exercise pages must be self-sufficient written guidance; the only videos in the course are the guest interviews, and they are only in Canvas.
- **Dates live in two places.**
  - Each exercise's `canvas:` front matter (machine-read).
  - The prose in `index.md`: schedule headers, Contents anchor slugs, grading table.
  - Keep them in sync. Schedule headers must start `### Week <Number>: …`, because the layout's quilt-block script, the CSS and the deployer's readings extraction depend on it. The site has no remote theme; all styling is in `_layouts/default.html` and `assets/css/style.scss` (plain CSS: avoid Sass `min()`/`max()`).
- **Quinn Daedal.** Always use this name for the Week Nine guest. Their former name must not appear anywhere: content, captions, file names or commit messages.
- **Deploy order.** Dry run first. Once a course is published, every redeploy needs `--publish`, or pages revert to unpublished. Modules whose start date has passed are frozen unless `--force`.
- **Tests.** Run `.venv\Scripts\python -m pytest canvas`. Media tools use a separate `.venv-media`.
