-- fact_orders: the central fact table.
-- Grain: one row per order line item (order_item_id), with foreign keys to
-- dim_customers and dim_products.

with order_items as (

    select * from {{ ref('stg_order_items') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

final as (

    select
        oi.order_item_id,
        oi.order_id,
        o.customer_id,
        oi.product_id,
        o.order_date,
        o.order_status,
        oi.quantity,
        oi.unit_price,
        round(oi.quantity * oi.unit_price, 2) as line_total

    from order_items oi
    inner join orders o on o.order_id = oi.order_id

)

select * from final
