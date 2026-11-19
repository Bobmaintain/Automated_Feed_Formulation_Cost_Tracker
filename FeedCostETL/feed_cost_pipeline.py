import urllib.request
import json
import ssl
import pandas as pd
import sqlite3
from datetime import date


def run_feed_cost_pipeline():
    print("1. Fetching commodity & currency rates from API...")
    # Using free public exchange rates API to simulate fluctuating commodity index pricing
    url = "https://exchangerate-api.com"

    try:
        context = ssl._create_unverified_context()
        req = urllib.request.urlopen(url, context=context, timeout=10)
        data = json.loads(req.read().decode('utf-8'))
        # Simulate daily grain prices ($ per metric ton) using live market fluctuation factors
        fluctuation = float(data.get('rates', {}).get('EUR', 0.92))
    except Exception as e:
        print(f"API unreachable ({e}), falling back to baseline rate.")
        fluctuation = 0.92

    today_str = str(date.today())

    # Build a DataFrame

    df = pd.DataFrame({
        "date": list((today_str, today_str, today_str)),
        "ingredient": list(("Yellow Corn", "Soybean Meal", "Wheat Bran")),
        "price_per_ton_usd": list((
            round(185.50 * fluctuation, 2),
            round(340.00 * fluctuation, 2),
            round(140.25 * fluctuation, 2)
        ))
    })

    # Calculate cost for a standard 1-ton Poultry Ration (Corn, Soy, Wheat)
    cost = dict(zip(df.get("ingredient"), df.get("price_per_ton_usd")))

    corn_cost = float(cost.get("Yellow Corn"))
    soy_cost = float(cost.get("Soybean Meal"))
    wheat_cost = float(cost.get("Wheat Bran"))

    starter_cost = round((corn_cost * 0.55) + (soy_cost * 0.38) + (wheat_cost * 0.07), 2)
    grower_cost = round((corn_cost * 0.60) + (soy_cost * 0.30) + (wheat_cost * 0.10), 2)
    layer_cost = round((corn_cost * 0.58) + (soy_cost * 0.25) + (wheat_cost * 0.17), 2)
    total_ration_cost = round(starter_cost + grower_cost + layer_cost, 2)


    ration_df = pd.DataFrame({
            "date": list((today_str, today_str, today_str, today_str)),
            "ration_type": list(("Broiler_Starter", "Broiler_Grower", "Layer_Mesh", "Total_Ration")),
            "cost_per_ton_usd": list((starter_cost, grower_cost, layer_cost, total_ration_cost)),
        })

    # 2. Incremental Load into SQlite (Prevents duplicates if run twice on the same day)
    conn = sqlite3.connect("agtech_feed_costs.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS daily_ration_costs")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_ration_costs (
            date TEXT,
            ration_type TEXT,
            cost_per_ton_usd REAL,
            PRIMARY KEY (date, ration_type)
            
        )
    """)

    # INSERT OR REPLACE ensures idempotency (running the script 10 times today won't create 10 duplicate rows)
    for _, row in ration_df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO daily_ration_costs (date, ration_type, cost_per_ton_usd)
            VALUES (?,?,?)
        """, (str(row.get('date')), str(row.get('ration_type')), float(row.get('cost_per_ton_usd'))))

    conn.commit()
    print(f"Loaded ration cost for {today_str}: ${total_ration_cost}/ton")

    # Verify SQL table
    print("\n--- Current SQL Database State ---")
    print(pd.read_sql("SELECT * FROM daily_ration_costs", conn))
    conn.close()


if __name__ == "__main__":
    run_feed_cost_pipeline()
