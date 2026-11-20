"""Turn the markdown files in content/ into the two data files the site reads.

Run from the repo root:  python3 tools/build.py
"""
from pathlib import Path
import sys

import yaml
import markdown
import re
import posixpath
import argparse
import json
import shutil
import textwrap
import itertools
from html import escape as html_escape
from markdown.extensions.toc import slugify as _slugify

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
        if path.name.startswith("_"):
            continue   # _section.md is a section's introduction, not a page (see read_sections)
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

def read_sections(content_dir):
    """Read each section's introduction: content/<section>/_section.md.

    It is shown in the section's reading panel and is never a page: no bubble, no search or Latest entry, no tags.
    Like a page it must say `visibility: public` to be published. Returns {section: html}.
    """
    intros = {}
    for section in SECTION_TITLES:
        path = content_dir / section / "_section.md"
        if not path.is_file():
            continue
        meta, body = split_front_matter(path.read_text(encoding="utf-8"))
        if meta.get("visibility") == "public" and body.strip():
            intros[section] = rewrite_links(to_html(body), f"{section}/_section")
    return intros


REQUIRED = ["title", "section", "tags", "summary"]

# ---------- step 4: keep public pages, turn markdown into HTML ----------

def is_public(page):
    """True only when the page says visibility: public. Anything else stays offline."""
    # The fail-safe filter: a missing line, a typo or any other word keeps the page offline.
    # .get() returns None for a missing field instead of crashing.
    return page.get("visibility") == "public"


def problems_in(page):
    """Return a list of missing required fields, e.g. ['summary']."""
    # Checks the page kept its side of the data contract; an empty value ("") counts as missing.
    # The one exception: `tags: []` is allowed (a page may have no meaningful tag), but the tags line itself must be there.
    return [field for field in REQUIRED if (page.get(field) is None if field == "tags" else not page.get(field))]


def to_html(body, toc=False):
    """Turn markdown text into HTML. With toc=True, give the ## headings ids and add a small "On this page" list."""
    # The markdown library does the conversion; "tables" and "fenced_code" switch on
    # tables and ``` code blocks, which are off by default.
    if not toc:
        return markdown.markdown(body, extensions=["tables", "fenced_code"])
    # Opt-in per page (front matter: toc: true). The ids start with "sec-" so they can never clash with an id the site
    # already uses (list, help, panel...). The links carry data-anchor, not just #id: a plain #id link would change the
    # address, and the site reads the address to decide which page is open. The site's script scrolls to the heading.
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"],
                           extension_configs={"toc": {"toc_depth": "2-2", "slugify": lambda value, sep: "sec-" + _slugify(value, sep)}})
    html = md.convert(body)
    heads = [(t["id"], t["name"]) for t in md.toc_tokens]
    if heads and "<h2" in html:
        nav = ('<nav class="toc" aria-label="On this page"><span class="toc-label">On this page</span>'
               + "".join(f'<a href="#{i}" data-anchor="{i}">{html_escape(n)}</a>' for i, n in heads) + "</nav>")
        html = html.replace("<h2", nav + "<h2", 1)   # just before the first heading: after the introduction
    return html

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

    # Every bubble: one centre ("home"), one per section, one per page, and one per tag (each tag only once).
    add({"id": "home", "kind": "home", "title": "Mehul Patankar"})
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
    # The centre links to every section, so no section can float off on its own.
    for key in SECTION_TITLES:
        connect("home", "section:" + key, "hub")
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
        if n["kind"] == "home":
            n["val"] = 60
        elif n["kind"] == "section":
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

# ---------- step 6: write the data files ----------

def write_js(path, var_name, data, append=False):
    """Write `window.<var_name> = <data as JSON>;` to path."""
    # Wraps the data as window.X = {...}; so a plain <script> tag can load it.
    # ensure_ascii=False keeps Hindi, Marathi or the rupee sign readable.
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "window." + var_name + " = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n"
    if append:
        text = path.read_text(encoding="utf-8") + text
    path.write_text(text, encoding="utf-8")


