
import os
import threading
from datetime import date
from io import BytesIO

import streamlit as st

from PIL import Image
from supabase import create_client, Client


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FindIt | Lost & Found",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# FINDIT — LIGHT GLASSMORPHISM DESIGN SYSTEM
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #172b4d;
    --muted: #718096;
    --blue: #3978ed;
    --blue-dark: #245ac7;
    --border: rgba(255,255,255,.85);
    --glass: rgba(255,255,255,.70);
    --shadow: 0 12px 40px rgba(45,75,130,.08);
}

.stApp {
    background:
        radial-gradient(ellipse at 8% 5%, rgba(151,190,255,.27), transparent 35%),
        radial-gradient(ellipse at 95% 25%, rgba(192,177,255,.20), transparent 35%),
        linear-gradient(135deg, #f5f8ff 0%, #edf3fc 50%, #f8faff 100%);
    color: var(--ink);
    font-family: 'DM Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1380px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

[data-testid="stHeader"] {
    background: rgba(245,248,255,.55);
    backdrop-filter: blur(18px);
}

[data-testid="stSidebar"] {
    background: rgba(255,255,255,.64);
    backdrop-filter: blur(24px);
    border-right: 1px solid rgba(255,255,255,.9);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.6rem;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--ink);
}

/* Brand */

.fi-brand {
    display: flex;
    align-items: center;
    gap: 11px;
    color: var(--ink);
    font-family: 'Outfit', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -1.2px;
    margin-bottom: 5px;
}

.fi-logo {
    width: 43px;
    height: 43px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #3978ed, #8bafff);
    color: white;
    border-radius: 15px;
    font-size: 1.45rem;
    box-shadow: 0 7px 20px rgba(57,120,237,.28);
}

/* Glass cards */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--glass);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(255,255,255,.95);
    border-radius: 22px;
    box-shadow: var(--shadow);
    transition: transform .25s ease, box-shadow .25s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 17px 45px rgba(45,75,130,.12);
}

div[data-testid="stForm"] {
    background: rgba(255,255,255,.72);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,.95);
    border-radius: 22px;
    padding: 1.4rem;
    box-shadow: var(--shadow);
}

/* Hero */

.fi-hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 90% 10%, rgba(255,255,255,.65), transparent 28%),
        linear-gradient(120deg, rgba(255,255,255,.90), rgba(222,235,255,.76));
    border: 1px solid rgba(255,255,255,.95);
    border-radius: 30px;
    padding: 3rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 18px 55px rgba(48,84,150,.09);
    animation: fiFade .65s ease both;
}

.fi-hero:after {
    content: "🔎";
    position: absolute;
    right: 7%;
    top: 50%;
    transform: translateY(-50%) rotate(-12deg);
    font-size: clamp(4rem, 10vw, 8rem);
    opacity: .13;
    pointer-events: none;
}

.fi-eyebrow {
    color: #3978ed;
    font-size: .75rem;
    font-weight: 800;
    letter-spacing: 2.5px;
    margin-bottom: 15px;
}

.fi-hero h1 {
    color: #172b4d;
    font-family: 'Outfit', sans-serif;
    font-size: clamp(2.2rem, 5vw, 3.7rem);
    font-weight: 800;
    letter-spacing: -2.5px;
    line-height: 1.08;
    margin: 0;
    max-width: 800px;
}

.fi-hero p {
    color: #64748b;
    font-size: 1.05rem;
    line-height: 1.8;
    max-width: 680px;
    margin-top: 16px;
    margin-bottom: 0;
}

/* Section headings */

.fi-section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.55rem;
    font-weight: 800;
    letter-spacing: -.8px;
    color: var(--ink);
    margin: .5rem 0 .25rem;
}

.fi-section-subtitle {
    color: var(--muted);
    margin-bottom: 1.3rem;
}

/* Stats */

.fi-stat {
    background: rgba(255,255,255,.68);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255,255,255,.95);
    border-radius: 21px;
    padding: 1.35rem 1.5rem;
    min-height: 112px;
    box-shadow: 0 9px 28px rgba(45,75,130,.06);
    transition: transform .25s ease, box-shadow .25s ease;
}

.fi-stat:hover {
    transform: translateY(-4px);
    box-shadow: 0 15px 35px rgba(45,75,130,.12);
}

.fi-stat-label {
    color: var(--muted);
    font-size: .88rem;
    font-weight: 600;
}

.fi-stat-value {
    color: var(--ink);
    font-family: 'Outfit', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    margin-top: 5px;
}

/* Listing labels */

.fi-chip {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 30px;
    font-size: .69rem;
    font-weight: 800;
    letter-spacing: .5px;
    background: #edf2f8;
    color: #475467;
}

.fi-lost {
    background: #fff0ed;
    color: #b42318;
}

.fi-found {
    background: #e8f8ef;
    color: #15803d;
}

.fi-open {
    background: #e8f0ff;
    color: #245ac7;
}

.fi-resolved {
    background: #f0f1f4;
    color: #667085;
}

.fi-muted {
    color: var(--muted);
    font-size: .92rem;
}

/* Inputs */

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] input {
    background: rgba(255,255,255,.85);
    border: 1px solid #e0e8f5;
    border-radius: 13px;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #75a1f5;
    box-shadow: 0 0 0 3px rgba(57,120,237,.10);
}

/* Buttons */

