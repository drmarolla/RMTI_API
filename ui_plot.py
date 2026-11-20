# Copyright 2026 Cesar Marolla. Licensed under the Apache License, Version 2.0.
"""One scientific look for every Plotly figure on the site.

    import ui_plot
    st.plotly_chart(ui_plot.style(fig))      # or let rmti_nav.install_plot_theme() do it for every page

What it fixes (reviewer notes on the 4D Risk Matrix page):
  * faint grid lines and tiny axis labels  -> darker light-blue grid, 13 to 14 px labels, navy text
  * right-hand labels colliding with lines -> right margin of at least 120 px on 2-D charts, legend moved below the plot
  * 3-D scene labels hard to read          -> 12 to 14 px tick and axis-title fonts, visible grid and axis lines
The function never raises: if a property is not supported by the installed Plotly it leaves the figure as it was.
Palette: red, light blue, white (navy for text).
"""
from __future__ import annotations

INK = "#0b2545"
AXIS = "#1e3a5f"
GRID = "#9cc3ee"          # clearly visible on white, still light blue (not gray)
SCENE_BG = "rgba(234,244,255,0.55)"
FONT = "Inter, Segoe UI, Arial, sans-serif"
MIN_RIGHT_2D = 120        # px: room for right-hand annotations such as tier labels
MIN_RIGHT_3D = 40         # px: room for a colour bar
THREE_D = {"scatter3d", "surface", "mesh3d", "cone", "volume", "isosurface", "streamtube"}


def _is_3d(fig) -> bool:
    try:
        return any(getattr(t, "type", "") in THREE_D for t in fig.data)
    except Exception:  # noqa: BLE001
        return False


def _n_traces(fig) -> int:
    try:
        return len(fig.data)
    except Exception:  # noqa: BLE001
        return 0


def _margin(fig, side: str) -> int:
    try:
        v = getattr(fig.layout.margin, side)
        return int(v) if v is not None else 0
    except Exception:  # noqa: BLE001
        return 0


def style(fig, *, legend_below: bool = True):
    """Apply the shared look in place and return the figure."""
    try:
        three_d = _is_3d(fig)
        fig.update_layout(font=dict(family=FONT, size=14, color=INK),
                          title_font=dict(family=FONT, size=17, color=INK),
                          paper_bgcolor="rgba(0,0,0,0)", hoverlabel=dict(font_size=14, font_family=FONT))
        # margins: never shrink what a page asked for, only make room
        r_min = MIN_RIGHT_3D if three_d else MIN_RIGHT_2D
        margin = dict(r=max(_margin(fig, "r"), r_min))
        if not three_d:
            margin["l"] = max(_margin(fig, "l"), 60)
        fig.update_layout(margin=margin)
        if not three_d:
            fig.update_xaxes(gridcolor=GRID, gridwidth=1, linecolor=AXIS, linewidth=1.5, showline=True, zeroline=False,
                             tickfont=dict(size=13, color=INK), title_font=dict(size=14, color=INK))
            fig.update_yaxes(gridcolor=GRID, gridwidth=1, linecolor=AXIS, linewidth=1.5, showline=True, zeroline=False,
                             tickfont=dict(size=13, color=INK), title_font=dict(size=14, color=INK))
            if legend_below and _n_traces(fig) > 1:
                fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0,
                                              font=dict(size=13, color=INK), bgcolor="rgba(255,255,255,0.9)"),
                                  margin=dict(b=max(_margin(fig, "b"), 100)))
        else:
            axis3d = dict(gridcolor=GRID, gridwidth=2, linecolor=AXIS, linewidth=3, showline=True, showbackground=True,
                          backgroundcolor=SCENE_BG, zerolinecolor=AXIS, tickfont=dict(size=12, color=INK),
                          title_font=dict(size=14, color=INK))
            fig.update_scenes(xaxis=axis3d, yaxis=axis3d, zaxis=axis3d)
        try:                                   # annotations: make small text readable
            fig.update_annotations(font=dict(size=13, color=INK))
        except Exception:  # noqa: BLE001
            pass
        try:                                   # subplot titles (make_subplots) are annotations too, covered above
            fig.update_layout(modebar=dict(bgcolor="rgba(255,255,255,0)", color=AXIS, activecolor="#d9262c"))
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001
        pass
    return fig
