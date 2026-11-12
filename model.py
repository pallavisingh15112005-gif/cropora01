"""
model.py
--------
Kaam: bhav ka anumaan lagana (predict) aur kisan ko salah dena.

Is file me 3 kaam hote hain:
1. predict_price() -> LinearRegression se agle 7 din ka rate
2. get_advice()    -> prediction dekh ke Hindi me salah
3. get_accuracy()  -> model kitna sahi hai (MAE)

LinearRegression kya hai?
  Data me ek seedhi line fit karta hai: rate = slope * time + c
  Slope positive ho to bhav badh raha hai, negative ho to gir raha hai.

Moving average kya hai?
  Pichle kuch rates ka simple average. Ye comparison ke liye hai --
  agar line aur average dono ek hi baat kahein to prediction bharosemand hai.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from data_loader import KEEP_CROPS, load_data, standardize_crop_name

# Agle kitne din (points) ka anumaan lagega
FORECAST_STEPS = 7


def _get_series(crop: str, df: pd.DataFrame | None = None):
    """
    Crop ka rate series nikalta hai (saari mandiyon ka average).

    Return: (crop_name, series, error)
      series ka index = date, value = modal_price
    """
    # Data load karo (agar bahar se diya hai to wahi)
    if df is None:
        df = load_data()

    # Crop naam standard karo (Hindi/English)
    crop_name = standardize_crop_name(crop)

    if crop_name is None:
        return None, None, (
            f"'{crop}' naam ka crop nahi mila. In 12 crops me se koi chuno: "
            + ", ".join(KEEP_CROPS)
        )

    # Sirf is crop ka data
    part = df[df["crop"] == crop_name]

    if part.empty:
        return None, None, f"{crop_name} ka koi data nahi mila."

    # Har date ka average rate -> ek line
    series = part.groupby("date")["modal_price"].mean().sort_index()

    # Model ke liye kam se kam 2 points zaroori hain
    if len(series) < 2:
        return None, None, f"{crop_name} ke liye kaafi data nahi hai."

    return crop_name, series, None


def predict_price(crop: str, days: int = 7, df: pd.DataFrame | None = None) -> dict:
    """
    Pichle `days` rate points par LinearRegression train karta hai aur
    agle 7 din (points) ka price predict karta hai.

    Comparison ke liye moving average bhi nikalta hai.

    Return: dictionary
        history_dates / history_prices -> jo data model ne dekha
        forecast_dates / forecast_prices -> agle 7 din ka anumaan
        change_percent -> aaj ke rate se anumaan kitna % upar/neeche
        linear_pred, ma_pred -> dono tariko ka agla rate
        slope -> har mahine rate kitna badal raha hai
        error -> None ya message
    """
    # 1. Crop ka data series lo
    crop_name, series, error = _get_series(crop, df)

    if error:
        return {"error": error}

    # 2. Kam se kam 2 points chahiye
    if days < 2:
        return {"error": "Prediction ke liye days kam se kam 2 hona chahiye."}

    # 3. Pichle `days` points hi training data hain
    history = series.tail(days)

    if len(history) < 2:
        return {"error": f"{crop_name} ke paas sirf {len(history)} rate point hai."}

    # 4. Model ka input (X) aur output (y) banao
    #    X = 0,1,2,3... (time), y = rate
    x = np.arange(len(history)).reshape(-1, 1)
    y = history.values

    # 5. LinearRegression train karo
    model = LinearRegression()
    model.fit(x, y)

    # 6. Agle FORECAST_STEPS points ke liye X banao aur predict karo
    future_x = np.arange(len(history), len(history) + FORECAST_STEPS).reshape(-1, 1)
    forecast = model.predict(future_x)

    # 7. Price negative nahi ho sakta, isliye 0 se neeche sab 0
    forecast_prices = [max(0.0, round(float(v), 2)) for v in forecast]

    # 8. Aaj ka (last) rate aur anumaan ka average
    last_price = float(y[-1])
    avg_forecast = round(float(np.mean(forecast_prices)), 2)
    change_percent = round((avg_forecast - last_price) / last_price * 100, 2)

    # 9. Moving average (pichle 3 points ka) -- comparison ke liye
    ma_window = min(3, len(y))
    ma_pred = round(float(np.mean(y[-ma_window:])), 2)

    # 10. Agle 7 din ki dates (data monthly hai, isliye mahine jodte hain)
    last_date = history.index[-1]
    forecast_dates = [
        (last_date + pd.DateOffset(months=i)).strftime("%Y-%m-%d")
        for i in range(1, FORECAST_STEPS + 1)
    ]

    # 11. Trend ka naam
    if change_percent > 0.5:
        trend = "up"
    elif change_percent < -0.5:
        trend = "down"
    else:
        trend = "flat"

    return {
        "crop": crop_name,
        "history_dates": [d.strftime("%Y-%m-%d") for d in history.index],
        "history_prices": [round(float(v), 2) for v in y],
        "forecast_dates": forecast_dates,
        "forecast_prices": forecast_prices,
        "last_price": round(last_price, 2),
        "avg_forecast": avg_forecast,
        "change_percent": change_percent,
        "trend": trend,
        # LinearRegression ka pehla anumaan
        "linear_pred": round(float(forecast_prices[0]), 2),
        # Moving average ka anumaan (pichle 3 ka average)
        "ma_pred": ma_pred,
        # Slope = har mahine rate kitna badal raha hai (₹ me)
        "slope": round(float(model.coef_[0]), 2),
        "error": None,
    }


def get_advice(crop: str, days: int = 7, df: pd.DataFrame | None = None) -> dict:
    """
    Prediction dekh ke Hindi me salah deta hai.

    Rule:
      - Agle 7 din me bhav 1% se zyada badhne ka anumaan -> "kuch din ruko"
      - Bhav girne ya sthir rehne ka anumaan            -> "abhi bechna theek hai"

    Return: dictionary
        advice -> "abhi bechna theek hai" ya "kuch din ruko"
        reason -> Hindi me wajah (numbers ke saath)
        ...
    """
    # 1. Pehle prediction nikaalo
    result = predict_price(crop, days, df)

    # Prediction fail hui to wahi error wapas do
    if result.get("error"):
        return {"error": result["error"]}

    change = result["change_percent"]
    current = result["last_price"]
    expected = result["avg_forecast"]

    # 2. Salah ka faisla
    if change >= 1.0:
        advice = "kuch din ruko"
        reason = (
            f"Agle {FORECAST_STEPS} din me {result['crop']} ka bhav "
            f"₹{current} se badhkar lagbhag ₹{expected} ({change}%) "
            "ho sakta hai. Thoda intezaar karo, behtar rate mil sakta hai."
        )
    elif change <= -1.0:
        advice = "abhi bechna theek hai"
        reason = (
            f"Agle {FORECAST_STEPS} din me {result['crop']} ka bhav "
            f"₹{current} se girkar lagbhag ₹{expected} ({change}%) "
            "ho sakta hai. Abhi bech do, warna nuksan ho sakta hai."
        )
    else:
        advice = "abhi bechna theek hai"
        reason = (
            f"{result['crop']} ka bhav lagbhag sthir hai "
            f"(₹{current} se ₹{expected}, {change}%). "
            "Rate zyada nahi badlega, isliye abhi bech sakte ho."
        )

    return {
        "crop": result["crop"],
        "advice": advice,
        "reason": reason,
        "current_price": current,
        "expected_price": expected,
        "change_percent": change,
        "error": None,
    }


def get_accuracy(crop: str, df: pd.DataFrame | None = None) -> dict:
    """
    Model ki accuracy check karta hai.

    Tarika:
      1. Data ke do hisse karo: train (80%) aur test (20%)
      2. Sirf train par model sikhata hai
      3. Test par predict karke asli rate se compare karta hai
      4. MAE = average galti (₹ me)

    Chhota MAE = achha model.
    """
    # 1. Crop ka data series lo
    crop_name, series, error = _get_series(crop, df)

    if error:
        return {"error": error}

    # 2. Accuracy ke liye kam se kam 10 points chahiye
    if len(series) < 10:
        return {"error": f"{crop_name} ke paas kam se kam 10 rate points chahiye."}

    # 3. Input (X) aur output (y)
    x = np.arange(len(series)).reshape(-1, 1)
    y = series.values

    # 4. 80% train, 20% test (time order me, shuffle nahi)
    split = int(len(series) * 0.8)
    x_train, x_test = x[:split], x[split:]
    y_train, y_test = y[:split], y[split:]

    # 5. Model train karo
    model = LinearRegression()
    model.fit(x_train, y_train)

    # 6. Test data par predict karo
    predictions = model.predict(x_test)

    # 7. MAE nikalo: har galti ka average (₹ me)
    mae = mean_absolute_error(y_test, predictions)

    # 8. MAE ko percent me bhi batao (samajhna aasan hota hai)
    avg_price = float(np.mean(y))
    mae_percent = round(mae / avg_price * 100, 2)

    # 9. Simple rating
    if mae_percent <= 5:
        rating = "achha"
    elif mae_percent <= 10:
        rating = "theek"
    else:
        rating = "sudhaarne ki zaroorat hai"

    return {
        "crop": crop_name,
        "mae": round(float(mae), 2),
        "mae_percent": mae_percent,
        "rating": rating,
        "avg_price": round(avg_price, 2),
        "train_points": split,
        "test_points": len(series) - split,
        "error": None,
    }


# Ye code sirf tab chalta hai jab file seedha run karo:
# python model.py
if __name__ == "__main__":
    for crop in ["Wheat", "Tomato", "Onion"]:
        print("=" * 50)
        print("Crop:", crop)

        # Prediction
        pred = predict_price(crop)
        if pred.get("error"):
            print("Error:", pred["error"])
            continue
        print("Aaj ka rate: ₹", pred["last_price"])
        print("Agle 7 din ka anumaan:", pred["forecast_prices"])
        print("Change:", pred["change_percent"], "% | trend:", pred["trend"])

        # Salah
        advice = get_advice(crop)
        print("Salah:", advice["advice"])
        print("Wajah:", advice["reason"])

        # Accuracy
        acc = get_accuracy(crop)
        print("MAE: ₹", acc["mae"], "| MAE%:", acc["mae_percent"], "|", acc["rating"])
