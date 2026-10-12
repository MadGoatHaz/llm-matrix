"""SVG chart generators (P4-1) — pure inline SVG, no client chart library.

The site is static and dependency-free (PLAN §5.1: no Chart.js/D3/CDN), so
every chart is a self-contained ``<svg>`` block generated here at build time
and embedded by the page renderers. Each chart:

* is **data-driven** — inputs are the submissions list + ``schema.json``;
  new submissions appear in the next build with no code change;
* is **responsive** — a ``viewBox`` + CSS ``width:100%`` (no fixed pixels);
* is **accessible** — ``role="img"`` + ``<title>``/``<desc>`` wired through
  ``aria-labelledby`` (WCAG 1.1.1 / 4.1.2);
* is **theme-styled** — colors come from CSS classes that resolve to the
  design tokens in ``css/style.css`` (no inline color values, so the dark
  theme stays single-sourced).

Charts: :func:`vram_distribution` (bar), :func:`backend_donut` (donut),
:func:`size_vram_scatter` (scatter). :func:`figure` wraps one in the shared
``<figure class="chart-card">`` container.
"""

from __future__ import annotations

import math

from . import utils

#: Color-slot classes (resolved to --chart-1..6 in css/style.css).
PALETTE_SIZE = 6


def _esc(v) -> str:
    return utils.html_escape(v)


def _fmt(v: float) -> str:
    """Compact number for axis/value labels (no trailing .0)."""
    return f"{v:g}"


def _nice_scale(max_value: float, target_ticks: int = 4) -> tuple[float, float]:
    """(axis_max, tick_step) on a 1/2/2.5/5×10^n grid above ``max_value``."""
    if max_value <= 0:
        return 1.0, 1.0
    raw = max_value / target_ticks
    mag = 10 ** math.floor(math.log10(raw))
    step = 10 * mag
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            step = m * mag
            break
    axis_max = step * math.ceil(max_value / step)
    return axis_max, step


def _svg_open(prefix: str, title: str, desc: str,
              viewbox: str) -> str:
    """The accessible <svg> opening tag + <title>/<desc> pair."""
    return (
        f'      <svg class="chart-svg" role="img" '
        f'aria-labelledby="{prefix}-title {prefix}-desc" viewBox="{viewbox}">\n'
        f'        <title id="{prefix}-title">{_esc(title)}</title>\n'
        f'        <desc id="{prefix}-desc">{_esc(desc)}</desc>\n'
    )


def figure(icon: str, heading: str, svg: str, legend: str = "") -> str:
    """A chart card: ``<figure class="chart-card">`` + heading + body.

    The figure carries the container ``aria-label`` (task contract); the
    SVG inside carries its own ``<title>``/``<desc>`` for the data.
    """
    return f'''    <figure class="chart-card" aria-label="{_esc(heading)}">
      <h3>{utils.icon(icon)} {_esc(heading)}</h3>
      <div class="chart-body">
{svg}
{legend}
      </div>
    </figure>'''


# ---------------------------------------------------------------------------
# 1. VRAM distribution (bar chart)
# ---------------------------------------------------------------------------

