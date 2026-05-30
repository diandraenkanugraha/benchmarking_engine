"""
app.py — NEXUS: Data Structure Mesin Benchmarking  (Phase 5 — Final)
======================================================================
Complete integration of all four modules:

    data_structures.py   ← ArrayDS, HashTableDS, BinarySearchTreeDS, AVLTreeDS
    benchmark_engine.py  ← DatasetGenerator, BenchmarkRunner, AnalysisGenerator
    visualizations.py    ← All chart / graph / HTML renderers

Run with:
    streamlit run app.py

pip install streamlit streamlit-lottie streamlit-echarts==0.4.0
            streamlit-agraph plotly pandas
"""
from __future__ import annotations

import re
import sys
import time
from typing import Any

# Tingkatkan batas rekursi untuk BST/AVL dengan dataset besar (10.000+ elemen)
sys.setrecursionlimit(50000)

import pandas as pd
import streamlit as st

# ── Phase 1: Data structures ──────────────────────────────────────────────────
from data_structures import (
    ArrayDS, HashTableDS, BinarySearchTreeDS, AVLTreeDS,
)

# ── Phase 2: Benchmark engine ─────────────────────────────────────────────────
from benchmark_engine import DatasetGenerator, BenchmarkRunner, AnalysisGenerator

# ── Phase 4: Visualizations ───────────────────────────────────────────────────
from visualizations import (
    create_animated_bar_chart,
    create_scaling_line_chart,
    create_heatmap,
    render_tree_graph,
    render_array_visualization,
    render_podium,
    render_metrics_row,
)

# ── Optional Lottie ───────────────────────────────────────────────────────────
try:
    from streamlit_lottie import st_lottie
    _LOTTIE_OK = True
