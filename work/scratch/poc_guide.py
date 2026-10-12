"""PoC: prove the guide pipeline renders end-to-end (P1-0 acceptance).

Renders content/guides/_sample.md to a temp guides/_sample/index.html and
checks the depth-2 shell, diagram pass-through, table, code block, related
links, and front-matter title. Run with the venv python that has `markdown`.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/madgoat/Documents/Local LLM Matrix")
sys.path.insert(0, str(ROOT))

from tools.site import guides  # noqa: E402


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="las_poc_"))
    content = tmp / "content" / "guides"
    content.mkdir(parents=True)
    shutil.copy2(ROOT / "content/guides/_sample.md", content / "_sample.md")

    html = guides.render_guide(content / "_sample.md")
    dest = tmp / "guides" / "_sample" / "index.html"
    dest.parent.mkdir(parents=True)
    dest.write_text(html, encoding="utf-8")

    text = dest.read_text(encoding="utf-8")
    checks = {
        "depth-2 css prefix (../../css/style.css)": "../../css/style.css" in text,
        "depth-2 js prefix (../../js/main.js)": "../../js/main.js" in text,
        "depth-2 nav link (../../index.html)": "../../index.html" in text,
        "diagram passed through raw": 'class="diagram diagram--kv"' in text,
        "markdown table rendered": "<table>" in text and "INT8" in text,
        "fenced code block rendered": "<code" in text and "llama-server" in text,
        "related links wired": 'href="quantization/"' in text and 'href="kv-cache/"' in text,
        "title from front-matter": "Sample Guide (Proof of Concept)" in text,
        "exactly one <h1> (toc adds id attrs)": text.count("<h1") == 1,
        "has nav + footer + OG tags": all(
            t in text for t in ('<nav', '<footer', 'property="og:title"')
        ),
    }
    for k, v in checks.items():
        print(("PASS " if v else "FAIL "), k)
    print("\nRESULT:", "ALL PASS" if all(checks.values()) else "SOME FAILED")
    print(f"(temp guide was {len(text)} bytes; removed after check)")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
