"""Search for replacement token values that pass WCAG AA (4.5:1) on the
hardest backgrounds they sit on, while staying visually distinct."""

def _chan(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)

def ratio(fg, bg):
    lf, lb = lum(fg), lum(bg)
    if lf < lb: lf, lb = lb, lf
    return (lf + 0.05) / (lb + 0.05)

def blend(fg, bg, a):
    def px(h):
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    f, b = px(fg), px(bg)
    return "#%02x%02x%02x" % tuple(round(f[i]*a + b[i]*(1-a)) for i in range(3))

BG, S1, S2 = "#0a0e17", "#131a2b", "#1a2332"

print("=== --text-muted candidates (need >=4.5 on all of bg/s1/s2; distinct from text-secondary #94a3b8) ===")
for c in ["#74849b", "#7a8aa1", "#8090a7", "#8494ab", "#8a9ab0"]:
    print(f"  {c}: bg={ratio(c,BG):.2f} s1={ratio(c,S1):.2f} s2={ratio(c,S2):.2f}")

print("\n=== --accent candidates (need >=4.5 on bg/s1/s2) ===")
for c in ["#3b82f6", "#4a90f8", "#5098ff", "#5b9dff", "#6aa5ff", "#78b0ff"]:
    print(f"  {c}: bg={ratio(c,BG):.2f} s1={ratio(c,S1):.2f} s2={ratio(c,S2):.2f}")

print("\n=== white on accent candidates (for button fills; need >=4.5) ===")
for c in ["#2563eb", "#1d4ed8", "#2b6cf0", "#3b82f6"]:
    print(f"  white/{c}: {ratio('#ffffff', c):.2f}")

print("\n=== badge tints with candidate accents (15% over surface) ===")
for c in ["#3b82f6", "#5098ff", "#5b9dff", "#6aa5ff"]:
    tint = blend(c, S1, 0.15)
    print(f"  {c} on tint {tint}: {ratio(c, tint):.2f}")

print("\n=== --purple candidates (badge purple, 15% over surface) ===")
for c in ["#8b5cf6", "#9d74f8", "#a78bfa", "#b195fc"]:
    tint = blend(c, S1, 0.15)
    print(f"  {c} on tint {tint}: {ratio(c, tint):.2f}")

print("\n=== nav bg (90% bg over bg) ===")
navbg = blend(BG, BG, 0.9)
print(f"  navbg = {navbg}")
for c in ["#3b82f6", "#5098ff", "#5b9dff"]:
    print(f"  {c} on navbg: {ratio(c, navbg):.2f}")

print("\n=== glow (15% accent over bg) for callout text check ===")
for c in ["#3b82f6", "#5b9dff"]:
    g = blend(c, BG, 0.15)
    print(f"  text #e2e8f0 on {c}-glow {g}: {ratio('#e2e8f0', g):.2f}")

print("\n=== final picks: verify full matrix ===")
picks = {"text-muted": "#8494ab", "accent": "#5b9dff", "accent-btn": "#2563eb", "purple": "#a78bfa"}
tm, ac, ab, pu = picks["text-muted"], picks["accent"], picks["accent-btn"], picks["purple"]
checks = [
    ("muted/bg", ratio(tm, BG)), ("muted/s1", ratio(tm, S1)), ("muted/s2", ratio(tm, S2)),
    ("accent/bg", ratio(ac, BG)), ("accent/s1", ratio(ac, S1)), ("accent/s2", ratio(ac, S2)),
    ("accent/navbg", ratio(ac, navbg)),
    ("white/accent-btn", ratio("#ffffff", ab)),
    ("badge blue", ratio(ac, blend(ac, S1, 0.15))),
    ("badge purple", ratio(pu, blend(pu, S1, 0.15))),
]
for name, r in checks:
    print(f"  {name}: {r:.2f} {'PASS' if r >= 4.5 else 'FAIL'}")