except ImportError:
    _LOTTIE_OK = False


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG  (must be the very first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="NEXUS — Mesin Benchmarking Struktur Data",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════════════════
#  INLINE LOTTIE ANIMATIONS  (programmatic — no CDN required)
# ══════════════════════════════════════════════════════════════════════════════

def _make_hero_lottie() -> dict:
    """Six coloured particles orbiting a central cyan node (512×512, 30 fps)."""
    import math as _m
    FRAMES  = 120
    FPS     = 30
    CX, CY  = 256, 256
    RADIUS  = 110
    COLOURS = [
        [0, 255, 255], [0, 200, 255], [160, 32, 240],
        [255, 0, 128], [0, 255, 160], [255, 200, 0],
    ]
    layers = [{
        "ddd": 0, "ind": 100, "ty": 4, "nm": "core", "sr": 1,
        "ks": {
            "o": {"a": 0, "k": 80},
            "p": {"a": 0, "k": [CX, CY, 0]},
            "s": {"a": 0, "k": [100, 100, 100]},
        },
        "shapes": [{"ty": "gr", "it": [
            {"ty": "el", "s": {"a": 0, "k": [28, 28]}},
            {"ty": "fl", "c": {"a": 0, "k": [0, 1, 1, 1]}, "o": {"a": 0, "k": 100}},
        ]}],
        "ip": 0, "op": FRAMES, "st": 0,
    }]
    for i, (r, g, b) in enumerate(COLOURS):
        phase     = (i / len(COLOURS)) * 2 * _m.pi
        direction = 1 if i % 2 == 0 else -1
        n_kf      = 37
        kf_pos    = []
        for kf in range(n_kf):
            angle = phase + direction * (kf / (n_kf - 1)) * 2 * _m.pi
            kf_pos.append({
                "t": round((kf / (n_kf - 1)) * (FRAMES - 1)),
                "s": [CX + RADIUS * _m.cos(angle), CY + RADIUS * _m.sin(angle), 0],
                "e": [CX + RADIUS * _m.cos(angle), CY + RADIUS * _m.sin(angle), 0],
                "i": {"x": [0.5], "y": [0.5]},
                "o": {"x": [0.5], "y": [0.5]},
            })
        for k in range(len(kf_pos) - 1):
            kf_pos[k]["e"] = kf_pos[k + 1]["s"]
        layers.append({
            "ddd": 0, "ind": i, "ty": 4, "nm": f"p{i}", "sr": 1,
            "ks": {
                "o": {"a": 0, "k": 90},
                "p": {"a": 1, "k": kf_pos},
                "s": {"a": 0, "k": [100, 100, 100]},
            },
            "shapes": [{"ty": "gr", "it": [
                {"ty": "el", "s": {"a": 0, "k": [14 + (i % 3) * 4, 14 + (i % 3) * 4]}},
                {"ty": "fl", "c": {"a": 0, "k": [r/255, g/255, b/255, 1]}, "o": {"a": 0, "k": 100}},
            ]}],
            "ip": 0, "op": FRAMES, "st": 0,
        })
    return {
        "v": "5.7.4", "fr": FPS, "ip": 0, "op": FRAMES,
        "w": 512, "h": 512, "nm": "hero", "ddd": 0, "assets": [], "layers": layers,
    }


def _make_sidebar_lottie() -> dict:
    """Pulsing diamond — compact 100×100 sidebar icon."""
    F = 60
    return {
        "v": "5.7.4", "fr": 24, "ip": 0, "op": F,
        "w": 100, "h": 100, "nm": "sb", "ddd": 0, "assets": [],
        "layers": [{
            "ddd": 0, "ind": 0, "ty": 4, "nm": "d", "sr": 1,
            "ks": {
                "o": {"a": 1, "k": [
                    {"t": 0,     "s": [100], "e": [40],  "i": {"x": [0.5], "y": [0.5]}, "o": {"x": [0.5], "y": [0.5]}},
                    {"t": F//2,  "s": [40],  "e": [100], "i": {"x": [0.5], "y": [0.5]}, "o": {"x": [0.5], "y": [0.5]}},
                    {"t": F - 1, "s": [100]},
                ]},
                "p": {"a": 0, "k": [50, 50, 0]},
                "s": {"a": 1, "k": [
                    {"t": 0,     "s": [80, 80, 100],  "e": [120, 120, 100], "i": {"x": [.42], "y": [0]}, "o": {"x": [.58], "y": [1]}},
                    {"t": F//2,  "s": [120, 120, 100], "e": [80, 80, 100],  "i": {"x": [.42], "y": [0]}, "o": {"x": [.58], "y": [1]}},
                    {"t": F - 1, "s": [80, 80, 100]},
                ]},
                "r": {"a": 0, "k": 45},
            },
            "shapes": [{"ty": "gr", "it": [
                {"ty": "rc", "s": {"a": 0, "k": [28, 28]}, "r": {"a": 0, "k": 3}},
                {"ty": "fl", "c": {"a": 0, "k": [0, 1, 1, 1]}, "o": {"a": 0, "k": 100}},
                {"ty": "st", "c": {"a": 0, "k": [0.6, 0, 1, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 2}},
            ]}],
            "ip": 0, "op": F, "st": 0,
        }],
    }


_HERO_LOTTIE    = _make_hero_lottie()
_SIDEBAR_LOTTIE = _make_sidebar_lottie()


# ══════════════════════════════════════════════════════════════════════════════
#  BINARY-SEARCH WRAPPER  (routes search → binary_search for benchmarking)
# ══════════════════════════════════════════════════════════════════════════════

class _ArrayBinaryDS(ArrayDS):
    """Thin ArrayDS subclass that benchmarks binary_search via the search() API."""

    def search(self, value: int) -> bool:  # noqa: D102
        return self.binary_search(value)


# Human-readable structure labels shown in the UI
_UI_STRUCTURES: list[str] = ["Array", "Hash Table", "BST", "AVL Tree"]


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

def _init_state() -> None:
    """Initialise all st.session_state keys with safe defaults."""
    defaults: dict[str, Any] = {
        "engine_initialised": False,
        # benchmark config
        "sel_sizes":          [100, 1_000, 10_000],
        "sel_dtype":          "random",
        "sel_structures":     list(_UI_STRUCTURES),
        "n_repeats":          5,
        # results
        "results_df":         None,
        "analysis":           None,
        "last_run_ts":        None,
        "benchmark_ran":      False,
        # tree tab
        "tree_bst":           None,
        "tree_avl":           None,
        "tree_val":           42,
        "tree_log":           [],
        # run trigger (sidebar → main body)
        "_run_trigger":       False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS  (all keyframes, glassmorphism, sidebar, tabs, metrics…)
# ══════════════════════════════════════════════════════════════════════════════

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');

:root {
    --bg-void:       #03040a;
    --bg-panel:      rgba(8,18,38,0.85);
    --bg-glass:      rgba(0,240,255,0.04);
    --border-cyan:   rgba(0,240,255,0.30);
    --border-bright: rgba(0,240,255,0.70);
    --cyan:          #00f0ff;
    --cyan-dim:      #00b4c4;
    --magenta:       #ff00c8;
    --purple:        #9d00ff;
    --gold:          #ffc800;
    --green:         #00ff9d;
    --txt-hi:        #e8f4ff;
    --txt-mid:       #7aaec8;
    --txt-lo:        #3a5a78;
    --trans:         all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"] {
    background: var(--bg-void) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%,rgba(0,180,255,.07),transparent),
        radial-gradient(ellipse 60% 40% at 80% 80%,rgba(157,0,255,.06),transparent),
        repeating-linear-gradient(0deg,transparent,transparent 80px,rgba(0,240,255,.012) 80px,rgba(0,240,255,.012) 81px),
        repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(0,240,255,.012) 80px,rgba(0,240,255,.012) 81px) !important;
    font-family:'Exo 2',sans-serif !important;
    color: var(--txt-hi) !important;
}
#MainMenu,footer,header,[data-testid="stDecoration"],.stDeployButton{visibility:hidden!important;display:none!important;}

@keyframes glitchBase{0%,24%,26%,100%{text-shadow:0 0 10px var(--cyan),0 0 30px var(--cyan),0 0 80px rgba(0,240,255,.4);opacity:1;}25%{opacity:.92;transform:translate(-1px,0) skewX(-.5deg);}}
@keyframes glitchL1{0%,4%,6%,100%{clip-path:inset(100% 0 0 0);opacity:0;}5%{clip-path:inset(30% 0 50% 0);opacity:.8;transform:translate(3px,0);color:var(--magenta);}}
@keyframes glitchL2{0%,9%,11%,100%{clip-path:inset(100% 0 0 0);opacity:0;}10%{clip-path:inset(60% 0 25% 0);opacity:.7;transform:translate(-3px,0);color:var(--cyan);}}
@keyframes slideUpFade{from{opacity:0;transform:translateY(36px) scale(.97);filter:blur(4px);}to{opacity:1;transform:translateY(0) scale(1);filter:blur(0);}}
@keyframes glowPulse{0%,100%{box-shadow:0 0 6px rgba(0,240,255,.3),0 0 20px rgba(0,240,255,.15),inset 0 0 15px rgba(0,240,255,.05);border-color:var(--border-cyan);}50%{box-shadow:0 0 16px rgba(0,240,255,.7),0 0 45px rgba(0,240,255,.35),0 0 80px rgba(0,240,255,.12),inset 0 0 25px rgba(0,240,255,.1);border-color:var(--border-bright);}}
@keyframes winnerGlow{0%,100%{text-shadow:0 0 8px var(--green),0 0 24px var(--green),0 0 50px rgba(0,255,157,.5);}50%{text-shadow:0 0 12px var(--cyan),0 0 35px var(--cyan),0 0 70px rgba(0,240,255,.7);}}
@keyframes float3d{0%{transform:perspective(900px) rotateY(-18deg) rotateX(6deg) translateY(0);}33%{transform:perspective(900px) rotateY(0deg) rotateX(10deg) translateY(-12px);}66%{transform:perspective(900px) rotateY(18deg) rotateX(6deg) translateY(-6px);}100%{transform:perspective(900px) rotateY(-18deg) rotateX(6deg) translateY(0);}}
@keyframes floatBob{0%,100%{transform:translateY(0);}50%{transform:translateY(-14px);}}
@keyframes scanSweep{0%{transform:translateY(-100%);opacity:.5;}100%{transform:translateY(2000%);opacity:0;}}
@keyframes btnGlowPulse{0%,100%{box-shadow:0 0 10px rgba(0,240,255,.4),0 0 30px rgba(0,240,255,.2);}50%{box-shadow:0 0 25px rgba(0,240,255,.8),0 0 60px rgba(0,240,255,.4),0 0 100px rgba(0,240,255,.2);}}
@keyframes shimmer{0%{background-position:-200% center;}100%{background-position:200% center;}}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0;}}
@keyframes tabActiveSweep{from{transform:scaleX(0);}to{transform:scaleX(1);}}

.cascade-fade-in{opacity:0;animation:slideUpFade .7s cubic-bezier(.22,1,.36,1) forwards;}
.cascade-fade-in:nth-child(1){animation-delay:.05s;}.cascade-fade-in:nth-child(2){animation-delay:.18s;}
.cascade-fade-in:nth-child(3){animation-delay:.30s;}.cascade-fade-in:nth-child(4){animation-delay:.42s;}
.cascade-fade-in:nth-child(5){animation-delay:.54s;}.cascade-fade-in:nth-child(6){animation-delay:.66s;}
.delay-1{animation-delay:.10s!important;}.delay-2{animation-delay:.25s!important;}
.delay-3{animation-delay:.40s!important;}.delay-4{animation-delay:.55s!important;}
.delay-5{animation-delay:.70s!important;}.delay-6{animation-delay:.85s!important;}

/* Strip ALL Streamlit top padding so hero sits flush at the top */
[data-testid="stMain"] > div:first-child,
[data-testid="stMainBlockContainer"],
.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
.nexus-hero{
    position:relative;overflow:hidden;
    height:100vh;max-height:100vh;
    display:flex;flex-direction:column;
    align-items:center;justify-content:center;
    padding:2rem 2rem 1rem;text-align:center;
    box-sizing:border-box;
}
.nexus-hero::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,var(--cyan) 50%,transparent);animation:scanSweep 6s linear infinite;z-index:1;opacity:.6;}
.nexus-hero::after{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:70vw;height:70vw;background:radial-gradient(circle,rgba(0,180,255,.06) 0%,rgba(157,0,255,.04) 40%,transparent 70%);pointer-events:none;z-index:0;}
.glitch-wrapper{position:relative;display:inline-block;z-index:2;margin-bottom:.5rem;}
.glitch-title{font-family:'Orbitron',monospace;font-weight:900;font-size:clamp(2.4rem,5.5vw,5rem);letter-spacing:.08em;color:var(--cyan);animation:glitchBase 5s ease-in-out infinite;position:relative;user-select:none;}
.glitch-title::before,.glitch-title::after{content:attr(data-text);position:absolute;top:0;left:0;width:100%;height:100%;}
.glitch-title::before{color:var(--magenta);animation:glitchL1 5s ease-in-out infinite;}
.glitch-title::after{color:var(--cyan);animation:glitchL2 5s ease-in-out infinite;}
.glitch-sub{font-family:'Share Tech Mono',monospace;font-size:clamp(.75rem,1.4vw,1rem);color:var(--txt-mid);letter-spacing:.28em;text-transform:uppercase;margin-top:-.3rem;margin-bottom:2rem;z-index:2;position:relative;}
.glitch-sub .cursor{display:inline-block;width:.55em;height:1em;background:var(--cyan);vertical-align:text-bottom;margin-left:2px;animation:blink 1s step-end infinite;}
.float3d-container{perspective:900px;z-index:2;margin:.5rem auto 2.5rem;}
.float3d-card{width:220px;height:130px;background:linear-gradient(135deg,rgba(0,240,255,.1),rgba(157,0,255,.08),rgba(0,240,255,.05));border:1px solid var(--border-cyan);border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:float3d 7s ease-in-out infinite;box-shadow:0 0 25px rgba(0,240,255,.25),0 0 60px rgba(0,240,255,.1),inset 0 0 30px rgba(0,240,255,.07);backdrop-filter:blur(12px);position:relative;overflow:hidden;}
.float3d-card-icon{font-size:2.5rem;margin-bottom:.4rem;filter:drop-shadow(0 0 12px var(--cyan));}
.float3d-card-label{font-family:'Share Tech Mono',monospace;font-size:.65rem;letter-spacing:.25em;color:var(--cyan-dim);text-transform:uppercase;}
.hero-badges{display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;margin-bottom:2.5rem;z-index:2;position:relative;}
.hero-badge{font-family:'Share Tech Mono',monospace;font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;padding:.4rem 1rem;border-radius:100px;border:1px solid;}
.hero-badge.cyan{color:var(--cyan);border-color:rgba(0,240,255,.4);background:rgba(0,240,255,.07);}
.hero-badge.magenta{color:var(--magenta);border-color:rgba(255,0,200,.4);background:rgba(255,0,200,.07);}
.hero-badge.purple{color:#bf7fff;border-color:rgba(157,0,255,.4);background:rgba(157,0,255,.07);}
.hero-badge.green{color:var(--green);border-color:rgba(0,255,157,.4);background:rgba(0,255,157,.07);}

div[data-testid="stButton"]>button{font-family:'Orbitron',monospace!important;font-weight:700!important;font-size:.85rem!important;letter-spacing:.2em!important;text-transform:uppercase!important;background:linear-gradient(135deg,rgba(0,240,255,.15),rgba(157,0,255,.10))!important;color:var(--cyan)!important;border:1px solid var(--border-bright)!important;border-radius:8px!important;padding:.85rem 2.8rem!important;transition:var(--trans)!important;animation:btnGlowPulse 3s ease-in-out infinite!important;position:relative!important;overflow:hidden!important;}
div[data-testid="stButton"]>button:hover{background:linear-gradient(135deg,rgba(0,240,255,.28),rgba(157,0,255,.20))!important;box-shadow:0 0 30px rgba(0,240,255,.6),0 0 80px rgba(0,240,255,.3),0 0 0 1px var(--cyan)!important;transform:translateY(-2px) scale(1.03)!important;}
div[data-testid="stButton"]>button:active{transform:translateY(0) scale(.98)!important;}

[data-testid="stMetric"]{background:var(--bg-glass)!important;border:1px solid var(--border-cyan)!important;border-radius:16px!important;padding:1.4rem 1.6rem!important;backdrop-filter:blur(20px)!important;animation:glowPulse 3s ease-in-out infinite!important;transition:var(--trans)!important;transform-style:preserve-3d!important;transform:perspective(600px) translateZ(0)!important;position:relative!important;overflow:hidden!important;}
[data-testid="stMetric"]::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,240,255,.6),transparent);pointer-events:none;}
[data-testid="stMetric"]:hover{transform:perspective(600px) translateZ(50px) translateY(-4px)!important;box-shadow:0 0 30px rgba(0,240,255,.5),0 20px 60px rgba(0,0,0,.6),0 0 0 1px rgba(0,240,255,.5)!important;border-color:var(--border-bright)!important;}
[data-testid="stMetricLabel"]>div{font-family:'Share Tech Mono',monospace!important;font-size:.72rem!important;letter-spacing:.18em!important;text-transform:uppercase!important;color:var(--txt-mid)!important;}
[data-testid="stMetricValue"]>div{font-family:'Orbitron',monospace!important;font-weight:700!important;font-size:1.9rem!important;color:var(--cyan)!important;text-shadow:0 0 20px rgba(0,240,255,.5)!important;}
[data-testid="stMetricDelta"]>div{font-family:'Share Tech Mono',monospace!important;font-size:.78rem!important;}

