"""
chatbot.py
----------
Kaam: user ke sawaal ka Hindi me jawab dena.

Tarika (simple keyword matching):
1. Message ko chhote letters me badlo
2. Usme crop ka naam dhoondo (Hindi ya English)
3. Usme mandi ka naam dhoondo (jaise "Karnal")
4. Sawaal ke hisaab se kaam chuno:
      - price  -> get_latest_price()
      - trend  -> get_trend()
      - salah  -> get_advice()
5. Hindi me jawab banao

Yahan koi AI/LLM nahi hai -- sirf keywords se samajhna, isliye ye
college project ke liye halka aur bharosemand hai.
"""

import re

from data_loader import CROP_NAME_MAP, load_data, standardize_crop_name
from features import get_latest_price, get_trend
from model import get_advice

# Crop na milne par yahi message jayega
NO_CROP_MSG = (
    "Kripya crop ka naam batayein, jaise: gehu, chawal, aloo, tamatar, "
    "pyaz, sarson, kela, seb."
)

# In shabdon ka matlab hai: user trend poochh raha hai
TREND_WORDS = [
    "trend", "rukh", "badh", "badhega", "gir", "girega", "gira",
    "upar", "neeche", "pichle", "hafta", "hafton", "mahina", "mahine",
    "mahino", "chart", "graph", "बढ़", "गिर", "रुझान",
]

# In shabdon ka matlab hai: user salah poochh raha hai
ADVICE_WORDS = [
    "salah", "salaah", "bech", "bechu", "bechna", "bechen", "bechun",
    "ruko", "ruku", "rukiye", "wait", "sell", "kya karu", "kya karun",
    "sahi hai", "theek hai", "सलाह", "बेच", "रुको",
]


def _find_crop(message: str):
    """
    Message me se crop ka naam dhoondhta hai.

    Pehle poore shabd (exact) match karta hai, phir lamba keyword
    (4+ letters) message ke andar kahin bhi ho to match kar leta hai.

    Return: standard crop naam ya None
    """
    text = message.lower().strip()

    # 1. Message ko chhote tukdon (words) me todo
    #    (Hindi akshar bhi bache rahein isliye Devanagari range rakhi hai)
    words = re.split(r"[^a-z0-9\u0900-\u097F]+", text)

    # 2. Exact word match -- sabse safe
    for word in words:
        if word in CROP_NAME_MAP:
            return CROP_NAME_MAP[word]

    # 3. Lambe keyword (4+ letters) kahin bhi mile to chalega
    #    (jaise "tamatarprice" bhi pakad me aa jaye)
    for key in sorted(CROP_NAME_MAP, key=len, reverse=True):
        if len(key) >= 4 and key in text:
            return CROP_NAME_MAP[key]

    return None


def _find_mandi(message: str, mandis):
    """
    Message me se mandi ka naam dhoondhta hai.

    "Karnal Mandi" ko hum "karnal" se bhi pehchan lete hain.
    Return: mandi ka poora naam ya None
    """
    text = message.lower()

    # Har mandi ke liye check karo
    for mandi in mandis:
        # "Karnal Mandi" -> "karnal"
        base = mandi.lower().replace("mandi", "").strip()

        # Poora naam ya sirf pehla hissa -- dono chalega
        if mandi.lower() in text or (base and base in text):
            return mandi

    return None


def _money(value: float) -> str:
    """Price ko sundar format me likhta hai: 2278 -> ₹2,278"""
    return f"₹{value:,.0f}"


def _unknown_place(message: str, mandis):
    """
    Message me aisi jagah dhoondhta hai jo mandi list me nahi hai.

    Jaise "Mirzapur me aloo ka bhav" -> "mirzapur"
    Isse hum user ko bata sakte hain ki uska shehar dataset me nahi hai.

    Return: jagah ka naam ya None
    """
    text = message.lower()

    # "kis shabd ke baad 'me' likha hai" -- wahi jagah ka naam hai
    for word in re.findall(r"([a-z\u0900-\u097F]+)\s+me\b", text):
        # Ye aam shabd hain, jagah nahi
        if word in ("ye", "yeh", "is", "us", "kis", "kaun", "kya", "aaj", "kal"):
            continue

        # Crop ka naam hai to jagah nahi
        if word in CROP_NAME_MAP:
            continue

        # Kisi mandi ka hissa hai to theek hai
        if any(word in m.lower() for m in mandis):
            continue

        return word

    return None


