"""Structural a11y/perf audit of a generated site tree.

Checks every page for: template-leak braces, single h1, heading-order
skips, skip link, main landmark id, theme-color, defer scripts, lang attr,
landmarks, th scope, and reports sizes (raw + gzip).
"""
import gzip
import sys
from html.parser import HTMLParser
from pathlib import Path


class HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings = []  # (level, text)
        self._in_heading = None
        self._buf = []
        self.th_missing_scope = 0
        self.total_th = 0
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = int(tag[1])
            self._buf = []
            if tag == "h1":
                self.h1_count += 1
        if tag == "th":
            self.total_th += 1
            if "scope" not in a:
                self.th_missing_scope += 1

    def handle_data(self, data):
        if self._in_heading:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._in_heading == int(tag[1]):
            self.headings.append((self._in_heading, " ".join("".join(self._buf).split())))
            self._in_heading = None


def gz_size(b: bytes) -> int:
    return len(gzip.compress(b, 9))


def audit(root: Path):
    pages = sorted(
        [p for p in root.glob("*.html")]
        + [p for p in root.glob("*/index.html")]
        + [p for p in root.glob("guides/*/index.html")]
    )
    pages = [p for p in pages if "tests" not in str(p)]
    total = 0
    total_gz = 0
    problems = 0
    for p in pages:
        b = p.read_bytes()
        text = b.decode("utf-8")
        g = gz_size(b)
        total += len(b)
        total_gz += g
        rel = str(p.relative_to(root))
        issues = []
        if "{{" in text or "}}" in text:
            issues.append("BRACE LEAK")
        hp = HeadingParser()
        hp.feed(text)
        hp.close()
        if hp.h1_count != 1:
            issues.append(f"h1 count={hp.h1_count}")
        # heading order: no level increases > 1
        prev = 0
        for lvl, txt in hp.headings:
            if prev and lvl > prev + 1:
                issues.append(f"heading skip {prev}->{lvl} @ '{txt[:40]}'")
            prev = lvl
        if '<a class="skip-link"' not in text:
            issues.append("no skip-link")
        if 'id="main-content"' not in text:
            issues.append("no #main-content")
        if 'name="theme-color"' not in text:
            issues.append("no theme-color")
        if '<html lang="en"' not in text:
            issues.append("no lang")
        if "<nav" not in text:
            issues.append("no nav landmark")
        if "<main" not in text:
            issues.append("no main landmark")
        if "<footer" not in text:
            issues.append("no footer landmark")
        # all scripts deferred
        import re
        for m in re.finditer(r"<script[^>]*>", text):
            tag = m.group(0)
            if tag.startswith("<script type="):
                continue  # JSON island
            if "defer" not in tag:
                issues.append(f"non-deferred script: {tag[:60]}")
        if hp.th_missing_scope:
            issues.append(f"{hp.th_missing_scope} th without scope (of {hp.total_th})")
        status = "OK " if not issues else "ISSUES"
        if issues:
            problems += 1
        print(f"{status} {rel:42} raw={len(b):>6}B gz={g:>6}B  {('; '.join(issues)) if issues else ''}")
        for lvl, txt in hp.headings[:6]:
            pass
    print(f"\n{len(pages)} pages, {total}B raw / {total_gz}B gzip total, {problems} with issues")
    return problems


if __name__ == "__main__":
    root = Path(sys.argv[1])
    sys.exit(1 if audit(root) else 0)
