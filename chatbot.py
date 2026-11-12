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

import difflib
import re

from data_loader import CROP_KEYWORDS, CROP_NAME_MAP, load_data
from features import compare_mandis, get_latest_price, get_trend
from model import get_advice

# Crop na milne par yahi message jayega
NO_CROP_MSG = (
    "Kripya crop ka naam batayein. Ye 12 crops hain: gehu, chawal, makka, "
    "chana, aloo, pyaz, tamatar, sarson, kela, seb, anar, papita."
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


# Fuzzy matching se pehle in aam shabdon ko chhod dena hai
# (warna "kya haal hai" jaisa sentence galti se crop ban jayega)
STOPWORDS = {
    "kya", "kyu", "kyun", "ka", "ki", "ke", "me", "hai", "hain", "ho",
    "kaise", "kaisa", "kitna", "kitne", "kitni", "bhav", "bhaav", "rate",
    "price", "mandi", "aaj", "kal", "abhi", "karo", "karu", "batao", "bata",
    "dikhao", "chahiye", "bechna", "bech", "ruko", "salah", "trend", "haal",
    "hal", "hello", "help", "thanks", "dhanyavad", "namaste", "sabse",
    "sasta", "mehnga", "mujhe", "mera", "meri", "kisan", "crop", "fasal",
    "mausam", "kaam", "baat", "acha", "achha", "theek", "nahi", "haan",
}


def _find_crop(message: str):
    """
    Message me se crop ka naam dhoondhta hai.

    Teen tarike se dhoondhta hai:
    1. Exact shabd       -> "aloo"
    2. Lamba keyword      -> "aloo_ka_bhav" ke andar bhi mil jaye
    3. Fuzzy (galat spelling) -> "aalu", "tamater", "gahu" bhi pakad le

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
    #    Dhyaan: match shabd ke shuru se hona chahiye, warna
    #    "price" ke andar "rice" match ho jata hai.
    for key in sorted(CROP_NAME_MAP, key=len, reverse=True):
        if len(key) < 4:
            continue

        pattern = r"(?<![a-z0-9\u0900-\u097F])" + re.escape(key)

        if re.search(pattern, text):
            return CROP_NAME_MAP[key]

    # 4. Fuzzy match -- galat spelling wale shabd bhi pehchan lo
    #    difflib "aalu" ko "aloo" se mila deta hai
    for word in words:
        # Bahut chhote shabd (jaise "ka", "me") aur aam shabd skip karo
        if len(word) < 4 or word in STOPWORDS:
            continue

        # Sabse milta-julta keyword dhoondo (0.8 = kam se kam 80% match)
        close = difflib.get_close_matches(word, CROP_KEYWORDS, n=1, cutoff=0.8)

        if close:
            return CROP_NAME_MAP[close[0]]

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


def _per_kg(value: float) -> str:
    """Per quintal se per kg banao (1 quintal = 100 kg): 2025 -> ₹20.25"""
    return f"₹{value / 100:,.2f}"


def _advice_block(crop: str, df) -> str:
    """
    Bechne ki salah ki 2 lines banata hai:
    - Salah kya hai
    - Kab bechna chahiye
    """
    advice = get_advice(crop, 7, df)

    if advice.get("error"):
        return ""

    expected = advice["expected_price"]
    change = advice["change_percent"]

    if advice["advice"] == "kuch din ruko":
        kab = "5-7 din ruk kar becho, rate badhne ka anumaan hai."
    else:
        kab = "Abhi bech do, rate girne ka anumaan hai."

    return (
        f"\n\n**Salah: {advice['advice'].upper()}**\n"
        f"- Agle 7 din ka anumaan: {_money(expected)}/quintal "
        f"({_per_kg(expected)}/kg, {change:+.1f}%)\n"
        f"- Kab beche: {kab}"
    )


def _mandi_wise_lines(crop: str, selected_mandi, df) -> str:
    """
    Har mandi ka modal bhav list karta hai (per quintal + per kg).
    Sabse zyada bhav wali mandi sabse upar.
    """
    comparison = compare_mandis(crop, df)

    if comparison.get("error"):
        return ""

    lines = ["", "**Mandi-wise modal bhav (per quintal / per kg):**"]

    for _, row in comparison["table"].iterrows():
        # Jo mandi user ne chuni hai use mark karo
        mark = "  <- aapki mandi" if selected_mandi == row["mandi"] else ""

        lines.append(
            f"- {row['mandi']}: {_money(row['modal_price'])} "
            f"({_per_kg(row['modal_price'])}/kg){mark}"
        )

    return "\n".join(lines)


def _price_answer(crop: str, mandi, df, place=None) -> dict:
    """
    Crop (aur mandi) ka latest bhav ka jawab banata hai.

    Jawab me aata hai:
    - per quintal aur per kg bhav (date ke saath)
    - saari mandiyon ka bhav
    - bechne ki salah aur kab bechna hai
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
            f"Mandi: saari mandiyon ka average ({result['mandis_count']} mandiyan)"
        )
        if place:
            note = (
                f"\n\nNote: '{place.capitalize()}' ka data is dataset me nahi hai, "
                "isliye saari mandiyon ka average bata raha hoon."
            )
    else:
        mandi_line = f"Mandi: {result['mandi']}"

    # 5. Price lines (quintal + kg, dono)
    answer = (
        f"{result['crop']} ka taaza bhav -- {result['date']}\n"
        f"- Modal bhav: {_money(result['modal_price'])}/quintal "
        f"({_per_kg(result['modal_price'])}/kg)\n"
        f"- Kam se kam: {_money(result['min_price'])}/quintal "
        f"({_per_kg(result['min_price'])}/kg)\n"
        f"- Zyada se zyada: {_money(result['max_price'])}/quintal "
        f"({_per_kg(result['max_price'])}/kg)\n"
        f"- {mandi_line}"
    )

    # 6. Saari mandiyon ka rate
    answer += _mandi_wise_lines(crop, mandi, df)

    # 7. Bechne ki salah
    answer += _advice_block(crop, df)

    return {
        "answer": answer + note,
        "crop": result["crop"],
        "mandi": result["mandi"],
        "error": None,
    }


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


