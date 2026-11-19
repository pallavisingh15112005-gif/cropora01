"""
style.py
--------
Kaam: poori website ka look theek karna (theme, hero, salah box, chart, footer).

Is file me 5 kaam hote hain:
1. apply_theme()          -> CSS se colors, cards, tabs, chat sab sundar
2. hero()                 -> upar ka bada heading (brand + tagline)
3. advice_box(kind, text) -> bechne ki salah ka colored box
4. style_fig(fig, title)  -> plotly chart ko ek jaise theme me laata hai
5. footer()               -> page ke neeche chhoti line

Colors `.streamlit/config.toml` se match karte hain (light theme + green).

Note: st.markdown me HTML ke andar khali line (blank line) nahi chahiye,
warna markdown us HTML ko tod deta hai. Isliye saara HTML ek hi block me hai.
"""

import textwrap

import streamlit as st

# ---------------- Theme colors (ek jagah rakhe hain) ----------------
GREEN = "#166534"        # primary (green)
GREEN_DARK = "#10241A"   # sidebar
LIME = "#84CC16"         # highlight
AMBER = "#D97706"        # warning / wait
RED = "#DC2626"          # danger
INK = "#1C1917"          # text
MUTED = "#6B6560"        # halka text
BG = "#FAF8F3"           # page background
CARD = "#FFFFFF"         # card background
BORDER = "#E7E2D8"       # border
GRID = "#EFEAE0"         # chart grid


def apply_theme():
    """
    Poori app par CSS lagata hai.

    Streamlit ke andar ke elements (metric card, tab, button, chat bubble)
    ke `data-testid` pakad kar unka look badal dete hain.
    """
    css = f"""
    <style>
    html, body, [class*="st-"], .stApp {{ font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif; }}
    .stApp {{ background: {BG}; }}
    .block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1180px; }}
    h1, h2, h3, h4 {{ color: {INK}; letter-spacing: -0.02em; }}
    h2 {{ font-size: 26px !important; font-weight: 700 !important; }}
    h3 {{ font-size: 20px !important; font-weight: 700 !important; }}
    [data-testid="stMetric"] {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
        padding: 14px 16px; box-shadow: 0 1px 2px rgba(28, 25, 23, 0.04);
    }}
    [data-testid="stMetricLabel"] p {{
        font-size: 12.5px !important; font-weight: 600 !important;
        color: {MUTED} !important; letter-spacing: 0.02em;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 26px !important; font-weight: 800 !important; color: {INK} !important;
    }}
    [data-testid="stMetricDelta"] {{ font-weight: 700 !important; }}
    [data-testid="stTabs"] [role="tablist"] {{ gap: 2px; border-bottom: 1px solid {BORDER}; }}
    [data-testid="stTab"] {{
        border-radius: 10px 10px 0 0; padding: 8px 10px;
        font-weight: 600; font-size: 14px; color: {MUTED};
    }}
    [data-testid="stTab"][aria-selected="true"] {{ color: {GREEN}; }}
    .stButton > button, .stFormSubmitButton > button {{
        border-radius: 11px; font-weight: 700; border: 1px solid {BORDER};
    }}
    .stFormSubmitButton > button {{
        background: {GREEN}; color: #FFFFFF; border: 1px solid {GREEN};
    }}
    .stFormSubmitButton > button:hover {{
        background: {GREEN_DARK}; border-color: {GREEN_DARK}; color: #FFFFFF;
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER}; border-radius: 12px; overflow: hidden;
    }}
    [data-testid="stChatMessage"] {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 10px 14px;
    }}
    [data-testid="stChatInput"] textarea {{ border-radius: 12px; }}
    [data-testid="stExpander"] details {{
        border: 1px solid {BORDER}; border-radius: 12px; background: {CARD};
    }}
    [data-testid="stSidebar"] {{ background: {GREEN_DARK}; border-right: none; }}
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label p, [data-testid="stSidebar"] p {{ color: #E8EEE9; }}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: #A9BDB0; }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background: rgba(255,255,255,0.08) !important;
        border-color: #24402E !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] *,
    [data-testid="stSidebar"] [data-baseweb="select"] * {{
        color: #E8EEE9 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] svg,
    [data-testid="stSidebar"] [data-baseweb="select"] svg {{
        fill: #A9BDB0 !important;
    }}
    [data-testid="stSidebar"] button {{
        color: #E8EEE9 !important;
        border-color: #24402E !important;
        background: rgba(255,255,255,0.06) !important;
    }}
    [data-testid="stSidebar"] button:hover {{
        background: rgba(255,255,255,0.12) !important;
        border-color: #2F5340 !important;
        color: #FFFFFF !important;
    }}
    </style>
    """

    st.markdown(textwrap.dedent(css).strip(), unsafe_allow_html=True)


