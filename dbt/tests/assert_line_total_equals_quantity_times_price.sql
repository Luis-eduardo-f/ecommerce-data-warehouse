-- Custom singular test: line_total must always equal
-- round(quantity * unit_price, 2) in fact_orders.
-- dbt fails this test if the query returns any rows.

select
    order_item_id,
    quantity,
    unit_price,
    line_total
from {{ ref('fact_orders') }}
where round(quantity * unit_price, 2) != line_total