.nexus-panel{background:var(--bg-panel);border:1px solid rgba(0,240,255,.15);border-radius:20px;padding:1.8rem 2rem;backdrop-filter:blur(16px);position:relative;overflow:hidden;margin-bottom:1.5rem;box-shadow:0 8px 40px rgba(0,0,0,.8);}
.nexus-panel::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--cyan) 30%,var(--magenta) 70%,transparent);opacity:.6;}
.nexus-panel-title{font-family:'Orbitron',monospace;font-weight:700;font-size:1.1rem;letter-spacing:.12em;color:var(--cyan);text-shadow:0 0 15px rgba(0,240,255,.4);text-transform:uppercase;margin-bottom:1rem;display:flex;align-items:center;gap:.6rem;}
.nexus-panel-title .dot{width:8px;height:8px;background:var(--cyan);border-radius:50%;box-shadow:0 0 8px var(--cyan);flex-shrink:0;}
.nexus-section-header{font-family:'Orbitron',monospace;font-weight:600;font-size:.8rem;letter-spacing:.22em;color:var(--txt-mid);text-transform:uppercase;margin-bottom:1.2rem;padding-bottom:.5rem;border-bottom:1px solid rgba(0,240,255,.12);display:flex;align-items:center;gap:.6rem;}
.nexus-section-header::before{content:'';display:inline-block;width:18px;height:2px;background:var(--cyan);box-shadow:0 0 6px var(--cyan);flex-shrink:0;}
.nexus-divider{height:1px;background:linear-gradient(90deg,transparent,var(--border-cyan),transparent);margin:1.5rem 0;position:relative;}
.nexus-divider::after{content:'◆';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:var(--cyan);font-size:.6rem;background:var(--bg-void);padding:0 .5rem;text-shadow:0 0 8px var(--cyan);}

[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(4,10,25,.97),rgba(6,14,35,.95))!important;border-right:1px solid rgba(0,240,255,.12)!important;backdrop-filter:blur(20px)!important;}
[data-testid="stSidebar"] label{font-family:'Share Tech Mono',monospace!important;font-size:.72rem!important;letter-spacing:.14em!important;text-transform:uppercase!important;color:var(--txt-mid)!important;}
[data-testid="stSidebar"] [data-testid="stSelectbox"]>div>div{background:rgba(0,240,255,.04)!important;border:1px solid rgba(0,240,255,.2)!important;border-radius:8px!important;color:var(--txt-hi)!important;}
.sidebar-title{font-family:'Orbitron',monospace;font-weight:700;font-size:1.05rem;color:var(--cyan);letter-spacing:.12em;text-transform:uppercase;text-shadow:0 0 12px rgba(0,240,255,.4);}
.sidebar-version{font-family:'Share Tech Mono',monospace;font-size:.62rem;color:var(--txt-lo);letter-spacing:.2em;margin-bottom:1.5rem;}
.sidebar-section-label{font-family:'Share Tech Mono',monospace;font-size:.65rem;letter-spacing:.22em;color:var(--purple);text-transform:uppercase;margin:1.2rem 0 .5rem;opacity:.8;}
.status-badge{display:inline-flex;align-items:center;gap:.5rem;font-family:'Share Tech Mono',monospace;font-size:.68rem;letter-spacing:.12em;padding:.35rem .8rem;border-radius:100px;margin-bottom:.5rem;}
.status-badge.online{background:rgba(0,255,157,.08);border:1px solid rgba(0,255,157,.3);color:var(--green);}
.status-badge.online::before{content:'';width:6px;height:6px;background:var(--green);border-radius:50%;box-shadow:0 0 6px var(--green);animation:glowPulse 1.8s ease-in-out infinite;}
.status-badge.ready{background:rgba(0,240,255,.06);border:1px solid rgba(0,240,255,.25);color:var(--cyan-dim);}

[data-testid="stTabs"] [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid rgba(0,240,255,.12)!important;}
[data-testid="stTabs"] [data-baseweb="tab"]{font-family:'Orbitron',monospace!important;font-size:.72rem!important;font-weight:600!important;letter-spacing:.14em!important;color:var(--txt-lo)!important;background:transparent!important;border:none!important;padding:.85rem 1.6rem!important;text-transform:uppercase!important;transition:var(--trans)!important;}
[data-testid="stTabs"] [data-baseweb="tab"]:hover{color:var(--txt-mid)!important;background:rgba(0,240,255,.04)!important;}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--cyan)!important;text-shadow:0 0 12px rgba(0,240,255,.5)!important;background:rgba(0,240,255,.06)!important;}
[data-testid="stTabs"] [aria-selected="true"]::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--cyan),var(--purple));box-shadow:0 0 10px var(--cyan);animation:tabActiveSweep .3s ease-out forwards;}
[data-baseweb="tab-highlight"]{display:none!important;}

.nexus-progress-wrap{background:rgba(0,240,255,.08);border:1px solid rgba(0,240,255,.2);border-radius:100px;height:6px;overflow:hidden;margin:.5rem 0 .2rem;}
.nexus-progress-bar{height:100%;border-radius:100px;background:linear-gradient(90deg,var(--cyan),var(--purple),var(--magenta));background-size:200% auto;animation:shimmer 1.4s linear infinite;transition:width .4s ease;}
.nexus-progress-label{font-family:'Share Tech Mono',monospace;font-size:.65rem;letter-spacing:.15em;color:var(--txt-mid);text-transform:uppercase;margin-top:.3rem;}

