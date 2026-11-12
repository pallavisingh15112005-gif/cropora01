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

from data_loader import KEEP_CROPS, load_data

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
