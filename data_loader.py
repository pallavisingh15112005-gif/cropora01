"""
data_loader.py
--------------
Kaam: mandi_prices.csv ko load karna aur saaf karna.

Cleaning ke 4 step:
1. missing values wali rows hatao
2. date ko datetime me badlo
3. price columns ko number me badlo
4. crop ke naam standard karo (Hindi/English -> ek hi naam)

Sirf 12 crops rakhe jaate hain.
"""

from pathlib import Path

import pandas as pd

# CSV file isi folder me hai
DATA_FILE = Path(__file__).parent / "mandi_prices.csv"

# Sirf ye 12 crops project me rahenge
KEEP_CROPS = [
    "Wheat",
    "Rice",
    "Maize",
    "Gram",
    "Potato",
    "Onion",
    "Tomato",
    "Mustard",
    "Banana",
    "Apple",
    "Pomegranate",
    "Papaya",
]

# Alag-alag naam (Hindi, English, spelling) -> ek standard English naam
# Key hamesha chhote letters (lowercase) me likhni hai.
CROP_NAME_MAP = {
    # Wheat - गेहूं
    "wheat": "Wheat",
    "gehu": "Wheat",
    "gehun": "Wheat",
    "gehoon": "Wheat",
    "गेहूं": "Wheat",
    "गेहू": "Wheat",
    # Rice - चावल / धान
    "rice": "Rice",
    "chawal": "Rice",
    "chaawal": "Rice",
    "paddy": "Rice",
    "dhan": "Rice",
    "चावल": "Rice",
    "धान": "Rice",
    # Maize - मक्का
    "maize": "Maize",
    "makka": "Maize",
    "makai": "Maize",
    "corn": "Maize",
    "मक्का": "Maize",
    "मकई": "Maize",
    # Gram - चना
    "gram": "Gram",
    "chana": "Gram",
    "channa": "Gram",
    "चना": "Gram",
    # Potato - आलू
    "potato": "Potato",
    "aloo": "Potato",
    "alu": "Potato",
    "आलू": "Potato",
    # Onion - प्याज
    "onion": "Onion",
    "pyaz": "Onion",
    "piyaz": "Onion",
    "kanda": "Onion",
    "प्याज": "Onion",
    # Tomato - टमाटर
    "tomato": "Tomato",
    "tamatar": "Tomato",
    "टमाटर": "Tomato",
    # Mustard - सरसों
    "mustard": "Mustard",
    "sarson": "Mustard",
    "sarso": "Mustard",
    "सरसों": "Mustard",
    # Banana - केला
    "banana": "Banana",
    "kela": "Banana",
    "केला": "Banana",
    # Apple - सेब
    "apple": "Apple",
    "seb": "Apple",
    "सेब": "Apple",
    # Pomegranate - अनार
    "pomegranate": "Pomegranate",
    "anar": "Pomegranate",
    "अनार": "Pomegranate",
    # Papaya - पपीता
    "papaya": "Papaya",
    "papeeta": "Papaya",
    "पपीता": "Papaya",
}

# Ye columns number hone chahiye
PRICE_COLUMNS = ["min_price", "max_price", "modal_price"]


def load_data(file_path=DATA_FILE) -> pd.DataFrame:
    """
    CSV load karta hai, saaf karta hai aur clean DataFrame return karta hai.
    """
    # 1. CSV padho
    df = pd.read_csv(file_path)

    # Column names ke space hatao aur chhote letters me karo
    df.columns = [col.strip().lower() for col in df.columns]

    # 2. Crop ke naam standard karo
    #    pehle text saaf karo: space hatao, chhote letters me karo
    df["crop"] = df["crop"].astype(str).str.strip().str.lower()
    #    phir mapping dict se standard naam nikaalo
    df["crop"] = df["crop"].map(CROP_NAME_MAP)

    # 3. Date ko datetime me badlo (jo parse na ho, wo NaT ban jayega)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 4. Price columns ko number me badlo (galat value -> NaN)
    for col in PRICE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5. Missing values wali rows hatao
    #    (date, crop ya price khali ho to us row ka koi matlab nahi)
    df = df.dropna(subset=["date", "crop", "modal_price"])

    # Price 0 ya negative ho to wo bhi bekaar hai
    df = df[df["modal_price"] > 0]

    # 6. Sirf 12 crops rakho (jo mapping me nahi mile wo hata do)
    df = df[df["crop"].isin(KEEP_CROPS)]

    # Purana data pehle, naya baad me
    df = df.sort_values(["crop", "state", "mandi", "date"]).reset_index(drop=True)

    return df
