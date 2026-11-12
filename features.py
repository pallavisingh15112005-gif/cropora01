"""
features.py
-----------
Kaam: clean data (data_loader se) ko ML ke liye features me badalna.

Features 3 tarah ke hain:
1. Time features      -> month, year
2. Price features     -> min_price, max_price, price_range
3. History features   -> lag_1, lag_2, lag_3 (pichle mahino ke rate)
                         aur rolling_mean_3 (pichle 3 mahine ka average)

Crop aur mandi ko number me badalna bhi zaroori hai, kyunki ML model
sirf numbers samajhta hai (text nahi).

Target (jo predict karna hai) = modal_price
"""

import pandas as pd
import plotly.graph_objects as go

from data_loader import KEEP_CROPS, load_data, standardize_crop_name

# Crop ka naam -> number (0 se 11 tak)
# Ye fixed hai, isliye app me bhi same number milega
CROP_CODES = {crop: i for i, crop in enumerate(KEEP_CROPS)}


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Date column se month aur year nikalta hai.

    Kyun? Rate mahine ke hisaab se badalta hai (season).
    """
    df = df.copy()

    # date column se mahina (1-12) aur saal nikal lo
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    return df


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Price columns se ek naya feature banata hai: price_range.

    price_range = max_price - min_price
    (matlab us din mandi me rate kitna upar-neeche raha)
    """
    df = df.copy()

    df["price_range"] = df["max_price"] - df["min_price"]

    return df


def add_history_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Har crop + mandi ke pichle mahino ke rate se features banata hai.

    - lag_1 = pichle mahine ka modal_price
    - lag_2 = 2 mahine pehle ka
    - lag_3 = 3 mahine pehle ka
    - rolling_mean_3 = pichle 3 mahino ka average

    Dhyaan do: shift(1) lagane se hum sirf PURANA data use karte hain.
    Aaj ka rate kabhi feature me nahi aata, warna model ko answer pehle
    se pata hoga (ise data leakage kehte hain).
    """
    df = df.copy()

    # Pehle data ko sahi order me lagao: crop -> mandi -> date
    # Iske bina shift galat mahine ka rate utha lega
    df = df.sort_values(["crop", "mandi", "date"]).reset_index(drop=True)

    # Har crop+mandi ka alag group (jaise "Wheat + Karnal Mandi")
    group = df.groupby(["crop", "mandi"])["modal_price"]

    df["lag_1"] = group.shift(1)   # 1 mahina purana rate
    df["lag_2"] = group.shift(2)   # 2 mahine purana
    df["lag_3"] = group.shift(3)   # 3 mahine purana

    # Pichle 3 mahine ka average (shift ke baad, taaki aaj ka rate na aaye)
    df["rolling_mean_3"] = group.transform(
        lambda s: s.shift(1).rolling(3).mean()
    )

    return df


def add_encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crop aur mandi (text) ko number me badalta hai.

    Example: crop "Wheat" -> 0, "Rice" -> 1 ...
    Model text nahi padh sakta, isliye ye step zaroori hai.
    """
    df = df.copy()

    # Crop ke number: CROP_CODES dict se
    df["crop_code"] = df["crop"].map(CROP_CODES)

    # Mandi ke number: jo mandi data me mili, use A-Z order me number do
    mandi_codes = {mandi: i for i, mandi in enumerate(sorted(df["mandi"].unique()))}
    df["mandi_code"] = df["mandi"].map(mandi_codes)

    return df