[data-testid="stDownloadButton"]>button{font-family:'Share Tech Mono',monospace!important;font-size:.72rem!important;letter-spacing:.14em!important;text-transform:uppercase!important;background:rgba(0,240,255,.06)!important;color:var(--cyan-dim)!important;border:1px solid rgba(0,240,255,.25)!important;border-radius:8px!important;padding:.5rem 1.4rem!important;transition:var(--trans)!important;animation:none!important;}
[data-testid="stDownloadButton"]>button:hover{background:rgba(0,240,255,.12)!important;color:var(--cyan)!important;border-color:var(--border-bright)!important;box-shadow:0 0 14px rgba(0,240,255,.35)!important;transform:translateY(-1px)!important;}

[data-testid="stExpander"]{border:1px solid rgba(0,240,255,.12)!important;border-radius:12px!important;overflow:hidden!important;margin:.4rem 0!important;}
[data-testid="stExpander"]>div:first-child{background:rgba(0,240,255,.03)!important;}
[data-testid="stExpander"] summary{font-family:'Orbitron',monospace!important;font-size:.75rem!important;letter-spacing:.14em!important;color:var(--txt-mid)!important;text-transform:uppercase!important;}
[data-testid="stExpander"] summary:hover{color:var(--cyan)!important;}

.placeholder-card{background:var(--bg-glass);border:1px dashed rgba(0,240,255,.2);border-radius:16px;padding:3rem 2rem;text-align:center;color:var(--txt-lo);font-family:'Share Tech Mono',monospace;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;}
.placeholder-card .ph-icon{font-size:3rem;margin-bottom:1rem;opacity:.4;animation:floatBob 3.5s ease-in-out infinite;display:block;}
.placeholder-card .ph-title{color:var(--txt-mid);font-size:.85rem;margin-bottom:.4rem;}

::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-void);}
::-webkit-scrollbar-thumb{background:rgba(0,240,255,.3);border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:var(--cyan);}
[data-testid="stAlert"]{border-radius:10px!important;border-left:3px solid var(--cyan)!important;background:rgba(0,240,255,.05)!important;}
</style>
"""


def _inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════════

def _render_landing() -> None:
    """
    Full-screen cyberpunk hero — pure CSS/HTML, no Lottie dependency.
    Single centered column; button rendered as Streamlit widget below.
    """
    # All hero visuals in one markdown block so Streamlit adds no gaps
    st.markdown("""
<div class="nexus-hero">

  <!-- Conic-gradient logo ring -->
  <div style="
      position:relative;z-index:2;margin-bottom:1.4rem;
      animation:floatBob 5s ease-in-out infinite;
  ">
    <div style="
        width:96px;height:96px;margin:0 auto;border-radius:50%;
        background:conic-gradient(
            from 0deg,
            rgba(0,240,255,0.95),
            rgba(157,0,255,0.75),
            rgba(255,0,200,0.85),
            rgba(0,240,255,0.95)
        );
        display:flex;align-items:center;justify-content:center;
        box-shadow:0 0 32px rgba(0,240,255,0.55),0 0 72px rgba(0,240,255,0.2),inset 0 0 20px rgba(0,0,0,0.6);
        animation:glowPulse 2.5s ease-in-out infinite;
    ">
      <div style="
          width:78px;height:78px;border-radius:50%;
          background:var(--bg-void);
          display:flex;align-items:center;justify-content:center;
          font-family:'Orbitron',monospace;font-weight:900;
          font-size:1.15rem;letter-spacing:.12em;
          color:var(--cyan);text-shadow:0 0 16px rgba(0,240,255,0.9);
      ">NX</div>
    </div>
  </div>

  <!-- Glitch title -->
  <div class="glitch-wrapper" style="z-index:2;">
    <div class="glitch-title" data-text="NEXUS">NEXUS</div>
  </div>

  <!-- Subtitle + blinking cursor -->
  <div class="glitch-sub" style="z-index:2;">
    Mesin Benchmarking Struktur Data
    <span class="cursor"></span>
  </div>

  <!-- 3-D floating card -->
  <div class="float3d-container" style="z-index:2;">
    <div class="float3d-card">
      <div class="float3d-card-icon">🔬</div>
      <div class="float3d-card-label">Analitik Performa</div>
    </div>
  </div>

  <!-- Badge row -->
  <div class="hero-badges" style="z-index:2;">
    <span class="hero-badge cyan">Array</span>
    <span class="hero-badge magenta">Hash Table</span>
    <span class="hero-badge purple">BST</span>
    <span class="hero-badge green">AVL Tree</span>
  </div>

