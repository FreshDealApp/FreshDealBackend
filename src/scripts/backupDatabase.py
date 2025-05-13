import os
import pyodbc
import pandas as pd
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

# Load required variables
required_env_vars = {
    "DB_SERVER": os.getenv("DB_SERVER"),
    "DB_NAME": os.getenv("DB_NAME"),
    "DB_USERNAME": os.getenv("DB_USERNAME"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    "DB_DRIVER": os.getenv("DB_DRIVER"),
}

# Validate env vars
missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    raise SystemExit(f"❌ Missing environment variables: {', '.join(missing_vars)}")

# Fix driver name for pyodbc (replace + with space)
driver_raw = required_env_vars['DB_DRIVER'].replace('+', ' ')

# Build connection string
conn_str = (
    f"DRIVER={{{driver_raw}}};"
    f"SERVER={required_env_vars['DB_SERVER']};"
    f"DATABASE={required_env_vars['DB_NAME']};"
    f"UID={required_env_vars['DB_USERNAME']};"
    f"PWD={required_env_vars['DB_PASSWORD']}"
)

# Create output folder
output_dir = "../exported_tables"
os.makedirs(output_dir, exist_ok=True)

# Connect and export tables
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Fetch all table names
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        print(f"📤 Exporting: {table}")
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        df.to_csv(os.path.join(output_dir, f"{table}.csv"), index=False)

    cursor.close()
    conn.close()
    print("✅ All tables exported to 'exported_tables' folder.")

except Exception as e:
    print("❌ Error:", e)