def get_latest_price(crop: str, mandi: str | None = None, df: pd.DataFrame | None = None) -> dict:
    """
    Kisi crop ka sabse latest (aaj tak ka last) rate deta hai.

    Parameters
    ----------
    crop  : crop ka naam -- Hindi ya English dono chalega
            (jaise "gehu", "गेहूं", "Wheat")
    mandi : mandi ka naam (optional). Agar nahi diya to saari mandiyon
            ka average nikalta hai.
    df    : clean data (optional). Agar nahi diya to load_data() khud
            data load kar lega.

    Return: ek dictionary, jaise
        {
            "crop": "Wheat",
            "mandi": "Karnal Mandi",
            "date": "2025-12-01",
            "min_price": 2100.0,
            "max_price": 2300.0,
            "modal_price": 2200.0,
            "mandis_count": 1,
            "error": None,
        }

    Agar data na mile to "error" me saaf message aata hai.
    """
    # 1. Data load karo (agar bahar se diya hai to wahi use karo)
    if df is None:
        df = load_data()

    # 2. Crop ka naam standard karo -- "gehu" ho ya "Wheat", dono kaam karenge
    crop_name = standardize_crop_name(crop)

    # Naam list me nahi mila -> saaf message bhejo
    if crop_name is None:
        return {
            "error": f"'{crop}' naam ka crop nahi mila. In 12 crops me se koi chuno: "
            + ", ".join(KEEP_CROPS)
        }

    # 3. Sirf is crop ka data rakho
    crop_df = df[df["crop"] == crop_name]

    if crop_df.empty:
        return {"error": f"{crop_name} ka koi data nahi mila."}

    # 4. Agar mandi di gayi hai to data ko us mandi tak seemit karo
    if mandi is None:
        # Mandi nahi di -> saari mandiyan
        selected_df = crop_df
        mandi_label = "saari mandiyan (average)"
    else:
        # Mandi ka naam compare karne ke liye chhote letters me karo
        wanted = str(mandi).strip().lower()
        selected_df = crop_df[crop_df["mandi"].str.lower() == wanted]

        # Mandi nahi mili -> available mandiyan bata do
        if selected_df.empty:
            return {
                "error": f"'{mandi}' mandi {crop_name} ke liye nahi mili. "
                "Ye mandiyan available hain: "
                + ", ".join(sorted(crop_df["mandi"].unique()))
            }

        mandi_label = selected_df["mandi"].iloc[0]

    # 5. Sabse latest date dhoondo
    latest_date = selected_df["date"].max()

    # 6. Sirf usi date ki rows rakho
    latest_rows = selected_df[selected_df["date"] == latest_date]

    # 7. Average nikaalo
    #    (ek mandi ho to average = wahi value,
    #     saari mandiyan hon to sabka average)
    return {
        "crop": crop_name,
        "mandi": mandi_label,
        "date": latest_date.strftime("%Y-%m-%d"),
        "min_price": round(float(latest_rows["min_price"].mean()), 2),
        "max_price": round(float(latest_rows["max_price"].mean()), 2),
        "modal_price": round(float(latest_rows["modal_price"].mean()), 2),
        "mandis_count": int(latest_rows["mandi"].nunique()),
        "error": None,
    }


def get_trend(crop: str, days: int = 7, df: pd.DataFrame | None = None) -> dict:
    """
    Pichle kuch rate points ka trend nikalta hai.

    Dhyaan do: is dataset me har mahine ka ek rate hai (daily data nahi).
    Isliye days ka matlab hai "kitne latest rate points" (matlab mahine).
    days=7 -> pichle 7 mahine ka trend.

    Parameters
    ----------
    crop : crop ka naam -- Hindi ya English dono chalega
    days : kitne latest points chahiye (default 7)
    df   : clean data (optional)

    Return: dictionary jisme
        dates           = list of dates (string)
        prices          = list of modal price
        change_percent  = pehle se aakhri rate me kitna % badla
        direction       = "badha" / "gira" / "stable"
        summary         = ek line ka Hindi message
        fig             = plotly line chart
        error           = None, ya error message
    """
    # 1. Data load karo
    if df is None:
        df = load_data()

    # 2. Crop ka naam standard karo
    crop_name = standardize_crop_name(crop)

    if crop_name is None:
        return {
            "error": f"'{crop}' naam ka crop nahi mila. In 12 crops me se koi chuno: "
            + ", ".join(KEEP_CROPS)
        }

    # 3. Kam se kam 2 points chahiye, warna trend ka matlab nahi
    if days < 2:
        return {"error": "Trend ke liye days kam se kam 2 hona chahiye."}

    # 4. Sirf is crop ka data
    crop_df = df[df["crop"] == crop_name]

    if crop_df.empty:
        return {"error": f"{crop_name} ka koi data nahi mila."}

    # 5. Har date ka average modal price (saari mandiyon ka)
    #    Isse ek hi line banti hai: date -> rate
    prices_by_date = (
        crop_df.groupby("date")["modal_price"].mean().sort_index()
    )

    # 6. Sirf aakhri `days` points rakho
    trend = prices_by_date.tail(days)

    if len(trend) < 2:
        return {"error": f"{crop_name} ke liye itne rate points nahi hain."}

    # 7. List banao (chart aur table ke liye)
    dates = [d.strftime("%Y-%m-%d") for d in trend.index]
    prices = [round(float(p), 2) for p in trend.values]

    # 8. Change nikalo: (aakhri - pehla) / pehla * 100
    first_price = prices[0]
    last_price = prices[-1]
    change_percent = round((last_price - first_price) / first_price * 100, 2)

    # 9. Direction decide karo (0.5% se chhota badlav = stable)
    if change_percent > 0.5:
        direction = "badha"
        color = "#2E7D32"   # hara
        arrow = "▲"
    elif change_percent < -0.5:
        direction = "gira"
        color = "#C62828"   # laal
        arrow = "▼"
    else:
        direction = "stable"
        color = "#1565C0"   # neela
        arrow = "▬"

    # 10. Ek line ka message
    summary = (
        f"{crop_name} ka bhav pichle {len(prices)} mahino me "
        f"{abs(change_percent)}% {direction} hai. "
        f"₹{first_price:,.0f} se ₹{last_price:,.0f} ({arrow})"
    )

    # 11. Plotly line chart banao
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=prices,
            mode="lines+markers",
            name=crop_name,
            line=dict(color=color, width=3),
            marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>Rate: ₹%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"{crop_name} - pichle {len(prices)} mahino ka trend",
        xaxis_title="Mahina",
        yaxis_title="Modal price (₹/quintal)",
        template="plotly_white",
        height=380,
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="x unified",
    )

    return {
        "crop": crop_name,
        "dates": dates,
        "prices": prices,
        "change_percent": change_percent,
        "direction": direction,
        "summary": summary,
        "fig": fig,
        "error": None,
    }


