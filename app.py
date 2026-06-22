import streamlit as st
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# ============================================================
# PALETA DE COLORES
# ============================================================
COLOR_PRIMARY   = "#0B6E99"   # Azul médico-teal
COLOR_SECONDARY = "#065A80"   # Navy médico
COLOR_ACCENT    = "#22C4D0"   # Teal clínico
COLOR_GES       = "#0891B2"   # Cian GES
COLOR_NO_GES    = "#DC2626"   # Rojo alerta médica
COLOR_SUCCESS   = "#16A34A"   # Verde clínico
COLOR_BG        = "#EBF5FB"   # Fondo clínico suave
COLOR_CARD      = "#FFFFFF"
COLOR_TEXT      = "#0F2D40"   # Azul-navy texto

PLOTLY_COLORS = [COLOR_GES, COLOR_NO_GES, "#AB47BC", "#26A69A", "#FFA726", "#EC407A"]
PLOTLY_TEMPLATE = "plotly_white"

# Layout base compartido por todos los gráficos
_GRID  = "rgba(11,110,153,0.07)"
_TICK  = dict(size=11, color="#6B94A8", family="Inter")
_AXIS  = dict(showgrid=True, gridcolor=_GRID, gridwidth=1,
              zeroline=False, showline=False, tickfont=_TICK)
_HOVER = dict(bgcolor="#0F2D40", font_color="#ffffff",
              font_size=12, font_family="Inter",
              bordercolor="rgba(0,0,0,0)", namelength=-1)
