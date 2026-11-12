"""
app.py
------
Mandi Bhav Bot -- Streamlit website.

Kisano ke liye crop price advisor:
- Sidebar me crop aur mandi chuno
- 5 tabs: Aaj ka Bhav, Trend, Prediction, Mandi Comparison, Chat

Chalane ka tarika:
    streamlit run app.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chatbot import reply
from data_loader import load_data
from features import (
    best_crop_of_week,
    check_alert,
    compare_mandis,
    get_latest_price,
    get_trend,
)
from model import get_accuracy, get_advice, predict_price

# Page ki basic setting
st.set_page_config(
    page_title="Mandi Bhav Bot",
    page_icon=":material/agriculture:",
    layout="wide",
)

# Crop ke Hindi naam (sirf dikhane ke liye)
CROP_HINDI = {
    "Wheat": "गेहूं",
    "Rice": "चावल",
    "Maize": "मक्का",
    "Gram": "चना",
    "Potato": "आलू",
    "Onion": "प्याज",
    "Tomato": "टमाटर",
    "Mustard": "सरसों",
    "Banana": "केला",
    "Apple": "सेब",
    "Pomegranate": "अनार",
    "Papaya": "पपीता",
}

# Dropdown me "saari mandiyan" ka option
ALL_MANDIS = "Saari mandiyan (average)"


@st.cache_data(show_spinner=False)
def get_data():
    """
    CSV ek hi baar load karo aur cache me rakh lo.
    (Har click par file dobara padhne ki zaroorat nahi)
    """
    return load_data()


# Data load
df = get_data()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Chunav")

    # Crop dropdown (Hindi naam ke saath)
    crop = st.selectbox(
        "Crop chuno",
        sorted(df["crop"].unique()),
        format_func=lambda c: f"{CROP_HINDI.get(c, c)} ({c})",
    )

    # Mandi dropdown
    mandi_list = [ALL_MANDIS] + sorted(df["mandi"].unique())
    mandi_choice = st.selectbox("Mandi chuno", mandi_list)

    # "Saari mandiyan" chuni ho to None bhejo
    mandi = None if mandi_choice == ALL_MANDIS else mandi_choice

    st.caption("Data: mandi_prices.csv (Jan 2024 - Dec 2025)")
    st.caption("Note: Bhav sample data se hain, asli mandi rate se verify karein.")

# ---------------- Title ----------------
st.title("Mandi Bhav Bot")
st.caption("Kisano ke liye crop price advisor -- bhav dekho, trend samjho, bechne ki salah lo.")

# ---------------- 5 Tabs ----------------
tab_price, tab_trend, tab_predict, tab_compare, tab_chat = st.tabs(
    ["Aaj ka Bhav", "Trend", "Prediction", "Mandi Comparison", "Chat"]
)


# ============ Tab 1: Aaj ka Bhav ============
with tab_price:
    st.subheader("Aaj ka bhav")

    # Latest price nikalo
    price = get_latest_price(crop, mandi, df)

    if price.get("error"):
        st.error(price["error"])
    else:
        # Teen bade numbers (cards ki tarah)
        with st.container(horizontal=True):
            st.metric(
                "Modal bhav",
                f"₹{price['modal_price']:,.0f}",
                border=True,
                help="Sabse common (modal) rate, per quintal",
            )
            st.metric("Kam se kam", f"₹{price['min_price']:,.0f}", border=True)
            st.metric("Zyada se zyada", f"₹{price['max_price']:,.0f}", border=True)

        # Date aur mandi
        st.caption(f"Date: {price['date']} | Mandi: {price['mandi']}")

        # Pichle 6 mahino ka rate (table)
        recent = df[df["crop"] == crop]
        if mandi is not None:
            recent = recent[recent["mandi"] == mandi]

        recent = recent.groupby("date")["modal_price"].mean().tail(6)

        st.markdown("**Pichle 6 mahino ka rate**")
        st.dataframe(
            pd.DataFrame(
                {
                    "Date": [d.strftime("%Y-%m-%d") for d in recent.index],
                    "Modal bhav (₹/quintal)": recent.values.round(0),
                }
            ),
            hide_index=True,
        )


# ============ Tab 2: Trend ============
with tab_trend:
    st.subheader("Bhav ka trend")

    # Kitne mahine ka trend dekhna hai
    points = st.segmented_control(
        "Kitne mahine ka trend?",
        options=[3, 6, 12],
        default=6,
        key="trend_points",
    )

    # Agar user ne kuch na chuna to 6 le lo
    points = points or 6

    # Trend nikalo
    trend = get_trend(crop, points, df)

    if trend.get("error"):
        st.error(trend["error"])
    else:
        # Summary line (badha / gira / stable)
        if trend["direction"] == "badha":
            st.success(trend["summary"])
        elif trend["direction"] == "gira":
            st.warning(trend["summary"])
        else:
            st.info(trend["summary"])

        # Plotly line chart
        st.plotly_chart(trend["fig"])

        # Table
        st.dataframe(
            pd.DataFrame(
                {
                    "Date": trend["dates"],
                    "Modal bhav (₹/quintal)": trend["prices"],
                }
            ),
            hide_index=True,
        )


# ============ Tab 3: Prediction ============
with tab_predict:
    st.subheader("Aage ka anumaan")

    # Prediction aur salah
    pred = predict_price(crop, 7, df)
    advice = get_advice(crop, 7, df)

    if pred.get("error"):
        st.error(pred["error"])
    else:
        # Salah ka card
        if advice.get("error"):
            st.warning(advice["error"])
        elif advice["advice"] == "abhi bechna theek hai":
            st.success(f"**Salah: {advice['advice'].upper()}**\n\n{advice['reason']}")
        else:
            st.warning(f"**Salah: {advice['advice'].upper()}**\n\n{advice['reason']}")

        # Numbers
        with st.container(horizontal=True):
            st.metric("Aaj ka bhav", f"₹{pred['last_price']:,.0f}", border=True)
            st.metric(
                "7 din ka anumaan",
                f"₹{pred['avg_forecast']:,.0f}",
                delta=f"{pred['change_percent']}%",
                border=True,
            )
            st.metric(
                "Moving average",
                f"₹{pred['ma_pred']:,.0f}",
                help="Pichle 3 rate points ka simple average",
                border=True,
            )

        # Graph: asli rate + anumaan
        fig = go.Figure()

        # 1. Asli rate (solid line)
        fig.add_trace(
            go.Scatter(
                x=pred["history_dates"],
                y=pred["history_prices"],
                mode="lines+markers",
                name="Asli rate",
                line=dict(color="#1565C0", width=3),
            )
        )

        # 2. Anumaan (dashed line) -- last asli point se jodne ke liye
        fig.add_trace(
            go.Scatter(
                x=[pred["history_dates"][-1]] + pred["forecast_dates"],
                y=[pred["last_price"]] + pred["forecast_prices"],
                mode="lines+markers",
                name="Anumaan",
                line=dict(color="#EF6C00", width=3, dash="dash"),
            )
        )

        fig.update_layout(
            title=f"{crop} -- asli rate aur agle 7 din ka anumaan",
            xaxis_title="Mahina",
            yaxis_title="Modal bhav (₹/quintal)",
            template="plotly_white",
            height=400,
            hovermode="x unified",
            margin=dict(l=40, r=20, t=50, b=40),
        )

        st.plotly_chart(fig)

        # Agle 7 din ka table
        st.markdown("**Agle 7 din ka anumaan**")
        st.dataframe(
            pd.DataFrame(
                {
                    "Date": pred["forecast_dates"],
                    "Anumaan (₹/quintal)": [round(p) for p in pred["forecast_prices"]],
                }
            ),
            hide_index=True,
        )

        # Model accuracy (MAE)
        acc = get_accuracy(crop, df)

        st.markdown("**Model accuracy**")
        if acc.get("error"):
            st.info(acc["error"])
        else:
            with st.container(horizontal=True):
                st.metric(
                    "MAE (average galti)",
                    f"₹{acc['mae']:,.0f}",
                    border=True,
                    help="Model kitne rupaye galat hota hai, average me",
                )
                st.metric("MAE %", f"{acc['mae_percent']}%", border=True)
                st.metric("Rating", acc["rating"], border=True)

            st.caption(
                f"Train points: {acc['train_points']} | Test points: {acc['test_points']} "
                f"| Average bhav: ₹{acc['avg_price']:,.0f}"
            )
            st.caption(
                "MAE kam ho to model behtar hai. LinearRegression sirf seedha trend "
                "pakadta hai, isliye mausam/season ke tez utar-chadhav me galti badh sakti hai."
            )


# ============ Tab 4: Mandi Comparison ============
with tab_compare:
    st.subheader("Mandi comparison")

    cmp = compare_mandis(crop, df)

    if cmp.get("error"):
        st.error(cmp["error"])
    else:
        # Sabse achhi aur sabse kam rate wali mandi
        with st.container(horizontal=True):
            st.metric(
                f"Sabse zyada bhav - {cmp['best_mandi']}",
                f"₹{cmp['best_price']:,.0f}",
                border=True,
            )
            st.metric(
                f"Sabse kam bhav - {cmp['worst_mandi']}",
                f"₹{cmp['worst_price']:,.0f}",
                border=True,
            )
            st.metric(
                "Farak (spread)",
                f"₹{cmp['spread']:,.0f}",
                f"{cmp['spread_pct']}%",
                border=True,
            )

        # Table: sabse mehnga sabse upar
        st.markdown(f"**{crop} -- saari mandiyon ka latest rate**")
        st.dataframe(
            cmp["table"],
            hide_index=True,
            column_config={
                "rank": st.column_config.NumberColumn("Rank", width="small"),
                "mandi": "Mandi",
                "date": "Date",
                "min_price": st.column_config.NumberColumn("Kam", format="₹%.0f"),
                "max_price": st.column_config.NumberColumn("Zyada", format="₹%.0f"),
                "modal_price": st.column_config.NumberColumn("Modal", format="₹%.0f"),
            },
        )

        # Bar chart
        st.bar_chart(
            cmp["table"],
            x="mandi",
            y="modal_price",
            height=320,
        )

    st.divider()

    # Best crop of the week
    st.subheader("Is hafte ke top 3 crops")

    best = best_crop_of_week(df=df)

    if best.get("error"):
        st.info(best["error"])
    else:
        with st.container(horizontal=True):
            for item in best["top"]:
                st.metric(
                    item["crop"],
                    f"+{item['change_percent']}%",
                    f"₹{item['first_price']:,.0f} se ₹{item['last_price']:,.0f}",
                    border=True,
                )

        with st.expander("Saare 12 crops ka change %"):
            st.dataframe(
                best["table"],
                hide_index=True,
                column_config={
                    "first_price": st.column_config.NumberColumn("Pehle", format="₹%.0f"),
                    "last_price": st.column_config.NumberColumn("Ab", format="₹%.0f"),
                    "change_percent": st.column_config.NumberColumn(
                        "Change %", format="%.2f%%"
                    ),
                },
            )

    st.divider()

    # Price alert
    st.subheader("Price alert")

    with st.form("alert_form"):
        # Alert ki limit
        limit = st.number_input(
            "Agar bhav is limit se upar jaye to alert do (₹ per quintal)",
            min_value=100.0,
            max_value=20000.0,
            value=3000.0,
            step=50.0,
            help="Modal bhav (saari mandiyon ka average) se compare hoga",
        )
        alert_clicked = st.form_submit_button("Alert check karo", type="primary")

    if alert_clicked:
        alert = check_alert(crop, limit, df)

        if alert.get("error"):
            st.error(alert["error"])
        elif alert["triggered"]:
            st.warning(alert["message"])
        else:
            st.success(alert["message"])


# ============ Tab 5: Chat ============
with tab_chat:
    st.subheader("Chatbot se poochho")

    # Chat history session_state me rakho
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Purane messages dikhao
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("fig") is not None:
                st.plotly_chart(msg["fig"])

    # Shuru me kuch example sawaal (pills)
    SUGGESTIONS = {
        ":material/currency_rupee: gehu ka bhav kya hai?": "gehu ka bhav kya hai?",
        ":material/trending_up: tamatar ka trend batao": "tamatar ka trend batao",
        ":material/storefront: Karnal mandi me aloo ka rate?": "Karnal mandi me aloo ka rate?",
        ":material/sell: kya main pyaz bech du?": "kya main pyaz bech du?",
    }

    prompt = None

    if not st.session_state.messages:
        chip = st.pills(
            "Try karo:",
            list(SUGGESTIONS.keys()),
            label_visibility="collapsed",
        )
        if chip:
            prompt = SUGGESTIONS[chip]

    # Chat input
    typed = st.chat_input("Apna sawaal likho, jaise 'gehu ka bhav kya hai?'")
    if typed:
        prompt = typed

    # Naya sawaal mila to jawab do
    if prompt:
        # 1. User ka message dikhao
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 2. Chatbot se jawab lo
        with st.chat_message("assistant", avatar=":material/agriculture:"):
            try:
                result = reply(prompt, df)
                answer = result["answer"]
            except Exception as error:
                answer = f"Sorry, kuch gadbad ho gayi: {error}"
                result = {}

            st.write(answer)

            # Trend wale sawaal me chart bhi dikhao
            if result.get("fig") is not None:
                st.plotly_chart(result["fig"])

        # 3. Jawab history me save karo
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "fig": result.get("fig"),
            }
        )
