"""Safety tests for tools/build.py. Run from the repo root:  python3 -m pytest -q"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "content"


def test_no_private_text_reaches_the_site(tmp_path):
    # Builds the test pages into a fresh temporary folder (never the real site/),
    # then proves no marker word from a private page reached either file.
    build.build(FIXTURES, tmp_path)
    output = (tmp_path / "graph-data.js").read_text() + (tmp_path / "pages-data.js").read_text()
    assert "PRIVATE-MARKER" not in output


def test_a_page_without_visibility_is_skipped(tmp_path):
    # The fail-safe rule: a page with no visibility line is skipped, not published.
    kept, skipped = build.build(FIXTURES, tmp_path)
    assert "journal/no-visibility" in skipped
    assert "journal/no-visibility" not in kept


def test_links_between_pages_become_ref_edges():
    # A link written in About becomes a page-to-page line in the graph.
    pages = [p for p in build.read_pages(FIXTURES) if build.is_public(p)]
    nodes, links = build.build_graph(pages)
    refs = {(l["source"], l["target"]) for l in links if l["type"] == "ref"}
    assert ("about/index", "projects/job-copilot") in refs

def test_every_section_is_linked_to_the_home_node():
    # The centre node keeps every section connected, so none can float off alone.
    pages = [p for p in build.read_pages(FIXTURES) if build.is_public(p)]
    nodes, links = build.build_graph(pages)
    assert sum(1 for n in nodes if n["kind"] == "home") == 1
    hubs = {l["target"] for l in links if l["type"] == "hub" and l["source"] == "home"}
    assert hubs == {"section:" + k for k in build.SECTION_TITLES}


def test_quotes_are_read_and_a_missing_file_is_fine(tmp_path):
    # Sayings keep their tags and sections; a content folder with no quotes.yml builds with none.
    quotes = build.read_quotes(FIXTURES / "quotes.yml")
    assert quotes[0] == {"text": "Test saying.", "by": "Someone", "tags": ["leadership"], "sections": ["blog"]}
    assert build.read_quotes(tmp_path / "nope.yml") == []


def test_a_saying_without_text_stops_the_build(tmp_path):
    bad = tmp_path / "quotes.yml"
    bad.write_text("- by: nobody\n")
    try:
        build.read_quotes(bad)
        assert False, "expected ValueError"
    except ValueError as err:
        assert "saying 1" in str(err)


# ---- local draft preview and the "On this page" list (Phase D1) ----

def test_a_normal_build_leaves_drafts_out_and_a_preview_lets_in_only_the_named_one(tmp_path):
    # Normal build: the draft is skipped. Preview build naming it: it is built; other non-public pages stay out.
    kept, skipped = build.build(FIXTURES, tmp_path / "normal")
    assert "journal/draft-secret" in skipped and "journal/draft-secret" not in kept
    kept2, skipped2 = build.build(FIXTURES, tmp_path / "preview", include_drafts=["journal/draft-secret"])
    assert "journal/draft-secret" in kept2
    assert "journal/no-visibility" in skipped2           # a different non-public page is still out
    assert "PRIVATE-MARKER" not in (tmp_path / "normal" / "pages-data.js").read_text()
    assert "PRIVATE-MARKER" in (tmp_path / "preview" / "pages-data.js").read_text()


def test_previewing_a_page_that_does_not_exist_is_an_error(tmp_path):
    try:
        build.build(FIXTURES, tmp_path, include_drafts=["journal/nope"])
        assert False, "expected ValueError"
    except ValueError as err:
        assert "journal/nope" in str(err)


def test_a_preview_is_never_written_into_the_published_folder(monkeypatch, capsys):
    # The command refuses to put a draft-including build in site/, the folder that is published.
    monkeypatch.setattr("sys.argv", ["build.py", "--preview", "journal/draft-secret", "--out", str(build.ROOT / "site")])
    assert build.main() == 1
    assert "Refusing" in capsys.readouterr().out


def test_on_this_page_list_is_opt_in_and_its_ids_cannot_clash():
    body = "Intro.\n\n## My Journey\n\ntext\n\n## What I'm Building and Learning\n\ntext"
    plain = build.to_html(body)
    assert "toc" not in plain and 'id="' not in plain            # other pages are untouched
    html = build.to_html(body, toc=True)
    assert html.index('class="toc"') < html.index("<h2")          # after the introduction, before the first heading
    assert 'data-anchor="sec-my-journey"' in html and 'id="sec-my-journey"' in html
    assert 'id="sec-what-im-building-and-learning"' in html       # every id starts with sec-
    assert 'href="#sec-' in html and html.count("data-anchor=") == 2
