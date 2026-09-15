-- dim_customers: one row per customer, enriched with lifetime order metrics.

with customers as (

    select * from {{ ref('stg_customers') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

order_item_totals as (

    select
        order_id,
        sum(quantity * unit_price) as line_total

    from {{ ref('stg_order_items') }}
    group by order_id

),

orders_with_totals as (

    select
        o.order_id,
        o.customer_id,
        o.order_date,
        coalesce(t.line_total, 0) as order_total

    from orders o
    left join order_item_totals t on t.order_id = o.order_id

),

final as (

    select
        c.customer_id,
        c.customer_name,
        c.email,
        c.signup_date,
        c.country,
        count(o.order_id)                    as lifetime_order_count,
        coalesce(sum(o.order_total), 0)      as lifetime_revenue,
        min(o.order_date)                    as first_order_date,
        max(o.order_date)                    as last_order_date

    from customers c
    left join orders_with_totals o on o.customer_id = c.customer_id
    group by
        c.customer_id,
        c.customer_name,
        c.email,
        c.signup_date,
        c.country

)

select * from final
