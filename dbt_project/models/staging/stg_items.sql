-- Stage the items data
-- In a real scenario, this would read from a source table
-- For demo purposes, we'll just create some sample data

WITH source_data AS (
    SELECT
        id::int AS item_id,
        name AS item_name,
        category,
        value::float AS item_value,
        quantity::int AS item_quantity,
        is_active::boolean AS is_active,
        created_at::timestamp AS created_at
    FROM {{ source('sample_data', 'raw_items') }}
)

SELECT
    item_id,
    item_name,
    category,
    item_value,
    item_quantity,
    is_active,
    created_at,
    CASE 
        WHEN category = 'A' THEN 0.9
        WHEN category = 'B' THEN 0.85
        WHEN category = 'C' THEN 0.8
        ELSE 0.95
    END AS discount_factor,
    CURRENT_TIMESTAMP AS processed_at
FROM source_data