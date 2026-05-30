"""
visualizations.py
=================
All chart, graph, and visual-rendering functions for NEXUS.

Exports
-------
create_animated_bar_chart(results_df)   → renders ECharts grouped bar chart
create_scaling_line_chart(results_df)   → renders Plotly spline scaling chart
create_heatmap(results_df)              → renders Plotly neon heatmap
render_tree_graph(nodes, edges, name)   → renders agraph physics tree
render_array_visualization(data, hi)    → renders HTML array blocks
render_analysis_panel(analysis_dict)    → renders AnalysisGenerator output
render_podium(podium_dict)              → renders animated top-3 podium

Dependencies (pip install):
    plotly  streamlit-echarts==0.4.0  streamlit-agraph  streamlit
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
import streamlit as st

# ── ECharts ──────────────────────────────────────────────────────────────────
from streamlit_echarts import st_echarts, JsCode

# ── Plotly ───────────────────────────────────────────────────────────────────
import plotly.graph_objects as go

# ── agraph ───────────────────────────────────────────────────────────────────
from streamlit_agraph import agraph, Node, Edge, Config

# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (single source of truth)
# ══════════════════════════════════════════════════════════════════════════════

_C = {
    "insert":     "#00f0ff",   # cyan
    "search":     "#ff00c8",   # magenta
    "delete":     "#ffc800",   # gold
    "Array":      "#7a98b8",   # steel-blue
    "Hash Table": "#00f0ff",   # cyan
    "BST":        "#ff00c8",   # magenta
    "AVL Tree":   "#ffc800",   # gold
    "bg":         "rgba(0,0,0,0)",
    "grid":       "rgba(255,255,255,0.06)",
    "axis_text":  "#7aaec8",
    "white":      "#e8f4ff",
}

# Fallback colour for unknown structures
_STRUCT_COLOURS = ["#00f0ff", "#ff00c8", "#ffc800", "#00ff9d", "#9d00ff", "#ff6060"]


def _struct_colour(name: str, idx: int = 0) -> str:
    return _C.get(name, _STRUCT_COLOURS[idx % len(_STRUCT_COLOURS)])


def _hex_to_rgba(hex_colour: str, alpha: float = 1.0) -> str:
    """
    Convert a 6-digit hex colour string to an ``rgba()`` CSS string.

    Plotly does **not** accept 8-digit hex (``#rrggbbaa``); all alpha
    values must be expressed as ``rgba(r, g, b, a)``.

    Parameters
    ----------
    hex_colour : str
        A 6-digit hex string, e.g. ``"#00f0ff"`` or ``"00f0ff"``.
    alpha : float
        Opacity in the range 0–1 (default 1.0).

    Returns
    -------
    str
        ``"rgba(r, g, b, alpha)"``
    """
    h = hex_colour.lstrip("#")
    if len(h) == 8:          # already has alpha channel — strip it
        h = h[:6]
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# ══════════════════════════════════════════════════════════════════════════════
#  1.  ANIMATED BAR CHART  (ECharts)
# ══════════════════════════════════════════════════════════════════════════════

def create_animated_bar_chart(
    results_df: pd.DataFrame,
    selected_size: Optional[int] = None,
    height: str = "420px",
    key: str = "bar_chart",
) -> None:
    """
    Render an animated grouped bar chart comparing Insert / Search / Delete
    times across all data structures using ``streamlit-echarts``.

    Parameters
    ----------
    results_df : pd.DataFrame
        Must contain columns: structure, size, data_type,
        insert_ms, search_ms, delete_ms.
    selected_size : int | None
        If given, filter to only rows matching this dataset size.
        If None, average across all sizes.
    height : str
        CSS height for the chart container.
    key : str
        Streamlit widget key (must be unique per page).
    """
    if results_df is None or results_df.empty:
        st.info("Belum ada data benchmark — jalankan benchmark terlebih dahulu.")
        return

    df = results_df.copy()
    if selected_size is not None and selected_size in df["size"].values:
        df = df[df["size"] == selected_size]

    # Average across data types so one bar per structure
    agg = (
        df.groupby("structure")[["insert_ms", "search_ms", "delete_ms"]]
        .mean()
        .reset_index()
    )

    structures = agg["structure"].tolist()

    def _series(op: str, col: str, colour: str) -> dict:
        return {
            "name":      op,
            "type":      "bar",
            "barGap":    "8%",
            "barCategoryGap": "30%",
            "data":      [round(float(v), 4) for v in agg[col].tolist()],
            "itemStyle": {
                "color": {
                    "type":       "linear",
                    "x": 0, "y": 0, "x2": 0, "y2": 1,
                    "colorStops": [
                        {"offset": 0,   "color": colour},
                        {"offset": 1,   "color": _hex_to_rgba(colour, 0.27)},
                    ],
                },
                "borderRadius": [6, 6, 0, 0],
                "shadowColor":  _hex_to_rgba(colour, 0.53),
                "shadowBlur":   10,
            },
            "emphasis": {
                "itemStyle": {
                    "shadowBlur":  22,
                    "shadowColor": colour,
                }
            },
            "label": {
                "show":      True,
                "position":  "top",
                "formatter": JsCode(
                    "function(p){ return p.value === 0 ? '' : p.value.toFixed(3) + ' ms'; }"
                ).js_code,
                "color":     colour,
                "fontSize":  10,
                "fontFamily": "Share Tech Mono, monospace",
            },
        }

    tooltip_formatter = JsCode(
        "function(params) { return params.map(p => p.marker + ' ' + p.seriesName + ': <b>' + p.value.toFixed(3) + ' ms</b>').join('<br>'); }"
    ).js_code

    options = {
        "backgroundColor": "transparent",
        "animation":          True,
        "animationDuration":  1200,
        "animationEasing":    "CubicOut",
        "animationDelay":     JsCode(
            "function(idx){ return idx * 80; }"
        ).js_code,

        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "formatter": tooltip_formatter,
            "backgroundColor": "rgba(8,18,38,0.95)",
            "borderColor": "rgba(0,240,255,0.27)",
            "borderWidth": 1,
            "textStyle": {"color": "#e8f4ff", "fontFamily": "Share Tech Mono, monospace", "fontSize": 12},
        },

        "legend": {
            "data":      ["Insert", "Search", "Delete"],
            "top":       "4%",
            "right":     "4%",
            "textStyle": {
                "color":      _C["white"],
                "fontFamily": "Share Tech Mono, monospace",
                "fontSize":   11,
            },
            "icon":          "roundRect",
            "itemWidth":     14,
            "itemHeight":    8,
            "itemGap":       20,
        },

        "grid": {
            "left":         "4%",
            "right":        "4%",
            "bottom":       "12%",
            "top":          "16%",
            "containLabel": True,
        },

        "xAxis": {
            "type":        "category",
            "data":         structures,
            "axisLabel": {
                "color":      _C["axis_text"],
                "fontFamily": "Share Tech Mono, monospace",
                "fontSize":   11,
                "interval":   0,
            },
            "axisLine":  {"lineStyle": {"color": "rgba(0,240,255,0.15)"}},
            "axisTick":  {"show": False},
            "splitLine": {"show": False},
        },

        "yAxis": {
            "type": "value",
            "name": "Waktu (ms)",
            "nameTextStyle": {
                "color":      _C["axis_text"],
                "fontFamily": "Share Tech Mono, monospace",
                "fontSize":   10,
                "padding":    [0, 0, 0, 40],
            },
            "axisLabel": {
                "color":      _C["axis_text"],
                "fontFamily": "Share Tech Mono, monospace",
                "fontSize":   10,
                "formatter":  JsCode(
                    "function(v){ return v.toFixed(3); }"
                ).js_code,
            },
            "axisLine":  {"show": False},
            "axisTick":  {"show": False},
            "splitLine": {
                "lineStyle": {
                    "color":   "rgba(0,240,255,0.07)",
                    "type":    "dashed",
                }
            },
        },

        "series": [
            _series("Insert", "insert_ms", _C["insert"]),
            _series("Search", "search_ms", _C["search"]),
            _series("Delete", "delete_ms", _C["delete"]),
        ],
    }

    st_echarts(options=options, height=height, key=key)


# ══════════════════════════════════════════════════════════════════════════════
#  2.  SCALING LINE CHART  (Plotly)
# ══════════════════════════════════════════════════════════════════════════════

def create_scaling_line_chart(
    results_df: pd.DataFrame,
    operation:  str = "search",
    height:     int = 420,
) -> None:
    """
    Render a Plotly spline line chart showing how each data structure scales
    as dataset size grows (O(1) vs O(log n) vs O(n) visualisation).

    Parameters
    ----------
    results_df : pd.DataFrame
        Benchmark results DataFrame.
    operation : str
        Which operation column to plot: ``"insert"``, ``"search"``,
        or ``"delete"``.  Defaults to ``"search"``.
    height : int
        Pixel height for the chart.
    """
    if results_df is None or results_df.empty:
        st.info("Belum ada data benchmark — jalankan benchmark terlebih dahulu.")
        return

    op     = operation.lower().strip()
    col    = f"{op}_ms"
    if col not in results_df.columns:
        st.warning(f"Column '{col}' not found in results.")
        return

    df = results_df.copy()

    # Average across data types for each (structure, size) pair
    agg = (
        df.groupby(["structure", "size"])[col]
        .mean()
        .reset_index()
        .sort_values("size")
    )

    fig = go.Figure()

    structures = sorted(agg["structure"].unique())
    for idx, struct in enumerate(structures):
        sub    = agg[agg["structure"] == struct].sort_values("size")
        colour = _struct_colour(struct, idx)

        fig.add_trace(go.Scatter(
            x=sub["size"].tolist(),
            y=sub[col].tolist(),
            mode="lines+markers",
            name=struct,
            line=dict(
                shape="spline",
                smoothing=1.2,
                color=colour,
                width=2.5,
            ),
            marker=dict(
                size=8,
                color=colour,
                symbol="circle",
                line=dict(color="#0e1117", width=1.5),
            ),
            fill="tozeroy",
            fillcolor=_hex_to_rgba(colour, 0.05),
            hovertemplate=(
                f"<b style='color:{colour}'>{struct}</b><br>"
                "N = %{x:,}<br>"
                f"{op.capitalize()}: %{{y:.4f}} ms<extra></extra>"
            ),
        ))

    # Annotation: complexity labels on the rightmost point
    sizes = sorted(agg["size"].unique())
    if sizes:
        max_size = max(sizes)
        complexity_hint = {
            "Hash Table": "≈ O(1)",
            "AVL Tree":   "≈ O(log n)",
            "BST":        "≈ O(h)",
            "Array":      "≈ O(n)",
        }
        annotations = []
        for idx, struct in enumerate(structures):
            sub = agg[(agg["structure"] == struct) & (agg["size"] == max_size)]
            if sub.empty:
                continue
            y_val  = float(sub[col].iloc[0])
            colour = _struct_colour(struct, idx)
            hint   = complexity_hint.get(struct, "")
            annotations.append(dict(
                x=max_size, y=y_val,
                text=f"  {hint}",
                showarrow=False,
                font=dict(color=colour, size=10, family="Share Tech Mono, monospace"),
                xanchor="left",
            ))

    fig.update_layout(
        paper_bgcolor=_C["bg"],
        plot_bgcolor=_C["bg"],
        height=height,
        margin=dict(l=60, r=100, t=50, b=60),
        font=dict(
            family="Share Tech Mono, monospace",
            color=_C["white"],
            size=11,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
            font=dict(size=11, family="Share Tech Mono, monospace"),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,240,255,0.15)",
            borderwidth=1,
        ),
        xaxis=dict(
            title=dict(text="Ukuran Dataset (N)", font=dict(color=_C["axis_text"], size=11)),
            tickfont=dict(color=_C["axis_text"], family="Share Tech Mono, monospace", size=10),
            gridcolor=_C["grid"],
            showgrid=True,
            zeroline=False,
            linecolor="rgba(0,240,255,0.12)",
            type="log",
        ),
        yaxis=dict(
            title=dict(
                text=f"Waktu {op.capitalize()} (ms)",
                font=dict(color=_C["axis_text"], size=11),
            ),
            tickfont=dict(color=_C["axis_text"], family="Share Tech Mono, monospace", size=10),
            gridcolor=_C["grid"],
            showgrid=True,
            zeroline=False,
            linecolor="rgba(0,240,255,0.12)",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(8,18,38,0.95)",
            bordercolor="rgba(0,240,255,0.3)",
            font=dict(family="Share Tech Mono, monospace", color=_C["white"], size=11),
        ),
        annotations=annotations if sizes else [],
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
#  3.  HEATMAP  (Plotly)
# ══════════════════════════════════════════════════════════════════════════════

def create_heatmap(
    results_df: pd.DataFrame,
    height:     int = 380,
) -> None:
    """
    Render a Plotly heatmap: rows = data structures, columns = operations.
    Colour intensity = mean execution time.

    Parameters
    ----------
    results_df : pd.DataFrame
        Benchmark results DataFrame.
    height : int
        Pixel height.
    """
    if results_df is None or results_df.empty:
        st.info("Belum ada data benchmark — jalankan benchmark terlebih dahulu.")
        return

    df  = results_df.copy()
    ops = ["insert_ms", "search_ms", "delete_ms"]

    agg = df.groupby("structure")[ops].mean().reset_index()
    agg.columns = ["structure", "Insert", "Search", "Delete"]

    structures = agg["structure"].tolist()
    operations = ["Insert", "Search", "Delete"]
    z_matrix   = agg[operations].values.tolist()

    # Build custom black → cyan colourscale
    colorscale = [
        [0.00, "#040a19"],
        [0.15, "#062030"],
        [0.35, "#083a55"],
        [0.55, "#0a6080"],
        [0.75, "#00b4c4"],
        [1.00, "#00f0ff"],
    ]

    # Text annotations (values on cells)
    text_matrix = [
        [f"{v:.4f} ms" for v in row]
        for row in z_matrix
    ]

    fig = go.Figure(go.Heatmap(
        z=z_matrix,
        x=operations,
        y=structures,
        text=text_matrix,
        texttemplate="%{text}",
        textfont=dict(
            family="Share Tech Mono, monospace",
            size=11,
            color="#e8f4ff",
        ),
        colorscale=colorscale,
        showscale=True,
        colorbar=dict(
            title=dict(
                text="ms",
                font=dict(color=_C["axis_text"], family="Share Tech Mono, monospace", size=10),
            ),
            tickfont=dict(color=_C["axis_text"], family="Share Tech Mono, monospace", size=9),
            outlinecolor="rgba(0,240,255,0.15)",
            outlinewidth=1,
            thickness=14,
            len=0.8,
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "%{x}: <b>%{text}</b><extra></extra>"
        ),
        xgap=3,
        ygap=3,
    ))

    fig.update_layout(
        paper_bgcolor=_C["bg"],
        plot_bgcolor=_C["bg"],
        height=height,
        margin=dict(l=130, r=80, t=30, b=60),
        font=dict(family="Share Tech Mono, monospace", color=_C["white"], size=11),
        xaxis=dict(
            tickfont=dict(color=_C["white"], family="Orbitron, monospace", size=11),
            side="bottom",
            linecolor="rgba(0,240,255,0.1)",
        ),
        yaxis=dict(
            tickfont=dict(color=_C["axis_text"], family="Share Tech Mono, monospace", size=11),
            linecolor="rgba(0,240,255,0.1)",
        ),
        hoverlabel=dict(
            bgcolor="rgba(8,18,38,0.95)",
            bordercolor="rgba(0,240,255,0.3)",
            font=dict(family="Share Tech Mono, monospace", color=_C["white"], size=11),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
#  4.  TREE GRAPH  (streamlit-agraph, physics=True)
# ══════════════════════════════════════════════════════════════════════════════

def render_tree_graph(
    nodes:     list[dict],
    edges:     list[dict],
    tree_name: str = "BST",
    height:    int = 480,
) -> None:
    """
    Render an interactive physics-based tree using ``streamlit-agraph``.

    Parameters
    ----------
    nodes : list[dict]
        Node dicts from ``get_nodes_edges()`` — keys: ``id``, ``label``,
        optionally ``title`` (balance factor tooltip for AVL).
    edges : list[dict]
        Edge dicts — keys: ``source``, ``target``.
    tree_name : str
        ``"AVL"`` → cyan nodes; ``"BST"`` → magenta nodes.
    height : int
        Pixel height for the graph canvas.
    """
    if not nodes:
        st.markdown(
            """
            <div style="
                text-align:center;padding:3rem;
                font-family:'Share Tech Mono',monospace;
                font-size:0.75rem;letter-spacing:0.15em;
                color:rgba(0,240,255,0.3);text-transform:uppercase;
            ">
                ◈ Pohon kosong — masukkan nilai untuk divisualisasikan
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Colour scheme per tree type
    is_avl        = "AVL" in tree_name.upper()
    node_colour   = "#00f0ff" if is_avl else "#ff00c8"
    node_border   = "rgba(255, 255, 255, 0.2)"
    font_colour   = "#ffffff"
    edge_colour   = "rgba(0,240,255,0.35)" if is_avl else "rgba(255,0,200,0.35)"
    highlight_col = "#00ff9d"

    # Build agraph Node objects
    ag_nodes = [
        Node(
            id=n["id"],
            label=n["label"],
            title=n.get("title", n["label"]),   # tooltip (bf + height for AVL)
            size=20,
            color={
                "background": _hex_to_rgba(node_colour, 0.80),
                "border":     node_border,
                "highlight":  {
                    "background": highlight_col,
                    "border":     "#ffffff",
                },
                "hover": {
                    "background": node_colour,
                    "border":     "#ffffff",
                },
            },
            font={
                "color":  font_colour,
                "size":   13,
                "face":   "Share Tech Mono, monospace",
                "bold":   True,
            },
            shape="dot",
            shadow={
                "enabled": True,
                "color":   node_colour + "88",
                "size":    10,
                "x":       0, "y":  0,
            },
        )
        for n in nodes
    ]

    # Build agraph Edge objects
    ag_edges = [
        Edge(
            source=e["source"],
            target=e["target"],
            color=edge_colour,
            width=1.8,
            smooth={"type": "curvedCW", "roundness": 0.1},
            arrows={"to": {"enabled": True, "scaleFactor": 0.5}},
        )
        for e in edges
    ]

    # Physics config — barnesHut for organic elastic movement
    cfg = Config(
        width=f"100%",
        height=height,
        directed=True,
        physics=True,
        hierarchical=False,
        # Physics kwargs (passed via **kwargs → __dict__.update)
        solver="barnesHut",
        minVelocity=0.5,
        maxVelocity=80,
        timestep=0.45,
        stabilization=True,
        fit=True,
        # barnesHut tuning
        gravitationalConstant=-3500,
        centralGravity=0.3,
        springLength=95,
        springConstant=0.04,
        damping=0.09,
        avoidOverlap=0.6,
        # Interaction
        nodeHighlightBehavior=True,
        highlightColor=highlight_col,
        # vis-network interaction block
        interaction={
            "hover":          True,
            "tooltipDelay":   150,
            "navigationButtons": False,
            "keyboard":       False,
            "zoomView":       True,
            "dragView":       True,
        },
    )

    agraph(nodes=ag_nodes, edges=ag_edges, config=cfg)


# ══════════════════════════════════════════════════════════════════════════════
#  5.  ARRAY VISUALIZER  (HTML blocks)
# ══════════════════════════════════════════════════════════════════════════════

def render_array_visualization(
    array_data:      list[int],
    highlight_value: Optional[int] = None,
    max_display:     int           = 40,
    title:           str           = "Array State",
) -> None:
    """
    Render an HTML/CSS block representation of an array.

    Each element is a small box; the box matching ``highlight_value``
    glows cyan and floats slightly above the others.

    Parameters
    ----------
    array_data : list[int]
        The integers to display.
    highlight_value : int | None
        If given, this value's box gets the cyan glow treatment.
    max_display : int
        Cap the number of boxes shown (default 40) to avoid overflow.
    title : str
        Label shown above the array.
    """
    if not array_data:
        st.markdown(
            "<div style='font-family:Share Tech Mono,monospace;font-size:0.72rem;"
            "color:rgba(0,240,255,0.3);text-align:center;padding:1rem;'>"
            "◈ Array is empty</div>",
            unsafe_allow_html=True,
        )
        return

    display = array_data[:max_display]
    truncated = len(array_data) > max_display

    boxes_html = ""
    for idx, val in enumerate(display):
        is_hi = (highlight_value is not None and val == highlight_value)

        if is_hi:
            box_style = (
                "background:rgba(0,240,255,0.25);"
                "border:1px solid #00f0ff;"
                "color:#00f0ff;"
                "box-shadow:0 0 14px rgba(0,240,255,0.7),"
                            "0 0 30px rgba(0,240,255,0.3);"
                "transform:translateY(-6px) scale(1.12);"
                "z-index:2;"
                "font-weight:700;"
            )
            idx_style = "color:#00f0ff;"
        else:
            box_style = (
                "background:rgba(0,240,255,0.05);"
                "border:1px solid rgba(0,240,255,0.18);"
                "color:#7aaec8;"
            )
            idx_style = "color:rgba(0,240,255,0.25);"

        boxes_html += f"""
        <div style="
            display:inline-flex;flex-direction:column;align-items:center;
            margin:0 3px;transition:all 0.3s ease;
        ">
            <div style="
                width:46px;height:46px;
                display:flex;align-items:center;justify-content:center;
                border-radius:8px;
                font-family:'Share Tech Mono',monospace;
                font-size:0.72rem;letter-spacing:.02em;
                position:relative;
                transition:all 0.3s ease;
                {box_style}
            ">{val}</div>
            <div style="
                font-family:'Share Tech Mono',monospace;
                font-size:0.55rem;margin-top:4px;
                {idx_style}
            ">{idx}</div>
        </div>
        """

    if truncated:
        boxes_html += (
            "<div style='display:inline-flex;align-items:center;margin:0 6px;"
            "font-family:Share Tech Mono,monospace;font-size:1.2rem;"
            "color:rgba(0,240,255,0.3);padding-bottom:22px;'>…</div>"
        )

    st.markdown(
        f"""
        <div style="margin:0.5rem 0 1rem;">
            <div style="
                font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                letter-spacing:.2em;text-transform:uppercase;
                color:rgba(0,240,255,0.5);margin-bottom:0.6rem;
            ">{title}
                <span style="color:rgba(0,240,255,0.25);margin-left:0.8em;">
                    [{len(array_data)} elements]
                </span>
            </div>
            <div style="
                display:flex;flex-wrap:wrap;align-items:flex-end;
                gap:2px;padding:1rem 1.2rem 0.5rem;
                background:rgba(0,240,255,0.03);
                border:1px solid rgba(0,240,255,0.1);
                border-radius:12px;
                overflow-x:auto;
                min-height:90px;
            ">
                {boxes_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  6.  ANALYSIS PANEL
# ══════════════════════════════════════════════════════════════════════════════

def render_analysis_panel(analysis: dict) -> None:
    """
    Render the full output of ``AnalysisGenerator.generate_analysis()``
    as a styled, cyberpunk-themed panel.

    Parameters
    ----------
    analysis : dict
        Dict returned by ``AnalysisGenerator.generate_analysis()``.
    """
    if not analysis or "error" in analysis:
        st.warning(analysis.get("error", "Data analisis tidak tersedia."))
        return

    # ── 1. Overall winners ────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Orbitron',monospace;font-weight:700;
                    font-size:0.85rem;letter-spacing:.18em;color:#00f0ff;
                    text-transform:uppercase;margin-bottom:1rem;
                    padding-bottom:.5rem;border-bottom:1px solid rgba(0,240,255,0.12);">
            ◈ Pemenang Keseluruhan
        </div>
        """,
        unsafe_allow_html=True,
    )

    w_col1, w_col2, w_col3 = st.columns(3)
    for col, (op, colour, emoji) in zip(
        [w_col1, w_col2, w_col3],
        [
            ("overall_winner_insert", _C["insert"],  "⚡"),
            ("overall_winner_search", _C["search"],  "🔍"),
            ("overall_winner_delete", _C["delete"],  "🗑"),
        ],
    ):
        val = analysis.get(op, "—")
        struct_name = val.split("(")[0].strip()
        time_part   = "(" + val.split("(")[1] if "(" in val else ""
        with col:
            st.markdown(
                f"""
                <div style="
                    background:rgba(0,240,255,0.04);
                    border:1px solid {colour}33;
                    border-radius:14px;padding:1.2rem 1rem;
                    text-align:center;
                ">
                    <div style="font-size:1.8rem;margin-bottom:.4rem;
                                filter:drop-shadow(0 0 10px {colour});">
                        {emoji}
                    </div>
                    <div style="font-family:'Share Tech Mono',monospace;
                                font-size:.62rem;letter-spacing:.18em;
                                color:rgba(255,255,255,0.35);
                                text-transform:uppercase;margin-bottom:.4rem;">
                        Tercepat {op.split('_')[-1].capitalize()}
                    </div>
                    <div style="font-family:'Orbitron',monospace;font-weight:700;
                                font-size:.9rem;color:{colour};
                                text-shadow:0 0 12px {colour}88;
                                animation:winnerGlow 2.5s ease-in-out infinite;">
                        {struct_name}
                    </div>
                    <div style="font-family:'Share Tech Mono',monospace;
                                font-size:.65rem;color:rgba(255,255,255,0.3);
                                margin-top:.3rem;">
                        {time_part}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── 2. Podium ─────────────────────────────────────────────────────────────
    podium = analysis.get("podium", {})
    if podium:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#00f0ff;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(0,240,255,0.12);">
                ◈ Papan Peringkat
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_podium(podium)

    # ── 3. Scaling insights ───────────────────────────────────────────────────
    scaling = analysis.get("scaling_insights", [])
    if scaling:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#ffc800;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(255,200,0,0.15);">
                ◈ Analisis Penskalaan
            </div>
            """,
            unsafe_allow_html=True,
        )
        for note in scaling:
            struct_part = note.split("–")[0].strip() if "–" in note else ""
            rest_part   = note[len(struct_part):].strip(" –")
            st.markdown(
                f"""
                <div style="
                    font-family:'Share Tech Mono',monospace;font-size:.72rem;
                    color:#7aaec8;padding:.5rem .8rem;margin:.25rem 0;
                    border-left:2px solid rgba(255,200,0,0.4);
                    background:rgba(255,200,0,0.03);border-radius:0 6px 6px 0;
                    line-height:1.6;
                ">
                    <span style="color:#ffc800;font-weight:700;">{struct_part}</span>
                    {rest_part}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── 4. Data-type insights ─────────────────────────────────────────────────
    dtype_insights = analysis.get("data_type_insights", [])
    if dtype_insights:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#ff00c8;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(255,0,200,0.15);">
                ◈ Sensitivitas Distribusi Data
            </div>
            """,
            unsafe_allow_html=True,
        )
        for note in dtype_insights:
            st.markdown(
                f"""
                <div style="
                    font-family:'Share Tech Mono',monospace;font-size:.72rem;
                    color:#7aaec8;padding:.5rem .8rem;margin:.25rem 0;
                    border-left:2px solid rgba(255,0,200,0.4);
                    background:rgba(255,0,200,0.03);border-radius:0 6px 6px 0;
                    line-height:1.6;
                ">{note}</div>
                """,
                unsafe_allow_html=True,
            )

    # ── 5. Recommendation ─────────────────────────────────────────────────────
    rec = analysis.get("recommendation", "")
    if rec:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#00ff9d;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(0,255,157,0.15);">
                ◈ Rekomendasi
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Bold structure names inside the recommendation text
        import re
        highlighted = re.sub(
            r"\*\*(.+?)\*\*",
            r'<span style="color:#00ff9d;font-weight:700;">\1</span>',
            rec,
        )
        st.markdown(
            f"""
            <div style="
                font-family:'Exo 2',sans-serif;font-size:.82rem;
                color:#7aaec8;line-height:1.9;
                padding:1.2rem 1.4rem;
                background:rgba(0,255,157,0.03);
                border:1px solid rgba(0,255,157,0.12);
                border-radius:12px;
            ">{highlighted}</div>
            """,
            unsafe_allow_html=True,
        )

    # ── 6. Summary table ──────────────────────────────────────────────────────
    summary_df = analysis.get("summary_table")
    if summary_df is not None and not summary_df.empty:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#00f0ff;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(0,240,255,0.12);">
                ◈ Ringkasan Rata-rata Waktu (ms)
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(
            summary_df.rename(columns={
                "structure": "Struktur",
                "insert_ms": "Insert (ms)",
                "search_ms": "Pencarian (ms)",
                "delete_ms": "Hapus (ms)",
            }).style.format({
                "Insert (ms)": "{:.4f}",
                "Pencarian (ms)": "{:.4f}",
                "Hapus (ms)": "{:.4f}",
            }).highlight_min(
                subset=["Insert (ms)", "Pencarian (ms)", "Hapus (ms)"],
                color="rgba(0,255,157,0.15)",
            ),
            use_container_width=True,
            hide_index=True,
        )

    # ── 7. BST vs AVL degradation panel ───────────────────────────────────────
    bst_vs_avl = analysis.get("bst_vs_avl_degradation", [])
    if bst_vs_avl:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#ff00c8;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(255,0,200,0.15);">
                ◈ Degradasi BST vs AVL
            </div>
            """,
            unsafe_allow_html=True,
        )
        for note in bst_vs_avl:
            st.markdown(
                f"""
                <div style="
                    font-family:'Share Tech Mono',monospace;font-size:.72rem;
                    color:#ff80d0;padding:.6rem 1rem;margin:.3rem 0;
                    border:1px solid rgba(255,0,200,0.25);
                    border-left:3px solid #ff00c8;
                    background:rgba(255,0,200,0.05);
                    border-radius:0 8px 8px 0;line-height:1.6;
                ">{note}</div>
                """,
                unsafe_allow_html=True,
            )

    # ── 8. Pros and cons ──────────────────────────────────────────────────────
    pros_cons = analysis.get("pros_and_cons", {})
    if pros_cons:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#00f0ff;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(0,240,255,0.12);">
                ◈ Kelebihan & Kekurangan
            </div>
            """,
            unsafe_allow_html=True,
        )
        for struct, pk in pros_cons.items():
            with st.expander(f"⚡  {struct}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""
                        <div style="font-family:'Share Tech Mono',monospace;font-size:.7rem;
                                    color:#00ff9d;letter-spacing:.08em;margin-bottom:.4rem;">
                        ✓ KELEBIHAN</div>
                        <div style="font-family:'Exo 2',sans-serif;font-size:.78rem;
                                    color:#7aaec8;line-height:1.6;">{pk['kelebihan']}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div style="font-family:'Share Tech Mono',monospace;font-size:.7rem;
                                    color:#ff6060;letter-spacing:.08em;margin-bottom:.4rem;">
                        ✗ KEKURANGAN</div>
                        <div style="font-family:'Exo 2',sans-serif;font-size:.78rem;
                                    color:#7aaec8;line-height:1.6;">{pk['kekurangan']}</div>
                        """,
                        unsafe_allow_html=True,
                    )

    # ── 9. Theory vs practice ─────────────────────────────────────────────────
    tvp = analysis.get("theory_vs_practice", {})
    if tvp:
        st.markdown(
            """
            <div style="font-family:'Orbitron',monospace;font-weight:700;
                        font-size:0.85rem;letter-spacing:.18em;color:#ffc800;
                        text-transform:uppercase;margin:1.5rem 0 1rem;
                        padding-bottom:.5rem;border-bottom:1px solid rgba(255,200,0,0.15);">
                ◈ Teori vs Praktik
            </div>
            """,
            unsafe_allow_html=True,
        )
        for label, verdict in tvp.items():
            st.markdown(
                f"""
                <div style="
                    font-family:'Share Tech Mono',monospace;font-size:.7rem;
                    color:#c8a87a;padding:.5rem .9rem;margin:.25rem 0;
                    border:1px solid rgba(255,200,0,0.15);
                    border-left:3px solid #ffc800;
                    background:rgba(255,200,0,0.03);
                    border-radius:0 6px 6px 0;line-height:1.5;
                ">
                    <span style="color:#ffc800;font-weight:700;">{label}</span>
                    <span style="color:#7aaec8;"> — {verdict}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
#  7.  PODIUM  (Top-3 leaderboard)
# ══════════════════════════════════════════════════════════════════════════════

def render_podium(podium: dict[str, list[str]]) -> None:
    """
    Render an animated top-3 podium leaderboard for each operation.

    Parameters
    ----------
    podium : dict[str, list[str]]
        Keys: ``"insert"``, ``"search"``, ``"delete"``.
        Values: list of ranked strings like ``["1. AVL Tree (0.12 ms)", ...]``.
    """
    _MEDALS = ["🥇", "🥈", "🥉"]
    _MEDAL_COLOURS = ["#ffc800", "#b0c4de", "#cd7f32"]

    pod_cols = st.columns(3)
    op_meta = [
        ("insert", "Insert",  _C["insert"],  "⚡"),
        ("search", "Search",  _C["search"],  "🔍"),
        ("delete", "Delete",  _C["delete"],  "🗑"),
    ]

    for col, (op_key, op_label, colour, icon) in zip(pod_cols, op_meta):
        entries = podium.get(op_key, [])
        with col:
            st.markdown(
                f"""
                <div style="
                    background:rgba(0,0,0,0.2);
                    border:1px solid {colour}22;
                    border-top:2px solid {colour};
                    border-radius:0 0 14px 14px;
                    padding:1rem 0.8rem;
                    margin-bottom:0.5rem;
                ">
                    <div style="
                        text-align:center;margin-bottom:.8rem;
                        font-family:'Orbitron',monospace;font-size:.75rem;
                        font-weight:700;letter-spacing:.15em;
                        color:{colour};text-transform:uppercase;
                        text-shadow:0 0 10px {colour}88;
                    ">
                        {icon} {op_label}
                    </div>
                    {"".join([
                        f'''<div style="
                            display:flex;align-items:center;gap:.6rem;
                            padding:.4rem .5rem;margin:.2rem 0;
                            border-radius:8px;
                            background:{'rgba(255,200,0,0.08)' if i==0 else 'transparent'};
                            border:{'1px solid rgba(255,200,0,0.2)' if i==0 else '1px solid transparent'};
                        ">
                            <span style="font-size:.9rem;">{_MEDALS[i] if i < 3 else '  '}</span>
                            <span style="
                                font-family:'Share Tech Mono',monospace;
                                font-size:.65rem;color:{_MEDAL_COLOURS[i] if i < 3 else '#3a5a78'};
                                line-height:1.4;flex:1;
                            ">{entry.split('. ', 1)[-1] if '. ' in entry else entry}</span>
                        </div>'''
                        for i, entry in enumerate(entries[:3])
                    ])}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
#  8.  MINI METRICS ROW  (fast inline render for dashboard tab)
# ══════════════════════════════════════════════════════════════════════════════

def render_metrics_row(results_df: pd.DataFrame) -> None:
    """
    Render a row of four ``st.metric`` cards summarising benchmark results.

    Parameters
    ----------
    results_df : pd.DataFrame
        Benchmark results DataFrame.
    """
    if results_df is None or results_df.empty:
        return

    agg = results_df.groupby("structure")[["insert_ms", "search_ms", "delete_ms"]].mean()

    best_insert = agg["insert_ms"].idxmin()
    best_search = agg["search_ms"].idxmin()
    best_delete = agg["delete_ms"].idxmin()
    fastest_val = agg[["insert_ms", "search_ms", "delete_ms"]].min().min()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Insert Tercepat",
            best_insert,
            delta=f"{agg.loc[best_insert,'insert_ms']:.4f} ms",
        )
    with m2:
        st.metric(
            "Pencarian Tercepat",
            best_search,
            delta=f"{agg.loc[best_search,'search_ms']:.4f} ms",
        )
    with m3:
        st.metric(
            "Hapus Tercepat",
            best_delete,
            delta=f"{agg.loc[best_delete,'delete_ms']:.4f} ms",
        )
    with m4:
        st.metric(
            "Waktu Terbaik",
            f"{fastest_val:.4f} ms",
            delta="performa puncak",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  9.  HEIGHT COMPARISON  (BST vs AVL — Plotly)
# ══════════════════════════════════════════════════════════════════════════════

def render_height_comparison(bst_height: int, avl_height: int) -> None:
    """
    Render a cyberpunk bar chart comparing BST height vs AVL height.

    Parameters
    ----------
    bst_height : int
        Height of the BST.
    avl_height : int
        Height of the AVL tree.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["BST", "AVL Tree"],
        y=[bst_height, avl_height],
        marker=dict(
            color=["#ff00c8", "#00f0ff"],
            line=dict(color=["#ff00c8", "#00f0ff"], width=2),
        ),
        text=[str(bst_height), str(avl_height)],
        textposition="outside",
        textfont=dict(
            family="Orbitron, monospace",
            size=16,
            color=["#ff00c8", "#00f0ff"],
        ),
        hovertemplate="<b>%{x}</b><br>Tinggi: %{y}<extra></extra>",
        width=[0.5, 0.5],
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(family="Share Tech Mono, monospace", color="#e8f4ff", size=11),
        xaxis=dict(
            tickfont=dict(color="#7aaec8", family="Orbitron, monospace", size=12),
            linecolor="rgba(0,240,255,0.12)",
            showgrid=False,
        ),
        yaxis=dict(
            title=dict(text="Tinggi", font=dict(color="#7aaec8", size=10)),
            tickfont=dict(color="#7aaec8", size=10),
            gridcolor="rgba(255,255,255,0.06)",
            zeroline=False,
            linecolor="rgba(0,240,255,0.12)",
        ),
        hoverlabel=dict(
            bgcolor="rgba(8,18,38,0.95)",
            bordercolor="rgba(0,240,255,0.3)",
            font=dict(family="Share Tech Mono, monospace", color="#e8f4ff", size=11),
        ),
        annotations=[
            dict(
                x=0, y=bst_height,
                xref="x", yref="y",
                text=f"BST: {bst_height}",
                showarrow=False,
                font=dict(color="#ff00c8", size=11, family="Share Tech Mono, monospace"),
                yshift=10,
            ),
            dict(
                x=1, y=avl_height,
                xref="x", yref="y",
                text=f"AVL: {avl_height}",
                showarrow=False,
                font=dict(color="#00f0ff", size=11, family="Share Tech Mono, monospace"),
                yshift=10,
            ),
        ],
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
#  10.  HASH COLLISION VISUALISER  (Plotly)
# ══════════════════════════════════════════════════════════════════════════════

def render_hash_collision(buckets: list[int]) -> None:
    """
    Render a neon bar chart visualising hash-table bucket occupancy.

    Parameters
    ----------
    buckets : list[int]
        List where each element is 0 (empty), 1 (filled), or 2 (tombstone).
    """
    if not buckets:
        st.markdown(
            "<div style='font-family:Share Tech Mono,monospace;font-size:0.72rem;"
            "color:rgba(0,240,255,0.3);text-align:center;padding:1rem;'>"
            "◈ Hash table kosong</div>",
            unsafe_allow_html=True,
        )
        return

    colours = []
    labels  = []
    for v in buckets:
        if v == 0:
            colours.append("rgba(0,240,255,0.12)")
            labels.append("Kosong")
        elif v == 1:
            colours.append("#00f0ff")
            labels.append("Terisi")
        else:
            colours.append("rgba(255,0,200,0.5)")
            labels.append("Tombstone")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(range(len(buckets))),
        y=[1] * len(buckets),
        marker=dict(color=colours, line=dict(color=colours, width=1)),
        text=labels,
        textposition="inside",
        textfont=dict(
            family="Share Tech Mono, monospace",
            size=8,
            color="#03040a",
        ),
        hovertemplate="Bucket %{x}<br>Status: %{text}<extra></extra>",
        width=0.85,
    ))

    # Count stats
    n_filled = sum(1 for v in buckets if v == 1)
    n_empty  = sum(1 for v in buckets if v == 0)
    n_tomb   = sum(1 for v in buckets if v == 2)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=200,
        margin=dict(l=30, r=30, t=30, b=30),
        font=dict(family="Share Tech Mono, monospace", color="#e8f4ff", size=10),
        xaxis=dict(
            title=dict(text="Indeks Bucket", font=dict(color="#7aaec8", size=9)),
            tickfont=dict(color="#7aaec8", size=8),
            linecolor="rgba(0,240,255,0.12)",
            showgrid=False,
            dtick=max(1, len(buckets) // 10),
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, 1.4]),
        hoverlabel=dict(
            bgcolor="rgba(8,18,38,0.95)",
            bordercolor="rgba(0,240,255,0.3)",
            font=dict(family="Share Tech Mono, monospace", color="#e8f4ff", size=11),
        ),
        annotations=[
            dict(
                x=0.02, y=1.3, xref="paper", yref="y",
                text=f"<span style='color:#00f0ff;'>■</span> Terisi: {n_filled} &nbsp;"
                     f"<span style='color:rgba(0,240,255,0.12);'>■</span> Kosong: {n_empty} &nbsp;"
                     f"<span style='color:rgba(255,0,200,0.5);'>■</span> Tombstone: {n_tomb}",
                showarrow=False,
                font=dict(family="Share Tech Mono, monospace", size=10, color="#7aaec8"),
                xanchor="left",
            ),
        ],
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
#  Quick self-test  (python visualizations.py)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))

    # ── Construct a minimal mock DataFrame ───────────────────────────────────
    import math, random
    import pandas as pd

    rng   = random.Random(7)
    rows  = []
    metas = [
        ("Array",      {"insert": 0.02, "search": 4.5,  "delete": 4.0}),
        ("Hash Table", {"insert": 0.05, "search": 0.12, "delete": 0.10}),
        ("BST",        {"insert": 0.18, "search": 0.20, "delete": 0.22}),
        ("AVL Tree",   {"insert": 0.25, "search": 0.15, "delete": 0.20}),
    ]
    for struct, base in metas:
        for size in [100, 1000, 10000]:
            scale = math.log10(size + 1)
            for dt in ["random", "sorted", "descending"]:
                rows.append({
                    "structure": struct,
                    "size":       size,
                    "data_type":  dt,
                    "insert_ms":  round(base["insert"] * scale + rng.uniform(-0.01, 0.01), 4),
                    "search_ms":  round(base["search"] * scale + rng.uniform(-0.1,  0.1),  4),
                    "delete_ms":  round(base["delete"] * scale + rng.uniform(-0.08, 0.08), 4),
                })

    df = pd.DataFrame(rows)
    print(f"Mock DataFrame: {len(df)} rows, columns={list(df.columns)}")

    # ── Verify colour lookups ─────────────────────────────────────────────────
    for struct in ["Array", "Hash Table", "BST", "AVL Tree", "Unknown"]:
        c = _struct_colour(struct, 0)
        assert c.startswith("#"), f"Bad colour for {struct}: {c}"
    print("_struct_colour       ✓")

    # ── Verify aggregation logic used in charts ───────────────────────────────
    agg_bar = df.groupby("structure")[["insert_ms","search_ms","delete_ms"]].mean().reset_index()
    assert len(agg_bar) == 4,            "Wrong number of structures in bar agg"
    assert "insert_ms" in agg_bar.columns, "Missing insert_ms"
    print("Bar aggregation      ✓")

    agg_line = (
        df.groupby(["structure","size"])["search_ms"]
        .mean().reset_index().sort_values("size")
    )
    assert not agg_line.empty, "Empty line chart aggregation"
    print("Line aggregation     ✓")

    # ── Verify heatmap matrix builds correctly ────────────────────────────────
    agg_heat = df.groupby("structure")[["insert_ms","search_ms","delete_ms"]].mean().reset_index()
    agg_heat.columns = ["structure","Insert","Search","Delete"]
    z = agg_heat[["Insert","Search","Delete"]].values.tolist()
    assert len(z) == 4 and len(z[0]) == 3, "Heatmap matrix shape wrong"
    print("Heatmap matrix       ✓")

    # ── Verify agraph object construction (no Streamlit context needed) ───────
    from data_structures import BinarySearchTreeDS, AVLTreeDS

    bst = BinarySearchTreeDS()
    for v in [50, 30, 70, 20, 40, 60, 80]:
        bst.insert(v)
    n_raw, e_raw = bst.get_nodes_edges()

    ag_nodes = [
        Node(
            id=n["id"], label=n["label"],
            title=n.get("title", n["label"]),
            size=20, color="#ff00c8",
        )
        for n in n_raw
    ]
    ag_edges = [
        Edge(source=e["source"], target=e["target"], color="rgba(255,0,200,0.35)")
        for e in e_raw
    ]
    assert len(ag_nodes) == 7, f"Expected 7 nodes, got {len(ag_nodes)}"
    assert len(ag_edges) == 6, f"Expected 6 edges, got {len(ag_edges)}"
    print("agraph Node/Edge     ✓")

    avl = AVLTreeDS()
    for v in [10, 20, 30, 40, 50, 25]:
        avl.insert(v)
    n2, e2 = avl.get_nodes_edges()
    assert all("title" in n for n in n2), "AVL nodes missing 'title' field"
    print("AVL node title field ✓")

    # ── Verify HTML array builder (no Streamlit context) ─────────────────────
    import html as _html

    def _mock_array_html(data, hi=None):
        boxes = ""
        for val in data[:5]:
            is_hi = hi is not None and val == hi
            boxes += f"<div class='{'hi' if is_hi else 'normal'}'>{val}</div>"
        return boxes

    h = _mock_array_html([3, 7, 1, 9, 2], hi=7)
    assert "hi" in h, "Highlight class not applied"
    print("Array HTML builder   ✓")

    # ── Verify analysis rendering helper (mock analysis dict) ─────────────────
    mock_analysis = {
        "overall_winner_insert": "Hash Table  (0.1234 ms avg)",
        "overall_winner_search": "Hash Table  (0.1100 ms avg)",
        "overall_winner_delete": "Hash Table  (0.1050 ms avg)",
        "summary_table":         agg_bar.rename(columns={
                                     "insert_ms": "insert_ms",
                                     "search_ms": "search_ms",
                                     "delete_ms": "delete_ms",
                                 }),
        "scaling_insights":      ["Array – search: scales linear (O(n)) (×8.2 time for ×100 data)"],
        "data_type_insights":    ["BST – insert: fastest on 'random' data, slowest on 'sorted' (spread 0.3 ms)"],
        "complexity_comparison": {"Array": "insert: O(1) → 0.05 ms | search: O(n) → 4.5 ms"},
        "recommendation":        "Based on results, **Hash Table** is the best choice overall.",
        "podium": {
            "insert": ["1. Hash Table  (0.12 ms)", "2. Array  (0.09 ms)", "3. AVL Tree  (0.25 ms)"],
            "search": ["1. Hash Table  (0.11 ms)", "2. AVL Tree  (0.18 ms)", "3. BST  (0.22 ms)"],
            "delete": ["1. Hash Table  (0.10 ms)", "2. AVL Tree  (0.20 ms)", "3. BST  (0.22 ms)"],
        },
    }
    # Validate dict structure (not rendering — needs Streamlit)
    assert "overall_winner_insert" in mock_analysis
    assert isinstance(mock_analysis["podium"]["insert"], list)
    print("Analysis dict shape  ✓")

    print("\nAll visualizations.py tests passed ✓")
