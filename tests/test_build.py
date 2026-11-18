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
