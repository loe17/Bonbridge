"""A small Markdown to HTML renderer.

BonBridge ships its documentation as Markdown (the files stay the source of
truth and are readable on GitHub), but shows it as formatted HTML in the web
interface.  Pulling in a Markdown library would mean a `pip` dependency on a
device that deliberately has none, and the subset used by the documentation is
small and well known, so it is rendered here.

Supported: ATX headings with anchors, fenced code blocks, GitHub style tables,
nested ordered and unordered lists, block quotes, horizontal rules, images,
links, inline code, bold, italics and paragraphs.  Everything else is escaped,
so a documentation file can never inject markup into the interface.
"""

from __future__ import annotations

import html
import re
from typing import Dict, List, Tuple

__all__ = ["render", "render_document", "extract_title", "build_toc"]

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE = re.compile(r"^\s*```+\s*([A-Za-z0-9_+-]*)\s*$")
_HR = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_UL_ITEM = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL_ITEM = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_QUOTE = re.compile(r"^\s*>\s?(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")

_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC = re.compile(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])")
_CODE = re.compile(r"`([^`]+)`")
_AUTOLINK = re.compile(r"(?<![\"(=])\bhttps?://[^\s<>\"')]+")


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug or "abschnitt"


def _inline(text: str, link_rewriter=None) -> str:
    """Render inline markup.  Code spans are protected from other rules."""
    placeholders: Dict[str, str] = {}

    def stash(rendered: str) -> str:
        token = f"\x00{len(placeholders)}\x00"
        placeholders[token] = rendered
        return token

    # 1. inline code first - nothing inside it is markup
    def code_sub(match: re.Match) -> str:
        return stash(f"<code>{html.escape(match.group(1))}</code>")

    text = _CODE.sub(code_sub, text)

    # 2. images and links, before escaping so the URLs survive
    def image_sub(match: re.Match) -> str:
        alt = html.escape(match.group(1), quote=True)
        src = match.group(2)
        if link_rewriter:
            src = link_rewriter(src, True)
        return stash(f'<img src="{html.escape(src, quote=True)}" alt="{alt}" loading="lazy">')

    text = _IMAGE.sub(image_sub, text)

    def link_sub(match: re.Match) -> str:
        label = match.group(1)
        href = match.group(2)
        if link_rewriter:
            href = link_rewriter(href, False)
        external = href.startswith("http://") or href.startswith("https://")
        target = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return stash(
            f'<a href="{html.escape(href, quote=True)}"{target}>{_inline_escape_only(label)}</a>'
        )

    text = _LINK.sub(link_sub, text)

    # 3. escape whatever is left, then apply emphasis
    text = html.escape(text)
    text = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _ITALIC.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    text = _AUTOLINK.sub(
        lambda m: f'<a href="{m.group(0)}" target="_blank" rel="noopener noreferrer">{m.group(0)}</a>',
        text,
    )

    for token, rendered in placeholders.items():
        text = text.replace(token, rendered)
    return text


def _inline_escape_only(text: str) -> str:
    escaped = html.escape(text)
    escaped = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", escaped)
    return escaped


