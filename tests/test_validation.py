"""Tests for the checks on sections and tags in tools/build.py.

Each test writes a few small pages into a temporary content folder and builds them.
Run from the repo root:  python3 -m pytest -q
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402

REAL_CONTENT = Path(__file__).resolve().parent.parent / "content"


def write_page(root, rel, tags="[a]", section=None, visibility="public", summary="s", extra=""):
    """Write content/<rel>.md with the given front matter. section defaults to the folder."""
    section = section or rel.split("/")[0]
    tags_line = "" if tags is None else f"tags: {tags}\n"
    path = root / f"{rel}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: T {rel}\nsection: {section}\n{tags_line}visibility: {visibility}\nsummary: {summary}\n{extra}---\n\nbody\n")


def run(root, tmp_path, preview=()):
    """Build; return (error text or None, warnings, graph nodes, graph links)."""
    warnings = []
    try:
        build.build(root, tmp_path / "out", include_drafts=preview, warnings=warnings)
    except ValueError as err:
        return str(err), warnings, None, None
    import json, re
    g = json.loads(re.sub(r"^window\.\w+ = |;\s*$", "", (tmp_path / "out" / "graph-data.js").read_text()))
    return None, warnings, g["nodes"], g["links"]


def test_the_real_content_builds_with_warnings_only(tmp_path):
    err, warnings, nodes, _ = run(REAL_CONTENT, tmp_path)
    assert err is None and nodes
    public = {p["id"] for p in build.read_pages(REAL_CONTENT) if build.is_public(p)}
    assert {n["id"] for n in nodes if n["kind"] == "page"} == public                              # exactly the public pages: drafts stay out
    assert any("share" in w and "system-design" in w for w in warnings)                         # a tag named like a section: warning


@pytest.mark.parametrize("tags, expect", [
    ("[AI]", "'ai'"),                                  # uppercase: suggests the fix
    ("[Fit Scoring]", "'fit-scoring'"),                # spaces
    ("[fit_scoring]", "'fit-scoring'"),                # underscore
    ("['#rag']", "'rag'"),                             # leading #
    ("[-ai]", "'ai'"),                                 # stray hyphen
])
def test_malformed_tags_are_errors_with_a_suggestion(tmp_path, tags, expect):
    write_page(tmp_path, "projects/x", tags=tags)
    err, *_ = run(tmp_path, tmp_path)
    assert err and "content/projects/x.md" in err and "must be lowercase words joined by hyphens" in err and expect in err


@pytest.mark.parametrize("tags, word", [("[2024]", "int"), ("[yes]", "bool"), ("[null]", "NoneType"), ("[[a, b]]", "list")])
def test_non_text_tags_are_errors_not_raw_exceptions(tmp_path, tags, word):
    write_page(tmp_path, "projects/x", tags=tags)
    err, *_ = run(tmp_path, tmp_path)
    assert err and "content/projects/x.md" in err and "not text" in err and word in err and "quotes" in err


def test_tags_that_are_not_a_list_are_an_error(tmp_path):
    write_page(tmp_path, "projects/x", tags="ai, llm")
    err, *_ = run(tmp_path, tmp_path)
    assert err and "tags must be a list" in err and "[ai, llm]" in err


def test_an_exact_duplicate_tag_is_an_error(tmp_path):
    write_page(tmp_path, "projects/x", tags="[ai, llm, ai]")
    err, *_ = run(tmp_path, tmp_path)
    assert err and "'ai' is listed more than once" in err


def test_an_unknown_section_is_a_clear_error_not_a_keyerror(tmp_path):
    write_page(tmp_path, "tutorials/x", section="tutorials")
    err, *_ = run(tmp_path, tmp_path)
    assert err and "content/tutorials/x.md" in err and "section 'tutorials' is not one of: about, projects, journal, blog, system-design" in err
    assert "Put the file in one of those folders" in err


def test_a_file_outside_any_section_folder_is_reported(tmp_path):
    (tmp_path / "loose.md").write_text("---\ntitle: T\ntags: [a]\nvisibility: public\nsummary: s\n---\nbody")
    err, *_ = run(tmp_path, tmp_path)
    assert err and "content/loose.md" in err and "section 'loose'" in err


def test_all_problems_come_back_together_in_one_numbered_report(tmp_path):
    write_page(tmp_path, "projects/a", tags="[AI]")
    write_page(tmp_path, "projects/b", tags="[2024]")
    write_page(tmp_path, "tutorials/c", section="tutorials")
    err, *_ = run(tmp_path, tmp_path)
    assert err.startswith("3 problems in content/ (nothing was built):") and "1. " in err and "2. " in err and "3. " in err
    assert "projects/a.md" in err and "projects/b.md" in err and "tutorials/c.md" in err and err.rstrip().endswith("run the build again.")


def test_an_empty_tag_list_is_allowed_and_the_page_still_connects(tmp_path):
    write_page(tmp_path, "projects/untagged", tags="[]")
    err, _, nodes, links = run(tmp_path, tmp_path)
    assert err is None
    page = next(n for n in nodes if n["id"] == "projects/untagged")
    assert page["tags"] == []
    assert any(l["source"] == "projects/untagged" and l["target"] == "section:projects" and l["type"] == "belongs" for l in links)


def test_a_missing_tags_line_is_still_an_error_and_says_how_to_fix_it(tmp_path):
    write_page(tmp_path, "projects/x", tags=None)
    err, *_ = run(tmp_path, tmp_path)
    assert err and "missing tags" in err and "tags: []" in err


@pytest.mark.parametrize("a, b, why", [("agent", "agents", "singular"), ("fitscoring", "fit-scoring", "hyphens"), ("leadership", "leadershp", "one letter apart")])
def test_look_alike_tags_are_warnings_not_errors(tmp_path, a, b, why):
    write_page(tmp_path, "projects/one", tags=f"[{a}]")
    write_page(tmp_path, "projects/two", tags=f"[{b}]")
    err, warnings, nodes, _ = run(tmp_path, tmp_path)
    assert err is None and nodes                                   # the build goes ahead, both tags exist
    assert any(a in w and b in w and why in w and "genuinely different" in w for w in warnings)


def test_short_names_are_never_called_look_alikes(tmp_path):
    write_page(tmp_path, "projects/one", tags="[ai, llm, rag]")
    write_page(tmp_path, "projects/two", tags="[a, llms]")        # 'llms' is the plural of 'llm': that one is flagged; ai / rag / a are not
    _, warnings, *_ = run(tmp_path, tmp_path)
    flagged = " ".join(w for w in warnings if "one topic spelt two ways" in w)
    assert "'llm'" in flagged and "'ai'" not in flagged and "'rag'" not in flagged


def test_tags_used_once_are_one_grouped_warning_and_never_an_error(tmp_path):
    write_page(tmp_path, "projects/one", tags="[solo, shared]")
    write_page(tmp_path, "projects/two", tags="[shared]")
    err, warnings, *_ = run(tmp_path, tmp_path)
    assert err is None
    once = [w for w in warnings if "used by only one page" in w]
    flat = " ".join(once[0].split())                                  # the report wraps long lines
    assert len(once) == 1 and "solo (projects/one)" in flat and "shared" not in flat.split("connects nothing yet:")[1]


def test_a_tag_named_like_a_section_is_a_warning(tmp_path):
    write_page(tmp_path, "projects/x", tags="[blog, journal]")
    err, warnings, *_ = run(tmp_path, tmp_path)
    assert err is None and any("'blog', 'journal'" in w and "share a name with a section" in w for w in warnings)


def test_a_draft_with_bad_tags_or_section_never_blocks_the_build(tmp_path):
    write_page(tmp_path, "projects/fine", tags="[ok]")
    write_page(tmp_path, "projects/draft", tags="[Bad Tag, 2024, ok, ok]", visibility="draft")
    write_page(tmp_path, "tutorials/draft2", section="tutorials", visibility="draft")
    err, warnings, nodes, _ = run(tmp_path, tmp_path)
    assert err is None
    assert [n["id"] for n in nodes if n["kind"] == "page"] == ["projects/fine"]               # drafts are not in the graph
    drafts = [w for w in warnings if w.startswith("(draft, not built)")]
    assert len(drafts) >= 3 and any("Did you mean 'bad-tag'" in w for w in drafts) and any("tutorials" in w for w in drafts)


def test_a_draft_named_for_preview_is_checked_like_a_public_page(tmp_path):
    write_page(tmp_path, "projects/draft", tags="[Bad Tag]", visibility="draft")
    err, *_ = run(tmp_path, tmp_path, preview=["projects/draft"])
    assert err and "content/projects/draft.md" in err and "'bad-tag'" in err


def test_a_draft_with_a_missing_field_is_not_a_problem_until_it_is_built(tmp_path):
    write_page(tmp_path, "projects/fine")
    write_page(tmp_path, "projects/draft", tags=None, visibility="draft")
    err, *_ = run(tmp_path, tmp_path)
    assert err is None


def test_existing_tag_names_are_never_changed(tmp_path):
    # Nothing is renamed, merged or rewritten: the tags in the graph are exactly the tags written in the files.
    write_page(tmp_path, "projects/x", tags="[ai, llm, rag, agents, embeddings]")
    _, _, nodes, _ = run(tmp_path, tmp_path)
    assert next(n for n in nodes if n["id"] == "projects/x")["tags"] == ["ai", "llm", "rag", "agents", "embeddings"]
    assert {n["title"] for n in nodes if n["kind"] == "tag"} == {"#ai", "#llm", "#rag", "#agents", "#embeddings"}
