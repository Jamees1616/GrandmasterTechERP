from app import app, db
from sqlalchemy import text

with app.app_context():
    columns = [
        row[1]
        for row in db.session.execute(
            text("PRAGMA table_info(customer)")
        ).fetchall()
    ]

    print("Existing columns:", columns)

    new_columns = {
        "gender": "VARCHAR(30)",
        "age_group": "VARCHAR(30)",
        "district": "VARCHAR(100)",
        "customer_type": "VARCHAR(50)"
    }

    for column, column_type in new_columns.items():
        if column not in columns:
            db.session.execute(
                text(
                    f"ALTER TABLE customer "
                    f"ADD COLUMN {column} {column_type}"
                )
            )
            print(f"Added column: {column}")
        else:
            print(f"Already exists: {column}")

    db.session.commit()
    print("SUCCESS: Customer demographics database migration complete.")