def read_quotes(path):
    """Read content/quotes.yml. Return a list of {text, by, tags, sections}; [] if the file is absent."""
    # Each saying must have text. tags and sections are optional lists, used by the front end
    # to show sayings that match the clicked tag or section.
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        raise ValueError(f"{path.name}: expected a list of sayings")
    quotes = []
    for i, item in enumerate(raw, 1):
        if not isinstance(item, dict) or not str(item.get("text", "")).strip():
            raise ValueError(f"{path.name}: saying {i} has no text")
        quotes.append({
            "text": str(item["text"]).strip(),
            "by": str(item.get("by") or "").strip(),
            "tags": [str(t) for t in item.get("tags") or []],
            "sections": [str(x) for x in item.get("sections") or []],
        })
    return quotes


# ---------- checks on sections and tags ----------

TAG_FORM = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")   # lowercase words joined by single hyphens


def suggest_tag(tag):
    """The tag spelt the way the site expects: lowercase, hyphens for spaces and underscores, no stray symbols."""
    tag = re.sub(r"[\s_]+", "-", str(tag).strip().lstrip("#").lower())
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "", tag)).strip("-")


def _edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def similar_reason(a, b):
    """Why two different tags look like one topic spelt two ways, or None. Short names (ai, llm, rag) are never compared."""
    if a.replace("-", "") == b.replace("-", ""):
        return "they differ only by hyphens"
    for short, long in ((a, b), (b, a)):
        if long in (short + "s", short + "es"):
            return "one is the singular of the other"
    if min(len(a), len(b)) >= 5 and _edit_distance(a, b) == 1:
        return "they are one letter apart"
    return None


def validate_content(pages, built_ids):
    """Check every page's section and tags. Return (errors, warnings), each a list of readable lines.

    A page that will be built (public, or named for a preview) gets errors for real mistakes. A page that will NOT be built
    (a draft) only gets warnings, so a draft can never stop the site from publishing. Look-alike tags, tags used once, and tags
    named like a section are warnings for everyone: they may well be intended.
    """
    errors, warnings = [], []
    used = {}   # tag -> ids of built pages using it
    for p in pages:
        built = p["id"] in built_ids
        path = f"content/{p['id']}.md"
        out, prefix = (errors, "") if built else (warnings, "(draft, not built) ")
        problem = lambda text: out.append(f"{prefix}{path}: {text}")
        if built:
            missing = problems_in(p)
            if missing:
                extra = " (use `tags: []` if the page has no tag)" if "tags" in missing else ""
                problem(f"missing {', '.join(missing)}{extra}. Every page needs: {', '.join(REQUIRED)}.")
        section = p.get("section")
        if not isinstance(section, str) or section not in SECTION_TITLES:
            problem(f"section {section!r} is not one of: {', '.join(SECTION_TITLES)}. "
                    f"Put the file in one of those folders under content/, or correct `section:` in the front matter.")
        tags = p.get("tags")
        if tags is None:
            continue   # a missing tags line is reported above
        if not isinstance(tags, list):
            problem(f"tags must be a list, like  tags: [ai, llm]  (found {type(tags).__name__}: {tags!r}).")
            continue
        seen = []
        for number, tag in enumerate(tags, 1):
            if not isinstance(tag, str):
                problem(f"tag {number} is {tag!r} (type {type(tag).__name__}), not text. YAML turns bare words such as yes, no, null "
                        f"and 2024 into non-text. Put it in quotes (\"{tag}\") or give it a name made of letters.")
            elif not TAG_FORM.match(tag):
                problem(f"tag {tag!r} must be lowercase words joined by hyphens, with letters and digits only. "
                        f"Did you mean {suggest_tag(tag)!r}?")
            elif tag in seen:
                problem(f"tag {tag!r} is listed more than once. Remove the repeat.")
            else:
                seen.append(tag)
                if built:
                    used.setdefault(tag, []).append(p["id"])
    names = sorted(used)
    for a, b in itertools.combinations(names, 2):
        why = similar_reason(a, b)
        if why:
            warnings.append(f"tags {a!r} ({', '.join(used[a])}) and {b!r} ({', '.join(used[b])}) look like one topic spelt two ways: "
                            f"{why}. If that is a mistake, use one spelling; if they are genuinely different, ignore this.")
    same = [t for t in names if t in SECTION_TITLES]
    if same:
        warnings.append(f"tag{'s' if len(same) > 1 else ''} {', '.join(repr(t) for t in same)} {'share' if len(same) > 1 else 'shares'} "
                        f"a name with a section. Pages in that section are already connected to it, so the tag adds nothing there.")
    once = [f"{t} ({used[t][0]})" for t in names if len(used[t]) == 1]
    if once:
        warnings.append(textwrap.fill(f"{len(once)} tag{'s are' if len(once) > 1 else ' is'} used by only one page. That is fine for a new topic; "
                                      f"it just connects nothing yet: " + ", ".join(once) + ".", width=110, subsequent_indent="      ", break_on_hyphens=False, break_long_words=False))
    return errors, warnings


