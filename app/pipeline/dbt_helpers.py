# app/pipeline/dbt_helpers.py
import os
import pandas as pd
from sqlalchemy import create_engine


def write_to_staging_table(data: list[dict]):
    """
    Write processed pipeline data into the raw_items table,
    which is the source for dbt models.
    """

    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}"
        f"@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
    )

    df = pd.DataFrame(data)

    # Rename to match expected column names
    df = df.rename(columns={
        "id": "id",
        "name": "name",
        "category": "category",
        "value": "value",
        "quantity": "quantity",
        "is_active": "is_active",
        "created_at": "created_at"
    })

    df.to_sql("raw_items", engine, schema="public",
              if_exists="replace", index=False)
