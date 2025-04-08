"""
Initialize the database with necessary tables for dbt models.
This script is run once during container initialization.
"""
from django.db import connections
import os
import sys
import django
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Add app directory to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import Django connections


def create_raw_items_table():
    """Create the raw_items table needed for dbt models"""
    with connections['default'].cursor() as cursor:
        # Drop table if exists
        cursor.execute("DROP TABLE IF EXISTS raw_items;")

        # Create table
        cursor.execute("""
        CREATE TABLE raw_items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category CHAR(1) NOT NULL,
            value NUMERIC(10, 2) NOT NULL,
            quantity INTEGER NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP NOT NULL
        );
        """)

        # Generate some sample data
        records = []
        categories = ['A', 'B', 'C', 'D']
        current_time = datetime.now()

        for i in range(1, 101):  # 100 sample records
            record = {
                'id': i,
                'name': f'Item {i}',
                'category': random.choice(categories),
                'value': round(random.uniform(10, 1000), 2),
                'quantity': random.randint(1, 100),
                'is_active': random.choice([True, False]),
                'created_at': (current_time - timedelta(days=random.randint(0, 30))).isoformat()
            }
            records.append(record)

        # Insert data
        for record in records:
            cursor.execute("""
            INSERT INTO raw_items (id, name, category, value, quantity, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                record['id'],
                record['name'],
                record['category'],
                record['value'],
                record['quantity'],
                record['is_active'],
                record['created_at']
            ))

        print(f"Created raw_items table with {len(records)} sample records")


def main():
    """Main function to initialize the database"""
    print("Initializing database...")
    create_raw_items_table()
    print("Database initialization completed")


if __name__ == "__main__":
    main()