# Ye columns model ko input ke roop me jayenge
FEATURE_COLUMNS = [
    "month",
    "year",
    "crop_code",
    "mandi_code",
    "min_price",
    "max_price",
    "price_range",
    "lag_1",
    "lag_2",
    "lag_3",
    "rolling_mean_3",
]

# Jo column predict karna hai
TARGET_COLUMN = "modal_price"


def build_features(df: pd.DataFrame | None = None):
    """
    Poora pipeline ek saath chalata hai aur model ke liye ready data deta hai.

    Return: (X, y)
      X = features (model ka input)
      y = modal_price (jo model ko seekhna hai)

    Agar df nahi diya to data_loader se fresh data load hota hai.
    """
    # 1. Data load karo (ya jo diya hai wahi use karo)
    if df is None:
        df = load_data()

    # 2. Saare feature groups lagao
    df = add_time_features(df)
    df = add_price_features(df)
    df = add_history_features(df)
    df = add_encode_features(df)

    # 3. Jin rows me purana data nahi hai (shuru ke 3 mahine),
    #    unme lag features khali honge -> unhe hata do
    df = df.dropna(subset=FEATURE_COLUMNS)

    # 4. Input (X) aur answer (y) alag karo
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    return X, y


def make_next_month_row(df: pd.DataFrame, crop: str, mandi: str) -> pd.DataFrame:
    """
    Aage ka rate predict karne ke liye ek row banata hai.

    App me jab kisan "Wheat, Karnal Mandi" chunta hai, tab hum
    us crop+mandi ka latest data lete hain aur next month ke liye
    ek feature row banate hain.

    Return: 1 row ka DataFrame (model ka input), ya None agar data na mile.
    """
    # Sirf chuni hui crop + mandi ka data
    part = df[(df["crop"] == crop) & (df["mandi"] == mandi)]

    # Data hi nahi mila to kuch nahi kar sakte
    if part.empty:
        return None

    # Purana pehle, naya baad me -> last row sabse latest hai
    part = part.sort_values("date")

    # Last 3 mahino ke rate (lag_1, lag_2, lag_3 ke liye)
    last_3 = part["modal_price"].tail(3).tolist()

    # Agar 3 mahine ka data nahi hai to prediction nahi banegi
    if len(last_3) < 3:
        return None

    # Latest row se min/max price aur date lo
    latest = part.iloc[-1]

    # Next month ki date (prediction kis mahine ke liye hai)
    next_date = latest["date"] + pd.DateOffset(months=1)

    # Ek nayi row banao (dictionary -> DataFrame)
    row = {
        "month": next_date.month,
        "year": next_date.year,
        "crop_code": CROP_CODES.get(crop),
        "mandi_code": _mandi_code(df, mandi),
        "min_price": latest["min_price"],
        "max_price": latest["max_price"],
        "price_range": latest["max_price"] - latest["min_price"],
        # last_3 ka ulta order: latest pehle
        "lag_1": last_3[-1],
        "lag_2": last_3[-2],
        "lag_3": last_3[-3],
        "rolling_mean_3": sum(last_3) / 3,
    }

    return pd.DataFrame([row])[FEATURE_COLUMNS]


def _mandi_code(df: pd.DataFrame, mandi: str) -> int:
    """
    Mandi ka number nikalta hai (wahi tarika jo add_encode_features me hai).
    """
    mandi_codes = {m: i for i, m in enumerate(sorted(df["mandi"].unique()))}
    return mandi_codes.get(mandi)


# Ye code sirf tab chalta hai jab file seedha run karo:
# python features.py
if __name__ == "__main__":
    X, y = build_features()

    print("Features ready!")
    print("X ka shape:", X.shape)
    print("y ka shape:", y.shape)
    print("\nPehli 5 rows:")
    print(X.head().to_string())
    print("\nPehle 5 rate (y):")
    print(y.head().to_string())
