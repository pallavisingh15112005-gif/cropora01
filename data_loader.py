"""
data_loader.py
--------------
Kaam: mandi_prices.csv ko load karna aur saaf karna.

Cleaning ke 5 step:
1. text columns ke extra space hatao
2. crop ke naam standard karo (Hindi/English -> ek hi English naam)
3. date ko datetime me badlo
4. price columns ko number me badlo
5. missing values wali rows hatao

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
    "gahu": "Wheat",
    "gahoon": "Wheat",
    "गेहूं": "Wheat",
    "गेहूँ": "Wheat",
    "गेहू": "Wheat",
    # Rice - चावल / धान
    "rice": "Rice",
    "chawal": "Rice",
    "chaawal": "Rice",
    "chaval": "Rice",
    "chawel": "Rice",
    "paddy": "Rice",
    "dhan": "Rice",
    "चावल": "Rice",
    "धान": "Rice",
    # Maize - मक्का
    "maize": "Maize",
    "makka": "Maize",
    "makkaa": "Maize",
    "makai": "Maize",
    "makki": "Maize",
    "corn": "Maize",
    "मक्का": "Maize",
    "मकई": "Maize",
    # Gram - चना
    "gram": "Gram",
    "chana": "Gram",
    "channa": "Gram",
    "chane": "Gram",
    "चना": "Gram",
    "चने": "Gram",
    # Potato - आलू
    "potato": "Potato",
    "aloo": "Potato",
    "aalu": "Potato",
    "aaloo": "Potato",
    "alu": "Potato",
    "batata": "Potato",
    "आलू": "Potato",
    "आलु": "Potato",
    # Onion - प्याज
    "onion": "Onion",
    "pyaz": "Onion",
    "pyaaz": "Onion",
    "pyaj": "Onion",
    "pyaaj": "Onion",
    "piyaz": "Onion",
    "piyaj": "Onion",
    "kanda": "Onion",
    "प्याज": "Onion",
    "प्याज़": "Onion",
    # Tomato - टमाटर
    "tomato": "Tomato",
    "tamatar": "Tomato",
    "tamater": "Tomato",
    "tamaatar": "Tomato",
    "tomatr": "Tomato",
    "टमाटर": "Tomato",
    # Mustard - सरसों
    "mustard": "Mustard",
    "sarson": "Mustard",
    "sarso": "Mustard",
    "sarsu": "Mustard",
    "सरसों": "Mustard",
    # Banana - केला
    "banana": "Banana",
    "kela": "Banana",
    "kella": "Banana",
    "केला": "Banana",
    # Apple - सेब
    "apple": "Apple",
    "seb": "Apple",
    "saeb": "Apple",
    "सेब": "Apple",
    # Pomegranate - अनार
    "pomegranate": "Pomegranate",
    "anar": "Pomegranate",
    "anaar": "Pomegranate",
    "अनार": "Pomegranate",
    # Papaya - पपीता
    "papaya": "Papaya",
    "papita": "Papaya",
    "papeeta": "Papaya",
    "papaiya": "Papaya",
    "पपीता": "Papaya",
}

# Fuzzy matching ke liye saare keywords ki list
CROP_KEYWORDS = list(CROP_NAME_MAP.keys())

# Ye columns number hone chahiye
PRICE_COLUMNS = ["min_price", "max_price", "modal_price"]

# In columns me value khali nahi honi chahiye
REQUIRED_COLUMNS = ["date", "state", "district", "mandi", "crop"] + PRICE_COLUMNS

# In columns me text hota hai (inhe saaf karna hai)
TEXT_COLUMNS = ["state", "district", "mandi", "crop"]


def standardize_crop_name(name):
    """
    Kisi bhi crop ke naam ko standard English naam me badalta hai.

    Example: "gehu" -> "Wheat", "टमाटर" -> "Tomato"
    Agar naam list me nahi mila to None return karta hai.

    (chatbot.py me bhi yahi function kaam aayega)
    """
    if name is None:
        return None

    # Name ko text banao, aage-piche ka space hatao, chhote letters me karo
    key = str(name).strip().lower()

    # Mapping dict me dhoondo
    return CROP_NAME_MAP.get(key)


def load_data(file_path=DATA_FILE) -> pd.DataFrame:
    """
    CSV load karta hai, saaf karta hai aur clean DataFrame return karta hai.

    Yahi ek function app, model aur chatbot -- sab use karenge.
    """
    # 1. CSV padho
    df = pd.read_csv(file_path)

    # Column names ke space hatao aur chhote letters me karo
    df.columns = [col.strip().lower() for col in df.columns]

    # 2. Text columns saaf karo (extra space hatao)
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 3. Crop ke naam standard karo
    #    "gehu", "गेहूं" sab "Wheat" ban jayenge
    df["crop"] = df["crop"].apply(standardize_crop_name)

    # 4. Date ko datetime me badlo (jo parse na ho, wo NaT ban jayega)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 5. Price columns ko number me badlo (galat value -> NaN)
    for col in PRICE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6. Missing values wali rows hatao
    #    (date, crop, mandi ya price khali ho to us row ka koi matlab nahi)
    df = df.dropna(subset=REQUIRED_COLUMNS)

    # Price 0 ya negative ho to wo bhi bekaar hai
    df = df[df["modal_price"] > 0]

    # 7. Sirf 12 crops rakho (jo mapping me nahi mile wo hata do)
    df = df[df["crop"].isin(KEEP_CROPS)]

    # Purana data pehle, naya baad me
    df = df.sort_values(["crop", "state", "mandi", "date"]).reset_index(drop=True)

    return df


# Ye code sirf tab chalta hai jab file seedha run karo:
# python data_loader.py
if __name__ == "__main__":
    data = load_data()

    print("Data load ho gaya!")
    print("Rows:", len(data))
    print("Crops:", data["crop"].nunique())
    print("Mandis:", data["mandi"].nunique())
    print("Date range:", data["date"].min().date(), "se", data["date"].max().date())
    print("\nPehli 5 rows:")
    print(data.head().to_string())
