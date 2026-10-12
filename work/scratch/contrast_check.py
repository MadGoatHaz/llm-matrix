"""WCAG contrast ratio checker for the site's color pairs.

Computes relative luminance per the WCAG 2.1 definition and reports the
contrast ratio for every foreground/background pair used in css/style.css.
Alpha tints (badges, glows) are composited over the surface they sit on.
"""

def _chan(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)

def ratio(fg: str, bg: str) -> float:
    lf, lb = lum(fg), lum(bg)
    if lf < lb:
        lf, lb = lb, lf
    return (lf + 0.05) / (lb + 0.05)

def blend(fg: str, bg: str, a: float) -> str:
    """Composite fg over bg with alpha a -> hex."""
    def px(h):
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    f, b = px(fg), px(bg)
    out = tuple(round(f[i] * a + b[i] * (1 - a)) for i in range(3))
    return "#%02x%02x%02x" % out

T = {
    "bg": "#0a0e17", "surface": "#131a2b", "surface2": "#1a2332",
    "border": "#1e2d3f", "text": "#e2e8f0", "text2": "#94a3b8",
    "text3": "#64748b", "accent": "#3b82f6", "accent_h": "#2563eb",
    "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444",
    "purple": "#8b5cf6", "cyan": "#06b6d4", "white": "#ffffff",
}

def blend_tokens(fg, bg, a):
    return blend(T[fg], T[bg], a)

NAV_BG = blend_tokens("bg", "bg", 0.9)

# (label, fg, bg, min_needed)
PAIRS = [
    ("body text / bg",            "text",    "bg",      4.5),
    ("body text / surface",       "text",    "surface", 4.5),
    ("body text / surface2",      "text",    "surface2",4.5),
    ("secondary text / bg",       "text2",   "bg",      4.5),
    ("secondary text / surface",  "text2",   "surface", 4.5),
    ("secondary text / surface2", "text2",   "surface2",4.5),
    ("muted text / bg",           "text3",   "bg",      4.5),
    ("muted text / surface",      "text3",   "surface", 4.5),
    ("muted text / surface2",     "text3",   "surface2",4.5),
    ("accent (links) / bg",       "accent",  "bg",      4.5),
    ("accent (links) / surface",  "accent",  "surface", 4.5),
    ("accent (links) / surface2", "accent",  "surface2",4.5),
    ("white on accent (btn)",     "white",   "accent",  4.5),
    ("white on accent-hover",     "white",   "accent_h",4.5),
    ("tier header accent / surface2", "accent","surface2",3.0),
    ("nav logo accent / nav bg",  "accent",  NAV_BG,    3.0),
    ("nav link text2 / nav bg",   "text2",   NAV_BG,    4.5),
    ("badge green on tint",       "success", blend_tokens("success","surface",0.15), 4.5),
    ("badge blue on tint",        "accent",  blend_tokens("accent","surface",0.15), 4.5),
    ("badge purple on tint",      "purple",  blend_tokens("purple","surface",0.15), 4.5),
    ("badge amber on tint",       "warning", blend_tokens("warning","surface",0.15), 4.5),
    ("badge cyan on tint",        "cyan",    blend_tokens("cyan","surface",0.15), 4.5),
    ("callout default glow text", "text",    blend_tokens("accent","bg",0.15), 4.5),
    ("hero h1 span accent / bg",  "accent",  "bg",      3.0),
    ("footer text3 / bg",         "text3",   "bg",      4.5),
    ("footer link text2 / bg",    "text2",   "bg",      4.5),
    ("stat value accent / surface","accent","surface",  3.0),
    ("stat label text3 / surface","text3",   "surface", 4.5),
    ("table th text2 / surface2", "text2",   "surface2",4.5),
    ("guide p text2 / bg",        "text2",   "bg",      4.5),
    ("guide td text2 / bg",       "text2",   "bg",      4.5),
    ("guide th text2 / surface2", "text2",   "surface2",4.5),
    ("diagram label text2 / surface","text2","surface", 4.5),
    ("diagram cell text2 / surface2","text2","surface2",4.5),
    ("diagram arrow text3 / surface","text3","surface", 3.0),
    ("cmd flag accent on glow/surface","accent",blend_tokens("accent","surface",0.15),4.5),
    ("cmd flag warn on tint/surface","warning",blend_tokens("warning","surface",0.12),4.5),
    ("rec advanced hint text3 / surface2","text3","surface2",4.5),
    ("compare bar text3 / surface","text3","surface", 4.5),
    ("compare col meta text3 / surface2","text3","surface2",4.5),
    ("rec contributor text3 / bg","text3","bg", 4.5),
    ("page header meta text3 / bg","text3","bg", 4.5),
    ("success (no pair, sanity) / bg","success","bg", 3.0),
    ("warning / bg","warning","bg", 3.0),
    ("cyan / bg","cyan","bg", 3.0),
    ("purple / bg","purple","bg", 3.0),
]

print(f"{'pair':45} {'fg':8} {'bg':8} {'ratio':>6} {'need':>5}  verdict")
fails = []
for label, fg, bg, need in PAIRS:
    fgk = T[fg] if fg in T else fg
    bgl = T[bg] if bg in T else bg
    r = ratio(fgk, bgl)
    ok = r >= need
    if not ok:
        fails.append((label, r, need))
    print(f"{label:45} {fgk:8} {bgl:8} {r:6.2f} {need:5.1f}  {'PASS' if ok else 'FAIL'}")

print()
print(f"{len(fails)} failing pairs:")
for label, r, need in fails:
    print(f"  - {label}: {r:.2f} < {need}")
