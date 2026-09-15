-- dim_products: one row per product, enriched with lifetime sales metrics.

with products as (

    select * from {{ ref('stg_products') }}

),

order_items as (

    select * from {{ ref('stg_order_items') }}

),

final as (

    select
        p.product_id,
        p.product_name,
        p.category,
        p.unit_price                                     as current_unit_price,
        coalesce(sum(oi.quantity), 0)                     as total_units_sold,
        coalesce(sum(oi.quantity * oi.unit_price), 0)      as total_revenue

    from products p
    left join order_items oi on oi.product_id = p.product_id
    group by
        p.product_id,
        p.product_name,
        p.category,
        p.unit_price

)

select * from final
