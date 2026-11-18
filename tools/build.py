"""Turn the markdown files in content/ into the two data files the site reads.

Run from the repo root:  python3 tools/build.py
"""
from pathlib import Path
import sys

import yaml
import markdown
import re
from collections import Counter
import posixpath

ROOT = Path(__file__).resolve().parent.parent


# ---------- step 3: read the files ----------

def split_front_matter(text):
    """Split a page into (front matter dict, body text)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    return meta, parts[2].lstrip("\n")


def read_pages(content_dir):
    """Read every .md file under content_dir. Return a list of page dicts, sorted by id."""
    pages = []
    # TODO 2 to 4: read every .md file and turn it into a page dict.
    #   What it does: walks all subfolders of content/, gives each page an id from its path
    #   (content/journal/x.md -> "journal/x"), and keeps the front matter and body together.
    for path in sorted(content_dir.rglob("*.md")):
        meta, body = split_front_matter(path.read_text(encoding="utf-8"))
        page_id = path.relative_to(content_dir).with_suffix("").as_posix()
        page = dict(meta)
        page["id"] = page_id
        page["body"] = body
        page.setdefault("section", page_id.split("/")[0])
        if page.get("date") is not None:
            page["date"] = str(page["date"])   # YAML gives a date object; we want text
        pages.append(page)
    return pages

REQUIRED = ["title", "section", "tags", "summary"]

# ---------- step 4: keep public pages, turn markdown into HTML ----------

def is_public(page):
    """True only when the page says visibility: public. Anything else stays offline."""
    # The fail-safe filter: a missing line, a typo or any other word keeps the page offline.
    # .get() returns None for a missing field instead of crashing.
    return page.get("visibility") == "public"


def problems_in(page):
    """Return a list of missing required fields, e.g. ['summary']."""
    # Checks the page kept its side of the data contract; an empty value ("" or []) counts as missing.
    return [field for field in REQUIRED if not page.get(field)]


def to_html(body):
    """Turn markdown text into HTML."""
    # The markdown library does the conversion; "tables" and "fenced_code" switch on
    # tables and ``` code blocks, which are off by default.
    return markdown.markdown(body, extensions=["tables", "fenced_code"])

SECTION_TITLES = {
    "about": "About",
    "projects": "Projects",
    "journal": "Journal",
    "blog": "Blog",
    "system-design": "System design",
}
# Matches a markdown link to a .md file: [text](../folder/page.md)
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+\.md)\)")


# ---------- step 5: make the graph ----------

def resolve_link(page_id, href):
    """Turn a relative .md link on page `page_id` into the id of the target page."""
    # ("about/index", "../projects/job-copilot.md") -> "projects/job-copilot":
    # join the page's folder with the link, fold the ".." away, drop ".md".
    folder = posixpath.dirname(page_id)
    target = posixpath.normpath(posixpath.join(folder, href))
    return target[:-3] if target.endswith(".md") else target


def find_links(page):
    """Return the ids of the pages this page links to, in order, without repeats."""
    # Finds each [text](something.md) in the body and turns its address into a page id, once each.
    found = []
    for _text, href in MD_LINK.findall(page["body"]):
        target = resolve_link(page["id"], href)
        if target not in found:
            found.append(target)
    return found


def build_graph(pages):
    """Return (nodes, links) for the 3D graph."""
    nodes, links, by_id = [], [], {}
    known = {p["id"] for p in pages}

    def add(node):
        node["degree"] = 0
        nodes.append(node)
        by_id[node["id"]] = node

    def connect(a, b, kind):
        links.append({"source": a, "target": b, "type": kind})
        by_id[a]["degree"] += 1
        by_id[b]["degree"] += 1

    # Every bubble: one per section, one per page, and one per tag (each tag only once).
    for key, title in SECTION_TITLES.items():
        add({"id": "section:" + key, "kind": "section", "section": key, "title": title})
    for p in pages:
        add({"id": p["id"], "kind": "page", "section": p["section"], "title": p["title"],
             "summary": p["summary"], "date": p.get("date"), "tags": p["tags"]})
        for tag in p["tags"]:
            if "tag:" + tag not in by_id:
                add({"id": "tag:" + tag, "kind": "tag", "title": "#" + tag})

    # Every line, after all bubbles exist: page to section, page to tag, and page to page
    # (once per pair, and only to pages that are published, so drafts stay hidden).
    seen = set()
    for p in pages:
        connect(p["id"], "section:" + p["section"], "belongs")
        for tag in p["tags"]:
            connect(p["id"], "tag:" + tag, "tag")
        for target in find_links(p):
            pair = tuple(sorted([p["id"], target]))
            if target in known and pair not in seen:
                seen.add(pair)
                connect(p["id"], target, "ref")

    # Sizes: big sections, small tags, and pages that grow with their connections.
    for n in nodes:
        if n["kind"] == "section":
            n["val"] = 40
        elif n["kind"] == "page":
            n["val"] = round(3 + 0.6 * n["degree"], 1)
        else:
            n["val"] = 1.2
        del n["degree"]
    return nodes, links


def rewrite_links(html, page_id):
    """Point .md links in the HTML at the site's own #/read/ addresses."""
    # href="../projects/x.md" -> href="#/read/projects/x", so links open the page on the site.
    def swap(match):
        return 'href="#/read/' + resolve_link(page_id, match.group(1)) + '"'
    return re.sub(r'href="([^"]+\.md)"', swap, html)

def main():
    pages = [p for p in read_pages(ROOT / "content") if is_public(p)]
    nodes, links = build_graph(pages)
    print("Nodes:", dict(Counter(n["kind"] for n in nodes)))
    print("Links:", dict(Counter(l["type"] for l in links)))
    for l in links:
        if l["type"] == "ref":
            print("  ref:", l["source"], "->", l["target"])
    print(rewrite_links(to_html(pages[0]["body"]), pages[0]["id"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())