def format_report(errors):
    """One readable message for a failed build: every problem at once, numbered."""
    lines = [f"{len(errors)} problem{'s' if len(errors) > 1 else ''} in content/ (nothing was built):"]
    lines += [textwrap.fill(f"{i}. {e}", width=110, initial_indent="  ", subsequent_indent="     ", break_on_hyphens=False, break_long_words=False) for i, e in enumerate(errors, 1)]
    lines.append("Fix these and run the build again.")
    return "\n".join(lines)


def build(content_dir, out_dir, include_drafts=(), warnings=None):
    """Run the whole pipeline. Return (ids kept, ids skipped).

    include_drafts names pages that are NOT public but should be built anyway. It is only ever used by the local preview
    (see main); a normal build passes nothing, so drafts stay out.
    warnings, if given, is a list that receives readable warnings (they never stop the build).
    """
    # read -> keep public -> stop on a broken page -> graph -> HTML -> two files.
    pages = read_pages(content_dir)
    unknown = [d for d in include_drafts if d not in {p["id"] for p in pages}]
    if unknown:
        raise ValueError(f"no such page to preview: {', '.join(unknown)}")
    shown = lambda p: is_public(p) or p["id"] in include_drafts
    public = [p for p in pages if shown(p)]
    skipped = [p["id"] for p in pages if not shown(p)]
    errors, notes = validate_content(pages, {p["id"] for p in public})
    if errors:
        raise ValueError(format_report(errors))
    if warnings is not None:
        warnings.extend(notes)
    nodes, links = build_graph(public)
    pages_data = {p["id"]: {"title": p["title"], "html": rewrite_links(to_html(p["body"], toc=bool(p.get("toc"))), p["id"])}
                  for p in public}
    write_js(out_dir / "graph-data.js", "GRAPH_DATA", {"nodes": nodes, "links": links})
    write_js(out_dir / "pages-data.js", "PAGES_DATA", pages_data)
    write_js(out_dir / "pages-data.js", "SECTIONS_DATA", {k: {"html": h} for k, h in read_sections(content_dir).items()}, append=True)
    write_js(out_dir / "quotes-data.js", "QUOTES_DATA", read_quotes(content_dir / "quotes.yml"))
    return [p["id"] for p in public], skipped

PREVIEW_DIR = ROOT / "private" / "preview"   # private/ is ignored by git; this folder is never published


def main():
    parser = argparse.ArgumentParser(description="Build the portal's data files.")
    parser.add_argument("--content", default=str(ROOT / "content"))
    parser.add_argument("--out", default=None)
    parser.add_argument("--preview", action="append", default=[], metavar="PAGE_ID",
                        help="LOCAL PREVIEW ONLY: also build this draft page (e.g. about/index) into private/preview/. "
                             "Other drafts stay out. Never use this for the published build.")
    args = parser.parse_args()
    out = Path(args.out) if args.out else (PREVIEW_DIR if args.preview else ROOT / "site")
    if args.preview and (out.resolve() == (ROOT / "site").resolve() or (ROOT / "site").resolve() in out.resolve().parents):
        print("Refusing: a preview that includes drafts must not be written into site/, the folder that gets published.")
        return 1
    notes = []
    try:
        kept, skipped = build(Path(args.content), out, include_drafts=args.preview, warnings=notes)
    except ValueError as err:
        print(f"Build failed:\n{err}")
        return 1
    print(f"Built {len(kept)} {'pages' if args.preview else 'public pages'}. Skipped {len(skipped)}: {', '.join(skipped) or 'none'}.")
    if notes:
        print(f"\nWarnings ({len(notes)}), these do not stop the build:")
        for note in notes:
            print(f"  - {note}")
        print()
    if args.preview:
        shutil.copy(ROOT / "site" / "index.html", out / "index.html")   # the preview uses the current page design
        print(f"PREVIEW (includes draft: {', '.join(args.preview)}). Not for publishing.")
        print(f"Open it with:  python3 -m http.server 8001 --directory {out}   then visit http://localhost:8001/#/read/{args.preview[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())