def hero():
    """Page ke upar bada brand card dikhata hai."""
    html = f"""
    <div style="background: linear-gradient(135deg, {GREEN} 0%, #1F7A3D 55%, #2C8F4B 100%); border-radius: 18px; padding: 26px 28px; margin-bottom: 18px; color: #FFFFFF; box-shadow: 0 8px 24px rgba(22, 101, 52, 0.18);">
    <div style="font-size: 12px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #CFF3D8; margin-bottom: 6px;">Cropora AI &middot; Mandi Bhav Bot</div>
    <div style="font-size: 34px; font-weight: 800; line-height: 1.15; letter-spacing: -0.02em;">Kisan ka smart bhav advisor</div>
    <div style="font-size: 15px; color: #DCF3E2; margin-top: 8px;">Aaj ka bhav dekho, trend samjho, aur sahi waqt par becho &mdash; per kg aur per quintal, mandi-wise.</div>
    <div style="margin-top: 16px;">
    <span style="display:inline-block; margin: 0 6px 6px 0; background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.25); padding: 5px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 600;">12 crops</span>
    <span style="display:inline-block; margin: 0 6px 6px 0; background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.25); padding: 5px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 600;">10 mandiyan</span>
    <span style="display:inline-block; margin: 0 6px 6px 0; background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.25); padding: 5px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 600;">AI anumaan + salah</span>
    <span style="display:inline-block; margin: 0 6px 6px 0; background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.25); padding: 5px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 600;">Hindi chatbot</span>
    </div>
    </div>
    """

    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


def advice_box(kind: str, text: str):
    """
    Bechne ki salah ka colored box.

    kind:
      "sell" -> green box (abhi bechna theek hai)
      "wait" -> amber box (kuch din ruko)
      "info" -> neutral box
    """
    styles = {
        "sell": {
            "bg": "#F0FDF4",
            "border": "#BBF7D0",
            "bar": GREEN,
            "label": "ABHI BECHNA THEEK HAI",
            "icon": "&#9989;",
            "title_color": GREEN,
        },
        "wait": {
            "bg": "#FFFBEB",
            "border": "#FDE68A",
            "bar": AMBER,
            "label": "KUCH DIN RUKO",
            "icon": "&#9203;",
            "title_color": "#B45309",
        },
        "info": {
            "bg": "#F8FAFC",
            "border": "#E2E8F0",
            "bar": "#64748B",
            "label": "JAANKARI",
            "icon": "&#8505;&#65039;",
            "title_color": "#475569",
        },
    }

    s = styles.get(kind, styles["info"])

    html = f"""
    <div style="background: {s['bg']}; border: 1px solid {s['border']}; border-left: 5px solid {s['bar']}; border-radius: 12px; padding: 14px 16px; margin: 6px 0 14px 0;">
    <div style="font-size: 12px; font-weight: 800; letter-spacing: 0.06em; color: {s['title_color']}; margin-bottom: 6px;">{s['icon']} {s['label']}</div>
    <div style="font-size: 14.5px; color: {INK}; line-height: 1.55;">{text}</div>
    </div>
    """

    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


def style_fig(fig, title: str | None = None):
    """
    Plotly chart ko site ke theme me laata hai.

    fig   -> plotly ka Figure
    title -> chart ke upar heading (na do to purana title rahega)

    Return: wahi fig (aage st.plotly_chart me dena hai)
    """
    layout = dict(
        template="plotly_white",
        font=dict(family="Plus Jakarta Sans, Segoe UI, sans-serif", size=13, color=INK),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[GREEN, LIME, AMBER, "#0284C7", RED],
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            font=dict(color=INK, size=12.5),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        ),
        margin=dict(l=48, r=20, t=58 if title else 26, b=42),
    )

    # Title diya hai to naya lagao, warna purana hi rehne do
    if title:
        layout["title"] = dict(
            text=title,
            x=0.01,
            xanchor="left",
            font=dict(size=15, color=INK),
        )

    fig.update_layout(**layout)

    # Grid halka, axes saaf
    fig.update_xaxes(
        showgrid=False,
        linecolor=BORDER,
        tickfont=dict(size=12, color=MUTED),
        title_font=dict(size=12.5, color=MUTED),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(size=12, color=MUTED),
        title_font=dict(size=12.5, color=MUTED),
    )

    return fig


def footer():
    """Page ke neeche chhoti si line."""
    html = f"""
    <div style="margin-top: 28px; padding-top: 14px; border-top: 1px solid {BORDER}; display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; font-size: 12.5px; color: {MUTED};">
    <div><b style="color:{GREEN};">Cropora AI</b> &middot; Mandi Bhav Bot</div>
    <div>Data: sample mandi_prices.csv &middot; Asli rate se verify karein</div>
    </div>
    """

    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)
