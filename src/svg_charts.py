"""Minimal dependency-free SVG charting helpers.

Produces standalone .svg files that render natively inside GitHub READMEs.
Only bar_chart() and line_chart() are needed by the analysis layer.
"""

import os

# A small, readable palette.
INK = "#1f2937"
MUTED = "#6b7280"
GRID = "#e5e7eb"
ACCENT = "#2563eb"
ACCENT_2 = "#10b981"
BG = "#ffffff"

FONT = "font-family='Segoe UI, Helvetica, Arial, sans-serif'"


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _nice_max(value):
    """Round an axis maximum up to a clean number for readable gridlines."""
    if value <= 0:
        return 1
    import math

    exp = math.floor(math.log10(value))
    base = 10 ** exp
    for mult in (1, 2, 2.5, 5, 10):
        candidate = mult * base
        if candidate >= value:
            return candidate
    return 10 * base


def _fmt_axis(value):
    if value >= 1_000_000:
        return "{:.1f}M".format(value / 1_000_000)
    if value >= 1_000:
        return "{:.0f}K".format(value / 1_000)
    if value == int(value):
        return "{:.0f}".format(value)
    return "{:.1f}".format(value)


def _save(path, svg):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(svg)


def bar_chart(path, labels, values, title="", width=820, height=420,
              color=ACCENT, value_prefix=""):
    """Vertical bar chart."""
    pad_left, pad_right = 70, 24
    pad_top, pad_bottom = 56, 90
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    vmax = _nice_max(max(values) if values else 1)
    n = len(values)
    slot = plot_w / n if n else plot_w
    bar_w = slot * 0.62

    parts = []
    parts.append(
        "<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        "viewBox='0 0 {w} {h}' role='img'>".format(w=width, h=height)
    )
    parts.append("<rect width='{}' height='{}' fill='{}'/>".format(width, height, BG))
    if title:
        parts.append(
            "<text x='{x}' y='32' {f} font-size='18' font-weight='600' "
            "fill='{c}'>{t}</text>".format(
                x=pad_left, f=FONT, c=INK, t=_esc(title)
            )
        )

    # Horizontal gridlines + y labels.
    ticks = 4
    for i in range(ticks + 1):
        gv = vmax * i / ticks
        y = pad_top + plot_h - (gv / vmax) * plot_h
        parts.append(
            "<line x1='{x1}' y1='{y}' x2='{x2}' y2='{y}' stroke='{c}' "
            "stroke-width='1'/>".format(
                x1=pad_left, x2=width - pad_right, y=y, c=GRID
            )
        )
        parts.append(
            "<text x='{x}' y='{y}' {f} font-size='11' fill='{c}' "
            "text-anchor='end'>{lbl}</text>".format(
                x=pad_left - 8, y=y + 4, f=FONT, c=MUTED,
                lbl=value_prefix + _fmt_axis(gv),
            )
        )

    for i, (label, value) in enumerate(zip(labels, values)):
        bar_h = (value / vmax) * plot_h if vmax else 0
        x = pad_left + i * slot + (slot - bar_w) / 2
        y = pad_top + plot_h - bar_h
        parts.append(
            "<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            "rx='3' fill='{c}'/>".format(x=x, y=y, w=bar_w, h=bar_h, c=color)
        )
        parts.append(
            "<text x='{x:.1f}' y='{y}' {f} font-size='11' fill='{c}' "
            "text-anchor='end' transform='rotate(-40 {x:.1f} {y})'>{lbl}</text>".format(
                x=x + bar_w / 2, y=height - pad_bottom + 18, f=FONT, c=MUTED,
                lbl=_esc(label),
            )
        )

    parts.append("</svg>")
    _save(path, "".join(parts))


def line_chart(path, labels, values, title="", width=820, height=420,
               color=ACCENT, value_prefix="", label_every=1):
    """Single-series line chart with markers."""
    pad_left, pad_right = 70, 24
    pad_top, pad_bottom = 56, 80
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    vmax = _nice_max(max(values) if values else 1)
    n = len(values)
    step = plot_w / (n - 1) if n > 1 else 0

    def point(i, v):
        x = pad_left + i * step
        y = pad_top + plot_h - (v / vmax) * plot_h if vmax else pad_top + plot_h
        return x, y

    parts = []
    parts.append(
        "<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        "viewBox='0 0 {w} {h}' role='img'>".format(w=width, h=height)
    )
    parts.append("<rect width='{}' height='{}' fill='{}'/>".format(width, height, BG))
    if title:
        parts.append(
            "<text x='{x}' y='32' {f} font-size='18' font-weight='600' "
            "fill='{c}'>{t}</text>".format(
                x=pad_left, f=FONT, c=INK, t=_esc(title)
            )
        )

    ticks = 4
    for i in range(ticks + 1):
        gv = vmax * i / ticks
        y = pad_top + plot_h - (gv / vmax) * plot_h
        parts.append(
            "<line x1='{x1}' y1='{y}' x2='{x2}' y2='{y}' stroke='{c}' "
            "stroke-width='1'/>".format(
                x1=pad_left, x2=width - pad_right, y=y, c=GRID
            )
        )
        parts.append(
            "<text x='{x}' y='{y}' {f} font-size='11' fill='{c}' "
            "text-anchor='end'>{lbl}</text>".format(
                x=pad_left - 8, y=y + 4, f=FONT, c=MUTED,
                lbl=value_prefix + _fmt_axis(gv),
            )
        )

    pts = [point(i, v) for i, v in enumerate(values)]

    # Soft area fill under the line.
    if pts:
        area = "M {:.1f} {:.1f} ".format(pts[0][0], pad_top + plot_h)
        area += " ".join("L {:.1f} {:.1f}".format(x, y) for x, y in pts)
        area += " L {:.1f} {:.1f} Z".format(pts[-1][0], pad_top + plot_h)
        parts.append(
            "<path d='{d}' fill='{c}' fill-opacity='0.10'/>".format(d=area, c=color)
        )

    poly = " ".join("{:.1f},{:.1f}".format(x, y) for x, y in pts)
    parts.append(
        "<polyline points='{p}' fill='none' stroke='{c}' stroke-width='2.5' "
        "stroke-linejoin='round'/>".format(p=poly, c=color)
    )

    for i, (x, y) in enumerate(pts):
        parts.append(
            "<circle cx='{:.1f}' cy='{:.1f}' r='3' fill='{}'/>".format(x, y, color)
        )
        if i % label_every == 0 or i == n - 1:
            parts.append(
                "<text x='{x:.1f}' y='{y}' {f} font-size='10' fill='{c}' "
                "text-anchor='end' transform='rotate(-45 {x:.1f} {y})'>{lbl}</text>".format(
                    x=x, y=height - pad_bottom + 16, f=FONT, c=MUTED,
                    lbl=_esc(labels[i]),
                )
            )

    parts.append("</svg>")
    _save(path, "".join(parts))