def vram_distribution(subs: list[dict], schema: dict,
                      prefix: str = "chart-vram") -> str:
    """Bar chart: how many submissions fall in each VRAM tier.

    One bar per schema tier (all tiers shown, zeros included, so the
    coverage gaps — e.g. no 96GB+ rigs — are visible).
    """
    tiers = schema.get("tiers", [])
    counts = [sum(1 for s in subs if s.get("tier") == t["id"]) for t in tiers]
    total = len(subs)
    labels = [t.get("label", t["id"]) for t in tiers]

    max_c = max(counts) if counts else 0
    axis_max, step = _nice_scale(max_c)
    if axis_max <= 0:
        axis_max, step = 1, 1

    # Geometry (viewBox units; the CSS scales it to the container width).
    W, H = 640, 320
    ml, mr, mt, mb = 46, 16, 24, 54
    plot_w, plot_h = W - ml - mr, H - mt - mb
    n = len(tiers)
    slot = plot_w / max(1, n)
    bar_w = slot * 0.58

    title = f"VRAM distribution: {total} submissions across {n} tiers"
    desc = ("Bar chart of community submissions per VRAM tier. "
            + "; ".join(f"{l}: {c}" for l, c in zip(labels, counts)))

    parts = [_svg_open(prefix, title, desc, f"0 0 {W} {H}")]

    # Y gridlines + tick labels.
    y = 0
    while y <= axis_max + 1e-9:
        yy = mt + plot_h - (y / axis_max) * plot_h
        parts.append(
            f'        <line class="grid-line" x1="{ml}" y1="{yy:.1f}" '
            f'x2="{ml + plot_w}" y2="{yy:.1f}"/>'
            f'        <text class="tick-label" x="{ml - 8}" y="{yy + 4:.1f}" '
            f'text-anchor="end">{_fmt(y)}</text>'
        )
        y += step

    # Bars + value labels + tier labels.
    for i, (c, label) in enumerate(zip(counts, labels)):
        x0 = ml + slot * i + (slot - bar_w) / 2
        h_px = (c / axis_max) * plot_h
        y0 = mt + plot_h - h_px
        parts.append(
            f'        <rect class="bar" x="{x0:.1f}" y="{y0:.1f}" '
            f'width="{bar_w:.1f}" height="{h_px:.1f}" rx="3">'
            f'<title>{_esc(label)}: {_fmt(c)} submission{"s" if c != 1 else ""}</title></rect>'
        )
        parts.append(
            f'        <text class="bar-value" x="{x0 + bar_w / 2:.1f}" '
            f'y="{y0 - 7:.1f}" text-anchor="middle">{_fmt(c)}</text>'
        )
        parts.append(
            f'        <text class="tick-label" x="{ml + slot * i + slot / 2:.1f}" '
            f'y="{mt + plot_h + 20}" text-anchor="middle">{_esc(label)}</text>'
        )

    # X axis title.
    parts.append(
        f'        <text class="axis-title" x="{ml + plot_w / 2}" '
        f'y="{H - 10}" text-anchor="middle">VRAM tier</text>'
    )
    parts.append("      </svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 2. Backend usage (donut chart)
# ---------------------------------------------------------------------------

def _polar(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _donut_segment(cx, cy, r_out, r_in, a0, a1) -> str:
    """The annular-sector <path> between angles a0..a1 (degrees)."""
    large = 1 if (a1 - a0) > 180 else 0
    x0, y0 = _polar(cx, cy, r_out, a0)
    x1, y1 = _polar(cx, cy, r_out, a1)
    x2, y2 = _polar(cx, cy, r_in, a1)
    x3, y3 = _polar(cx, cy, r_in, a0)
    return (f"M {x0:.2f} {y0:.2f} "
            f"A {r_out} {r_out} 0 {large} 1 {x1:.2f} {y1:.2f} "
            f"L {x2:.2f} {y2:.2f} "
            f"A {r_in} {r_in} 0 {large} 0 {x3:.2f} {y3:.2f} Z")


def backend_donut(subs: list[dict], schema: dict,
                  prefix: str = "chart-backend") -> tuple[str, str]:
    """Donut chart: submissions per inference backend.

    Returns ``(svg, legend_html)`` — the legend is HTML (real text,
    keyboard/screen-reader friendly) with color swatches matching the
    segments' CSS classes.
    """
    counts: dict[str, int] = {}
    for s in subs:
        b = utils.normalize_backend(s.get("backend", ""), schema)
        if b:
            counts[b] = counts.get(b, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    total = sum(counts.values())

    W, H = 320, 320
    cx, cy, r_out, r_in = W / 2, H / 2, 128, 78

    title = (f"Backend usage: {total} submissions across "
             f"{len(ordered)} backends")
    desc = ("Donut chart of submissions per inference backend. "
            + "; ".join(f"{b}: {c} ({c / total * 100:.0f}%)"
                        for b, c in ordered) if total else
            "No submissions with a backend yet.")

    parts = [_svg_open(prefix, title, desc, f"0 0 {W} {H}")]

    if total and len(ordered) == 1:
        # A 100% segment degenerates a path (start == end): draw a ring.
        parts.append(
            f'        <circle class="seg-1" cx="{cx}" cy="{cy}" '
            f'r="{(r_out + r_in) / 2}" fill="none" '
            f'stroke-width="{r_out - r_in}">'
            f'<title>{_esc(ordered[0][0])}: 1 (100%)</title></circle>'
        )
    else:
        angle = -90.0  # start at 12 o'clock, clockwise
        for i, (b, c) in enumerate(ordered):
            sweep = c / total * 360
            a0, a1 = angle, angle + sweep
            angle = a1
            cls = f"seg-{(i % PALETTE_SIZE) + 1}"
            if total > 1 and sweep >= 359.999:
                parts.append(
                    f'        <circle class="{cls}" cx="{cx}" cy="{cy}" '
                    f'r="{(r_out + r_in) / 2}" fill="none" '
                    f'stroke-width="{r_out - r_in}">'
                    f'<title>{_esc(b)}: {c} (100%)</title></circle>'
                )
            else:
                parts.append(
                    f'        <path class="{cls}" d="{_donut_segment(cx, cy, r_out, r_in, a0, a1)}">'
                    f'<title>{_esc(b)}: {c} submission{"s" if c != 1 else ""} '
                    f'({c / total * 100:.0f}%)</title></path>'
                )

    parts.append(
        f'        <text class="donut-center-value" x="{cx}" y="{cy - 2}" '
        f'text-anchor="middle">{total}</text>'
        f'        <text class="donut-center-label" x="{cx}" y="{cy + 18}" '
        f'text-anchor="middle">submissions</text>'
    )
    parts.append("      </svg>")
    svg = "\n".join(parts)

    legend_items = []
    for i, (b, c) in enumerate(ordered):
        cls = f"swatch-{(i % PALETTE_SIZE) + 1}"
        legend_items.append(
            f'        <li class="chart-legend-item">'
            f'<span class="chart-legend-swatch {cls}" aria-hidden="true"></span>'
            f'{_esc(b)} <span class="chart-legend-count">{c}</span></li>'
        )
    legend = ("      <ul class=\"chart-legend\" aria-label=\"Backends\">\n"
              + "\n".join(legend_items) + "\n      </ul>"
              if legend_items else "")
    return svg, legend


# ---------------------------------------------------------------------------
# 3. Model size vs VRAM (scatter plot)
# ---------------------------------------------------------------------------

def size_vram_scatter(subs: list[dict], schema: dict,
                      prefix: str = "chart-scatter") -> str:
    """Scatter plot: total model size (B params) vs VRAM footprint (GB).

    Points are submissions with a parseable size; the VRAM value is the
    best estimate from :func:`tools.site.utils.estimate_vram_gb`. Shows the
    "big name, small footprint" MoE story (e.g. 35B-A3B at ~13GB) against
    dense 27B at 48GB.
    """
    points = []
    for s in subs:
        size = utils.parse_model_size(utils.model_name(s))
        if size is None:
            continue
        vram = utils.estimate_vram_gb(s, schema)
        if vram is None:
            continue
        label = utils.short_model(utils.model_name(s))
        points.append((size, vram, label, s.get("id", "")))

    max_x = max((p[0] for p in points), default=0)
    max_y = max((p[1] for p in points), default=0)
    axis_x, step_x = _nice_scale(max_x)
    axis_y, step_y = _nice_scale(max_y)

    W, H = 640, 380
    ml, mr, mt, mb = 56, 18, 24, 58
    plot_w, plot_h = W - ml - mr, H - mt - mb

    n_pts = len(points)
    title = (f"Model size vs VRAM: {n_pts} submissions plotted")
    desc = (
        "Scatter plot of total parameter count (x-axis, billions) against "
        "VRAM footprint (y-axis, GB). "
        + "; ".join(f"{l}: {x:g}B / {y:g}GB" for x, y, l, _ in points)
        if points else "No submissions with both a size and a VRAM figure."
    )

    parts = [_svg_open(prefix, title, desc, f"0 0 {W} {H}")]

    def px(x: float) -> float:
        return ml + (x / axis_x) * plot_w

    def py(y: float) -> float:
        return mt + plot_h - (y / axis_y) * plot_h

    # Grid + ticks (both axes).
    x = 0.0
    while x <= axis_x + 1e-9:
        parts.append(
            f'        <line class="grid-line" x1="{px(x):.1f}" y1="{mt}" '
            f'x2="{px(x):.1f}" y2="{mt + plot_h}"/>'
            f'        <text class="tick-label" x="{px(x):.1f}" '
            f'y="{mt + plot_h + 20}" text-anchor="middle">{_fmt(x)}</text>'
        )
        x += step_x
    y = 0.0
    while y <= axis_y + 1e-9:
        parts.append(
            f'        <line class="grid-line" x1="{ml}" y1="{py(y):.1f}" '
            f'x2="{ml + plot_w}" y2="{py(y):.1f}"/>'
            f'        <text class="tick-label" x="{ml - 8}" y="{py(y) + 4:.1f}" '
            f'text-anchor="end">{_fmt(y)}</text>'
        )
        y += step_y

    # Axis lines.
    parts.append(
        f'        <line class="axis-line" x1="{ml}" y1="{mt + plot_h}" '
        f'x2="{ml + plot_w}" y2="{mt + plot_h}"/>'
        f'        <line class="axis-line" x1="{ml}" y1="{mt}" '
        f'x2="{ml}" y2="{mt + plot_h}"/>'
    )

    # Points (draw small-to-large so the big models sit on top).
    for size, vram, label, _sid in sorted(points, key=lambda p: p[0]):
        parts.append(
            f'        <circle class="dot" cx="{px(size):.1f}" '
            f'cy="{py(vram):.1f}" r="6">'
            f'<title>{_esc(label)}: {size:g}B params, ~{vram:g}GB VRAM</title></circle>'
        )

    # Axis titles.
    parts.append(
        f'        <text class="axis-title" x="{ml + plot_w / 2}" y="{H - 12}" '
        f'text-anchor="middle">Model size (billions of parameters)</text>'
    )
    parts.append(
        f'        <text class="axis-title" transform="rotate(-90 14 {mt + plot_h / 2})" '
        f'x="14" y="{mt + plot_h / 2}" text-anchor="middle">VRAM (GB)</text>'
    )
    parts.append("      </svg>")
    return "\n".join(parts)
