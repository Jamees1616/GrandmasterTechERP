import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Render/Supabase sometimes provides postgres://
# SQLAlchemy expects postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

columns = {
    "service_charge": "NUMERIC(12, 2) DEFAULT 0",
    "parts_cost": "NUMERIC(12, 2) DEFAULT 0",
    "total_cost": "NUMERIC(12, 2) DEFAULT 0",
    "amount_paid": "NUMERIC(12, 2) DEFAULT 0",
    "balance": "NUMERIC(12, 2) DEFAULT 0",
    "profit": "NUMERIC(12, 2) DEFAULT 0",
}

with engine.begin() as connection:
    for column, definition in columns.items():
        print(f"Checking column: {column}")
        connection.execute(
            text(
                f"ALTER TABLE job_card "
                f"ADD COLUMN IF NOT EXISTS {column} {definition}"
            )
        )
        print(f"✓ {column} ready")

print("\nJob Card financial migration completed successfully.")