def _price_answer(crop: str, mandi, df, place=None) -> dict:
    """
    Crop (aur mandi) ka latest bhav ka jawab banata hai.
    Agar mandi ka data na mile to average dikha deta hai.
    """
    # 1. Latest price nikalo
    result = get_latest_price(crop, mandi, df)

    # 2. Mandi di gayi thi par mili nahi -> average dikhao
    note = ""
    if result.get("error") and mandi is not None:
        result = get_latest_price(crop, None, df)
        note = (
            f"\n\nNote: '{mandi}' ka data is dataset me nahi hai, "
            "isliye saari mandiyon ka average bata raha hoon."
        )

    # 3. Phir bhi error hai to wahi bhej do
    if result.get("error"):
        return {"answer": result["error"], "error": result["error"]}

    # 4. Mandi ki line banao
    if mandi is None:
        mandi_line = (
            f"- Mandi: saari mandiyon ka average "
            f"({result['mandis_count']} mandiyan)"
        )
        if place:
            note = (
                f"\n\nNote: '{place.capitalize()}' ka data is dataset me nahi hai, "
                "isliye saari mandiyon ka average bata raha hoon."
            )
    else:
        mandi_line = f"- Mandi: {result['mandi']}"

    # 5. Jawab tayyar karo
    answer = (
        f"{result['crop']} ka taaza bhav ({result['date']}):\n"
        f"- Kam se kam: {_money(result['min_price'])}\n"
        f"- Zyada se zyada: {_money(result['max_price'])}\n"
        f"- Modal (main) bhav: {_money(result['modal_price'])} per quintal\n"
        f"{mandi_line}"
    )

    return {
        "answer": answer + note,
        "crop": result["crop"],
        "mandi": result["mandi"],
        "error": None,
    }


def _trend_answer(crop: str, df) -> dict:
    """Pichle 7 mahino ka trend aur % badlav batata hai."""
    # 1. Trend nikalo (default 7 points)
    result = get_trend(crop, 7, df)

    if result.get("error"):
        return {"answer": result["error"], "error": result["error"]}

    # 2. Rates ki chhoti list banao: 2764 -> 2736 -> ...
    prices = " -> ".join(_money(p) for p in result["prices"])

    answer = (
        f"{result['summary']}\n"
        f"Pichle {len(result['prices'])} mahino ke rate: {prices}"
    )

    return {
        "answer": answer,
        "crop": result["crop"],
        "fig": result["fig"],
        "error": None,
    }


def _advice_answer(crop: str, df) -> dict:
    """Prediction dekh ke bechne ki salah deta hai."""
    # 1. Salah nikalo
    result = get_advice(crop, 7, df)

    if result.get("error"):
        return {"answer": result["error"], "error": result["error"]}

    # 2. Jawab
    answer = (
        f"Salah: {result['advice'].upper()}\n"
        f"{result['reason']}"
    )

    return {
        "answer": answer,
        "crop": result["crop"],
        "advice": result["advice"],
        "error": None,
    }


def reply(message: str, df=None) -> dict:
    """
    User ka message lo, Hindi me jawab do.

    Example:
        reply("Mirzapur me aloo ka bhav kya hai?")

    Return: dictionary
        answer -> Hindi jawab (string)
        crop   -> kaunsa crop samjha
        error  -> None ya message
    """
    # 1. Khali message
    if not message or not message.strip():
        return {"answer": NO_CROP_MSG, "error": "empty"}

    # 2. Data load karo
    if df is None:
        df = load_data()

    # 3. Message me se crop dhoondo
    crop = _find_crop(message)

    if crop is None:
        # Madad maang raha hai to examples dikhao
        if any(word in message.lower() for word in ["help", "madad", "kaise", "example"]):
            return {
                "answer": (
                    "Main aise sawaal samajh sakta hoon:\n"
                    "- 'gehu ka bhav kya hai?'\n"
                    "- 'Karnal mandi me aloo ka rate?'\n"
                    "- 'tamatar ka trend batao'\n"
                    "- 'pyaz bech du ya ruku?'"
                ),
                "error": None,
            }

        return {"answer": NO_CROP_MSG, "error": "no_crop"}

    # 4. Message me se mandi dhoondo
    mandis = sorted(df["mandi"].unique())
    mandi = _find_mandi(message, mandis)

    # Agar koi anjaan jagah likhi hai (jaise "Mirzapur") to yaad rakho
    place = None
    if mandi is None:
        place = _unknown_place(message, mandis)

    # 5. Sawaal ka type pehchano
    text = message.lower()

    if any(word in text for word in ADVICE_WORDS):
        # Salah wala sawaal
        return _advice_answer(crop, df)

    if any(word in text for word in TREND_WORDS):
        # Trend wala sawaal
        return _trend_answer(crop, df)

    # 6. Default: bhav batao
    return _price_answer(crop, mandi, df, place)


# Ye code sirf tab chalta hai jab file seedha run karo:
# python chatbot.py
if __name__ == "__main__":
    samples = [
        "Mirzapur me aloo ka bhav kya hai?",
        "gehu ka rate batao",
        "Karnal mandi me tamatar ka bhav?",
        "pyaz ka trend batao",
        "kya main sarson bech du ya ruku?",
        "hello",
    ]

    for question in samples:
        print("=" * 60)
        print("User:", question)
        print("Bot:", reply(question)["answer"])
