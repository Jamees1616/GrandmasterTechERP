import os
from sqlalchemy import create_engine, text

database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is not set.")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)

with engine.begin() as connection:
    columns = {
        "gender": "VARCHAR(30)",
        "age_group": "VARCHAR(30)",
        "district": "VARCHAR(100)",
        "customer_type": "VARCHAR(50)",
    }

    for column, column_type in columns.items():
        connection.execute(
            text(
                f"ALTER TABLE customer "
                f"ADD COLUMN IF NOT EXISTS {column} {column_type}"
            )
        )
        print(f"Checked/added column: {column}")

print("SUCCESS: PostgreSQL customer demographics migration complete.")
