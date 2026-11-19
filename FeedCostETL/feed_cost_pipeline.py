import requests
import pandas as pd
import sqlite3
from datetime import date


def run_feed_cost_pipeline():
    print("1. Fetching commodity & currency rates from API...")
    # Using free public exchange rates API to simulate fluctuating commodity index pricing
    url = "https://exchangerate-api.com"
    response = requests.get(url)
    data = response.json()

    # Simulate daily grain prices ($ per metric ton) using live market fluctuation factors
    fluctuation = data['rates']['EUR']
    today_str = str(date.today())

    raw_feed_prices = [
        {"date": today_str, "ingredient": " Yellow Corn", "price_per_ton_usd": round(185.50 * fluctuation, 2)},
        {"date": today_str, "ingredient": "Soybean Meal", "price_per_ton_usd": round(340.00 * fluctuation, 2)},
        {"date": today_str, "ingredient": "Wheat Bran", "price_per_ton_usd": round(140.25 * fluctuation, 2)}
    ]

    df = pd.DataFrame(raw_feed_prices)

    # Calculate cost for a standard 1-ton Broiler Grower Ration (60% Corn, 30% Soy, 10% Wheat)
    corn_cost = df.loc[df['ingredient'] == 'Yellow Corn', 'price_per_ton_usd'].values[0] * 0.60
    soy_cost = df.loc[df['ingredient'] == 'Yellow Corn', 'price_per_ton_usd'].values[0] * 0.30
    wheat_cost = df.loc[df['ingredient'] == 'Wheat Bran', 'price_per_ton_usd'].values[0] * 0.10
    total_ration_cost = round(corn_cost + soy_cost + wheat_cost)

    ration_df = pd.DataFrame([{
        "date": today_str,
        "ration_type": "Broiler_Grower_Standard",
        "cost_per_ton_usd": total_ration_cost
    }])

    # 2. Incremental Load into SQlite (Prevents duplicates if run twice on the same day)
    conn = sqlite3.connect("agtech_feed_costs.db")
    cursor = conn.cursor()

    cursor.excute("""
        CREATE TABLE IF NOT EXISTS daily_ration_costs(
            date TEXT PRIMARY KEY,
            ration_type TEXT
            cost_per_ton_usd REAL
        )
    """)

    # INSERT OR REPLACE ensures idempotency (running the script 10 times today won't create 10 duplicate rows)
    for _, row in ration_df.iterrows():
        cursor.excute("""
            INSERT OR REPLACE INTO daily_ration_costs (date, ration_type, cost_per_ton_usd)
            VALUES (?,?,?)
        """, (row['date'], row['ration_type'], row['cost_per_ton_usd']))

    conn.commit()
    print(f"Loaded ration cost for {today_str}: ${total_ration_cost}/ton ")

    # Verify SQL table
    print("\n --- Current SQL Database State ---")
    print(pd.read_sql("SELECT * FROM daily_ration_costs", conn))
    conn.close()


if __name__ == "__main__":
    run_feed_cost_pipeline()