</div>
""", unsafe_allow_html=True)

    # Streamlit button must be outside the HTML block
    _, btn_col, _ = st.columns([1.2, 1, 1.2])
    with btn_col:
        if st.button("\U0001f680  Initialize Engine", key="init_btn", use_container_width=True):
            st.session_state["engine_initialised"] = True
            st.rerun()

    # Feature cards
    st.markdown(
        '<div class="nexus-divider" style="margin-top:1.6rem;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="text-align:center;margin:.8rem 0 1rem;">'
        '<span style="font-family:\'Share Tech Mono\',monospace;font-size:.65rem;'
        'letter-spacing:.25em;color:var(--txt-lo);text-transform:uppercase;">'
        'Kemampuan Sistem</span></div>',
        unsafe_allow_html=True,
    )
    feats = [
        ("\u26a1", "Presisi Nanodetik",  "Timing perf_counter_ns dengan warm-up dan averaging",        "cyan"),
        ("\U0001f333", "5 Implementasi", "Array \u00b7 Binary \u00b7 Hash \u00b7 BST \u00b7 AVL \u2014 semua dari nol", "purple"),
        ("\U0001f4ca", "Visualisasi Langsung", "Bar ECharts animasi, spline Plotly, dan fisika agraph",  "magenta"),
        ("\U0001f9e0", "Analisis Mendalam", "Wawasan kompleksitas O(n) dan rekomendasi otomatis","green"),
    ]
    for col, (icon, title, desc, colour) in zip(st.columns(4), feats):
        with col:
            st.markdown(
                f'<div class="nexus-panel cascade-fade-in" style="text-align:center;padding:1.2rem .8rem;">'
                f'<div style="font-size:2rem;margin-bottom:.5rem;filter:drop-shadow(0 0 12px var(--{colour}));">{icon}</div>'
                f'<div style="font-family:\'Orbitron\',monospace;font-size:.7rem;font-weight:700;'
                f'letter-spacing:.1em;color:var(--{colour});text-transform:uppercase;margin-bottom:.4rem;">{title}</div>'
                f'<div style="font-family:\'Exo 2\',sans-serif;font-size:.74rem;color:var(--txt-lo);line-height:1.5;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════════════
#  CSV EXPORT HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _build_csv(df: "pd.DataFrame") -> bytes:
    """
    Bangun CSV yang diformat dengan header metadata di atas, diikuti
    tabel data dengan nama kolom Bahasa Indonesia.

    Format:
        # NEXUS Laporan Benchmarking
        # Tanggal: ...
        # Konfigurasi: ...
        # (baris kosong)
        Struktur,Ukuran,Tipe Data,Insert (ms),Pencarian (ms),Hapus (ms)
        ...
    """
    import io as _io

    # ── Metadata header ───────────────────────────────────────────────────────
    now      = time.strftime("%Y-%m-%d %H:%M:%S")
    sizes    = ", ".join(str(s) for s in sorted(df["size"].unique()))
    dtypes   = ", ".join(df["data_type"].unique())
    structs  = ", ".join(df["structure"].unique())
    n_rep    = st.session_state.get("n_repeats", "—")

    header_lines = [
        "# NEXUS Laporan Benchmarking",
        f"# Tanggal: {now}",
        f"# Struktur Data: {structs}",
        f"# Ukuran Dataset: {sizes}",
        f"# Tipe Data: {dtypes}",
        f"# Pengulangan Averaging: {n_rep}x",
        "#",
    ]

    # ── Rename columns to Indonesian ──────────────────────────────────────────
    col_map = {
        "structure": "Struktur",
        "size":      "Ukuran",
        "data_type": "Tipe Data",
        "insert_ms": "Insert (ms)",
        "search_ms": "Pencarian (ms)",
        "delete_ms": "Hapus (ms)",
    }
    export_df = df.rename(columns=col_map)

    # ── Assemble final CSV bytes ──────────────────────────────────────────────
    buf = _io.StringIO()
    for line in header_lines:
        buf.write(line + "\n")
    buf.write("\n")
    export_df.to_csv(buf, index=False, float_format="%.5f")

    return buf.getvalue().encode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def _render_sidebar() -> None:
    """Full sidebar: branding, config controls, run button, CSV download."""
    with st.sidebar:
        # ── Pure-CSS NEXUS logo (no Lottie dependency) ────────────────────────
        st.markdown(
            '<div style="display:flex;align-items:center;gap:.9rem;margin-bottom:.3rem;">'

            # Mini ring logo
            '<div style="'
            'flex-shrink:0;width:42px;height:42px;border-radius:50%;'
            'background:conic-gradient(from 0deg,rgba(0,240,255,.95),rgba(157,0,255,.75),rgba(255,0,200,.85),rgba(0,240,255,.95));'
            'display:flex;align-items:center;justify-content:center;'
            'box-shadow:0 0 14px rgba(0,240,255,.45);'
            'animation:glowPulse 2.5s ease-in-out infinite;'
            '">'
            '<div style="'
            'width:32px;height:32px;border-radius:50%;background:#03040a;'
            'display:flex;align-items:center;justify-content:center;'
            'font-family:\'Orbitron\',monospace;font-weight:900;font-size:.55rem;'
            'letter-spacing:.08em;color:#00f0ff;text-shadow:0 0 8px rgba(0,240,255,.9);'
            '">NX</div>'
            '</div>'

            # Text block
            '<div>'
            '<div class="sidebar-title">NEXUS</div>'
            '<div class="sidebar-version">v2.0.5 · UAS BUILD</div>'
            '</div>'

            '</div>',
            unsafe_allow_html=True,
        )

        if st.session_state["benchmark_ran"]:
            st.markdown('<span class="status-badge online">Mesin Aktif</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge ready">◈ Siaga</span>', unsafe_allow_html=True)

        st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)

        # Dataset config
        st.markdown('<div class="sidebar-section-label">▸ Dataset Config</div>', unsafe_allow_html=True)

        size_labels = {100: "100 — Kecil", 1_000: "1.000 — Sedang", 10_000: "10.000 — Besar"}
        sel_sizes = st.multiselect(
            "Ukuran Dataset",
            options=[100, 1_000, 10_000],
            default=st.session_state["sel_sizes"],
            format_func=lambda x: size_labels[x],
            key="ms_sizes",
        )
        if sel_sizes:
            st.session_state["sel_sizes"] = sel_sizes

        dtype_opts = {"random": "🎲  Acak", "sorted": "📈  Terurut (Naik)", "descending": "📉  Menurun"}
        sel_dtype = st.selectbox(
            "Distribusi Data",
            options=list(dtype_opts.keys()),
            format_func=lambda x: dtype_opts[x],
            index=list(dtype_opts.keys()).index(st.session_state["sel_dtype"]),
            key="sb_dtype",
        )
        st.session_state["sel_dtype"] = sel_dtype

        # Structure selection
        st.markdown('<div class="sidebar-section-label">▸ Struktur Data</div>', unsafe_allow_html=True)
        sel_structs = st.multiselect(
            "Struktur untuk Dibenchmark",
            options=_UI_STRUCTURES,
            default=st.session_state["sel_structures"],
            key="ms_structs",
        )
        if sel_structs:
            st.session_state["sel_structures"] = sel_structs

        # Advanced
        with st.expander("⚙  Pengaturan Lanjutan"):
            n_rep = st.slider(
                "Pengulangan Averaging", 1, 10,
                value=st.session_state["n_repeats"],
                help="Lebih tinggi = lebih akurat, lebih lambat",
                key="sl_reps",
            )
            st.session_state["n_repeats"] = n_rep

        st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)

        if st.button("⚡  JALANKAN BENCHMARK", key="run_btn", use_container_width=True, type="primary"):
            st.session_state["_run_trigger"] = True

        if st.session_state.get("last_run_ts"):
            st.markdown(
                f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.6rem;'
                f'color:var(--txt-lo);text-align:center;margin-top:.5rem;">'
                f'Terakhir dijalankan: {st.session_state["last_run_ts"]}</div>',
                unsafe_allow_html=True,
            )

        if st.session_state["benchmark_ran"] and st.session_state["results_df"] is not None:
            csv_bytes = _build_csv(st.session_state["results_df"])
            st.download_button(
                label="⬇  Ekspor CSV",
                data=csv_bytes,
                file_name=f"nexus_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_csv_sidebar",
            )

        st.markdown(
            '<div style="margin-top:2rem;padding-top:1rem;border-top:1px solid rgba(0,240,255,.08);text-align:center;">'
            '<div style="font-family:\'Share Tech Mono\',monospace;font-size:.58rem;color:var(--txt-lo);letter-spacing:.12em;line-height:1.8;">'
            'UAS STRUKTUR DATA<br>'
            '<span style="color:rgba(0,240,255,.3);">──────────────────</span><br>'
            'Mesin Benchmarking<br>'
            'Python · Streamlit · OOP'
            '</div></div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  BENCHMARK RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def _run_benchmarks() -> None:
    """
    Execute the full benchmark suite with animated progress, then persist
    results and pre-built trees into session_state.
    """
    sel_sizes   = st.session_state["sel_sizes"]
    sel_dtype   = st.session_state["sel_dtype"]
    sel_structs = st.session_state["sel_structures"]
    n_rep       = st.session_state["n_repeats"]

    if not sel_sizes or not sel_structs:
        st.warning("⚠  Pilih minimal satu ukuran dan satu struktur data.")
        st.session_state["_run_trigger"] = False
        return

    # Expand "Array" → two variants
    ds_to_run: list[tuple[str, type]] = []
    for name in sel_structs:
        if name == "Array":
            ds_to_run.append(("Array (Linear)", ArrayDS))
            ds_to_run.append(("Array (Binary)", _ArrayBinaryDS))
        elif name == "Hash Table":
            ds_to_run.append(("Hash Table", HashTableDS))
        elif name == "BST":
            ds_to_run.append(("BST", BinarySearchTreeDS))
        elif name == "AVL Tree":
            ds_to_run.append(("AVL Tree", AVLTreeDS))

    total_steps  = len(ds_to_run) * len(sel_sizes)
    current_step = 0
    gen    = DatasetGenerator()
    runner = BenchmarkRunner(n_repeats=n_rep, search_sample_size=100)
    rows: list[dict] = []

    prog = st.empty()

    for ds_label, ds_class in ds_to_run:
        for size in sorted(sel_sizes):
            current_step += 1
            pct = int((current_step / total_steps) * 100)

            prog.markdown(
                f'<div style="padding:.8rem 1rem;background:rgba(0,240,255,.03);'
                f'border:1px solid rgba(0,240,255,.12);border-radius:12px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;">'
                f'<span style="font-family:\'Orbitron\',monospace;font-size:.72rem;'
                f'letter-spacing:.12em;color:var(--cyan);text-transform:uppercase;">⚡ Menjalankan Benchmark</span>'
                f'<span style="font-family:\'Share Tech Mono\',monospace;font-size:.7rem;color:var(--txt-mid);">{pct}%</span>'
                f'</div>'
                f'<div class="nexus-progress-wrap"><div class="nexus-progress-bar" style="width:{pct}%;"></div></div>'
                f'<div class="nexus-progress-label">{ds_label} &nbsp;·&nbsp; n={size:,}'
                f'<span style="color:var(--txt-lo);"> ({current_step}/{total_steps})</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            dataset = gen.generate(size, sel_dtype)

            insert_ms = runner.run_benchmark(ds_class(), dataset, "insert")
            search_ms = runner.run_benchmark(ds_class(), dataset, "search")
            delete_ms = runner.run_benchmark(ds_class(), dataset, "delete")

            rows.append({
                "structure": ds_label,
                "size":       size,
                "data_type":  sel_dtype,
                "insert_ms":  round(insert_ms, 5),
                "search_ms":  round(search_ms, 5),
                "delete_ms":  round(delete_ms, 5),
            })

    prog.empty()

    df = pd.DataFrame(rows)
    st.session_state["results_df"]    = df
    st.session_state["analysis"]      = None   # reset — computed lazily in Tab 3
    st.session_state["benchmark_ran"] = True
    st.session_state["last_run_ts"]   = time.strftime("%H:%M:%S")
    st.session_state["_run_trigger"]  = False

    # Pre-build small trees (30 elements) for Tab 2 — never crash the browser
    small_ds = gen.generate(30, sel_dtype)
    bst = BinarySearchTreeDS()
    avl = AVLTreeDS()
    for v in small_ds:
        bst.insert(v)
        avl.insert(v)
    st.session_state["tree_bst"] = bst
    st.session_state["tree_avl"] = avl
    st.session_state["tree_log"] = [f"Diisi otomatis dengan 30 nilai ({sel_dtype})"]

    n_structs = len(ds_to_run)
    n_sizes   = len(sel_sizes)
    st.success(
        f"✅  Benchmark selesai — {len(rows)} pengujian pada "
        f"{n_structs} struktur × {n_sizes} ukuran."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD HEADER
# ══════════════════════════════════════════════════════════════════════════════

def _render_header() -> None:
    st.markdown(
        '<div class="cascade-fade-in delay-1" style="display:flex;align-items:center;'
        'justify-content:space-between;padding:1rem 0 1.5rem;'
        'border-bottom:1px solid rgba(0,240,255,.1);margin-bottom:1.5rem;">'
        '<div>'
        '<div style="font-family:\'Orbitron\',monospace;font-weight:900;'
        'font-size:clamp(1.2rem,2.5vw,1.8rem);color:var(--cyan);'
        'text-shadow:0 0 20px rgba(0,240,255,.4);letter-spacing:.1em;">'
        'NEXUS'
        '<span style="color:var(--txt-lo);font-weight:400;font-size:.6em;margin-left:.5em;">BENCHMARKING ENGINE</span>'
        '</div>'
        '<div style="font-family:\'Share Tech Mono\',monospace;font-size:.65rem;'
        'color:var(--txt-lo);letter-spacing:.2em;margin-top:.2rem;">'
        '◈ SISTEM AKTIF  ·  5 IMPLEMENTASI  ·  3 OPERASI'
        '</div></div>'
        '<div style="text-align:right;">'
        '<div style="font-family:\'Share Tech Mono\',monospace;font-size:.65rem;color:var(--green);letter-spacing:.15em;">● MESIN AKTIF</div>'
        '<div style="font-family:\'Share Tech Mono\',monospace;font-size:.58rem;color:var(--txt-lo);">presisi perf_counter_ns</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _render_tab_dashboard() -> None:
    df = st.session_state.get("results_df")

    st.markdown(
        '<div class="nexus-section-header cascade-fade-in delay-1">Ringkasan Performa</div>',
        unsafe_allow_html=True,
    )

    if df is not None and not df.empty:
        render_metrics_row(df)
    else:
        m1, m2, m3, m4 = st.columns(4)
        for col, label in zip([m1, m2, m3, m4],
                               ["Insert Tercepat", "Pencarian Tercepat", "Hapus Tercepat", "Waktu Terbaik"]):
            with col:
                st.metric(label, "—", delta="jalankan benchmark")

    st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)

    if df is None or df.empty:
        st.markdown(
            '<div class="cascade-fade-in delay-2" style="text-align:center;padding:3rem;'
            'font-family:\'Share Tech Mono\',monospace;font-size:.72rem;'
            'letter-spacing:.15em;color:var(--txt-lo);text-transform:uppercase;">'
            '◈ Atur parameter di sidebar dan tekan '
            '<span style="color:var(--cyan);">⚡ JALANKAN BENCHMARK</span> untuk mengisi dashboard ini'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # Bar chart
    st.markdown(
        '<div class="nexus-section-header cascade-fade-in delay-2">Perbandingan Operasi</div>',
        unsafe_allow_html=True,
    )

    available_sizes = sorted(df["size"].unique().tolist())

    # selectbox works with 1 or more options; select_slider crashes with only 1
    if len(available_sizes) > 1:
        selected_bar_size = st.select_slider(
            "Ukuran dataset pada bar chart",
            options=available_sizes,
            value=available_sizes[-1],
            format_func=lambda x: f"n = {x:,}",
            key="sl_bar_size",
        )
    else:
        selected_bar_size = available_sizes[0]
        st.caption(f"Menampilkan hasil untuk n = {selected_bar_size:,}")

    st.markdown(
        '<div class="nexus-panel cascade-fade-in delay-3">'
        '<div class="nexus-panel-title"><span class="dot"></span> Bar Terkelompok — Insert / Pencarian / Hapus</div>',
        unsafe_allow_html=True,
    )
    create_animated_bar_chart(df, selected_size=selected_bar_size, height="400px", key="main_bar")
    st.markdown('</div>', unsafe_allow_html=True)

    # Line chart + Heatmap
    col_line, col_heat = st.columns(2, gap="medium")

    with col_line:
        st.markdown(
            '<div class="nexus-panel cascade-fade-in delay-4">'
            '<div class="nexus-panel-title"><span class="dot"></span> Penskalaan — Pertumbuhan O(·)</div>',
            unsafe_allow_html=True,
        )
        op_choice = st.radio(
            "Operasi", options=["insert", "search", "delete"],
            format_func=lambda x: {"insert":"Insert","search":"Pencarian","delete":"Hapus"}[x],
            horizontal=True, key="radio_line_op",
        )
        create_scaling_line_chart(df, operation=op_choice, height=360)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_heat:
        st.markdown(
            '<div class="nexus-panel cascade-fade-in delay-5">'
            '<div class="nexus-panel-title"><span class="dot"></span> Heatmap — Rata-rata Waktu (ms)</div>',
            unsafe_allow_html=True,
        )
        create_heatmap(df, height=380)
        st.markdown('</div>', unsafe_allow_html=True)

    # Raw data + CSV download
    st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)
    with st.expander("🗃  Data Benchmark Mentah"):
        st.dataframe(
            df.style.format({
                "insert_ms": "{:.5f}",
                "search_ms": "{:.5f}",
                "delete_ms": "{:.5f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
        dl_col, _, _ = st.columns([1, 1, 1])
        with dl_col:
            csv_bytes = _build_csv(df)
            st.download_button(
                label="⬇  Unduh CSV Lengkap",
                data=csv_bytes,
                file_name=f"nexus_benchmark_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_csv_main",
            )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — TREE VISUALIZER
# ══════════════════════════════════════════════════════════════════════════════

def _render_tab_tree() -> None:
    st.markdown(
        '<div class="nexus-section-header cascade-fade-in delay-1">Visualisasi Pohon Interaktif</div>',
        unsafe_allow_html=True,
    )

    col_ctrl, col_vis = st.columns([1, 2.6], gap="large")

    with col_ctrl:
        st.markdown(
            '<div class="nexus-panel">'
            '<div class="nexus-panel-title"><span class="dot"></span> Operasi</div>',
            unsafe_allow_html=True,
        )

        tree_op  = st.selectbox("Operasi", ["Tambah", "Cari", "Hapus"], key="sb_tree_op")
        tree_val = st.number_input(
            "Nilai", min_value=1, max_value=9999,
            value=st.session_state["tree_val"], step=1, key="ni_tree_val",
        )
        st.session_state["tree_val"] = int(tree_val)

        c_exec, c_reset = st.columns(2)
        with c_exec:
            exec_clicked  = st.button("▶  Eksekusi", key="btn_exec",  use_container_width=True)
        with c_reset:
            reset_clicked = st.button("🔄  Reset",  key="btn_reset", use_container_width=True)

        # Lazy-init trees on first visit
        if st.session_state["tree_bst"] is None:
            gen       = DatasetGenerator()
            seed_vals = gen.generate(20, st.session_state["sel_dtype"])
            bst = BinarySearchTreeDS()
            avl = AVLTreeDS()
            for v in seed_vals:
                bst.insert(v)
                avl.insert(v)
            st.session_state["tree_bst"] = bst
            st.session_state["tree_avl"] = avl
            st.session_state["tree_log"] = [f"Diisi awal dengan {len(seed_vals)} nilai"]

        if reset_clicked:
            st.session_state["tree_bst"] = BinarySearchTreeDS()
            st.session_state["tree_avl"] = AVLTreeDS()
            st.session_state["tree_log"] = ["Pohon direset ✓"]
            st.rerun()

        if exec_clicked:
            bst = st.session_state["tree_bst"]
            avl = st.session_state["tree_avl"]
            v   = st.session_state["tree_val"]
            log = st.session_state["tree_log"]

            if tree_op == "Tambah":
                bst.insert(v)
                avl.insert(v)
                log.append(f"✚  Disisipkan {v}")
            elif tree_op == "Cari":
                fb = bst.search(v)
                fa = avl.search(v)
                log.append(
                    f"🔍  Cari {v} → BST: {'✓' if fb else '✗'}  AVL: {'✓' if fa else '✗'}"
                )
            elif tree_op == "Hapus":
                ob = bst.delete(v)
                oa = avl.delete(v)
                log.append(
                    f"✖  Hapus {v} → BST: {'ok' if ob else 'tidak ada'}  "
                    f"AVL: {'ok' if oa else 'tidak ada'}"
                )

            st.session_state["tree_log"] = log[-12:]
            st.rerun()

        # Tree stats
        bst = st.session_state["tree_bst"]
        avl = st.session_state["tree_avl"]
        bn, _ = bst.get_nodes_edges()
        an, _ = avl.get_nodes_edges()
        avl_h  = avl._root.height          if avl._root else 0
        avl_bf = avl._balance_factor(avl._root) if avl._root else 0

        st.markdown(
            f'<div style="margin-top:1rem;padding:1rem;background:rgba(0,240,255,.03);'
            f'border:1px solid rgba(0,240,255,.1);border-radius:12px;">'
            f'<div style="font-family:\'Orbitron\',monospace;font-size:.65rem;font-weight:700;'
            f'letter-spacing:.14em;color:var(--cyan);text-transform:uppercase;margin-bottom:.8rem;">Statistik Pohon</div>'
            f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.68rem;color:var(--txt-mid);line-height:2.2;">'
            f'<span style="color:var(--magenta);">BST</span> simpul: <span style="color:var(--txt-hi);">{len(bn)}</span><br>'
            f'<span style="color:var(--cyan);">AVL</span> simpul: <span style="color:var(--txt-hi);">{len(an)}</span><br>'
            f'<span style="color:var(--cyan);">AVL</span> tinggi: <span style="color:var(--green);">{avl_h}</span><br>'
            f'<span style="color:var(--cyan);">AVL</span> faktor keseimbangan: <span style="color:var(--green);">{avl_bf}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Operation log
        if st.session_state["tree_log"]:
            st.markdown(
                '<div style="margin-top:1rem;">'
                '<div style="font-family:\'Share Tech Mono\',monospace;font-size:.62rem;'
                'letter-spacing:.15em;color:var(--txt-lo);text-transform:uppercase;margin-bottom:.5rem;">'
                'Log Operasi</div></div>',
                unsafe_allow_html=True,
            )
            for entry in reversed(st.session_state["tree_log"]):
                colour = "#00ff9d" if "✚" in entry else ("#ff6060" if "✖" in entry else "#7aaec8")
                st.markdown(
                    f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.65rem;'
                    f'color:{colour};padding:.2rem 0;border-bottom:1px solid rgba(0,240,255,.06);">'
                    f'{entry}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('</div>', unsafe_allow_html=True)

    with col_vis:
        bst_col, avl_col = st.columns(2, gap="medium")

        with bst_col:
            st.markdown(
                '<div style="font-family:\'Orbitron\',monospace;font-size:.72rem;font-weight:700;'
                'letter-spacing:.12em;color:#ff00c8;text-transform:uppercase;'
                'text-shadow:0 0 10px rgba(255,0,200,.4);margin-bottom:.6rem;">◈ BST</div>',
                unsafe_allow_html=True,
            )
            bn, be = st.session_state["tree_bst"].get_nodes_edges()
            render_tree_graph(bn, be, tree_name="BST", height=480)

        with avl_col:
            st.markdown(
                '<div style="font-family:\'Orbitron\',monospace;font-size:.72rem;font-weight:700;'
                'letter-spacing:.12em;color:#00f0ff;text-transform:uppercase;'
                'text-shadow:0 0 10px rgba(0,240,255,.4);margin-bottom:.6rem;">◈ Pohon AVL</div>',
                unsafe_allow_html=True,
            )
            an, ae = st.session_state["tree_avl"].get_nodes_edges()
            render_tree_graph(an, ae, tree_name="AVL", height=480)

        # Array strip
        st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)
        gen       = DatasetGenerator()
        arr_data  = gen.generate(24, st.session_state["sel_dtype"])
        highlight = arr_data[len(arr_data) // 2]
        render_array_visualization(
            arr_data, highlight_value=highlight,
            title="Contoh Array  (disorot = target pencarian)",
        )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — DEEP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def _render_tab_analysis() -> None:
    st.markdown(
        '<div class="nexus-section-header cascade-fade-in delay-1">Mesin Analisis Mendalam</div>',
        unsafe_allow_html=True,
    )

    df = st.session_state.get("results_df")

    if df is None or df.empty:
        st.markdown(
            '<div class="placeholder-card cascade-fade-in delay-2">'
            '<span class="ph-icon">🧠</span>'
            '<div class="ph-title">Mesin Analisis Siaga</div>'
            'Jalankan benchmark terlebih dahulu — mesin akan otomatis menghasilkan '
            'wawasan kompleksitas, peringkat pemenang, observasi penskalaan, '
            'dan laporan sensitivitas distribusi data.'
            '</div>',
            unsafe_allow_html=True,
        )
        _render_complexity_reference()
        return

    # Lazy compute
    if st.session_state.get("analysis") is None:
        with st.spinner("🧠  Menghitung analisis mendalam…"):
            st.session_state["analysis"] = AnalysisGenerator().generate_analysis(df)

    analysis = st.session_state["analysis"]
    if not analysis or "error" in analysis:
        st.error(analysis.get("error", "Analisis gagal."))
        return

    # ── 1. Winners ────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-family:\'Orbitron\',monospace;font-weight:700;font-size:.85rem;'
        'letter-spacing:.18em;color:var(--cyan);text-transform:uppercase;'
        'margin-bottom:1rem;padding-bottom:.5rem;border-bottom:1px solid rgba(0,240,255,.12);">'
        '◈ Pemenang Keseluruhan</div>',
        unsafe_allow_html=True,
    )

    wc1, wc2, wc3 = st.columns(3)
    for col, (emoji, key_name, colour) in zip(
        [wc1, wc2, wc3],
        [("⚡", "overall_winner_insert", "#00f0ff"),
         ("🔍", "overall_winner_search", "#ff00c8"),
         ("🗑", "overall_winner_delete", "#ffc800")],
    ):
        val         = analysis[key_name]
        struct_name = val.split("(")[0].strip()
        time_part   = "(" + val.split("(")[1] if "(" in val else ""
        op_label    = key_name.split("_")[-1].capitalize()
        with col:
            st.markdown(
                f'<div style="background:rgba(0,0,0,.2);border:1px solid {colour}22;'
                f'border-top:2px solid {colour};border-radius:0 0 14px 14px;'
                f'padding:1.2rem 1rem;text-align:center;margin-bottom:.8rem;">'
                f'<div style="font-size:1.8rem;margin-bottom:.4rem;filter:drop-shadow(0 0 10px {colour});">{emoji}</div>'
                f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.62rem;'
                f'letter-spacing:.18em;color:rgba(255,255,255,.3);text-transform:uppercase;margin-bottom:.4rem;">'
                f'{op_label} Tercepat</div>'
                f'<div style="font-family:\'Orbitron\',monospace;font-weight:700;font-size:.9rem;'
                f'color:{colour};text-shadow:0 0 12px {colour}88;animation:winnerGlow 2.5s ease-in-out infinite;">'
                f'{struct_name}</div>'
                f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.65rem;'
                f'color:rgba(255,255,255,.3);margin-top:.3rem;">{time_part}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── 2. Podium ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-family:\'Orbitron\',monospace;font-weight:700;font-size:.85rem;'
        'letter-spacing:.18em;color:var(--cyan);text-transform:uppercase;'
        'margin:1.5rem 0 1rem;padding-bottom:.5rem;border-bottom:1px solid rgba(0,240,255,.12);">'
        '◈ Papan Peringkat</div>',
        unsafe_allow_html=True,
    )
    render_podium(analysis.get("podium", {}))

    # ── 3. Summary table ──────────────────────────────────────────────────────
    summary_df = analysis.get("summary_table")
    if summary_df is not None and not summary_df.empty:
        st.markdown(
            '<div style="font-family:\'Orbitron\',monospace;font-weight:700;font-size:.85rem;'
            'letter-spacing:.18em;color:var(--gold);text-transform:uppercase;'
            'margin:1.5rem 0 1rem;padding-bottom:.5rem;border-bottom:1px solid rgba(255,200,0,.12);">'
            '◈ Ringkasan Rata-rata Waktu</div>',
            unsafe_allow_html=True,
        )
        display_df = summary_df.rename(columns={
            "structure": "Struktur",
            "insert_ms": "Insert (ms)",
            "search_ms": "Pencarian (ms)",
            "delete_ms": "Hapus (ms)",
        })
        st.dataframe(
            display_df.style
            .format({"Insert (ms)": "{:.5f}", "Pencarian (ms)": "{:.5f}", "Hapus (ms)": "{:.5f}"})
            .highlight_min(
                subset=["Insert (ms)", "Pencarian (ms)", "Hapus (ms)"],
                color="rgba(0,255,157,0.18)",
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)

    # ── 4. Scaling insights ───────────────────────────────────────────────────
    scaling = analysis.get("scaling_insights", [])
    with st.expander(f"📈  Wawasan Penskalaan  ({len(scaling)} observasi)", expanded=True):
        if scaling:
            for note in scaling:
                parts       = note.split("–", 1)
                struct_part = parts[0].strip()
                rest_part   = parts[1].strip() if len(parts) > 1 else note
                st.markdown(
                    f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.72rem;'
                    f'color:#7aaec8;padding:.5rem .8rem;margin:.2rem 0;'
                    f'border-left:2px solid rgba(255,200,0,.4);'
                    f'background:rgba(255,200,0,.03);border-radius:0 6px 6px 0;line-height:1.6;">'
                    f'<span style="color:#ffc800;font-weight:700;">{struct_part}</span>'
                    f' – {rest_part}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Jalankan dengan beberapa ukuran dataset untuk melihat observasi penskalaan.")

    # ── 5. Data-type insights ─────────────────────────────────────────────────
    dtype_ins = analysis.get("data_type_insights", [])
    with st.expander(f"🎲  Sensitivitas Distribusi Data  ({len(dtype_ins)} observasi)"):
        for note in dtype_ins:
            st.markdown(
                f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.72rem;'
                f'color:#7aaec8;padding:.5rem .8rem;margin:.2rem 0;'
                f'border-left:2px solid rgba(255,0,200,.4);'
                f'background:rgba(255,0,200,.03);border-radius:0 6px 6px 0;line-height:1.6;">'
                f'{note}</div>',
                unsafe_allow_html=True,
            )

    # ── 6. Theory vs practice ─────────────────────────────────────────────────
    complexity = analysis.get("complexity_comparison", {})
    with st.expander("📚  Teori vs Praktik  (Kompleksitas Big-O)"):
        for struct, detail in complexity.items():
            st.markdown(
                f'<div style="margin:.4rem 0;padding:.7rem 1rem;'
                f'background:rgba(0,240,255,.03);border:1px solid rgba(0,240,255,.1);border-radius:8px;">'
                f'<span style="font-family:\'Orbitron\',monospace;font-size:.72rem;'
                f'font-weight:700;color:var(--cyan);letter-spacing:.1em;">{struct}</span><br>'
                f'<span style="font-family:\'Share Tech Mono\',monospace;font-size:.65rem;'
                f'color:var(--txt-mid);">{detail}</span></div>',
                unsafe_allow_html=True,
            )

    # ── 7. Recommendation ─────────────────────────────────────────────────────
    rec = analysis.get("recommendation", "")
    if rec:
        st.markdown(
            '<div style="font-family:\'Orbitron\',monospace;font-weight:700;font-size:.85rem;'
            'letter-spacing:.18em;color:var(--green);text-transform:uppercase;'
            'margin:1.5rem 0 1rem;padding-bottom:.5rem;border-bottom:1px solid rgba(0,255,157,.15);">'
            '◈ Rekomendasi</div>',
            unsafe_allow_html=True,
        )
        highlighted = re.sub(
            r"\*\*(.+?)\*\*",
            r'<span style="color:#00ff9d;font-weight:700;">\1</span>',
            rec,
        )
        st.markdown(
            f'<div style="font-family:\'Exo 2\',sans-serif;font-size:.85rem;color:#7aaec8;'
            f'line-height:1.9;padding:1.3rem 1.5rem;'
            f'background:rgba(0,255,157,.03);border:1px solid rgba(0,255,157,.12);'
            f'border-radius:12px;">{highlighted}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="nexus-divider"></div>', unsafe_allow_html=True)
    _render_complexity_reference()


# ── Complexity reference (always visible in Tab 3) ────────────────────────────

def _render_complexity_reference() -> None:
    st.markdown(
        '<div style="font-family:\'Orbitron\',monospace;font-weight:600;font-size:.72rem;'
        'letter-spacing:.2em;color:var(--txt-lo);text-transform:uppercase;margin:1.5rem 0 1rem;">'
        'Referensi Kompleksitas Teoritis</div>',
        unsafe_allow_html=True,
    )

    comp_data = [
        ("Array (Linear)",  "#7a98b8", "O(1)",      "O(n)",       "O(n)",      "Sederhana, ramah cache"),
        ("Array (Binary)",  "#00b4c4", "O(1)",      "O(log n)*",  "O(n)",      "*Butuh input terurut"),
        ("Hash Table",      "#00f0ff", "O(1) avg",  "O(1) avg",   "O(1) avg",  "O(n) kasus terburuk"),
        ("BST",             "#ff00c8", "O(h)",      "O(h)",       "O(h)",      "h=n jika input terurut"),
        ("AVL Tree",        "#ffc800", "O(log n)",  "O(log n)",   "O(log n)",  "Dijamin seimbang"),
    ]
    cols = st.columns(len(comp_data))
    for col, (name, colour, ins, srch, dlt, note) in zip(cols, comp_data):
        with col:
            st.markdown(
                f'<div style="background:rgba(0,0,0,.25);border:1px solid {colour}22;'
                f'border-top:2px solid {colour};border-radius:0 0 12px 12px;'
                f'padding:1rem .8rem;text-align:center;">'
                f'<div style="font-family:\'Orbitron\',monospace;font-size:.68rem;font-weight:700;'
                f'color:{colour};text-shadow:0 0 10px {colour};letter-spacing:.1em;margin-bottom:.8rem;">{name}</div>'
                f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:.65rem;'
                f'color:var(--txt-mid);line-height:2.2;">'
                f'Insert: <span style="color:{colour};">{ins}</span><br>'
                f'Search: <span style="color:{colour};">{srch}</span><br>'
                f'Delete: <span style="color:{colour};">{dlt}</span></div>'
                f'<div style="margin-top:.7rem;font-family:\'Share Tech Mono\',monospace;'
                f'font-size:.58rem;color:var(--txt-lo);border-top:1px solid rgba(255,255,255,.05);'
                f'padding-top:.5rem;">{note}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Application entry point — routes between landing page and dashboard."""
    _init_state()
    _inject_css()

    if not st.session_state["engine_initialised"]:
        _render_landing()
        return

    _render_sidebar()

    # Handle benchmark trigger in the main body so st.empty progress bar renders
    if st.session_state.get("_run_trigger"):
        _run_benchmarks()
        st.rerun()

    _render_header()

    tab1, tab2, tab3 = st.tabs([
        "📊  Dasbor",
        "🌳  Visualisasi Pohon",
        "🧠  Analisis Mendalam",
    ])

    with tab1:
        _render_tab_dashboard()

    with tab2:
        _render_tab_tree()

    with tab3:
        _render_tab_analysis()


if __name__ == "__main__":
    main()
