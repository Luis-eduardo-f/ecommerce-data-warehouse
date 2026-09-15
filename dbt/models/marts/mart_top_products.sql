-- mart_top_products: product-level sales ranking, overall and within
-- category, using window functions. Cancelled orders are excluded.

with fact as (

    select * from {{ ref('fact_orders') }}
    where order_status != 'cancelled'

),

products as (

    select * from {{ ref('dim_products') }}

),

product_sales as (

    select
        p.product_id,
        p.product_name,
        p.category,
        sum(f.quantity)     as units_sold,
        sum(f.line_total)   as total_revenue

    from fact f
    inner join products p on p.product_id = f.product_id
    group by
        p.product_id,
        p.product_name,
        p.category

)

select
    product_id,
    product_name,
    category,
    units_sold,
    total_revenue,
    rank() over (order by total_revenue desc)                       as revenue_rank,
    rank() over (partition by category order by total_revenue desc) as category_revenue_rank,
    round(
        100.0 * total_revenue / sum(total_revenue) over (),
    2) as pct_of_total_revenue

from product_sales
order by revenue_rank
