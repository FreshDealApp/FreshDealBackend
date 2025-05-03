import os
import pandas as pd
from sqlalchemy import create_engine, text, DateTime as SQLDateTime
from dotenv import load_dotenv

load_dotenv()
MYSQL_URI = os.getenv("MYSQL_URI")
if not MYSQL_URI:
    raise SystemExit("❌ Missing MYSQL_URI in .env")

engine = create_engine(MYSQL_URI)
csv_dir = "exported_tables"

# disable foreign key checks during import
txt_fk_off = text("SET FOREIGN_KEY_CHECKS=0;")
txt_fk_on = text("SET FOREIGN_KEY_CHECKS=1;")

# helper to clear tables before import
def clear_table(name, conn):
    try:
        conn.execute(text(f"DELETE FROM `{name}`;"))
        print(f"🧹 Cleared table: {name}")
    except Exception:
        pass

# disable FK checks and clear dependent tables
with engine.begin() as conn:
    conn.execute(txt_fk_off)
    for table in [
        "user_cart",
        "refund_records",
        "restaurant_punishments",
        "user_achievements",
        "purchase_reports"
    ]:
        clear_table(table, conn)

# define import order without listings.csv
ordered_files = [
    "achievements.csv",
    "users.csv",
    "restaurants.csv",
    "purchases.csv",
    "purchase_reports.csv",
    "restaurant_badge_points.csv",
    "restaurant_comments.csv",
    "user_achievements.csv",
    "user_devices.csv",
    "user_favorites.csv",
    "comment_badges.csv",
    "customerAddresses.csv",
    "discountEarned.csv",
    "user_cart.csv"
]

for file in ordered_files:
    table_name = file.rsplit('.', 1)[0]
    path = os.path.join(csv_dir, file)
    print(f"\n📥 Importing {file} → {table_name}")

    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        print(f"⚠️ Skipped {file} — missing or empty.")
        continue

    df = pd.read_csv(path)
    if df.empty:
        print(f"⚠️ Skipped {file} — no data.")
        continue

    # set up dtype overrides for restaurant_comments timestamp
    dtype_overrides = None
    if table_name == "restaurant_comments":
        dtype_overrides = {"timestamp": SQLDateTime()}

    # clear existing rows
    with engine.begin() as conn:
        clear_table(table_name, conn)

    # import data
    df.to_sql(
        table_name,
        con=engine,
        index=False,
        if_exists="append",
        dtype=dtype_overrides
    )
    print(f"✅ Imported {table_name} ({len(df)} rows)")

    # ensure id columns are INT
    if table_name in {"achievements", "users", "restaurants", "purchases"}:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE `{table_name}` MODIFY `id` INT;"))
            print(f"🔧 Adjusted {table_name}.id → INT")

# re-enable foreign key checks
with engine.begin() as conn:
    conn.execute(txt_fk_on)

print("\n🎉 All CSVs (excluding listings.csv) imported successfully.")
