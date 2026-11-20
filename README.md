# mehulp.github.io

Source for my personal site, served at https://mehulp.github.io.

The site is a knowledge graph: Home at the centre, five sections around it (About, Projects, Journal, Blog, System design), and a bubble for every page and tag. Click a bubble to read it. Pages that share a tag, or that link to each other, are connected.

Content is plain markdown in `content/`. A build script in `tools/` turns it into data files, `site/index.html` draws it, and a GitHub Action publishes the result.

## How it fits together

```
content/    my writing, one markdown file per page (and an intro per section)
tools/      build.py (markdown to data files) and check_layout.py (checks the repo's own layout)
site/       index.html, the whole front end in one file, plus the generated data files
tests/      pytest tests for the build
private/    local only and ignored by git: backups and draft previews
```

`site/graph-data.js`, `site/pages-data.js` and `site/quotes-data.js` are **generated** by the build and ignored by git. Don't edit them. `site/index.html` is written by hand and the build never touches it.

## Run it locally

Set up once:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Then, from the repo root:

```
.venv/bin/python tools/build.py                    # regenerate the data files from content/
python3 -m http.server 8000 --directory site       # serve the site, then open http://localhost:8000
```

Run the build again after changing anything in `content/`. After changing `site/index.html`, just reload the browser. Run the tests with `.venv/bin/python -m pytest -q`.

## Writing a page

A page is a markdown file under `content/<section>/`, with front matter at the top:

```
---
title: Job Search Copilot
section: projects          # about, projects, journal, blog or system-design
tags: [ai, python]
visibility: public         # anything else (or missing) keeps the page offline
summary: One sentence, shown in cards and lists.
date: 2026-11-20           # optional; dated pages appear in "Latest"
toc: true                  # optional; adds an "On this page" list from the ## headings
---

The text, in markdown. The title comes from the front matter, so don't repeat it as a `#` heading.
```

- **Draft or public:** only `visibility: public` is published. Everything else is skipped, so a draft can live in the repo safely.
- **Links between pages:** write a normal relative markdown link, such as `[My Story](../about/index.md)`. The build turns it into a link on the site and a connection in the graph.
- **External links:** use an HTML link that opens in a new tab: `<a href="https://..." target="_blank" rel="noopener">text</a>`.
- **Section introductions:** `content/<section>/_section.md` holds the text shown when a section is clicked. It needs `visibility: public` and is not a page: no bubble, no search or Latest entry.
- **Sayings:** `content/quotes.yml` holds the rotating saying in the sidebar (Split layout). Everything in that file is published.

### Previewing a draft

```
.venv/bin/python tools/build.py --preview about/index
```

This builds the named page, even if it is a draft, into the ignored `private/preview/` folder and prints a command to serve it. It never writes into `site/`. Run it again after changing `site/index.html`, because the preview keeps its own copy.

## Publishing

A push to `main` runs `.github/workflows/publish.yml`: it checks the repo layout, runs the tests, builds the site and publishes `site/` to GitHub Pages. If any step fails, nothing is published. Work on a branch and merge to `main` when it is ready.

The Umami analytics script in `site/index.html` only loads on the live site, never on `localhost` or a local file.

## Tags

Tags go in a page's front matter, for example `tags: [ai, python]`. Pages that share a tag are connected in the graph.

- Write them in **lowercase words joined by hyphens**: `fit-scoring`, not `Fit Scoring`, `Fit_Scoring` or `#fit-scoring`.
- **Reuse an existing tag** rather than adding a near-copy: `agents`, not `agent`.
- **Keep different ideas apart.** `ai` is the field; `llm`, `rag`, `embeddings` and `agents` are specific techniques. They are not interchangeable.
- Use as many or as few tags as the page honestly needs. `tags: []` is allowed; leave the line out and the build asks for it.
- A new topic can start with one page. A tag used once just connects nothing yet.
- Don't name a tag after a section (`blog`, `journal`...): pages in a section are already connected to it.
- Numbers and words like `yes` or `null` must be quoted, as in `tags: ["2024"]`, or YAML turns them into non-text.

The build **stops with a numbered report** (file, problem, suggested fix) for a bad tag list, a tag that is not text, a badly formed tag, a tag listed twice, an unknown `section`, or a missing required field. It only **warns** about look-alike tags (`agent` and `agents`), tags used by one page, and tags named like a section. A draft never stops the build: problems in drafts are reported as warnings.