class _Renderer:
    def __init__(self, link_rewriter=None):
        self.out: List[str] = []
        self.headings: List[Tuple[int, str, str]] = []
        self.link_rewriter = link_rewriter
        self._used_slugs: Dict[str, int] = {}

    # -- helpers -------------------------------------------------------

    def _anchor(self, text: str) -> str:
        base = _slug(text)
        count = self._used_slugs.get(base, 0)
        self._used_slugs[base] = count + 1
        return base if count == 0 else f"{base}-{count}"

    def inline(self, text: str) -> str:
        return _inline(text, self.link_rewriter)

    # -- block parsing -------------------------------------------------

    def render(self, source: str) -> str:
        lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        index = 0
        total = len(lines)

        while index < total:
            line = lines[index]

            if not line.strip():
                index += 1
                continue

            fence = _FENCE.match(line)
            if fence:
                language = fence.group(1)
                index += 1
                block: List[str] = []
                while index < total and not _FENCE.match(lines[index]):
                    block.append(lines[index])
                    index += 1
                index += 1  # closing fence
                css = f' class="lang-{html.escape(language)}"' if language else ""
                self.out.append(f"<pre><code{css}>{html.escape(chr(10).join(block))}</code></pre>")
                continue

            heading = _HEADING.match(line)
            if heading:
                level = len(heading.group(1))
                text = heading.group(2)
                anchor = self._anchor(text)
                self.headings.append((level, text, anchor))
                self.out.append(
                    f'<h{level} id="{anchor}">{self.inline(text)}'
                    f'<a class="anchor" href="#{anchor}" aria-hidden="true">#</a></h{level}>'
                )
                index += 1
                continue

            if _HR.match(line) and not _UL_ITEM.match(line):
                self.out.append("<hr>")
                index += 1
                continue

            # table: a header row followed by a separator row
            if "|" in line and index + 1 < total and _TABLE_SEP.match(lines[index + 1]):
                index = self._table(lines, index)
                continue

            if _QUOTE.match(line):
                block = []
                while index < total and _QUOTE.match(lines[index]):
                    block.append(_QUOTE.match(lines[index]).group(1))  # type: ignore[union-attr]
                    index += 1
                inner = _Renderer(self.link_rewriter).render("\n".join(block))
                self.out.append(f"<blockquote>{inner}</blockquote>")
                continue

            if _UL_ITEM.match(line) or _OL_ITEM.match(line):
                index = self._list(lines, index)
                continue

            # paragraph
            block = []
            while index < total and lines[index].strip():
                candidate = lines[index]
                if (
                    _HEADING.match(candidate)
                    or _FENCE.match(candidate)
                    or _UL_ITEM.match(candidate)
                    or _OL_ITEM.match(candidate)
                    or _QUOTE.match(candidate)
                    or _HR.match(candidate)
                ):
                    break
                block.append(candidate.strip())
                index += 1
            if block:
                self.out.append(f"<p>{self.inline(' '.join(block))}</p>")

        return "\n".join(self.out)

    def _table(self, lines: List[str], index: int) -> int:
        def cells(row: str) -> List[str]:
            row = row.strip()
            if row.startswith("|"):
                row = row[1:]
            if row.endswith("|"):
                row = row[:-1]
            return [c.strip() for c in row.split("|")]

        header = cells(lines[index])
        alignments: List[str] = []
        for spec in cells(lines[index + 1]):
            left = spec.startswith(":")
            right = spec.endswith(":")
            alignments.append("center" if left and right else ("right" if right else "left"))
        index += 2

        body: List[List[str]] = []
        while index < len(lines) and "|" in lines[index] and lines[index].strip():
            body.append(cells(lines[index]))
            index += 1

        html_parts = ["<table><thead><tr>"]
        for position, cell in enumerate(header):
            align = alignments[position] if position < len(alignments) else "left"
            html_parts.append(f'<th style="text-align:{align}">{self.inline(cell)}</th>')
        html_parts.append("</tr></thead><tbody>")
        for row in body:
            html_parts.append("<tr>")
            for position, cell in enumerate(row):
                align = alignments[position] if position < len(alignments) else "left"
                html_parts.append(f'<td style="text-align:{align}">{self.inline(cell)}</td>')
            html_parts.append("</tr>")
        html_parts.append("</tbody></table>")
        self.out.append("".join(html_parts))
        return index

    def _list(self, lines: List[str], index: int, depth: int = 0) -> int:
        first_ul = _UL_ITEM.match(lines[index])
        ordered = first_ul is None
        base_indent = len((first_ul or _OL_ITEM.match(lines[index])).group(1))  # type: ignore[union-attr]
        tag = "ol" if ordered else "ul"
        self.out.append(f"<{tag}>")

        total = len(lines)
        while index < total:
            line = lines[index]
            if not line.strip():
                # a blank line ends the list unless the next line continues it
                if index + 1 < total and (
                    _UL_ITEM.match(lines[index + 1]) or _OL_ITEM.match(lines[index + 1])
                ):
                    index += 1
                    continue
                break

            ul = _UL_ITEM.match(line)
            ol = _OL_ITEM.match(line)
            if not ul and not ol:
                # continuation line of the current item
                self.out.append(f" {self.inline(line.strip())}")
                index += 1
                continue

            indent = len((ul or ol).group(1))  # type: ignore[union-attr]
            if indent < base_indent:
                break
            if indent > base_indent:
                index = self._list(lines, index, depth + 1)
                continue

            is_ordered_item = ol is not None
            if is_ordered_item != ordered:
                break

            content = (ol.group(3) if ol else ul.group(2))  # type: ignore[union-attr]
            self.out.append(f"<li>{self.inline(content)}</li>")
            index += 1

        self.out.append(f"</{tag}>")
        return index


def render(source: str, link_rewriter=None) -> str:
    """Render Markdown to an HTML fragment."""
    return _Renderer(link_rewriter).render(source)


def render_with_toc(source: str, link_rewriter=None) -> Tuple[str, List[Dict[str, str]]]:
    renderer = _Renderer(link_rewriter)
    body = renderer.render(source)
    toc = [
        {"level": str(level), "text": text, "anchor": anchor}
        for level, text, anchor in renderer.headings
        if level in (2, 3)
    ]
    return body, toc


def extract_title(source: str) -> str:
    for line in source.splitlines():
        heading = _HEADING.match(line)
        if heading and len(heading.group(1)) == 1:
            return heading.group(2).strip()
    return ""


def build_toc(source: str) -> List[Dict[str, str]]:
    return render_with_toc(source)[1]


def render_document(
    source: str,
    *,
    title: str = "",
    css: str = "",
    link_rewriter=None,
    nav_html: str = "",
    language: str = "de",
) -> str:
    """Render a complete standalone HTML page."""
    body, toc = render_with_toc(source, link_rewriter)
    heading = title or extract_title(source) or "BonBridge"
    toc_html = ""
    if len(toc) >= 3:
        items = "".join(
            f'<li class="lvl{entry["level"]}"><a href="#{entry["anchor"]}">'
            f"{html.escape(entry['text'])}</a></li>"
            for entry in toc
        )
        label = "Inhalt" if language.startswith("de") else "Contents"
        toc_html = f'<nav class="toc"><div class="toc-title">{label}</div><ul>{items}</ul></nav>'
    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{html.escape(language)}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(heading)} - BonBridge</title>"
        f"<style>{css}</style></head><body>"
        f"{nav_html}"
        f'<main class="doc">{toc_html}<article>{body}</article></main>'
        "</body></html>"
    )
