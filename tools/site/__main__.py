"""Entry point for ``python -m tools.site``.

Equivalent to ``python tools/generate_site.py`` — generates all site pages and
``data.json`` into the repo root.
"""

from . import main

if __name__ == "__main__":
    main()