def _trend_answer(crop: str, df) -> dict:
    """Pichle 7 mahino ka trend aur % badlav batata hai."""
    # 1. Trend nikalo (default 7 points)
    result = get_trend(crop, 7, df)

    if result.get("error"):
        return {"answer": result["error"], "error": result["error"]}

    # 2. Rates ki chhoti list banao: 2764 -> 2736 -> ...
    prices = " -> ".join(_money(p) for p in result["prices"])

    # 3. Sabse latest rate (per quintal + per kg, date ke saath)
    last_price = result["prices"][-1]
    last_date = result["dates"][-1]

    answer = (
        f"{result['summary']}\n"
        f"Ab ka bhav ({last_date}): {_money(last_price)}/quintal "
        f"({_per_kg(last_price)}/kg)\n"
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
    if result["advice"] == "kuch din ruko":
        kab = "5-7 din ruk kar becho, rate badhne ka anumaan hai."
    else:
        kab = "Abhi bech do, rate girne ka anumaan hai."

    answer = (
        f"**Salah: {result['advice'].upper()}**\n"
        f"{result['reason']}\n"
        f"- Aaj ka bhav: {_money(result['current_price'])}/quintal "
        f"({_per_kg(result['current_price'])}/kg)\n"
        f"- Agle 7 din ka anumaan: {_money(result['expected_price'])}/quintal "
        f"({_per_kg(result['expected_price'])}/kg)\n"
        f"- Kab beche: {kab}"
    )

    # 3. Kis mandi me kitna -- sabse achhi aur sabse kam mandi
    comparison = compare_mandis(crop, df)
    if not comparison.get("error"):
        answer += (
            f"\n- Sabse zyada bhav: {comparison['best_mandi']} me "
            f"{_money(comparison['best_price'])}/quintal "
            f"({_per_kg(comparison['best_price'])}/kg)\n"
            f"- Sabse kam bhav: {comparison['worst_mandi']} me "
            f"{_money(comparison['worst_price'])}/quintal "
            f"({_per_kg(comparison['worst_price'])}/kg)"
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