_LEGEND = dict(
    font=dict(size=12, family="Inter", color=COLOR_TEXT),
    bgcolor="rgba(255,255,255,0.7)",
    bordercolor="rgba(11,110,153,0.10)",
    borderwidth=1,
    orientation="h",
)
_MARGIN = dict(t=44, b=30, l=8, r=8)
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="Inter",
    font_color=COLOR_TEXT,
    hoverlabel=_HOVER,
)

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="GESAssist · Análisis GES",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS GLOBAL
# ============================================================
st.markdown(f"""
<style>
  /*
    DIRECCIÓN VISUAL — GESAssist v3.0
    Medical dashboard elevado a nivel editorial-tech.
    Tipografía: Syne (headers de impacto) + Inter (body preciso).
    Paleta: azul profundo médico + teal clínico + blanco glacial.
    Animación: hero con blob SVG morfante + entrada escalonada de métricas.
    Formas: hero con corte diagonal inferior + blob orgánico + dot-grid de fondo.
    Nivel 3: partículas flotantes, spring cubic-bezier, counter glow, shimmer on hover.
  */

  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@300;400;500;600;700&display=swap');

  /* ── Variables ── */
  :root {{
    --bg:        #EDF4F8;
    --bg-alt:    #E1EDF5;
    --card:      #ffffff;
    --glass:     rgba(255,255,255,0.72);
    --text:      {COLOR_TEXT};
    --muted:     #4A7B94;
    --subtle:    #7A9AAD;
    --border:    rgba(11,110,153,0.10);
    --border-s:  rgba(11,110,153,0.18);
    --sh-sm:     0 2px 12px rgba(11,110,153,0.06), 0 1px 3px rgba(11,110,153,0.04);
    --sh-md:     0 8px 32px rgba(11,110,153,0.11), 0 2px 8px rgba(11,110,153,0.06);
    --sh-lg:     0 20px 56px rgba(11,110,153,0.16), 0 6px 16px rgba(11,110,153,0.08);
    --sh-glow:   0 0 0 3px rgba(34,196,208,0.22), 0 8px 32px rgba(11,110,153,0.18);
    --spring:    cubic-bezier(0.34, 1.56, 0.64, 1);
    --ease-out:  cubic-bezier(0.16, 1, 0.3, 1);
    --r-sm:      14px;
    --r-md:      22px;
    --r-lg:      32px;
  }}

  /* ── Respeta prefers-reduced-motion ── */
  @media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }}
  }}

  /* ── Base ── */
  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
  }}
  .stApp {{
    background: var(--bg);
    /* Dot-grid de profundidad */
    background-image: radial-gradient(circle, rgba(11,110,153,0.08) 1px, transparent 1px);
    background-size: 28px 28px;
  }}
  .stApp > header {{ background: transparent !important; }}

  /* ── Keyframes ── */
  @keyframes hpulse {{
    0%,100% {{ background-position: 0% 50%; }}
    50%      {{ background-position: 100% 50%; }}
  }}
  @keyframes slideUp {{
    from {{ opacity: 0; transform: translateY(22px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  @keyframes fadeIn {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
  }}
  @keyframes floatA {{
    0%,100% {{ transform: translate(0, 0) scale(1); }}
    33%      {{ transform: translate(12px, -18px) scale(1.04); }}
    66%      {{ transform: translate(-8px, 10px) scale(0.97); }}
  }}
  @keyframes floatB {{
    0%,100% {{ transform: translate(0, 0) scale(1); }}
    50%      {{ transform: translate(-16px, 20px) scale(1.06); }}
  }}
  @keyframes blobMorph {{
    0%,100% {{ border-radius: 60% 40% 55% 45% / 50% 60% 40% 50%; }}
    25%      {{ border-radius: 40% 60% 45% 55% / 60% 40% 60% 40%; }}
    50%      {{ border-radius: 55% 45% 60% 40% / 40% 55% 45% 60%; }}
    75%      {{ border-radius: 45% 55% 40% 60% / 55% 45% 55% 45%; }}
  }}
  @keyframes shimmerSlide {{
    from {{ background-position: -200% 0; }}
    to   {{ background-position:  200% 0; }}
  }}
  @keyframes ringPulse {{
    0%,100% {{ box-shadow: 0 0 0 0 rgba(34,196,208,0); }}
    50%      {{ box-shadow: 0 0 0 8px rgba(34,196,208,0.14); }}
  }}
  @keyframes countUp {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  /* ═══════════════════════════════
     SIDEBAR — rediseño completo
     ═══════════════════════════════ */

  /* Contenedor principal */
  [data-testid="stSidebar"] {{
    background: linear-gradient(175deg, #03161F 0%, #042030 45%, #053040 100%) !important;
    border-right: none !important;
    border-radius: 0 24px 24px 0;
    box-shadow: 4px 0 32px rgba(3,22,31,0.55), 1px 0 0 rgba(34,196,208,0.12);
  }}

  /* Scroll interno sin scrollbar visible */
  [data-testid="stSidebar"] > div {{
    scrollbar-width: thin;
    scrollbar-color: rgba(34,196,208,0.18) transparent;
  }}
  [data-testid="stSidebar"] > div::-webkit-scrollbar {{
    width: 3px;
  }}
  [data-testid="stSidebar"] > div::-webkit-scrollbar-thumb {{
    background: rgba(34,196,208,0.22);
    border-radius: 3px;
  }}

  /* Padding interno */
  [data-testid="stSidebar"] section[data-testid="stSidebarContent"] {{
    padding: 0 20px 24px !important;
  }}

  /* Texto p y small */
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] small {{
    color: rgba(180,220,240,0.65) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    line-height: 1.55 !important;
  }}

  /* Labels de controles */
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stSlider label,
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stTextInput label {{
    color: rgba(100,180,220,0.70) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.10em !important;
    margin-bottom: 6px !important;
    display: block !important;
  }}

  /* h2 de sección */
  [data-testid="stSidebar"] h2 {{
    color: #fff !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.02em !important;
  }}

  /* ── Slider ── */
  [data-testid="stSidebar"] .stSlider {{
    padding: 4px 0 8px !important;
  }}
  /* Track */
  [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [data-testid="stSliderTrack"] {{
    background: rgba(255,255,255,0.08) !important;
    height: 4px !important;
    border-radius: 4px !important;
  }}
  /* Fill del track */
  [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [data-testid="stSliderTrack"] > div:nth-child(2) {{
    background: linear-gradient(90deg, {COLOR_PRIMARY}, {COLOR_ACCENT}) !important;
    border-radius: 4px !important;
  }}
  /* Thumb */
  [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"] {{
    background: {COLOR_ACCENT} !important;
    border: 3px solid #fff !important;
    box-shadow: 0 0 0 3px rgba(34,196,208,0.30), 0 2px 8px rgba(0,0,0,0.40) !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    transition: box-shadow 0.2s ease !important;
  }}
  [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"]:hover {{
    box-shadow: 0 0 0 6px rgba(34,196,208,0.22), 0 2px 12px rgba(0,0,0,0.50) !important;
  }}
  /* Valor min/max del slider */
  [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
  [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"] {{
    color: rgba(100,180,220,0.50) !important;
    font-size: 0.65rem !important;
    font-family: 'Inter', sans-serif !important;
  }}

  /* ── Selectbox ── */
  /* Estilo sobre [data-baseweb="select"] que envuelve todo el control */
  [data-testid="stSidebar"] [data-baseweb="select"] {{
    border-radius: 12px !important;
  }}
  /* El div hijo directo es el contenedor visual con borde */
  [data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    transition: border-color 0.2s, background 0.2s !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="select"] > div:hover {{
    background: rgba(34,196,208,0.07) !important;
    border-color: rgba(34,196,208,0.38) !important;
  }}
  /* Valor seleccionado */
  [data-testid="stSidebar"] [data-baseweb="select"] [value] {{
    color: #dff0fb !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.84rem !important;
  }}
  /* Flecha */
  [data-testid="stSidebar"] [data-baseweb="select"] svg {{
    fill: rgba(34,196,208,0.65) !important;
  }}

  /* ── Reset: el <input> oculto dentro del selectbox NO debe tener estilos de text-input ── */
  [data-testid="stSidebar"] [data-baseweb="select"] input {{
    background: transparent !important;
    background-color: transparent !important;
    -webkit-box-shadow: none !important;
    box-shadow: none !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    height: auto !important;
    color: #e8f4fb !important;
    -webkit-text-fill-color: #e8f4fb !important;
  }}

  /* ── Text input (solo .stTextInput) ── */
  [data-testid="stSidebar"] .stTextInput > div > div {{
    border-radius: 12px !important;
  }}
  [data-testid="stSidebar"] .stTextInput input {{
    background: transparent !important;
    background-color: transparent !important;
    -webkit-box-shadow: 0 0 0 1000px #031e2d inset !important;
    box-shadow: 0 0 0 1000px #031e2d inset !important;
    color: #e8f4fb !important;
    -webkit-text-fill-color: #e8f4fb !important;
    caret-color: {COLOR_ACCENT} !important;
    border: 1px solid rgba(255,255,255,0.13) !important;
    border-radius: 12px !important;
    padding: 9px 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    height: 40px !important;
  }}
  [data-testid="stSidebar"] .stTextInput input:focus {{
    border-color: {COLOR_ACCENT} !important;
    outline: none !important;
    -webkit-box-shadow: 0 0 0 1000px #031e2d inset, 0 0 0 3px rgba(34,196,208,0.20) !important;
    box-shadow: 0 0 0 1000px #031e2d inset, 0 0 0 3px rgba(34,196,208,0.20) !important;
  }}
  [data-testid="stSidebar"] .stTextInput input::placeholder {{
    color: rgba(255,255,255,0.25) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.25) !important;
  }}
  [data-testid="stSidebar"] .stTextInput input:-webkit-autofill,
  [data-testid="stSidebar"] .stTextInput input:-webkit-autofill:hover,
  [data-testid="stSidebar"] .stTextInput input:-webkit-autofill:focus {{
    -webkit-box-shadow: 0 0 0 1000px #031e2d inset !important;
    -webkit-text-fill-color: #e8f4fb !important;
  }}

  /* ── HR en sidebar ── */
  [data-testid="stSidebar"] hr {{
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.06) !important;
    margin: 20px 0 !important;
  }}

  /* ── Clases custom del sidebar ── */
  .sb-brand {{
    padding: 22px 0 16px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 22px;
  }}
  .sb-brand-logo {{
    width: 36px; height: 36px;
    background: linear-gradient(135deg, {COLOR_PRIMARY}, {COLOR_ACCENT});
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    box-shadow: 0 4px 14px rgba(34,196,208,0.30), 0 0 0 1px rgba(34,196,208,0.20);
    flex-shrink: 0;
  }}
  .sb-brand-name {{
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 800;
    color: #fff;
    line-height: 1.1;
    letter-spacing: -0.2px;
  }}
  .sb-brand-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 0.58rem;
    font-weight: 700;
    color: {COLOR_ACCENT};
    text-transform: uppercase;
    letter-spacing: 0.12em;
    opacity: 0.85;
  }}

  .sb-section-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.60rem; font-weight: 700;
    color: rgba(34,196,208,0.65);
    text-transform: uppercase; letter-spacing: 0.13em;
    margin: 22px 0 12px;
    display: flex; align-items: center; gap: 8px;
  }}
  .sb-section-label::before {{
    content: '';
    display: block;
    width: 16px; height: 2px;
    background: linear-gradient(90deg, {COLOR_ACCENT}, transparent);
    border-radius: 2px;
    flex-shrink: 0;
  }}

  .sb-filter-block {{
    margin-bottom: 16px;
  }}

  .sb-footer {{
    margin-top: 28px;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .sb-footer-text {{
    font-family: 'Inter', sans-serif;
    font-size: 0.60rem;
    color: rgba(255,255,255,0.28);
    line-height: 1.5;
  }}
  .sb-version {{
    background: rgba(34,196,208,0.10);
    border: 1px solid rgba(34,196,208,0.22);
    border-radius: 100px;
    padding: 3px 10px;
    font-family: 'Inter', sans-serif;
    font-size: 0.58rem;
    font-weight: 700;
    color: rgba(34,196,208,0.80);
    letter-spacing: 0.06em;
    white-space: nowrap;
  }}

  /* ── Botón colapsador ── */
  /* El wrapper div es transparente; el <button> dentro es lo visible */
  [data-testid="stSidebarCollapseButton"] {{
    background: transparent !important;
    box-shadow: none !important;
  }}
  [data-testid="stSidebarCollapseButton"] button {{
    background: {COLOR_PRIMARY} !important;
    border-radius: 0 8px 8px 0 !important;
    border: none !important;
    box-shadow: 2px 0 12px rgba(11,110,153,0.40) !important;
    transition: background 0.2s ease, box-shadow 0.2s ease !important;
  }}
  [data-testid="stSidebarCollapseButton"] button:hover {{
    background: {COLOR_ACCENT} !important;
    box-shadow: 2px 0 18px rgba(34,196,208,0.55) !important;
  }}
  /* El <span> tiene color inline que Streamlit inyecta — lo sobreescribimos */
  [data-testid="stSidebarCollapseButton"] span[color] {{
    color: #ffffff !important;
  }}
  [data-testid="stSidebarCollapseButton"] svg,
  [data-testid="stSidebarCollapseButton"] svg path {{
    fill: #ffffff !important;
    color: #ffffff !important;
  }}
  /* Estado colapsado — mismo tratamiento */
  [data-testid="stSidebarCollapsedControl"] {{
    background: transparent !important;
    box-shadow: none !important;
  }}
  [data-testid="stSidebarCollapsedControl"] button {{
    background: {COLOR_PRIMARY} !important;
    border-radius: 0 8px 8px 0 !important;
    border: none !important;
    box-shadow: 2px 0 12px rgba(11,110,153,0.40) !important;
    transition: background 0.2s ease !important;
  }}
  [data-testid="stSidebarCollapsedControl"] button:hover {{
    background: {COLOR_ACCENT} !important;
  }}
  [data-testid="stSidebarCollapsedControl"] svg,
  [data-testid="stSidebarCollapsedControl"] svg path {{
    fill: #ffffff !important;
  }}

  /* ── Hero ── */
  .hero {{
    background: linear-gradient(128deg, #031E2E 0%, #042E45 22%, {COLOR_SECONDARY} 50%, {COLOR_PRIMARY} 78%, {COLOR_ACCENT} 100%);
    background-size: 300% 300%;
    animation: hpulse 12s ease infinite;
    border-radius: var(--r-lg);
    padding: 44px 56px 52px;
    margin-bottom: 28px;
    box-shadow: 0 16px 56px rgba(4,46,69,0.35), 0 4px 16px rgba(11,110,153,0.20);
    position: relative;
    overflow: hidden;
    clip-path: polygon(0 0, 100% 0, 100% 88%, 94% 100%, 0 100%);
  }}
  /* Blob orgánico animado — fondo */
  .hero-blob-a {{
    position: absolute;
    top: -80px; right: -60px;
    width: 320px; height: 320px;
    background: rgba(34,196,208,0.12);
    border-radius: 60% 40% 55% 45% / 50% 60% 40% 50%;
    animation: blobMorph 9s ease-in-out infinite, floatA 14s ease-in-out infinite;
    pointer-events: none;
    filter: blur(1px);
  }}
  .hero-blob-b {{
    position: absolute;
    bottom: -100px; left: 30%;
    width: 260px; height: 260px;
    background: rgba(255,255,255,0.055);
    border-radius: 45% 55% 40% 60% / 60% 40% 60% 40%;
    animation: blobMorph 11s ease-in-out infinite reverse, floatB 18s ease-in-out infinite;
    pointer-events: none;
  }}
  /* Partículas decorativas */
  .hero-dot {{
    position: absolute;
    border-radius: 50%;
    background: rgba(255,255,255,0.25);
    pointer-events: none;
  }}
  .hero-dot-1 {{ width:6px; height:6px; top:20%; left:72%; animation: floatA 7s ease-in-out infinite; }}
  .hero-dot-2 {{ width:4px; height:4px; top:60%; left:82%; animation: floatB 9s ease-in-out infinite; }}
  .hero-dot-3 {{ width:8px; height:8px; top:35%; left:88%; animation: floatA 11s ease-in-out infinite 2s; }}
  /* Línea decorativa */
  .hero::before {{
    content: '';
    position: absolute;
    top: 0; left: 56px; right: 56px; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.20), transparent);
    pointer-events: none;
  }}
  .hero-inner {{
    position: relative; z-index: 2;
    animation: slideUp 0.7s var(--ease-out) both;
  }}
  .hero-badge {{
    display: inline-flex; align-items: center; gap: 7px;
    background: rgba(255,255,255,0.11);
    color: rgba(255,255,255,0.92);
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem; font-weight: 700;
    padding: 5px 16px;
    border-radius: 100px;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.22);
    backdrop-filter: blur(8px);
    transition: background 0.22s, transform 0.22s var(--spring);
    cursor: default;
  }}
  .hero-badge:hover {{
    background: rgba(255,255,255,0.20);
    transform: scale(1.05);
  }}
  .hero h1 {{
    color: #fff !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 2.15rem !important;
    font-weight: 800 !important;
    margin: 0 0 10px;
    letter-spacing: -0.5px;
    line-height: 1.18;
    text-shadow: 0 2px 20px rgba(0,0,0,0.18);
  }}
  .hero p {{
    color: rgba(255,255,255,0.78) !important;
    font-size: 0.95rem !important;
    margin: 0; line-height: 1.68;
    max-width: 620px;
  }}
  /* Accent strip en el borde izquierdo */
  .hero-accent-line {{
    position: absolute;
    left: 0; top: 20%; bottom: 20%;
    width: 4px;
    background: linear-gradient(180deg, transparent, {COLOR_ACCENT}, transparent);
    border-radius: 0 4px 4px 0;
    opacity: 0.7;
  }}

  /* ── Métricas — glassmorphism + entrada escalonada ── */
  [data-testid="metric-container"] {{
    background: var(--glass) !important;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid var(--border-s) !important;
    border-top: 3px solid {COLOR_GES} !important;
    border-radius: var(--r-md) !important;
    padding: 22px 24px 20px !important;
    box-shadow: var(--sh-sm) !important;
    transition: transform 0.28s var(--spring), box-shadow 0.28s ease;
    animation: slideUp 0.6s var(--ease-out) both;
    position: relative;
    overflow: hidden;
  }}
  /* Shimmer al hover */
  [data-testid="metric-container"]::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.22) 50%, transparent 100%);
    background-size: 200% 100%;
    opacity: 0;
    transition: opacity 0.3s;
    pointer-events: none;
  }}
  [data-testid="metric-container"]:hover::after {{
    opacity: 1;
    animation: shimmerSlide 0.9s ease forwards;
  }}
  [data-testid="metric-container"]:hover {{
    transform: translateY(-5px) scale(1.01);
    box-shadow: var(--sh-glow) !important;
  }}
  /* Stagger de entrada para cada métrica */
  [data-testid="column"]:nth-child(1) [data-testid="metric-container"] {{ animation-delay: 0.05s; }}
  [data-testid="column"]:nth-child(2) [data-testid="metric-container"] {{ animation-delay: 0.12s; }}
  [data-testid="column"]:nth-child(3) [data-testid="metric-container"] {{ animation-delay: 0.19s; }}
  [data-testid="column"]:nth-child(4) [data-testid="metric-container"] {{ animation-delay: 0.26s; }}
  [data-testid="stMetricValue"] {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_ACCENT} 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    line-height: 1.1;
    animation: countUp 0.5s var(--ease-out) both 0.3s;
  }}
  [data-testid="stMetricLabel"] {{
    color: var(--muted) !important;
    font-size: 0.70rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}
  [data-testid="stMetricDelta"] {{
    font-size: 0.76rem !important;
    font-weight: 600 !important;
  }}

  /* ── Section headers — estilo editorial ── */
  .section-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 32px 0 18px;
    animation: fadeIn 0.5s var(--ease-out) both;
    transition: transform 0.2s ease;
    cursor: default;
  }}
  .section-header:hover {{ transform: translateX(3px); }}
  .section-header .sh-line {{
    flex-shrink: 0;
    width: 4px; height: 36px;
    background: linear-gradient(180deg, {COLOR_PRIMARY}, {COLOR_ACCENT});
    border-radius: 2px;
    box-shadow: 0 0 10px rgba(34,196,208,0.30);
  }}
  .section-header .sh-content {{
    display: flex; flex-direction: column; gap: 2px;
  }}
  .section-header .sh-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.62rem; font-weight: 700;
    color: {COLOR_ACCENT};
    text-transform: uppercase; letter-spacing: 0.12em;
    line-height: 1;
  }}
  .section-header h3 {{
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
    margin: 0 !important;
    line-height: 1.2;
    letter-spacing: -0.2px;
  }}
  /* Línea separadora decorativa después del header */
  .section-header::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border-s), transparent);
    margin-left: 8px;
  }}

  /* ── Chart cards — contenedor de gráficos ── */
  .chart-card {{
    background: var(--card);
    border-radius: var(--r-md);
    padding: 4px;
    border: 1px solid var(--border);
    box-shadow: var(--sh-sm);
    margin-bottom: 6px;
    transition: transform 0.28s var(--spring), box-shadow 0.28s ease;
  }}
  .chart-card:hover {{
    transform: translateY(-4px);
    box-shadow: var(--sh-md);
  }}

  /* ── Tabs — pills premium ── */
  .stTabs [data-baseweb="tab-list"] {{
    background: var(--card);
    border-radius: 100px;
    padding: 5px;
    box-shadow: var(--sh-sm);
    gap: 4px;
    border: 1px solid var(--border-s) !important;
  }}
  .stTabs [data-baseweb="tab"] {{
    border-radius: 100px;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700;
    font-size: 0.88rem;
    color: var(--muted) !important;
    padding: 9px 26px;
    border: none !important;
    transition: background 0.22s ease, color 0.22s ease, box-shadow 0.22s ease;
    letter-spacing: 0.01em;
  }}
  .stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover {{
    background: rgba(11,110,153,0.09) !important;
    color: {COLOR_PRIMARY} !important;
  }}
  .stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_GES} 100%) !important;
    color: #fff !important;
    box-shadow: 0 4px 16px rgba(11,110,153,0.30);
    animation: ringPulse 2.5s ease infinite;
  }}
  .stTabs [data-baseweb="tab-panel"] {{ padding-top: 22px; }}

  /* ── Cards genéricas ── */
  .card {{
    background: var(--card);
    border-radius: var(--r-md);
    padding: 26px;
    border: 1px solid var(--border);
    box-shadow: var(--sh-sm);
    margin-bottom: 16px;
    color: var(--text);
    transition: transform 0.28s var(--spring), box-shadow 0.28s ease;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: var(--sh-md);
  }}


  /* ── Botones — pill premium ── */
  .stDownloadButton > button {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_GES} 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 100px !important;
    padding: 10px 30px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.87rem !important;
    letter-spacing: 0.02em;
    box-shadow: 0 4px 16px rgba(11,110,153,0.26) !important;
    transition: transform 0.22s var(--spring), box-shadow 0.22s ease !important;
    position: relative; overflow: hidden;
  }}
  .stDownloadButton > button:hover {{
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 8px 28px rgba(11,110,153,0.38) !important;
  }}
  .stDownloadButton > button:active {{
    transform: translateY(0) scale(0.98) !important;
  }}
  .stFormSubmitButton > button {{
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_GES} 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 100px !important;
    padding: 13px 38px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    font-size: 0.96rem !important;
    letter-spacing: 0.02em;
    box-shadow: 0 4px 16px rgba(11,110,153,0.28) !important;
    width: 100%;
    transition: transform 0.22s var(--spring), box-shadow 0.22s ease !important;
  }}
  .stFormSubmitButton > button:hover {{
    transform: translateY(-3px) scale(1.01) !important;
    box-shadow: 0 8px 28px rgba(11,110,153,0.40) !important;
  }}

  /* ── Tabla ── */
  [data-testid="stDataFrame"] {{
    border-radius: var(--r-md) !important;
    overflow: hidden;
    box-shadow: var(--sh-sm);
    border: 1px solid var(--border-s) !important;
  }}

  /* ── Alerts ── */
  .stAlert {{
    border-radius: var(--r-sm) !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    border-left-width: 3px !important;
  }}

  /* ── Gauge ── */
  .gauge-card {{
    background: var(--card);
    border-radius: var(--r-md);
    padding: 16px 14px 10px;
    box-shadow: var(--sh-sm);
    border: 1px solid var(--border-s);
    margin-bottom: 16px;
    height: 100%;
  }}

  /* ── Verdict card ── */
  .verdict-card {{
    background:
      radial-gradient(120% 90% at 100% 0%, color-mix(in srgb, var(--v-color) 10%, transparent) 0%, transparent 60%),
      var(--card);
    border: 1px solid var(--border-s);
    border-left: 4px solid var(--v-color);
    border-radius: var(--r-md);
    padding: 22px 24px;
    box-shadow: var(--sh-sm);
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
    animation: fadeIn 0.5s ease both;
  }}
  .verdict-label {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }}
  .verdict-main {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .verdict-icon {{ font-size: 1.7rem; line-height: 1; }}
  .verdict-value {{
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.32rem;
    line-height: 1.1;
    color: var(--v-color);
  }}
  .verdict-meta {{
    margin-top: auto;
    display: flex;
    flex-direction: column;
    gap: 9px;
    padding-top: 14px;
    border-top: 1px dashed var(--border);
  }}
  .verdict-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.86rem;
  }}
  .verdict-row span {{ color: var(--muted); }}
  .verdict-row strong {{
    color: var(--text);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }}

  /* ── Informe de auditoría (container con borde) ── */
  [data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: var(--r-md) !important;
    border-color: var(--border-s) !important;
    box-shadow: var(--sh-sm);
    background: var(--card);
  }}
  [data-testid="stVerticalBlockBorderWrapper"] h3 {{
    font-family: 'Syne', sans-serif;
    font-size: 1.12rem !important;
    color: {COLOR_PRIMARY};
    margin: 18px 0 8px !important;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }}
  [data-testid="stVerticalBlockBorderWrapper"] h3:first-child {{ margin-top: 4px !important; }}
  [data-testid="stVerticalBlockBorderWrapper"] p {{
    color: var(--text);
    line-height: 1.7;
    font-size: 0.93rem;
  }}

  /* ── Informe de auditoría — tarjetas por sección ── */
  .report-wrap {{
    background: var(--card);
    border: 1px solid var(--border-s);
    border-radius: var(--r-md);
    box-shadow: var(--sh-sm);
    padding: 8px 28px;
    animation: fadeIn 0.5s ease both;
  }}
  .report-step {{
    display: flex;
    gap: 18px;
    padding: 22px 0;
    border-bottom: 1px solid var(--border);
  }}
  .report-step:last-child {{ border-bottom: none; }}
  .report-num {{
    flex: 0 0 auto;
    width: 38px; height: 38px;
    display: grid; place-items: center;
    border-radius: 50%;
    background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, {COLOR_GES} 100%);
    color: #fff;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.02rem;
    box-shadow: 0 4px 12px rgba(11,110,153,0.28);
  }}
  .report-body {{ flex: 1 1 auto; min-width: 0; }}
  .report-body h4 {{
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.08rem !important;
    color: {COLOR_TEXT} !important;
    margin: 4px 0 8px !important;
    letter-spacing: -0.01em;
  }}
  .report-body p {{
    color: var(--text);
    line-height: 1.72;
    font-size: 0.93rem;
    margin: 0 0 8px;
  }}
  .report-body p:last-child {{ margin-bottom: 0; }}
  .report-body strong {{ color: {COLOR_PRIMARY}; font-weight: 700; }}

  /* Resaltado del veredicto final */
  .report-step.is-verdict {{
    background: linear-gradient(135deg, rgba(8,145,178,0.05) 0%, transparent 70%);
    margin: 0 -28px;
    padding: 22px 28px;
    border-radius: 0 0 var(--r-md) var(--r-md);
    border-bottom: none;
  }}
  .report-step.is-verdict .report-num {{
    background: linear-gradient(135deg, #065A80 0%, {COLOR_PRIMARY} 100%);
  }}
  .report-step.is-verdict .report-body h4 {{ color: {COLOR_PRIMARY} !important; }}

  /* ── AI form card ── */
  .ai-card {{
    background: var(--glass);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: var(--r-lg);
    border: 1px solid var(--border-s);
    box-shadow: var(--sh-md);
    overflow: hidden;
  }}


  /* ── HR ── */
  hr {{
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 24px 0 !important;
  }}

  /* ── Slider ── */
  .stSlider > div > div > div > div {{ background-color: {COLOR_PRIMARY} !important; }}

  /* ── Gráficos Plotly — card con hover ── */
  [data-testid="stPlotlyChart"] {{
    background: linear-gradient(160deg, #ffffff 70%, rgba(8,145,178,0.04) 100%) !important;
    border-radius: var(--r-md) !important;
    border: 1px solid var(--border-s) !important;
    box-shadow: var(--sh-sm) !important;
    padding: 14px 10px 6px !important;
    transition: transform 0.3s var(--spring), box-shadow 0.3s ease !important;
    overflow: hidden;
    position: relative;
  }}
  [data-testid="stPlotlyChart"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, {COLOR_GES}, {COLOR_ACCENT}, {COLOR_PRIMARY});
    border-radius: var(--r-md) var(--r-md) 0 0;
  }}
  [data-testid="stPlotlyChart"]:hover {{
    transform: translateY(-5px) !important;
    box-shadow: var(--sh-md) !important;
  }}

  /* ── Loader IA ── */
  .ia-loader {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 22px;
    padding: 52px 24px;
    background: linear-gradient(160deg, #ffffff 60%, rgba(8,145,178,0.05) 100%);
    border: 1px solid var(--border-s);
    border-radius: var(--r-md);
    box-shadow: var(--sh-sm);
    animation: fadeIn 0.4s ease both;
  }}
  .ia-loader-ring {{
    position: relative;
    width: 72px; height: 72px;
  }}
  .ia-loader-ring::before,
  .ia-loader-ring::after {{
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 3px solid transparent;
  }}
  .ia-loader-ring::before {{
    border-top-color: {COLOR_PRIMARY};
    border-right-color: {COLOR_ACCENT};
    animation: iaSpin 0.9s linear infinite;
  }}
  .ia-loader-ring::after {{
    inset: 12px;
    border-bottom-color: {COLOR_GES};
    border-left-color: {COLOR_ACCENT};
    animation: iaSpin 1.4s linear infinite reverse;
  }}
  .ia-loader-pulse {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.5rem;
    animation: iaBeat 1.1s ease-in-out infinite;
  }}
  @keyframes iaSpin {{
    to {{ transform: rotate(360deg); }}
  }}
  @keyframes iaBeat {{
    0%, 100% {{ transform: translate(-50%, -50%) scale(1); }}
    50%      {{ transform: translate(-50%, -50%) scale(1.18); }}
  }}
  .ia-loader-text {{
    text-align: center;
  }}
  .ia-loader-title {{
    font-family: 'Syne', sans-serif;
    font-size: 1.02rem;
    font-weight: 700;
    color: {COLOR_PRIMARY};
    margin-bottom: 6px;
  }}
  .ia-loader-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 0.84rem;
    color: var(--muted);
  }}
  .ia-loader-dots span {{
    display: inline-block;
    animation: iaDots 1.4s infinite both;
  }}
  .ia-loader-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
  .ia-loader-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
  @keyframes iaDots {{
    0%, 80%, 100% {{ opacity: 0.2; }}
    40%           {{ opacity: 1; }}
  }}
  .ia-loader-bar {{
    width: min(320px, 80%);
    height: 4px;
    border-radius: 100px;
    background: var(--bg-alt);
    overflow: hidden;
    position: relative;
  }}
  .ia-loader-bar::after {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    height: 100%; width: 40%;
    border-radius: 100px;
    background: linear-gradient(90deg, transparent, {COLOR_PRIMARY}, {COLOR_ACCENT}, transparent);
    animation: iaSlide 1.3s ease-in-out infinite;
  }}
  @keyframes iaSlide {{
    0%   {{ left: -40%; }}
    100% {{ left: 100%; }}
  }}

  /* ── Sección de hallazgo rediseñada ── */
  .insight-section {{
    margin-top: 32px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .insight-box {{
    background: linear-gradient(135deg, rgba(8,145,178,0.07) 0%, rgba(34,196,208,0.04) 100%);
    border: 1px solid rgba(8,145,178,0.18);
    border-left: 4px solid {COLOR_ACCENT};
    border-radius: 0 var(--r-md) var(--r-md) var(--r-md);
    padding: 24px 28px;
    position: relative;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
  }}
  .insight-box:hover {{
    transform: translateX(4px);
    box-shadow: var(--sh-sm);
  }}
  .insight-box::before {{
    content: '💡';
    position: absolute;
    top: -15px; left: 0px;
    font-size: 1rem; line-height: 1;
    background: var(--card);
    padding: 2px 6px;
    border-radius: 6px;
    border: 1px solid var(--border);
  }}
  .insight-title {{
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {COLOR_GES};
    margin-bottom: 8px;
  }}
  .insight-box p {{
    color: var(--text) !important;
    font-size: 0.93rem;
    line-height: 1.75;
    margin: 0;
  }}
  .disclaimer-box {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(11,110,153,0.05);
    border: 1px solid rgba(11,110,153,0.12);
    border-radius: var(--r-sm);
    padding: 14px 20px;
    font-size: 0.85rem;
    color: var(--muted);
    font-family: 'Inter', sans-serif;
  }}
  .disclaimer-box .disc-icon {{
    font-size: 1.1rem;
    flex-shrink: 0;
  }}

  /* ── Footer mejorado ── */
  .footer-wrap {{
    margin-top: 56px;
    background: linear-gradient(135deg, {COLOR_SECONDARY} 0%, {COLOR_PRIMARY} 55%, #0A7A9E 100%);
    border-radius: var(--r-lg);
    padding: 38px 44px 30px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--sh-md);
  }}
  .footer-wrap::before {{
    content: '';
    position: absolute;
    top: -60px; right: -40px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(34,196,208,0.35) 0%, transparent 70%);
    pointer-events: none;
  }}
  .footer-wrap::after {{
    content: '';
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px);
    background-size: 22px 22px;
    pointer-events: none;
  }}
  .footer-top {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 24px;
    position: relative;
    z-index: 1;
  }}
  .footer-brand {{
    max-width: 320px;
  }}
  .footer-logo {{
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
  }}
  .footer-logo .dot-accent {{ color: {COLOR_ACCENT}; }}
  .footer-tagline {{
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    line-height: 1.6;
    color: rgba(255,255,255,0.72);
  }}
  .footer-cols {{
    display: flex;
    gap: 48px;
    flex-wrap: wrap;
  }}
  .footer-col h5 {{
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: {COLOR_ACCENT};
    margin: 0 0 12px;
  }}
  .footer-col ul {{
    list-style: none;
    padding: 0; margin: 0;
    display: flex;
    flex-direction: column;
    gap: 7px;
  }}
  .footer-col li {{
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: rgba(255,255,255,0.78);
  }}
  .footer-divider {{
    height: 1px;
    background: rgba(255,255,255,0.14);
    margin: 26px 0 16px;
    position: relative;
    z-index: 1;
  }}
  .footer-bottom {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    position: relative;
    z-index: 1;
  }}
  .footer-copy {{
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: rgba(255,255,255,0.6);
    letter-spacing: 0.03em;
  }}
  .footer-copy strong {{ color: rgba(255,255,255,0.92); font-weight: 700; }}
  .footer-badge {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 100px;
    padding: 5px 14px;
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.04em;
  }}
  .footer-badge .pulse {{
    width: 7px; height: 7px;
    border-radius: 50%;
    background: {COLOR_ACCENT};
    box-shadow: 0 0 0 0 rgba(34,196,208,0.7);
    animation: badgePulse 2s infinite;
  }}
  @keyframes badgePulse {{
    0%   {{ box-shadow: 0 0 0 0 rgba(34,196,208,0.6); }}
    70%  {{ box-shadow: 0 0 0 8px rgba(34,196,208,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(34,196,208,0); }}
  }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    return pd.read_csv("data/dataset_limpio.csv")

df = cargar_datos()

# ============================================================
# HERO HEADER
# ============================================================
st.markdown("""
<div class="hero">
  <div class="hero-accent-line"></div>
  <div class="hero-blob-a"></div>
  <div class="hero-blob-b"></div>
  <div class="hero-dot hero-dot-1"></div>
  <div class="hero-dot hero-dot-2"></div>
  <div class="hero-dot hero-dot-3"></div>
  <div class="hero-inner">
    <div class="hero-badge">🏥 Sistema de Salud · Chile · GES 2026</div>
    <h1>GESAssist</h1>
    <p style="font-size:1.0rem;font-weight:500;color:rgba(255,255,255,0.65);font-family:'Inter',sans-serif;margin:-4px 0 16px;letter-spacing:0.01em;">Análisis Inteligente de Diagnósticos GES</p>
    <p>Explora y visualiza diagnósticos médicos clasificados según las Garantías Explícitas en Salud.<br>
    Filtra por edad, tipo de caso y diagnóstico — y consulta nuestro asistente de IA clínica.</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tab1, tab2 = st.tabs(["📊  Dashboard Interactivo", "🤖  Asistente IA"])

# ============================================================
# TAB 1 — DASHBOARD
# ============================================================
with tab1:

    # ── Sidebar / Filtros ──────────────────────────────────
    st.sidebar.markdown("""
<div class="sb-brand">
  <div style="display:flex;align-items:center;gap:12px;">
    <div class="sb-brand-logo">🏥</div>
    <div>
      <div class="sb-brand-name">GESAssist</div>
      <div class="sb-brand-sub">Sistema GES · Chile</div>
    </div>
  </div>
</div>
<div class="sb-section-label">Filtros del dashboard</div>
""", unsafe_allow_html=True)

    edad_min = int(df["age"].min())
    edad_max = int(df["age"].max())

    rango_edad = st.sidebar.slider(
        "Rango de edad",
        min_value=edad_min,
        max_value=edad_max,
        value=(edad_min, edad_max)
    )

    opcion_ges = st.sidebar.selectbox(
        "Tipo de caso",
        options=["Todos", "GES", "No GES"]
    )

    buscar_diagnostico = st.sidebar.text_input(
        "Buscar diagnóstico",
        placeholder="Ej: CATARATA, CANCER…"
    )

    st.sidebar.markdown("""
<div class="sb-footer">
  <div class="sb-footer-text">Datos con fines<br>académicos · 2026</div>
  <div class="sb-version">v3.0</div>
</div>
""", unsafe_allow_html=True)

    # ── Aplicar filtros ────────────────────────────────────
    df_filtrado = df[
        (df["age"] >= rango_edad[0]) &
        (df["age"] <= rango_edad[1])
    ].copy()

    if opcion_ges == "GES":
        df_filtrado = df_filtrado[df_filtrado["ges"]]
    elif opcion_ges == "No GES":
        df_filtrado = df_filtrado[~df_filtrado["ges"]]

    if buscar_diagnostico.strip():
        texto = buscar_diagnostico.upper().strip()
        df_filtrado = df_filtrado[
            df_filtrado["diagnostic"].str.contains(texto, case=False, na=False)
        ]

    # ── KPIs ───────────────────────────────────────────────
    total_casos    = len(df_filtrado)
    total_sin_filtro = len(df)
    casos_ges      = int(df_filtrado["ges"].sum()) if total_casos > 0 else 0
    casos_no_ges   = total_casos - casos_ges
    pct_ges        = (casos_ges / total_casos * 100) if total_casos > 0 else 0

    delta_total = total_casos - total_sin_filtro
    delta_ges   = casos_ges - int(df["ges"].sum())
    delta_no    = casos_no_ges - (total_sin_filtro - int(df["ges"].sum()))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de casos",  f"{total_casos:,}",
                delta=f"{delta_total:+,}" if delta_total != 0 else None)
    col2.metric("Casos GES",       f"{casos_ges:,}",
                delta=f"{delta_ges:+,}" if delta_ges != 0 else None)
    col3.metric("Casos No GES",    f"{casos_no_ges:,}",
                delta=f"{delta_no:+,}" if delta_no != 0 else None, delta_color="inverse")
    col4.metric("Porcentaje GES",  f"{pct_ges:.1f}%")

    if total_casos == 0:
        st.warning("No hay datos para los filtros seleccionados. Ajusta los filtros del panel lateral.")
    else:
        df_filtrado["clasificacion"] = df_filtrado["ges"].map({True: "GES", False: "No GES"})

        # ── Fila 1: Barras + Histograma ────────────────────
        st.markdown("""
        <div class="section-header">
          <div class="sh-line"></div>
          <div class="sh-content">
            <span class="sh-label">Clasificación</span>
            <h3>Distribución GES vs No GES</h3>
          </div>
        </div>
        """, unsafe_allow_html=True)

        c_left, c_right = st.columns(2)

        with c_left:
            conteo = (
                df_filtrado["clasificacion"]
                .value_counts()
                .reset_index()
            )
            conteo.columns = ["Clasificación", "Cantidad"]
            fig1 = px.bar(
                conteo,
                x="Clasificación", y="Cantidad",
                text="Cantidad",
                color="Clasificación",
                color_discrete_map={"GES": COLOR_GES, "No GES": COLOR_NO_GES},
                template=PLOTLY_TEMPLATE,
            )
            fig1.update_traces(
                textposition="outside",
                textfont=dict(size=14, family="Inter", weight=700, color=COLOR_TEXT),
                marker_line_width=0,
                marker_cornerradius=10,
                hovertemplate="<b>%{x}</b><br>Casos: %{y:,}<extra></extra>",
            )
            fig1.update_layout(
                **BASE_LAYOUT,
                margin=dict(t=44, b=40, l=8, r=8),
                legend=_LEGEND,
                showlegend=False,
                bargap=0.45,
                height=360,
                title=dict(text="Casos GES vs No GES", font=dict(size=15, family="Syne", color=COLOR_TEXT), x=0.01, xanchor="left"),
                xaxis=dict(**{**_AXIS, "tickfont": dict(size=13, family="Inter", color=COLOR_TEXT)}),
                xaxis_title=None,
                yaxis=dict(**_AXIS, title="Cantidad de casos",
                           title_font=dict(size=11, color="#6B94A8")),
            )
            st.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)

        with c_right:
            fig2 = px.pie(
                conteo,
                names="Clasificación", values="Cantidad",
                color="Clasificación",
                color_discrete_map={"GES": COLOR_GES, "No GES": COLOR_NO_GES},
                hole=0.62,
                template=PLOTLY_TEMPLATE,
            )
            fig2.update_traces(
                textinfo="percent",
                textfont=dict(size=13, family="Inter", color="#ffffff"),
                marker_line=dict(color="#ffffff", width=4),
                pull=[0.04, 0],
                hovertemplate="<b>%{label}</b><br>%{value:,} casos (%{percent})<extra></extra>",
            )
            fig2.update_layout(
                **BASE_LAYOUT,
                showlegend=True,
                height=340,
                title=dict(text="Distribución de cobertura", font=dict(size=15, family="Syne", color=COLOR_TEXT), x=0.01, xanchor="left"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.12,
                            xanchor="center", x=0.5, font=dict(size=12, family="Inter")),
                margin=dict(t=44, b=30, l=8, r=8),
                annotations=[dict(
                    text=f"<b>{pct_ges:.0f}%</b><br><span style='font-size:11px'>GES</span>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=24, family="Syne", color=COLOR_TEXT),
                )],
            )
            st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

        # ── Distribución de edades ─────────────────────────
        st.markdown("""
        <div class="section-header">
          <div class="sh-line"></div>
          <div class="sh-content">
            <span class="sh-label">Demografía</span>
            <h3>Distribución de edad por clasificación</h3>
          </div>
        </div>
        """, unsafe_allow_html=True)

        fig3 = px.histogram(
            df_filtrado,
            x="age", color="clasificacion",
            nbins=25,
            color_discrete_map={"GES": COLOR_GES, "No GES": COLOR_NO_GES},
            labels={"age": "Edad", "clasificacion": "Clasificación"},
            template=PLOTLY_TEMPLATE,
            barmode="overlay",
            opacity=0.78,
        )
        fig3.update_traces(
            marker_line_width=0,
            marker_cornerradius=4,
            hovertemplate="<b>Edad: %{x}</b><br>Frecuencia: %{y}<extra></extra>",
        )
        fig3.update_layout(
            **BASE_LAYOUT,
            margin=dict(t=48, b=30, l=8, r=20),
            height=380,
            title=dict(text="Frecuencia de casos por edad y clasificación GES", font=dict(size=15, family="Syne", color=COLOR_TEXT), x=0.01, xanchor="left"),
            xaxis=dict(**_AXIS, title="Edad del paciente"),
            yaxis=dict(**_AXIS, title="Frecuencia"),
            legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=12)),
            bargap=0.06,
        )
        st.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)

        # ── Diagnósticos más frecuentes ────────────────────
        st.markdown("""
        <div class="section-header">
          <div class="sh-line"></div>
          <div class="sh-content">
            <span class="sh-label">Análisis clínico</span>
            <h3>Diagnósticos más frecuentes</h3>
          </div>
        </div>
        """, unsafe_allow_html=True)

        top_n = st.slider("Diagnósticos a mostrar", min_value=5, max_value=20, value=10)

        top_diag = (
            df_filtrado["diagnostic"]
            .value_counts()
            .head(top_n)
            .reset_index()
        )
        top_diag.columns = ["Diagnóstico", "Cantidad"]

        fig4 = px.bar(
            top_diag,
            x="Cantidad", y="Diagnóstico",
            orientation="h",
            text="Cantidad",
            color="Cantidad",
            color_continuous_scale=[[0, "#B8DFF0"], [0.5, COLOR_PRIMARY], [1, COLOR_SECONDARY]],
            template=PLOTLY_TEMPLATE,
        )
        fig4.update_traces(
            textposition="outside",
            textfont=dict(size=11, family="Inter", color=COLOR_TEXT),
            marker_line_width=0,
            marker_cornerradius=6,
            hovertemplate="<b>%{y}</b><br>Casos: %{x:,}<extra></extra>",
        )
        fig4.update_layout(
            **BASE_LAYOUT,
            legend=_LEGEND,
            height=max(360, top_n * 34),
            title=dict(text=f"Top {top_n} diagnósticos más frecuentes", font=dict(size=15, family="Syne", color=COLOR_TEXT), x=0.01, xanchor="left"),
            yaxis=dict(**{**_AXIS, "tickfont": dict(size=10, family="Inter", color="#4A7B94"), "showgrid": False},
                       categoryorder="total ascending"),
            xaxis=dict(**_AXIS, title="Cantidad de casos"),
            coloraxis_showscale=False,
            yaxis_title=None,
            margin=dict(t=48, b=16, l=4, r=60),
        )
        st.plotly_chart(fig4, use_container_width=True, config=PLOTLY_CONFIG)

        # ── Grupos etarios ─────────────────────────────────
        st.markdown("""
        <div class="section-header">
          <div class="sh-line"></div>
          <div class="sh-content">
            <span class="sh-label">Segmentación</span>
            <h3>Casos por grupo etario</h3>
          </div>
        </div>
        """, unsafe_allow_html=True)

        df_filtrado["grupo_edad"] = pd.cut(
            df_filtrado["age"],
            bins=[0, 18, 30, 45, 60, 75, 100],
            labels=["0–18", "19–30", "31–45", "46–60", "61–75", "76+"]
        )

        grupo_edad = (
            df_filtrado
            .groupby(["grupo_edad", "clasificacion"], observed=False)
            .size()
            .reset_index(name="Cantidad")
        )

        fig5 = px.bar(
            grupo_edad,
            x="grupo_edad", y="Cantidad",
            color="clasificacion",
            barmode="group",
            color_discrete_map={"GES": COLOR_GES, "No GES": COLOR_NO_GES},
            labels={"grupo_edad": "Grupo etario", "clasificacion": "Clasificación"},
            template=PLOTLY_TEMPLATE,
            text="Cantidad",
        )
        fig5.update_traces(
            textposition="outside",
            textfont=dict(size=11, family="Inter", weight=600, color=COLOR_TEXT),
            marker_line_width=0,
            marker_cornerradius=7,
            hovertemplate="<b>%{x}</b> · %{data.name}<br>Casos: %{y:,}<extra></extra>",
        )
        fig5.update_layout(
            **BASE_LAYOUT,
            margin=dict(t=48, b=30, l=8, r=20),
            height=400,
            title=dict(text="Casos por grupo etario y cobertura GES", font=dict(size=15, family="Syne", color=COLOR_TEXT), x=0.01, xanchor="left"),
            xaxis=dict(**{**_AXIS, "showgrid": False}, title="Grupo etario"),
            yaxis=dict(**_AXIS, title="Cantidad de casos"),
            legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=12)),
            bargap=0.22,
            bargroupgap=0.06,
        )
        st.plotly_chart(fig5, use_container_width=True, config=PLOTLY_CONFIG)

        # ── Tabla de datos ─────────────────────────────────
        st.markdown("""
        <div class="section-header">
          <div class="sh-line"></div>
          <div class="sh-content">
            <span class="sh-label">Dataset</span>
            <h3>Registros filtrados</h3>
          </div>
        </div>
        """, unsafe_allow_html=True)

        display_df = df_filtrado[["id", "diagnostic", "age", "ges"]].copy()
        display_df["ges"] = display_df["ges"].map({True: "✅ GES", False: "❌ No GES"})
        st.dataframe(
            display_df.rename(columns={
                "id": "ID",
                "diagnostic": "Diagnóstico",
                "age": "Edad",
                "ges": "Clasificación"
            }),
            use_container_width=True,
            hide_index=True
        )

        csv_df = df_filtrado[["id", "diagnostic", "age", "ges"]].copy()
        csv_df["ges"] = csv_df["ges"].map({True: "GES", False: "No GES"})
        csv_df = csv_df.rename(columns={
            "id": "ID", "diagnostic": "Diagnostico",
            "age": "Edad", "ges": "Clasificacion",
        })
        csv_bytes = csv_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥  Descargar datos filtrados (CSV)",
            data=csv_bytes,
            file_name="dataset_filtrado_ges.csv",
            mime="text/csv",
            key="download_csv",
        )

        # ── Hallazgo principal ────────────────────────────
        st.divider()

        st.markdown(f"""
        <div class="insight-section">
          <div class="insight-box">
            <div class="insight-title">Hallazgo principal</div>
            <p>
              En el conjunto filtrado se identificaron <strong>{total_casos:,} casos</strong>,
              de los cuales <strong>{casos_ges:,} corresponden a GES ({pct_ges:.1f}%)</strong>
              y <strong>{casos_no_ges:,} no corresponden a GES</strong>.
              El análisis sugiere que la clasificación GES no depende únicamente del diagnóstico —
              también influyen la <strong>edad del paciente</strong> y la forma en que se registra el diagnóstico en el sistema.
            </p>
          </div>
          <div class="disclaimer-box">
            <span class="disc-icon">ℹ️</span>
            <span>Este dashboard tiene fines <strong>académicos y de exploración</strong>. No reemplaza una evaluación médica profesional.</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# TAB 2 — ASISTENTE IA
# ============================================================
with tab2:
    st.markdown("""
    <div class="section-header">
      <div class="sh-line"></div>
      <div class="sh-content">
        <span class="sh-label">Inteligencia Artificial · Llama-3</span>
        <h3>Asistente de Elegibilidad GES</h3>
      </div>
    </div>
    <p style="color:var(--muted);font-size:0.92rem;margin-bottom:26px;line-height:1.65;">
      Ingresa un diagnóstico y los datos del paciente para obtener un análisis de elegibilidad GES
      basado en datos históricos y razonamiento clínico-administrativo.
    </p>
    """, unsafe_allow_html=True)

    # ── Resolución del token: Secrets de Streamlit → variable de entorno → input manual ──
    secret_token = None
    try:
        if "HF_TOKEN" in st.secrets:
            secret_token = st.secrets["HF_TOKEN"]
    except Exception:
        secret_token = None

    env_token = os.getenv("HF_TOKEN")
    if env_token == "hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX":
        env_token = None

    auto_token = secret_token or env_token
    token_source = "Secrets de Streamlit" if secret_token else ("Variable de entorno" if env_token else None)

    with st.expander("🔑  Configurar API Key de Hugging Face", expanded=not bool(auto_token)):
        if auto_token:
            st.success(f"Token detectado automáticamente · Origen: **{token_source}**")
            st.caption("No necesitas hacer nada. Si quieres usar otro token solo para esta sesión, pégalo abajo.")
        else:
            st.caption(
                "Para desplegar en Streamlit Cloud, agrega `HF_TOKEN` en **Settings → Secrets**. "
                "Mientras tanto, puedes pegar tu token aquí (se guarda solo en tu sesión del navegador, no en el código)."
            )
        manual_token = st.text_input(
            "Hugging Face Access Token",
            type="password",
            placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            key="hf_token_input",
            help="Crea un token gratuito en huggingface.co → Settings → Access Tokens (rol: Read).",
        )

    hf_token = auto_token or (manual_token.strip() if manual_token else None)

    if not hf_token:
        st.warning("⚠️ **Asistente IA desactivado.** Configura tu `HF_TOKEN` en el panel de arriba para activar esta función.")
    else:

        with st.form("ia_form"):
            col_a, col_b = st.columns(2)

            with col_a:
                user_diagnostic = st.text_input(
                    "Diagnóstico",
                    placeholder="Ej: Catarata, Cáncer de Mama, Apendicitis…"
                )
                user_age = st.number_input(
                    "Edad del paciente",
                    min_value=0, max_value=120, value=30
                )

            with col_b:
                user_prevision = st.selectbox(
                    "Previsión",
                    ["FONASA", "ISAPRE", "Fuerzas Armadas (CAPREDENA/DIPRECA)", "Particular"]
                )
                user_formulario = st.radio(
                    "Formulario de Constancia GES",
                    ["Sí, firmado", "No, pendiente"],
                    horizontal=True
                )

            submit_button = st.form_submit_button("🔍  Analizar elegibilidad GES")

            if submit_button:
                if not user_diagnostic.strip():
                    st.error("Por favor ingresa un diagnóstico válido.")
                else:
                    loader_ph = st.empty()
                    loader_ph.markdown("""
                    <div class="ia-loader">
                      <div class="ia-loader-ring">
                        <div class="ia-loader-pulse">🩺</div>
                      </div>
                      <div class="ia-loader-text">
                        <div class="ia-loader-title">Analizando elegibilidad GES</div>
                        <div class="ia-loader-sub">Consultando datos históricos y modelo Llama-3<span class="ia-loader-dots"><span>.</span><span>.</span><span>.</span></span></div>
                      </div>
                      <div class="ia-loader-bar"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.container():
                        try:
                            # RAG empírico
                            diag_upper    = user_diagnostic.upper().strip()
                            df_rag        = df[df["diagnostic"].str.contains(diag_upper, case=False, na=False)]
                            df_rag        = df_rag[(df_rag["age"] >= user_age - 5) & (df_rag["age"] <= user_age + 5)]
                            total_sim     = len(df_rag)
                            ges_sim       = int(df_rag["ges"].sum()) if total_sim > 0 else 0
                            prob_empirica = (ges_sim / total_sim * 100) if total_sim > 0 else 0

                            if total_sim > 0:
                                rag_context = (
                                    f"DATO EMPÍRICO: En el dataset histórico encontramos {total_sim} casos similares "
                                    f"(pacientes entre {max(0,user_age-5)} y {user_age+5} años con diagnóstico '{user_diagnostic}'). "
                                    f"El {prob_empirica:.1f}% fue clasificado como GES. "
                                    f"Menciona obligatoriamente este porcentaje y justifica si tiene sentido clínico."
                                )
                            else:
                                rag_context = (
                                    f"DATO EMPÍRICO: No hay casos históricos para '{user_diagnostic}' "
                                    f"en el rango de edad ±5 años. Menciona esto e indica que puede ser atípico."
                                )

                            # Llamada al modelo (parte lenta) — el loader sigue visible
                            client = InferenceClient(
                                model="meta-llama/Meta-Llama-3-8B-Instruct",
                                token=hf_token
                            )

                            system_prompt = """Eres un experto médico y auditor del sistema de salud en Chile.
"GES" significa "Garantías Explícitas en Salud" (Decreto Supremo N° 29).

Evalúa el caso cruzando los datos clínicos con estas Reglas de Elegibilidad:
1. Previsión: Solo FONASA o ISAPRE. Excluye FF.AA. y Particulares.
2. Red Cerrada: Obligatorio atenderse en la red definida por su seguro.
3. Formalidad: El Formulario de Constancia GES debe estar firmado.
4. Edad: Determinista. Ej. Artrosis cadera >= 65 años, Escoliosis < 25 años, Catarata > 15 años.
5. Ley 21.331: Isapres no pueden rechazar cobertura por preexistencias psiquiátricas.

Estructura tu respuesta EXACTAMENTE en este formato Markdown:

### 1. 📊 Análisis Empírico
(Menciona el dato estadístico histórico inyectado sobre probabilidad GES).

### 2. 🩺 Criterio Clínico y Etario
(Evalúa el Diagnóstico vs la Edad según las reglas GES).

### 3. ⚖️ Criterio Administrativo y Previsional
(Evalúa la Previsión y el estado del Formulario).

### 4. 🛑 Veredicto Final
(Concluye si es ELEGIBLE, NO ELEGIBLE, o PENDIENTE DE TRÁMITE y justifica).

Responde siempre en español, de forma profesional y estructurada."""

                            user_prompt = (
                                f"Paciente de {user_age} años.\n"
                                f"Diagnóstico: '{user_diagnostic}'.\n"
                                f"Previsión: {user_prevision}.\n"
                                f"Formulario GES: {user_formulario}.\n\n"
                                f"{rag_context}\n\n"
                                f"Genera el Informe de Auditoría Estructurado."
                            )

                            response = client.chat_completion(
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user",   "content": user_prompt}
                                ],
                                max_tokens=1000
                            )

                            # Resultado listo → quitar loader y renderizar
                            loader_ph.empty()

                            report_md = response.choices[0].message.content
                            _low = report_md.lower()
                            if "no elegible" in _low:
                                v_label, v_color, v_icon = "NO ELEGIBLE", "#DC2626", "🛑"
                            elif "pendiente" in _low:
                                v_label, v_color, v_icon = "PENDIENTE DE TRÁMITE", "#D97706", "⏳"
                            elif "elegible" in _low:
                                v_label, v_color, v_icon = "ELEGIBLE", "#059669", "✅"
                            else:
                                v_label, v_color, v_icon = "EVALUADO", COLOR_PRIMARY, "📋"

                            g_col, v_col = st.columns([1.35, 1], gap="medium")

                            with g_col:
                                st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
                                fig_gauge = go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=prob_empirica,
                                    number={"suffix": "%", "font": {"size": 40, "color": COLOR_TEXT, "family": "Inter"}},
                                    title={
                                        "text": (
                                            f"Probabilidad GES histórica<br>"
                                            f"<span style='font-size:0.78em;color:#90A4AE'>"
                                            f"Basado en {total_sim} casos similares</span>"
                                        ),
                                        "font": {"size": 14, "color": COLOR_TEXT, "family": "Inter"}
                                    },
                                    gauge={
                                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#CFD8DC"},
                                        "bar": {"color": COLOR_PRIMARY, "thickness": 0.28},
                                        "bgcolor": "white",
                                        "borderwidth": 0,
                                        "steps": [
                                            {"range": [0, 33],  "color": "#FFCDD2"},
                                            {"range": [33, 66], "color": "#FFF9C4"},
                                            {"range": [66, 100],"color": "#C8E6C9"},
                                        ],
                                        "threshold": {
                                            "line": {"color": COLOR_PRIMARY, "width": 3},
                                            "thickness": 0.8,
                                            "value": prob_empirica
                                        }
                                    }
                                ))
                                fig_gauge.update_layout(
                                    height=300,
                                    margin=dict(t=70, b=20, l=30, r=30),
                                    paper_bgcolor="white",
                                    font_family="Inter"
                                )
                                st.plotly_chart(fig_gauge, use_container_width=True, config=PLOTLY_CONFIG)
                                st.markdown('</div>', unsafe_allow_html=True)

                            with v_col:
                                st.markdown(f"""
                                <div class="verdict-card" style="--v-color:{v_color};">
                                  <span class="verdict-label">Veredicto de elegibilidad</span>
                                  <div class="verdict-main">
                                    <span class="verdict-icon">{v_icon}</span>
                                    <span class="verdict-value">{v_label}</span>
                                  </div>
                                  <div class="verdict-meta">
                                    <div class="verdict-row">
                                      <span>Casos analizados</span><strong>{total_sim}</strong>
                                    </div>
                                    <div class="verdict-row">
                                      <span>Clasificados GES</span><strong>{ges_sim}</strong>
                                    </div>
                                    <div class="verdict-row">
                                      <span>Coincidencia histórica</span><strong>{prob_empirica:.0f}%</strong>
                                    </div>
                                  </div>
                                </div>
                                """, unsafe_allow_html=True)

                            st.markdown("""
                            <div class="section-header" style="margin-top:8px;">
                              <div class="sh-line"></div>
                              <div class="sh-content">
                                <span class="sh-label">Resultado</span>
                                <h3>Informe de Auditoría GES</h3>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)

                            def _inline_md(t):
                                t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
                                t = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<em>\1</em>", t)
                                return t.strip()

                            _headers = list(re.finditer(r"(?m)^#{2,4}\s*(.+?)\s*$", report_md))
                            if _headers:
                                steps_html = ""
                                for _i, _h in enumerate(_headers):
                                    _title = _h.group(1).strip()
                                    _start = _h.end()
                                    _end = _headers[_i + 1].start() if _i + 1 < len(_headers) else len(report_md)
                                    _body = report_md[_start:_end].strip()
                                    _m = re.match(r"^(\d+)[\.\)]\s*(.+)$", _title)
                                    if _m:
                                        _num, _title_txt = _m.group(1), _m.group(2).strip()
                                    else:
                                        _num, _title_txt = str(_i + 1), _title
                                    _paras = [p.strip() for p in re.split(r"\n\s*\n", _body) if p.strip()]
                                    _body_html = "".join(f"<p>{_inline_md(p)}</p>" for p in _paras)
                                    _is_last = _i == len(_headers) - 1
                                    steps_html += f"""
                                    <div class="report-step{' is-verdict' if _is_last else ''}">
                                      <div class="report-num">{_num}</div>
                                      <div class="report-body">
                                        <h4>{_inline_md(_title_txt)}</h4>
                                        {_body_html}
                                      </div>
                                    </div>"""
                                st.markdown(f'<div class="report-wrap">{steps_html}</div>', unsafe_allow_html=True)
                            else:
                                with st.container(border=True):
                                    st.markdown(report_md)

                        except Exception as e:
                            loader_ph.empty()
                            st.error(f"Error al conectar con la API de Hugging Face: {e}")

# ============================================================
# FOOTER
# ============================================================
st.markdown(f"""
<div class="footer-wrap">
  <div class="footer-top">
    <div class="footer-brand">
      <div class="footer-logo">GESAssist<span class="dot-accent">.</span></div>
      <div class="footer-tagline">
        Plataforma de análisis de Garantías Explícitas en Salud.
        Visualiza, filtra y evalúa la elegibilidad GES con apoyo de inteligencia artificial.
      </div>
    </div>
    <div class="footer-cols">
      <div class="footer-col">
        <h5>Plataforma</h5>
        <ul>
          <li>Dashboard interactivo</li>
          <li>Asistente IA · Llama-3</li>
          <li>Exportación de datos</li>
        </ul>
      </div>
      <div class="footer-col">
        <h5>Contexto</h5>
        <ul>
          <li>Sistema GES · Chile</li>
          <li>Decreto Supremo N° 29</li>
          <li>Uso académico</li>
        </ul>
      </div>
    </div>
  </div>
  <div class="footer-divider"></div>
  <div class="footer-bottom">
    <div class="footer-copy">
      © 2026 <strong>GESAssist</strong> · Desarrollado por el equipo <strong>BrechaVital</strong> · Datos con fines académicos
    </div>
    <div class="footer-badge"><span class="pulse"></span> Sistema operativo · v3.0</div>
  </div>
</div>
""", unsafe_allow_html=True)