.stButton > button,
.stFormSubmitButton > button {
    border-radius: 13px;
    font-weight: 700;
    min-height: 2.8rem;
    transition: all .2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 18px rgba(57,120,237,.13);
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(120deg, #3978ed, #6596f5);
    border: none;
    color: white;
}

/* FindIt monochrome checkbox styling */
[data-testid="stCheckbox"] input[type="checkbox"] {
    accent-color: #222222 !important;
}

[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div {
    border-color: #222222 !important;
}

[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div[aria-checked="true"],
[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] > div {
    background-color: #222222 !important;
    border-color: #222222 !important;
}

[data-testid="stCheckbox"] [data-baseweb="checkbox"] svg {
    color: #ffffff !important;
    fill: #ffffff !important;
}

[data-testid="stCheckbox"] input[type="checkbox"]:focus-visible {
    outline: 2px solid #777777 !important;
    outline-offset: 2px;
}

/* Metrics */

[data-testid="stMetric"] {
    background: rgba(255,255,255,.70);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,.95);
    padding: 1.2rem;
    border-radius: 19px;
    box-shadow: 0 8px 25px rgba(45,75,130,.06);
}

[data-testid="stMetricValue"] {
    color: var(--ink);
    font-family: 'Outfit', sans-serif;
}

/* Navigation */

[data-testid="stSidebar"] [role="radiogroup"] label {
    background: rgba(255,255,255,.50);
    border-radius: 12px;
    padding: 9px 12px;
    margin-bottom: 5px;
    transition: background .2s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(220,233,255,.8);
}

/* Images */

[data-testid="stImage"] img {
    border-radius: 17px;
    object-fit: cover;
}

/* Animations */

@keyframes fiFade {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

[data-testid="stVerticalBlock"] > div {
    animation: fiFade .4s ease both;
}

hr {
    border-color: rgba(190,205,228,.55);
}

@media (max-width: 800px) {
    .block-container {
        padding-top: 1rem;
    }

    .fi-hero {
        padding: 1.7rem;
        border-radius: 22px;
    }

    .fi-hero:after {
        display: none;
    }

    .fi-hero h1 {
        font-size: 2.3rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *:before, *:after {
        animation-duration: .01ms !important;
        transition-duration: .01ms !important;
    }
}

/* ============================================================
   FINDIT UI REFRESH — CLEAN, PREMIUM MARKETPLACE
   CSS-only refresh: keeps all existing app logic and features.
   ============================================================ */
:root {
    --ink: #172033;
    --muted: #697586;
    --blue: #315fe8;
    --blue-dark: #244bc4;
    --border: #e8edf4;
    --glass: #ffffff;
    --shadow: 0 8px 28px rgba(23, 32, 51, .055);
}
.stApp {
    background: #f6f8fb !important;
    color: var(--ink);
}
.block-container {
    max-width: 1240px !important;
    padding-top: 2.2rem !important;
    padding-bottom: 4rem !important;
}
[data-testid="stHeader"] {
    background: rgba(246,248,251,.88) !important;
    backdrop-filter: blur(14px);
}
[data-testid="stSidebar"] {
    background: #fff !important;
    border-right: 1px solid #edf0f5 !important;
    box-shadow: 5px 0 24px rgba(23,32,51,.025);
}
[data-testid="stSidebar"] > div:first-child { padding: 1.5rem 1rem; }
.fi-brand {
    font-size: 1.9rem !important;
    letter-spacing: -1.4px !important;
    margin: .25rem 0 1.4rem !important;
}
.fi-logo {
    width: 44px !important;
    height: 44px !important;
    border-radius: 14px !important;
    background: #315fe8 !important;
    box-shadow: 0 7px 16px rgba(49,95,232,.2) !important;
}
.fi-hero {
    background: linear-gradient(115deg, #172b4d 0%, #244b83 58%, #315fe8 100%) !important;
    border: 0 !important;
    border-radius: 24px !important;
    padding: clamp(1.7rem, 4vw, 3.1rem) !important;
    margin: .3rem 0 1.8rem !important;
    box-shadow: 0 16px 36px rgba(28,57,105,.15) !important;
}
.fi-hero:after {
    content: "⌕" !important;
    color: #fff !important;
    opacity: .11 !important;
    font-size: clamp(8rem, 17vw, 13rem) !important;
    font-weight: 800;
    right: 6% !important;
}
.fi-eyebrow {
    color: #b9d0ff !important;
    font-size: .72rem !important;
    letter-spacing: 2.2px !important;
}
.fi-hero h1 {
    color: #fff !important;
    font-size: clamp(2.15rem, 4.5vw, 3.45rem) !important;
    letter-spacing: -2px !important;
    max-width: 760px;
}
.fi-hero p {
    color: rgba(255,255,255,.78) !important;
    font-size: 1rem !important;
    max-width: 650px;
}
.fi-section-title {
    font-size: 1.45rem !important;
    letter-spacing: -.7px !important;
}
.fi-section-subtitle { color: #778397 !important; }
.fi-stat {
    background: #fff !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    box-shadow: var(--shadow) !important;
    padding: 1.25rem 1.4rem !important;
}
.fi-stat:hover {
    transform: translateY(-3px);
    box-shadow: 0 13px 30px rgba(23,32,51,.08) !important;
}
.fi-stat-label { color: #7a8495 !important; font-size: .82rem !important; }
.fi-stat-value { color: #172033 !important; font-size: 2.05rem !important; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #fff !important;
    border: 1px solid #e9edf3 !important;
    border-radius: 18px !important;
    box-shadow: 0 5px 20px rgba(23,32,51,.035) !important;
    backdrop-filter: none !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 10px 28px rgba(23,32,51,.07) !important;
}
div[data-testid="stForm"] {
    background: #fff !important;
    border: 1px solid #e9edf3 !important;
    border-radius: 18px !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stMetric"] {
    background: #fff !important;
    border: 1px solid #e9edf3 !important;
    border-radius: 17px !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stMetricLabel"] { color: #778397 !important; }
[data-testid="stMetricValue"] { color: #172033 !important; }
.fi-chip {
    padding: 6px 11px !important;
    font-size: .66rem !important;
    letter-spacing: .7px !important;
}
.fi-lost { background: #fff0ed !important; color: #c04436 !important; }
.fi-found { background: #e9f8ef !important; color: #16834a !important; }
.fi-open { background: #edf3ff !important; color: #315fe8 !important; }
.fi-resolved { background: #f0f2f5 !important; color: #687386 !important; }
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] input {
    background: #fff !important;
    border: 1px solid #dfe5ee !important;
    border-radius: 11px !important;
    min-height: 2.8rem;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #7898f4 !important;
    box-shadow: 0 0 0 3px rgba(49,95,232,.1) !important;
}
.stButton > button, .stFormSubmitButton > button {
    border-radius: 11px !important;
    min-height: 2.75rem !important;
    font-weight: 700 !important;
    border: 1px solid #dfe5ee !important;
    transition: transform .18s ease, box-shadow .18s ease, background .18s ease !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(23,32,51,.09) !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: #315fe8 !important;
    color: #fff !important;
    border: 1px solid #315fe8 !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: #244bc4 !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    background: #f7f9fc !important;
    border: 1px solid transparent !important;
    border-radius: 11px !important;
    padding: 10px 12px !important;
    margin: 4px 0 !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: #edf3ff !important;
    border-color: #dce7ff !important;
}
[data-testid="stImage"] img {
    border-radius: 14px !important;
    object-fit: cover !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #e8edf4;
}
[data-testid="stTabs"] button[role="tab"] {
    border-radius: 10px 10px 0 0;
    font-weight: 650;
}
[data-testid="stAlert"] { border-radius: 13px !important; }
hr { border-color: #e8edf4 !important; }
@media (max-width: 800px) {
    .block-container { padding: 1rem 1rem 3rem !important; }
    .fi-hero { border-radius: 18px !important; }
    .fi-hero:after { display: none !important; }
    .fi-hero h1 { font-size: 2.2rem !important; }
}
@media (prefers-reduced-motion: reduce) {
    *, *:before, *:after {
        animation-duration: .01ms !important;
        transition-duration: .01ms !important;
    }
}


/* ============================================================
   REAL DARK THEME — follows Streamlit's selected Light/Dark mode
   ============================================================ */
body:has(#fi-dark-theme-marker),
body:has(#fi-dark-theme-marker),
body:has(#fi-dark-theme-marker),
body:has(#fi-dark-theme-marker),
body:has(#fi-dark-theme-marker) {
    color-scheme: dark;
    --ink: #edf2fb;
    --muted: #a7b3c7;
    --blue: #82a6ff;
    --blue-dark: #638df4;
    --border: #303b4d;
    --glass: #202a39;
    --shadow: 0 8px 28px rgba(0,0,0,.22);
    background: #111827 !important;
    color: #edf2fb !important;
}
body:has(#fi-dark-theme-marker) .stApp,
body:has(#fi-dark-theme-marker) .stApp,
body:has(#fi-dark-theme-marker) .stApp,
body:has(#fi-dark-theme-marker) {
    background: #111827 !important;
    color: #edf2fb !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stAppViewContainer"],
body:has(#fi-dark-theme-marker) [data-testid="stAppViewContainer"],
body:has(#fi-dark-theme-marker) [data-testid="stAppViewContainer"] {
    background: #111827 !important;
    color: #edf2fb !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stHeader"],
body:has(#fi-dark-theme-marker) [data-testid="stHeader"],
body:has(#fi-dark-theme-marker) [data-testid="stHeader"] {
    background: rgba(17,24,39,.88) !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stSidebar"],
body:has(#fi-dark-theme-marker) [data-testid="stSidebar"],
body:has(#fi-dark-theme-marker) [data-testid="stSidebar"] {
    background: #182231 !important;
    border-right: 1px solid #2b3748 !important;
    color: #edf2fb !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"],
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"] p,
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"] li,
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"] strong,
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"] em,
body:has(#fi-dark-theme-marker) label,
body:has(#fi-dark-theme-marker) .stMarkdown,
body:has(#fi-dark-theme-marker) .stText,
body:has(#fi-dark-theme-marker) [data-testid="stCaptionContainer"],
body:has(#fi-dark-theme-marker) [data-testid="stWidgetLabel"],
body:has(#fi-dark-theme-marker) [data-testid="stForm"] label,
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"],
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"] p,
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"] li,
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"] strong,
body:has(#fi-dark-theme-marker) label,
body:has(#fi-dark-theme-marker) [data-testid="stCaptionContainer"],
body:has(#fi-dark-theme-marker) [data-testid="stWidgetLabel"],
body:has(#fi-dark-theme-marker) [data-testid="stMarkdownContainer"],
body:has(#fi-dark-theme-marker) label {
    color: #dce5f3 !important;
}
body:has(#fi-dark-theme-marker) h1,
body:has(#fi-dark-theme-marker) h2,
body:has(#fi-dark-theme-marker) h3,
body:has(#fi-dark-theme-marker) h4,
body:has(#fi-dark-theme-marker) h1,
body:has(#fi-dark-theme-marker) h2,
body:has(#fi-dark-theme-marker) h3,
body:has(#fi-dark-theme-marker) h4 {
    color: #f3f6fc !important;
}
body:has(#fi-dark-theme-marker) .fi-hero,
body:has(#fi-dark-theme-marker) .fi-hero,
body:has(#fi-dark-theme-marker) .fi-hero {
    background: linear-gradient(115deg,#17263b 0%,#1c3558 58%,#244b91 100%) !important;
    border: 1px solid #34445d !important;
}
body:has(#fi-dark-theme-marker) .fi-hero h1,
body:has(#fi-dark-theme-marker) .fi-hero p,
body:has(#fi-dark-theme-marker) .fi-eyebrow,
body:has(#fi-dark-theme-marker) .fi-hero h1,
body:has(#fi-dark-theme-marker) .fi-hero p,
body:has(#fi-dark-theme-marker) .fi-eyebrow {
    color: #f4f7ff !important;
}
body:has(#fi-dark-theme-marker) .fi-hero p,
body:has(#fi-dark-theme-marker) .fi-hero p { color: #c4d1e5 !important; }
body:has(#fi-dark-theme-marker) .fi-stat,
body:has(#fi-dark-theme-marker) div[data-testid="stVerticalBlockBorderWrapper"],
body:has(#fi-dark-theme-marker) div[data-testid="stForm"],
body:has(#fi-dark-theme-marker) [data-testid="stMetric"],
body:has(#fi-dark-theme-marker) .fi-stat,
body:has(#fi-dark-theme-marker) div[data-testid="stVerticalBlockBorderWrapper"],
body:has(#fi-dark-theme-marker) div[data-testid="stForm"],
body:has(#fi-dark-theme-marker) [data-testid="stMetric"],
body:has(#fi-dark-theme-marker) div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #202b3a !important;
    border-color: #344154 !important;
    box-shadow: 0 8px 24px rgba(0,0,0,.18) !important;
    color: #e7edf7 !important;
}
body:has(#fi-dark-theme-marker) .fi-stat-label,
body:has(#fi-dark-theme-marker) .fi-muted,
body:has(#fi-dark-theme-marker) .fi-section-subtitle,
body:has(#fi-dark-theme-marker) [data-testid="stMetricLabel"],
body:has(#fi-dark-theme-marker) [data-testid="stCaptionContainer"],
body:has(#fi-dark-theme-marker) .fi-stat-label,
body:has(#fi-dark-theme-marker) .fi-muted,
body:has(#fi-dark-theme-marker) .fi-section-subtitle,
body:has(#fi-dark-theme-marker) [data-testid="stMetricLabel"],
body:has(#fi-dark-theme-marker) [data-testid="stCaptionContainer"] {
    color: #aebbd0 !important;
}
body:has(#fi-dark-theme-marker) .fi-stat-value,
body:has(#fi-dark-theme-marker) [data-testid="stMetricValue"],
body:has(#fi-dark-theme-marker) .fi-stat-value,
body:has(#fi-dark-theme-marker) [data-testid="stMetricValue"] {
    color: #f3f6fc !important;
}
body:has(#fi-dark-theme-marker) div[data-testid="stTextInput"] input,
body:has(#fi-dark-theme-marker) div[data-testid="stTextArea"] textarea,
body:has(#fi-dark-theme-marker) div[data-testid="stDateInput"] input,
body:has(#fi-dark-theme-marker) [data-baseweb="select"] > div,
body:has(#fi-dark-theme-marker) [data-baseweb="input"] input,
body:has(#fi-dark-theme-marker) [data-baseweb="textarea"] textarea,
body:has(#fi-dark-theme-marker) div[data-testid="stTextInput"] input,
body:has(#fi-dark-theme-marker) div[data-testid="stTextArea"] textarea,
body:has(#fi-dark-theme-marker) div[data-testid="stDateInput"] input,
body:has(#fi-dark-theme-marker) [data-baseweb="select"] > div,
body:has(#fi-dark-theme-marker) [data-baseweb="input"] input,
body:has(#fi-dark-theme-marker) [data-baseweb="textarea"] textarea {
    background: #151e2b !important;
    color: #f0f4fb !important;
    border-color: #435168 !important;
}
body:has(#fi-dark-theme-marker) input::placeholder,
body:has(#fi-dark-theme-marker) textarea::placeholder,
body:has(#fi-dark-theme-marker) input::placeholder,
body:has(#fi-dark-theme-marker) textarea::placeholder {
    color: #8998ad !important;
    opacity: 1 !important;
}
body:has(#fi-dark-theme-marker) [data-baseweb="select"] *,
body:has(#fi-dark-theme-marker) [role="listbox"],
body:has(#fi-dark-theme-marker) [role="option"],
body:has(#fi-dark-theme-marker) [data-baseweb="select"] *,
body:has(#fi-dark-theme-marker) [role="listbox"],
body:has(#fi-dark-theme-marker) [role="option"] {
    color: #e7edf7 !important;
}
body:has(#fi-dark-theme-marker) [role="listbox"],
body:has(#fi-dark-theme-marker) [role="option"],
body:has(#fi-dark-theme-marker) [role="listbox"],
body:has(#fi-dark-theme-marker) [role="option"] {
    background: #202b3a !important;
}
body:has(#fi-dark-theme-marker) .stButton > button,
body:has(#fi-dark-theme-marker) .stFormSubmitButton > button,
body:has(#fi-dark-theme-marker) .stButton > button,
body:has(#fi-dark-theme-marker) .stFormSubmitButton > button {
    background: #293649 !important;
    color: #f0f4fb !important;
    border-color: #46546a !important;
}
body:has(#fi-dark-theme-marker) .stButton > button[kind="primary"],
body:has(#fi-dark-theme-marker) .stFormSubmitButton > button[kind="primary"],
body:has(#fi-dark-theme-marker) .stButton > button[kind="primary"],
body:has(#fi-dark-theme-marker) .stFormSubmitButton > button[kind="primary"] {
    background: #416fe8 !important;
    color: #fff !important;
    border-color: #416fe8 !important;
}
body:has(#fi-dark-theme-marker) .fi-chip,
body:has(#fi-dark-theme-marker) .fi-chip { background: #354154 !important; color: #e1e9f5 !important; }
body:has(#fi-dark-theme-marker) .fi-lost,
body:has(#fi-dark-theme-marker) .fi-lost { background: #512d31 !important; color: #ffb9b2 !important; }
body:has(#fi-dark-theme-marker) .fi-found,
body:has(#fi-dark-theme-marker) .fi-found { background: #1f4538 !important; color: #a8ebc8 !important; }
body:has(#fi-dark-theme-marker) .fi-open,
body:has(#fi-dark-theme-marker) .fi-open { background: #263e68 !important; color: #b9d0ff !important; }
body:has(#fi-dark-theme-marker) .fi-resolved,
body:has(#fi-dark-theme-marker) .fi-resolved { background: #394354 !important; color: #c5cfdd !important; }
body:has(#fi-dark-theme-marker) [data-testid="stTabs"] [data-baseweb="tab-list"],
body:has(#fi-dark-theme-marker) [data-testid="stTabs"] [data-baseweb="tab-list"] {
    border-color: #344154 !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stTabs"] button[role="tab"],
body:has(#fi-dark-theme-marker) [data-testid="stTabs"] button[role="tab"] {
    color: #cbd6e6 !important;
}
body:has(#fi-dark-theme-marker) hr,
body:has(#fi-dark-theme-marker) hr { border-color: #344154 !important; }
body:has(#fi-dark-theme-marker) [data-testid="stAlert"],
body:has(#fi-dark-theme-marker) [data-testid="stAlert"] {
    background: #202b3a !important;
    color: #e7edf7 !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stSidebar"] [role="radiogroup"] label,
body:has(#fi-dark-theme-marker) [data-testid="stSidebar"] [role="radiogroup"] label {
    background: #202b3a !important;
    color: #dce5f3 !important;
    border-color: #344154 !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stSidebar"] [role="radiogroup"] label:hover,
body:has(#fi-dark-theme-marker) [data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: #293b55 !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stCheckbox"] label,
body:has(#fi-dark-theme-marker) [data-testid="stCheckbox"] label {
    color: #e0e8f4 !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stImage"] img,
body:has(#fi-dark-theme-marker) [data-testid="stImage"] img {
    border: 1px solid #344154;
}


/* Dark-mode contrast fixes for Streamlit native widgets and tooltips */
body:has(#fi-dark-theme-marker) [data-testid="stExpander"],
body:has(#fi-dark-theme-marker) [data-testid="stExpander"] details,
body:has(#fi-dark-theme-marker) [data-testid="stExpander"] summary,
body:has(#fi-dark-theme-marker) [data-testid="stExpander"] summary:hover {
    background: #182638 !important;
    color: #edf3ff !important;
    border-color: #34465f !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stExpander"] summary *,
body:has(#fi-dark-theme-marker) [data-testid="stExpander"] summary p,
body:has(#fi-dark-theme-marker) [data-testid="stExpander"] summary span {
    color: #edf3ff !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stTooltipContent"],
body:has(#fi-dark-theme-marker) [role="tooltip"],
body:has(#fi-dark-theme-marker) [data-baseweb="tooltip"] {
    background: #263449 !important;
    color: #f3f6fc !important;
    border: 1px solid #455873 !important;
    box-shadow: 0 8px 24px rgba(0,0,0,.35) !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stTooltipContent"] *,
body:has(#fi-dark-theme-marker) [role="tooltip"] *,
body:has(#fi-dark-theme-marker) [data-baseweb="tooltip"] * {
    color: #f3f6fc !important;
}
body:has(#fi-dark-theme-marker) a,
body:has(#fi-dark-theme-marker) a:visited {
    color: #82b2ff !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stCaptionContainer"],
body:has(#fi-dark-theme-marker) [data-testid="stCaptionContainer"] *,
body:has(#fi-dark-theme-marker) [data-testid="stWidgetLabel"] *,
body:has(#fi-dark-theme-marker) small {
    color: #b9c7da !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stTextInput"] input,
body:has(#fi-dark-theme-marker) [data-testid="stTextArea"] textarea {
    caret-color: #ffffff !important;
    -webkit-text-fill-color: #f0f4fb !important;
}
body:has(#fi-dark-theme-marker) [data-testid="stPopover"],
body:has(#fi-dark-theme-marker) [data-testid="stDialog"] {
    color: #edf3ff !important;
}

</style>
""", unsafe_allow_html=True)


def render_theme_toggle():
    """Render the app's Light/Dark selector inside the Settings menu."""
    st.markdown("**Appearance**")
    theme = st.radio(
        "Choose theme",
        ["Light", "Dark"],
        horizontal=True,
        key="fi_theme_mode",
        label_visibility="collapsed",
    )
    if theme == "Dark":
        st.markdown(
            '<div id="fi-dark-theme-marker" style="display:none"></div>',
            unsafe_allow_html=True,
        )


# ============================================================
# SUPABASE AND AUTHENTICATION
# ============================================================

def get_setting(section, key, env_name=None):
    try:
        value = st.secrets[section][key]
        if value:
            return value
    except Exception:
        pass

    return os.getenv(env_name or key.upper())


def supabase_client():
    if st.session_state.get("_supabase_client") is not None:
        return st.session_state["_supabase_client"]

    url = get_setting("supabase", "url", "SUPABASE_URL")
    key = get_setting("supabase", "anon_key", "SUPABASE_ANON_KEY")

    if not url or not key:
        return None

    client = create_client(url, key)
    st.session_state["_supabase_client"] = client
    return client


def friendly_error(exc):
    message = str(exc)

    if "Invalid login credentials" in message:
        return "Email or password is incorrect."

    if "Email not confirmed" in message:
        return "Please confirm your email using the link sent by Supabase."

    if "row-level security" in message.lower() or "permission denied" in message.lower():
        return "Permission denied. Please check your Supabase database policies."

    return message[:400]


def get_user():
    return st.session_state.get("user")


def get_profile(client, user_id):
    result = (
        client.table("profiles")
        .select("user_id, username")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def save_username(client, user_id, username):
    clean = username.strip().lstrip("@")
    if not (3 <= len(clean) <= 20):
        raise ValueError("Username must be 3–20 characters.")
    if not clean.replace("_", "").replace(".", "").isalnum():
        raise ValueError("Use only letters, numbers, dots and underscores.")
    client.table("profiles").upsert({
        "user_id": user_id,
        "username": clean,
    }, on_conflict="user_id").execute()


def start_listing_conversation(client, listing, user):
    existing = (
        client.table("conversations")
        .select("id")
        .eq("listing_id", str(listing["id"]))
        .eq("starter_id", user["id"])
        .limit(1)
        .execute()
    )
    if existing.data:
        conversation_id = existing.data[0]["id"]
    else:
        created = client.table("conversations").insert({
            "listing_id": str(listing["id"]),
            "starter_id": user["id"],
            "owner_id": listing["owner_id"],
        }).execute()
        conversation_id = created.data[0]["id"]
    st.session_state["open_conversation_id"] = conversation_id
    st.session_state["main_navigation"] = "Messages"
    st.rerun()


def do_logout():
    client = st.session_state.get("_supabase_client")

    try:
        if client:
            client.auth.sign_out()
    except Exception:
        pass

    for key in (
        "user",
        "page",
        "confirm_delete_id",
        "_supabase_client",
        "main_navigation",
    ):
        st.session_state.pop(key, None)

    st.rerun()

# ============================================================
# IMAGE UPLOADS AND DATABASE FUNCTIONS
# ============================================================

def upload_image(client: Client, uploaded_file, user_id: str):
    if uploaded_file is None:
        return None

    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((1600, 1600))

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=88, optimize=True)

    path = f"{user_id}/{os.urandom(8).hex()}.jpg"

    client.storage.from_("findit-images").upload(
        path,
        buffer.getvalue(),
        file_options={
            "content-type": "image/jpeg",
            "upsert": "false",
        },
    )

    return client.storage.from_("findit-images").get_public_url(path)


def fetch_listings(client: Client):
    result = (
        client.table("listings")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def fetch_claims(client: Client):
    result = (
        client.table("claims")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


# ============================================================
# REUSABLE UI COMPONENTS
# ============================================================

def render_brand():
    st.markdown(
        '<div class="fi-brand"><span class="fi-logo">🔎</span> FindIt</div>',
        unsafe_allow_html=True,
    )


def render_hero(eyebrow, title, description):
    st.markdown(f"""
    <div class="fi-hero">
        <div class="fi-eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


def render_listing_card(item, show_claim_button=False, client=None, user=None):
    listing_type = item.get("listing_type", "found")
    status = item.get("status", "open")

    type_label = "LOST ITEM" if listing_type == "lost" else "FOUND ITEM"
    type_class = "fi-lost" if listing_type == "lost" else "fi-found"
    status_class = "fi-open" if status == "open" else "fi-resolved"

    with st.container(border=True):
        # Larger image area
        left, right = st.columns([1.25, 1.8], gap="large")

        with left:
            if item.get("image_url"):
                st.image(
                    item["image_url"],
                    use_container_width=True,
                )
            else:
                st.markdown(
                    '<div style="height:240px;display:flex;align-items:center;'
                    'justify-content:center;background:rgba(238,244,253,.8);'
                    'border:1px dashed #cbd8ec;border-radius:17px;'
                    'font-size:3rem;">📦</div>',
                    unsafe_allow_html=True,
                )

        with right:
            st.markdown(
                f'<span class="fi-chip {type_class}">{type_label}</span> '
                f'<span class="fi-chip {status_class}">{status.upper()}</span>',
                unsafe_allow_html=True,
            )

            st.markdown(f"### {item.get('title', 'Untitled item')}")
            st.write(item.get("description") or "No description provided.")

            meta1, meta2 = st.columns(2)

            with meta1:
                st.caption(f"**Category**  \n{item.get('category', 'Other')}")
                st.caption(f"**Colour**  \n{item.get('color') or 'Not specified'}")

            with meta2:
                st.caption(f"**Location**  \n{item.get('location', 'Not specified')}")
                st.caption(f"**Date**  \n{item.get('event_date') or 'Not specified'}")

            if show_claim_button and client and user:
                if item.get("owner_id") != user["id"] and status == "open":
                    if st.button(
                        "💬 Message owner",
                        key=f"dm_listing_{item['id']}",
                        use_container_width=True,
                    ):
                        try:
                            start_listing_conversation(client, item, user)
                        except Exception as exc:
                            st.error("Couldn't start this conversation. " + friendly_error(exc))

                    with st.form(f"claim_{item['id']}"):
                        message = st.text_area(
                            "Message to the owner",
                            placeholder="Describe a detail that helps verify ownership. Keep private details to yourself.",
                            key=f"claim_message_{item['id']}",
                        )

                        submitted = st.form_submit_button(
                            "Request to connect",
                            type="primary",
                            use_container_width=True,
                        )

                        if submitted:
                            try:
                                client.table("claims").insert({
                                    "listing_id": item["id"],
                                    "claimant_id": user["id"],
                                    "message": message.strip() or "I'd like to discuss this item.",
                                }).execute()

                                st.success("Request sent to the listing owner.")
                                st.rerun()

                            except Exception as exc:
                                st.error(friendly_error(exc))


# ============================================================
# ADMINISTRATION
# ============================================================

ADMIN_EMAIL = "finditadmin092@gmail.com"


def is_admin_user(client, user):
    """Check the admin role stored in Supabase, never from browser input."""
    try:
        result = (
            client.table("admin_users")
            .select("user_id")
            .eq("user_id", user["id"])
            .limit(1)
            .execute()
        )
        return bool(result.data)
    except Exception:
        return False


def admin_service_client():
    """Server-side Supabase admin client. Never expose this key to the browser."""
    url = get_setting("supabase", "url", "SUPABASE_URL")
    service_key = get_setting(
        "supabase", "service_role_key", "SUPABASE_SERVICE_ROLE_KEY"
    )
    if not url or not service_key:
        return None
    return create_client(url, service_key)


def write_admin_log(admin_client, admin_user, action, reason,
                    target_user_id=None, target_listing_id=None, details=None):
    admin_client.table("admin_action_logs").insert({
        "admin_user_id": admin_user["id"],
        "action": action,
        "target_user_id": target_user_id,
        "target_listing_id": (
            str(target_listing_id) if target_listing_id is not None else None
        ),
        "reason": reason.strip(),
        "details": details or {},
    }).execute()


def render_admin_panel(client, user):
    render_hero(
        "RESTRICTED AREA",
        "FindIt administration",
        "Review community activity, moderate listings, and manage user access.",
    )

    admin_client = admin_service_client()
    if admin_client is None:
        st.error(
            "Admin actions are not configured yet. Add "
            "SUPABASE_SERVICE_ROLE_KEY to Streamlit Community Cloud secrets "
            "as described in supabase_admin_setup.sql."
        )
        st.info(
            "The service-role key is private. Never put it in app.py, GitHub, "
            "or a public message."
        )
        return

    try:
        all_listings = (
            admin_client.table("listings")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        ).data or []
        all_claims = (
            admin_client.table("claims")
            .select("*")
            .execute()
        ).data or []
        users_response = admin_client.auth.admin.list_users()
        auth_users = getattr(users_response, "users", users_response) or []
    except Exception as exc:
        st.error("Could not load admin data: " + friendly_error(exc))
        return

    active_listings = [x for x in all_listings if x.get("status") == "open"]
    suspended_users = [
        u for u in auth_users
        if getattr(u, "banned_until", None)
    ]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Registered accounts", len(auth_users))
    m2.metric("All listings", len(all_listings))
    m3.metric("Open listings", len(active_listings))
    m4.metric("Claims", len(all_claims))

    st.divider()
    tab_listings, tab_users, tab_claims, tab_logs = st.tabs(
        ["Listing moderation", "User management", "Claims review", "Admin activity"]
    )

    with tab_listings:
        st.subheader("Community listings")
        search_listing = st.text_input(
            "Search listings",
            placeholder="Search by item title, description or location",
            key="admin_listing_search",
        ).strip().lower()

        filtered_listings = [
            item for item in all_listings
            if not search_listing or search_listing in " ".join(
                str(item.get(k) or "")
                for k in ("title", "description", "location", "category")
            ).lower()
        ]

        for item in filtered_listings:
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.markdown("**" + str(item.get("title", "Untitled")) + "**")
                    st.caption(
                        f"{item.get('listing_type', 'item').upper()} · "
                        f"{item.get('status', 'unknown').upper()} · "
                        f"{item.get('location', 'No location')}"
                    )
                    st.write(item.get("description") or "No description.")
                    st.caption(
                        f"Owner ID: {item.get('owner_id')} · "
                        f"Listing ID: {item.get('id')}"
                    )
                with right:
                    if item.get("image_url"):
                        st.image(item["image_url"], use_container_width=True)

                with st.expander("Moderate this listing"):
                    reason = st.text_input(
                        "Reason for moderation",
                        key=f"listing_reason_{item.get('id')}",
                        placeholder="Explain why action is being taken",
                    )
                    a1, a2 = st.columns(2)
                    with a1:
                        if st.button(
                            "Unlist / resolve",
                            key=f"admin_unlist_{item.get('id')}",
                            use_container_width=True,
                        ):
                            if len(reason.strip()) < 3:
                                st.warning("Enter a reason (at least 3 characters).")
                            else:
                                try:
                                    admin_client.table("listings").update(
                                        {"status": "resolved"}
                                    ).eq("id", item["id"]).execute()
                                    write_admin_log(
                                        admin_client, user, "listing_unlisted",
                                        reason, target_user_id=item.get("owner_id"),
                                        target_listing_id=item.get("id")
                                    )
                                    st.success("Listing unlisted.")
                                    st.rerun()
                                except Exception as exc:
                                    st.error(friendly_error(exc))
                    with a2:
                        if st.button(
                            "Delete listing",
                            key=f"admin_delete_{item.get('id')}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            if len(reason.strip()) < 3:
                                st.warning("Enter a reason (at least 3 characters).")
                            else:
                                try:
                                    admin_client.table("listings").delete().eq(
                                        "id", item["id"]
                                    ).execute()
                                    write_admin_log(
                                        admin_client, user, "listing_deleted",
                                        reason, target_user_id=item.get("owner_id"),
                                        target_listing_id=item.get("id")
                                    )
                                    st.success(
                                        "Listing deleted. Its related claims may "
                                        "also be removed by your database cascade."
                                    )
                                    st.rerun()
                                except Exception as exc:
                                    st.error(friendly_error(exc))

        if not filtered_listings:
            st.info("No listings match that search.")

    with tab_users:
        st.subheader("Account management")
        st.caption(
            "Suspensions are applied through Supabase Auth. A permanent ban "
            "uses a very long ban duration and can still be reversed by an admin."
        )

        user_rows = []
        for auth_user in auth_users:
            uid = getattr(auth_user, "id", None)
            email = getattr(auth_user, "email", None) or "(no email)"
            banned_until = getattr(auth_user, "banned_until", None)
            user_rows.append((email, uid, banned_until))

        user_rows.sort(key=lambda row: row[0].lower())
        labels = [
            f"{email} — {uid}" for email, uid, _ in user_rows
            if uid != user["id"]
        ]
        label_to_row = {
            f"{email} — {uid}": (email, uid, banned)
            for email, uid, banned in user_rows
            if uid != user["id"]
        }

        if not labels:
            st.info("No other user accounts were found.")
        else:
            selected_label = st.selectbox("Select an account", labels)
            selected_email, selected_uid, selected_banned = label_to_row[
                selected_label
            ]
            st.write("**Account:**", selected_email)
            st.write(
                "**Current access:**",
                "Suspended" if selected_banned else "Not suspended",
            )

            reason = st.text_area(
                "Moderation reason",
                key="admin_user_reason",
                placeholder="Explain the reason for this account action",
            )
            duration = st.selectbox(
                "Suspension duration",
                ["24 hours", "7 days", "30 days", "Permanent (reversible by admin)"],
            )

            b1, b2 = st.columns(2)
            with b1:
                if st.button(
                    "Suspend account",
                    type="primary",
                    use_container_width=True,
                ):
                    if len(reason.strip()) < 3:
                        st.warning("Enter a reason (at least 3 characters).")
                    else:
                        ban_values = {
                            "24 hours": "24h",
                            "7 days": "168h",
                            "30 days": "720h",
                            "Permanent (reversible by admin)": "876000h",
                        }
                        try:
                            admin_client.auth.admin.update_user_by_id(
                                selected_uid,
                                {"ban_duration": ban_values[duration]},
                            )
                            write_admin_log(
                                admin_client, user, "account_suspended",
                                reason, target_user_id=selected_uid,
                                details={"duration": duration}
                            )
                            st.success(f"{selected_email} has been suspended.")
                            st.rerun()
                        except Exception as exc:
                            st.error(friendly_error(exc))
            with b2:
                if st.button(
                    "Restore account access",
                    use_container_width=True,
                ):
                    if len(reason.strip()) < 3:
                        st.warning("Enter a reason for restoring access.")
                    else:
                        try:
                            admin_client.auth.admin.update_user_by_id(
                                selected_uid,
                                {"ban_duration": "none"},
                            )
                            write_admin_log(
                                admin_client, user, "account_restored",
                                reason, target_user_id=selected_uid
                            )
                            st.success(f"Access restored for {selected_email}.")
                            st.rerun()
                        except Exception as exc:
                            st.error(friendly_error(exc))

    with tab_claims:
        st.subheader("Claims review")
        if not all_claims:
            st.info("There are no claims to review.")
        for claim in all_claims:
            listing = next(
                (item for item in all_listings if item.get("id") == claim.get("listing_id")),
                None,
            )
            listing_title = listing.get("title", "Deleted listing") if listing else "Deleted listing"
            claim_status = claim.get("status", "pending")
            with st.container(border=True):
                st.markdown(f"**{listing_title}** · {claim_status.upper()}")
                st.write(claim.get("message") or "No message provided.")
                st.caption(
                    f"Claim ID: {claim.get('id')} · "
                    f"Listing ID: {claim.get('listing_id')} · "
                    f"Claimant ID: {claim.get('claimant_id')}"
                )
                if claim_status == "pending":
                    decision = st.selectbox(
                        "Admin decision",
                        ["pending", "accepted", "rejected"],
                        key=f"admin_claim_decision_{claim.get('id')}",
                    )
                    if st.button(
                        "Save claim decision",
                        key=f"admin_claim_save_{claim.get('id')}",
                    ):
                        try:
                            admin_client.table("claims").update(
                                {"status": decision}
                            ).eq("id", claim["id"]).execute()
                            write_admin_log(
                                admin_client, user, "claim_moderated",
                                "Admin changed claim status",
                                target_user_id=claim.get("claimant_id"),
                                details={
                                    "claim_id": str(claim.get("id")),
                                    "new_status": decision,
                                },
                            )
                            st.success("Claim status updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(friendly_error(exc))

    with tab_logs:
        st.subheader("Recent admin activity")
        try:
            logs = (
                admin_client.table("admin_action_logs")
                .select("*")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            ).data or []
            if not logs:
                st.info("No moderation actions have been recorded yet.")
            else:
                st.dataframe(logs, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error("Could not load the audit log: " + friendly_error(exc))


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    client = supabase_client()

    # Configuration check
    if client is None:
        render_brand()

        render_hero(
            "COMMUNITY LOST & FOUND",
            "A little help goes a long way.",
            "Find missing belongings, report items you've found, and help return things to their owners.",
        )

        st.error(
            "FindIt is not configured. Add your Supabase URL and anon key "
            "to Streamlit Community Cloud secrets."
        )

        st.code(
            '[supabase]\n'
            'url = "https://YOUR-PROJECT.supabase.co"\n'
            'anon_key = "YOUR-SUPABASE-ANON-KEY"',
            language="toml",
        )

        st.stop()

    user = get_user()

    # ========================================================
    # LOGIN AND SIGNUP
    # ========================================================

    if not user:
        with st.sidebar.expander("⚙️ Settings", expanded=False):
            render_theme_toggle()

        render_brand()

        render_hero(
            "LOST SOMETHING? FOUND SOMETHING?",
            "Let's help it find its way home.",
            "A community space to report lost and found items, discover possible matches, and connect with the right person.",
        )

        login_col, signup_col = st.columns(2, gap="large")

        with login_col:
            st.markdown("## Welcome back")
            st.markdown(
                '<p class="fi-muted">Log in to manage your listings and requests.</p>',
                unsafe_allow_html=True,
            )

            with st.form("login_form"):
                email = st.text_input("Email address", key="login_email").strip().lower()
                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                )
                submitted = st.form_submit_button(
                    "Log in",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    try:
                        response = client.auth.sign_in_with_password({
                            "email": email,
                            "password": password,
                        })

                        st.session_state.user = {
                            "id": response.user.id,
                            "email": response.user.email,
                        }

                        st.rerun()

                    except Exception as exc:
                        st.error(friendly_error(exc))

        with signup_col:
            st.markdown("## New to FindIt?")
            st.markdown(
                '<p class="fi-muted">Create an account to publish reports and contact listing owners.</p>',
                unsafe_allow_html=True,
            )

            with st.form("signup_form"):
                new_username = st.text_input(
                    "Unique username",
                    placeholder="e.g. Satyajit007",
                    help="3–20 characters. Letters, numbers, dots and underscores.",
                ).strip().lstrip("@")

                new_email = st.text_input(
                    "Email address",
                    key="signup_email",
                ).strip().lower()

                new_password = st.text_input(
                    "Password (at least 8 characters)",
                    type="password",
                    key="signup_password",
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                )

                submitted = st.form_submit_button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    if not (3 <= len(new_username) <= 20) or not new_username.replace("_", "").replace(".", "").isalnum():
                        st.error("Choose a username 3–20 characters long using letters, numbers, dots or underscores.")

                    elif not new_email or "@" not in new_email:
                        st.error("Enter a valid email address.")

                    elif len(new_password) < 8:
                        st.error("Use a password with at least 8 characters.")

                    elif new_password != confirm_password:
                        st.error("The passwords do not match.")

                    else:
                        try:
                            response = client.auth.sign_up({
                                "email": new_email,
                                "password": new_password,
                                "options": {
                                    "data": {"username": new_username}
                                },
                            })

                            if response.session:
                                st.session_state.user = {
                                    "id": response.user.id,
                                    "email": response.user.email,
                                }
                                st.success("Account created.")
                                st.rerun()
                            else:
                                st.success(
                                    "Account created. Check your email for the confirmation link, then log in."
                                )

                        except Exception as exc:
                            st.error(friendly_error(exc))

        st.caption(
            "FindIt uses Supabase authentication to protect your account. "
            "Never share your password."
        )

        st.stop()

    # Ensure every account has a unique public username.
    try:
        profile = get_profile(client, user["id"])
    except Exception as exc:
        st.error("Username setup needs the Supabase messaging SQL migration. " + friendly_error(exc))
        st.stop()

    if not profile or not profile.get("username"):
        render_brand()
        render_hero(
            "CHOOSE YOUR ID",
            "Create your FindIt username",
            "Pick a unique username so other members can recognise you without sharing personal contact details.",
        )
        with st.form("choose_username_form"):
            desired_username = st.text_input(
                "Unique username",
                placeholder="e.g. Satyajit007",
                help="3–20 characters. Letters, numbers, dots and underscores.",
            )
            submitted_username = st.form_submit_button(
                "Save username",
                type="primary",
                use_container_width=True,
            )
            if submitted_username:
                try:
                    save_username(client, user["id"], desired_username)
                    st.success("Username saved!")
                    st.rerun()
                except Exception as exc:
                    message = str(exc)
                    if "duplicate" in message.lower() or "unique" in message.lower():
                        st.error("That username is already taken. Try another one.")
                    else:
                        st.error(message)
        st.stop()

    user["username"] = profile["username"]

    # Determine admin status from the protected Supabase role table.
    admin_mode = is_admin_user(client, user)

    # ========================================================
    # SIDEBAR NAVIGATION
    # ========================================================

    with st.sidebar:
        render_brand()

        st.markdown(
            '<p class="fi-muted">Your community lost & found space</p>',
            unsafe_allow_html=True,
        )

        st.divider()

        page = st.radio(
            "Navigation",
            [
                "Home & Search",
                "Report an item",
                "My dashboard",
                "Claims inbox",
                "Messages",
            ] + (["Admin panel"] if admin_mode else []),
            format_func=lambda x: {
                "Home & Search": "⌕   Explore items",
                "Report an item": "＋   Report an item",
                "My dashboard": "▦   My dashboard",
                "Claims inbox": "✉   Claims inbox",
                "Messages": "💬   Messages",
                "Admin panel": "⚙   Admin panel",
            }.get(x, x),
            label_visibility="collapsed",
            key="main_navigation",
        )

        st.divider()

        with st.expander("⚙️ Settings", expanded=False):
            render_theme_toggle()

            st.divider()
            st.markdown("**ACCOUNT**")
            st.caption(user.get("email", "Signed in"))
            st.caption(f"Current username: **@{user.get('username', 'member')}**")

            with st.form("change_username_form"):
                updated_username = st.text_input(
                    "Change username",
                    placeholder="Enter a new unique username",
                    help="3–20 characters. Letters, numbers, dots and underscores. Usernames must be available.",
                ).strip().lstrip("@")
                change_username = st.form_submit_button(
                    "Update username",
                    use_container_width=True,
                )

                if change_username:
                    if updated_username.lower() == user.get("username", "").lower():
                        st.info("That's already your current username.")
                    else:
                        try:
                            save_username(client, user["id"], updated_username)
                            user["username"] = updated_username
                            st.session_state["user"] = user
                            st.success(f"Username changed to @{updated_username}.")
                            st.rerun()
                        except Exception as exc:
                            message = str(exc).lower()
                            if "duplicate" in message or "unique" in message or "already exists" in message:
                                st.error("That username is already taken. Please choose an available one.")
                            elif "username must" in message or "use only" in message:
                                st.error(str(exc))
                            else:
                                st.error("Couldn't update your username. " + friendly_error(exc))

            st.divider()
            st.caption(
                "Keep personal details private. Avoid posting full addresses, "
                "ID numbers or sensitive information."
            )

            if st.button("Log out", use_container_width=True):
                do_logout()

    # Load listings
    try:
        listings = fetch_listings(client)
    except Exception as exc:
        st.error("Couldn't load listings. " + friendly_error(exc))
        st.stop()

    open_listings = [
        x for x in listings
        if x.get("status") == "open"
    ]

    my_listings = [
        x for x in listings
        if x.get("owner_id") == user["id"]
    ]

    # ========================================================
    # HOME AND SEARCH
    # ========================================================

    if page == "Home & Search":
        render_hero(
            "FIND IT. RETURN IT.",
            "Lost something? Start here.",
            "Search community reports, discover possible matches, or share an item you've found. Every small detail can help.",
        )

        stat1, stat2, stat3 = st.columns(3)

        with stat1:
            st.markdown(
                f'<div class="fi-stat"><div class="fi-stat-label">Open listings</div>'
                f'<div class="fi-stat-value">{len(open_listings)}</div></div>',
                unsafe_allow_html=True,
            )

        with stat2:
            st.markdown(
                f'<div class="fi-stat"><div class="fi-stat-label">Your reports</div>'
                f'<div class="fi-stat-value">{len(my_listings)}</div></div>',
                unsafe_allow_html=True,
            )

        with stat3:
            st.markdown(
                f'<div class="fi-stat"><div class="fi-stat-label">Community listings</div>'
                f'<div class="fi-stat-value">{len(listings)}</div></div>',
                unsafe_allow_html=True,
            )

        st.write("")

        st.markdown(
            '<div class="fi-section-title">Explore listings</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p class="fi-section-subtitle">Search and filter community reports to find what you are looking for.</p>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            qcol, typecol = st.columns([2.2, 1])

            with qcol:
                query = st.text_input(
                    "Search keywords",
                    placeholder="Try black wallet, blue bottle, library...",
                )

            with typecol:
                type_filter = st.selectbox(
                    "Report type",
                    ["All types", "Lost", "Found"],
                )

            f1, f2, f3 = st.columns([1.1, 1.4, 1])

            with f1:
                categories = ["All categories"] + sorted(
                    set(x.get("category", "Other") for x in listings)
                )

                category_filter = st.selectbox(
                    "Category",
                    categories,
                )

            with f2:
                location_filter = st.text_input(
                    "Location",
                    placeholder="Campus, library, bus stop...",
                )

            with f3:
                open_only = st.checkbox(
                    "Open listings only",
                    value=True,
                )

        filtered = []

        q = query.lower().strip()
        loc = location_filter.lower().strip()

        for item in listings:
            searchable = " ".join(
                str(item.get(k) or "")
                for k in [
                    "title",
                    "description",
                    "category",
                    "color",
                    "location",
                ]
            ).lower()

            if q and q not in searchable:
                continue

            if (
                type_filter != "All types"
                and item.get("listing_type") != type_filter.lower()
            ):
                continue

            if (
                category_filter != "All categories"
                and item.get("category") != category_filter
            ):
                continue

            if loc and loc not in str(item.get("location", "")).lower():
                continue

            if open_only and item.get("status") != "open":
                continue

            filtered.append(item)

        result_col, action_col = st.columns([3, 1])

        with result_col:
            st.markdown(f"**{len(filtered)} result(s) found**")

        with action_col:
            if st.button(
                "＋ Report an item",
                use_container_width=True,
            ):
                st.session_state["main_navigation"] = "Report an item"
                st.rerun()

        if not filtered:
            st.info(
                "No matching listings yet. Try a broader search or report the item."
            )

        for item in filtered:
            render_listing_card(
                item,
                show_claim_button=True,
                client=client,
                user=user,
            )

        # ----------------------------------------------------
        # POSSIBLE MATCHES
        # ----------------------------------------------------

        st.divider()

        st.markdown(
            '<div class="fi-section-title">Possible matches</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p class="fi-section-subtitle">Suggested lost and found pairs based on item details. '
            'Suggestions are not proof of ownership.</p>',
            unsafe_allow_html=True,
        )

        open_lost = [
            x for x in listings
            if x.get("listing_type") == "lost"
            and x.get("status") == "open"
            and x.get("owner_id") != user["id"]
        ]

        open_found = [
            x for x in listings
            if x.get("listing_type") == "found"
            and x.get("status") == "open"
            and x.get("owner_id") != user["id"]
        ]

        matches = []

        ignored = {
            "the", "a", "an", "and", "or", "with", "my",
            "is", "it", "of", "to", "in",
        }

        for lost in open_lost:
            for found in open_found:
                score = 0

                if (
                    lost.get("category")
                    and lost.get("category") == found.get("category")
                ):
                    score += 3

                if (
                    lost.get("color")
                    and found.get("color")
                    and lost["color"].lower() == found["color"].lower()
                ):
                    score += 2

                lost_words = set(
                    (
                        lost.get("title", "")
                        + " "
                        + lost.get("description", "")
                    ).lower().split()
                )

                found_words = set(
                    (
                        found.get("title", "")
                        + " "
                        + found.get("description", "")
                    ).lower().split()
                )

                score += min(
                    4,
                    len((lost_words & found_words) - ignored),
                )

                if (
                    lost.get("location")
                    and found.get("location")
                    and lost["location"].lower() == found["location"].lower()
                ):
                    score += 1

                if score >= 3:
                    matches.append((score, lost, found))

        matches.sort(key=lambda x: x[0], reverse=True)

        if not matches:
            st.info(
                "No strong matches found yet. New reports may reveal a match."
            )

        for score, lost, found in matches[:5]:
            with st.expander(
                f"Possible match · {lost['title']} ↔ {found['title']} · Score {score}"
            ):
                left, right = st.columns(2)

                with left:
                    st.markdown("**Lost report**")
                    render_listing_card(lost)

                with right:
                    st.markdown("**Found report**")
                    render_listing_card(found)

    # ========================================================
    # REPORT AN ITEM
    # ========================================================

    elif page == "Report an item":
        render_hero(
            "ADD TO THE COMMUNITY",
            "Report an item",
            "Share useful details to help someone recognise the item. Keep one or two identifying details private for verification.",
        )

        with st.container(border=True):
            with st.form("report_form", clear_on_submit=True):
                type_col, date_col = st.columns(2)

                with type_col:
                    listing_type = st.radio(
                        "What are you reporting?",
                        ["Lost item", "Found item"],
                        horizontal=True,
                    )

                with date_col:
                    event_date = st.date_input(
                        "Date lost or found",
                        value=date.today(),
                        max_value=date.today(),
                    )

                title = st.text_input(
                    "Item name",
                    placeholder="e.g. Black wireless earbuds case",
                )

                category = st.selectbox(
                    "Category",
                    [
                        "Electronics",
                        "Wallet / Cards",
                        "Keys",
                        "Bag",
                        "Clothing",
                        "Books / Stationery",
                        "Jewellery",
                        "Bottle / Container",
                        "Other",
                    ],
                )

                color = st.text_input(
                    "Colour or visible characteristics",
                    placeholder="e.g. matte black with a small blue sticker",
                )

                description = st.text_area(
                    "Description",
                    placeholder="Brand, size, distinctive marks, etc. Avoid sensitive numbers.",
                    height=140,
                )

                location = st.text_input(
                    "Where was it lost or found?",
                    placeholder="e.g. Block B library, near the main gate",
                )

                uploaded = st.file_uploader(
                    "Item photo (JPG, JPEG or PNG)",
                    type=["jpg", "jpeg", "png"],
                    help="A clear photo can make an item easier to recognise.",
                )

                if uploaded:
                    st.image(
                        uploaded,
                        caption="Image preview",
                        use_container_width=True,
                    )

                submitted = st.form_submit_button(
                    "Publish listing",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    if len(title.strip()) < 2:
                        st.error("Enter an item name.")

                    elif len(description.strip()) < 8:
                        st.error(
                            "Add a slightly more detailed description (at least 8 characters)."
                        )

                    elif len(location.strip()) < 2:
                        st.error("Enter the place where it was lost or found.")

                    else:
                        try:
                            image_url = (
                                upload_image(client, uploaded, user["id"])
                                if uploaded else None
                            )

                            payload = {
                                "owner_id": user["id"],
                                "listing_type": (
                                    "lost"
                                    if listing_type == "Lost item"
                                    else "found"
                                ),
                                "title": title.strip()[:100],
                                "category": category,
                                "color": color.strip()[:120],
                                "description": description.strip()[:1500],
                                "location": location.strip()[:200],
                                "event_date": event_date.isoformat(),
                                "image_url": image_url,
                                "status": "open",
                            }

                            client.table("listings").insert(payload).execute()

                            st.success("Your listing has been published!")
                            st.rerun()

                        except Exception as exc:
                            st.error(
                                "Could not publish the listing. "
                                + friendly_error(exc)
                            )

    # ========================================================
    # MY DASHBOARD — UNLIST / RELIST / DELETE
    # ========================================================

    elif page == "My dashboard":
        render_hero(
            "YOUR SPACE",
            "My dashboard",
            "Manage your reports, update their status, or remove listings you no longer need.",
        )

        mine = [
            x for x in listings
            if x.get("owner_id") == user["id"]
        ]

        open_mine = [
            x for x in mine
            if x.get("status") == "open"
        ]

        resolved_mine = [
            x for x in mine
            if x.get("status") != "open"
        ]

        s1, s2, s3 = st.columns(3)

        with s1:
            st.metric("All reports", len(mine))

        with s2:
            st.metric("Open", len(open_mine))

        with s3:
            st.metric("Resolved", len(resolved_mine))

        st.write("")

        if not mine:
            st.info(
                "You haven't published a listing yet. "
                "Use Report an item to create your first report."
            )

        for item in mine:
            item_id = item["id"]
            item_status = item.get("status", "open")

            with st.container(border=True):
                render_listing_card(item)

                st.caption(
                    f"Manage listing · Current status: {item_status.upper()}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if item_status == "open":
                        if st.button(
                            "Unlist item",
                            key=f"unlist_{item_id}",
                            use_container_width=True,
                        ):
                            try:
                                result = (
                                    client.table("listings")
                                    .update({"status": "resolved"})
                                    .eq("id", item_id)
                                    .eq("owner_id", user["id"])
                                    .select("id")
                                    .execute()
                                )

                                if result.data:
                                    st.success("Item unlisted successfully.")
                                    st.rerun()
                                else:
                                    st.warning(
                                        "The listing was not updated. Refresh and try again."
                                    )

                            except Exception as exc:
                                st.error(friendly_error(exc))

                    else:
                        if st.button(
                            "Relist item",
                            key=f"relist_{item_id}",
                            use_container_width=True,
                        ):
                            try:
                                result = (
                                    client.table("listings")
                                    .update({"status": "open"})
                                    .eq("id", item_id)
                                    .eq("owner_id", user["id"])
                                    .select("id")
                                    .execute()
                                )

                                if result.data:
                                    st.success("Item relisted successfully.")
                                    st.rerun()
                                else:
                                    st.warning(
                                        "The listing was not updated. Refresh and try again."
                                    )

                            except Exception as exc:
                                st.error(friendly_error(exc))

                with col2:
                    if st.button(
                        "Delete permanently",
                        key=f"delete_{item_id}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        st.session_state["confirm_delete_id"] = item_id
                        st.rerun()

                # Delete confirmation
                if st.session_state.get("confirm_delete_id") == item_id:
                    st.warning(
                        "Are you sure? This permanently deletes the listing. "
                        "Associated claims may also be deleted. This cannot be undone. "
                        "The uploaded photo may remain in Supabase Storage."
                    )

                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:
                        if st.button(
                            "Yes, delete permanently",
                            key=f"confirm_delete_{item_id}",
                            type="primary",
                            use_container_width=True,
                        ):
                            try:
                                result = (
                                    client.table("listings")
                                    .delete()
                                    .eq("id", item_id)
                                    .eq("owner_id", user["id"])
                                    .select("id")
                                    .execute()
                                )

                                if result.data:
                                    st.session_state.pop(
                                        "confirm_delete_id",
                                        None,
                                    )
                                    st.success("Listing deleted successfully.")
                                    st.rerun()
                                else:
                                    st.error(
                                        "No listing was deleted. It may already be deleted, "
                                        "or you may not have permission."
                                    )

                            except Exception as exc:
                                st.error(friendly_error(exc))

                    with cancel_col:
                        if st.button(
                            "Cancel",
                            key=f"cancel_delete_{item_id}",
                            use_container_width=True,
                        ):
                            st.session_state.pop(
                                "confirm_delete_id",
                                None,
                            )
                            st.rerun()

    # ========================================================
    # CLAIMS INBOX
    # ========================================================

    elif page == "Claims inbox":
        render_hero(
            "CONNECTIONS",
            "Claims inbox",
            "Review requests on your listings and keep track of the items you have asked about.",
        )

        try:
            claims = fetch_claims(client)

        except Exception as exc:
            st.error(friendly_error(exc))
            st.stop()

        owned_ids = {
            x["id"]
            for x in listings
            if x.get("owner_id") == user["id"]
        }

        received = [
            c for c in claims
            if c.get("listing_id") in owned_ids
        ]

        sent = [
            c for c in claims
            if c.get("claimant_id") == user["id"]
        ]

        tab_received, tab_sent = st.tabs([
            f"Requests received ({len(received)})",
            f"Requests sent ({len(sent)})",
        ])

        with tab_received:
            if not received:
                st.info("No requests received yet.")

            for claim in received:
                listing = next(
                    (
                        x for x in listings
                        if x["id"] == claim.get("listing_id")
                    ),
                    None,
                )

                claim_status = claim.get("status", "pending")

                with st.container(border=True):
                    title = (
                        listing.get("title", "Listing")
                        if listing else "Listing"
                    )

                    st.markdown(f"### {title}")

                    st.markdown(
                        f"**Status:** `{claim_status.upper()}`"
                    )

                    st.write(claim.get("message", "No message"))
                    st.caption(f"Request ID: {claim.get('id')}")

                    if claim_status == "pending":
                        new_claim_status = st.selectbox(
                            "Decision",
                            ["pending", "accepted", "rejected"],
                            key=f"decision_{claim['id']}",
                        )

                        if st.button(
                            "Update request",
                            key=f"update_claim_{claim['id']}",
                            type="primary",
                        ):
                            try:
                                client.table("claims").update(
                                    {"status": new_claim_status}
                                ).eq(
                                    "id", claim["id"]
                                ).execute()

                                st.success("Request updated.")
                                st.rerun()

                            except Exception as exc:
                                st.error(friendly_error(exc))

                    if claim_status == "accepted":
                        st.info(
                            "Request accepted. Coordinate privately and verify ownership before handing over the item."
                        )

        with tab_sent:
            if not sent:
                st.info(
                    "You haven't requested to connect about any listings yet."
                )

            for claim in sent:
                listing = next(
                    (
                        x for x in listings
                        if x["id"] == claim.get("listing_id")
                    ),
                    None,
                )

                with st.container(border=True):
                    title = (
                        listing.get("title", "Listing")
                        if listing else "Listing"
                    )

                    st.markdown(f"### {title}")

                    st.markdown(
                        f"**Status:** `{claim.get('status', 'pending').upper()}`"
                    )

                    st.write(claim.get("message", ""))

    # ========================================================
    # PRIVATE MESSAGES
    # ========================================================

    elif page == "Messages":
        render_hero(
            "PRIVATE CONVERSATIONS",
            "Messages",
            "Chat with other FindIt members about specific lost or found listings.",
        )
        try:
            conversations = (
                client.table("conversations")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            ).data or []
            profiles_result = client.table("profiles").select("user_id, username").execute()
            usernames = {
                p["user_id"]: p.get("username") or "FindIt member"
                for p in (profiles_result.data or [])
            }
            listing_titles = {
                str(x["id"]): x.get("title", "Listing") for x in listings
            }
        except Exception as exc:
            st.error("Couldn't load messages. " + friendly_error(exc))
            conversations = []

        if not conversations:
            st.info("No conversations yet. Open a listing and select **Message owner** to start one.")
        else:
            options = {}
            for convo in conversations:
                other_id = convo["owner_id"] if convo["starter_id"] == user["id"] else convo["starter_id"]
                label = f"@{usernames.get(other_id, 'member')} · {listing_titles.get(str(convo['listing_id']), 'Listing')}"
                options[label] = convo["id"]

            labels = list(options.keys())
            selected_id = st.session_state.get("open_conversation_id")
            selected_label = next((k for k, v in options.items() if v == selected_id), labels[0])
            chosen = st.selectbox("Your conversations", labels, index=labels.index(selected_label))
            conversation_id = options[chosen]
            st.session_state["open_conversation_id"] = conversation_id

            try:
                convo_row = next(c for c in conversations if c["id"] == conversation_id)
                other_id = convo_row["owner_id"] if convo_row["starter_id"] == user["id"] else convo_row["starter_id"]
                st.caption(
                    f"Chatting with **@{usernames.get(other_id, 'member')}** about "
                    f"**{listing_titles.get(str(convo_row['listing_id']), 'this listing')}**"
                )

                # Keep one Realtime subscription for the currently open conversation.
                active_id = st.session_state.get("_findit_realtime_conversation_id")
                if active_id != conversation_id:
                    old_channel = st.session_state.get("_findit_realtime_channel")
                    if old_channel is not None:
                        try:
                            client.remove_channel(old_channel)
                        except Exception:
                            pass

                    message_event = threading.Event()

                    def on_new_message(payload):
                        # Realtime callbacks may run outside Streamlit's script thread.
                        # A thread-safe event lets the fragment fetch safely on its next tick.
                        message_event.set()

                    channel = (
                        client.channel(f"findit-messages-{conversation_id}")
                        .on_postgres_changes(
                            "INSERT",
                            on_new_message,
                            schema="public",
                            table="messages",
                            filter=f"conversation_id=eq.{conversation_id}",
                        )
                        .subscribe()
                    )
                    st.session_state["_findit_realtime_channel"] = channel
                    st.session_state["_findit_realtime_conversation_id"] = conversation_id
                    st.session_state["_findit_realtime_event"] = message_event
                    st.session_state[f"_findit_messages_cache_{conversation_id}"] = (
                        client.table("messages")
                        .select("*")
                        .eq("conversation_id", conversation_id)
                        .order("created_at")
                        .execute()
                    ).data or []

                message_event = st.session_state["_findit_realtime_event"]
                cache_key = f"_findit_messages_cache_{conversation_id}"

                @st.fragment(run_every="1s")
                def live_chat():
                    # The one-second fragment tick only checks the local event.
                    # It queries Supabase only after Realtime reports a new INSERT.
                    if message_event.is_set():
                        latest = (
                            client.table("messages")
                            .select("*")
                            .eq("conversation_id", conversation_id)
                            .order("created_at")
                            .execute()
                        ).data or []
                        st.session_state[cache_key] = latest
                        message_event.clear()

                    messages = st.session_state.get(cache_key, [])
                    with st.container(border=True):
                        if not messages:
                            st.caption("This is the start of your conversation.")
                        for msg in messages:
                            sender = (
                                "You"
                                if msg["sender_id"] == user["id"]
                                else f"@{usernames.get(msg['sender_id'], 'member')}"
                            )
                            with st.chat_message(
                                "user" if msg["sender_id"] == user["id"] else "assistant"
                            ):
                                st.caption(sender)
                                st.write(msg["body"])
                                created_at = msg.get("created_at", "")
                                st.caption(created_at.replace("T", " ")[:16])

                    st.caption("🟢 Live updates enabled")

                    with st.form(f"send_message_{conversation_id}", clear_on_submit=True):
                        body = st.text_area(
                            "Message",
                            placeholder="Write a message...",
                            max_chars=2000,
                        )
                        send = st.form_submit_button(
                            "Send message",
                            type="primary",
                            use_container_width=True,
                        )
                        if send:
                            if not body.strip():
                                st.warning("Write a message first.")
                            else:
                                client.table("messages").insert({
                                    "conversation_id": conversation_id,
                                    "sender_id": user["id"],
                                    "body": body.strip(),
                                }).execute()
                                # Show the sender's message immediately; the Realtime
                                # event will keep the other participant in sync.
                                st.session_state[cache_key] = (
                                    client.table("messages")
                                    .select("*")
                                    .eq("conversation_id", conversation_id)
                                    .order("created_at")
                                    .execute()
                                ).data or []
                                message_event.clear()
                                st.rerun(scope="fragment")

                live_chat()

            except Exception as exc:
                st.error("Couldn't open this conversation. " + friendly_error(exc))

    # ========================================================
    # ADMIN PANEL
    # ========================================================

    elif page == "Admin panel" and admin_mode:
        render_admin_panel(client, user)

    # ========================================================
    # FOOTER
    # ========================================================

    st.divider()

    st.markdown(
        """
        <div style="text-align:center;padding:12px;color:#8291a8;font-size:.85rem;">
            <strong style="color:#526581;">🔎 FindIt</strong>
            <br>
            Helping lost belongings find their way home.
            <br>
            Verify ownership before returning an item.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
