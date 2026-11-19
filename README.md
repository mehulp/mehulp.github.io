# mehulp.github.io

Source for my personal site, served at https://mehulp.github.io.
Content lives in content/, a build script in tools/ generates the site, and a GitHub Action publishes it.

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
