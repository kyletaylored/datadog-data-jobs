-- Calculate item metrics
-- In a real scenario, this would build upon the staging models
-- and contain more complex business logic

WITH item_data AS (
    SELECT
        item_id,
        item_name,
        category,
        item_value,
        item_quantity,
        is_active,
        discount_factor,
        item_value * item_quantity AS total_value,
        item_value * item_quantity * discount_factor AS discounted_value,
        created_at,
        processed_at
    FROM {{ ref('stg_items') }}
)

SELECT
    item_id,
    item_name,
    category,
    item_value,
    item_quantity,
    total_value,
    discounted_value,
    is_active,
    CASE 
        WHEN total_value > 5000 THEN 'premium'
        WHEN total_value > 1000 THEN 'standard'
        ELSE 'basic'
    END AS pricing_tier,
    created_at,
    processed_at,
    CURRENT_TIMESTAMP AS transformed_at
FROM item_data