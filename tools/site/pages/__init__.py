"""One module per site page.

Each module exposes a ``render(...)`` function returning the page's complete
HTML document (built via :func:`tools.site.template.page_shell`). Renderers
are pure functions of the parsed data — they perform no file I/O, which keeps
them trivially testable and the generator the single writer of HTML.

Modules:
    homepage     — ``index.html`` (hero, stats, highlights, how-it-works)
    matrix       — ``matrix.html`` (the filterable, sortable data table)
    community    — ``community.html`` (contributor showcase)
    guides_index — ``guides.html`` (guides hub)
    about        — ``about.html`` (about the project)
"""

from __future__ import annotations
