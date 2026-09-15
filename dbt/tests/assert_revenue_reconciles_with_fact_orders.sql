-- Reconciliation test: total revenue across mart_revenue_by_month must
-- match the total non-cancelled line_total in fact_orders. Fails (returns a
-- row) only if the two totals diverge by more than a cent of rounding
-- noise, which would indicate a bug in the monthly rollup logic.

with mart_total as (

    select sum(monthly_revenue) as total_revenue
    from {{ ref('mart_revenue_by_month') }}

),

fact_total as (

    select sum(line_total) as total_revenue
    from {{ ref('fact_orders') }}
    where order_status != 'cancelled'

)

select
    mart_total.total_revenue as mart_total_revenue,
    fact_total.total_revenue as fact_total_revenue
from mart_total
cross join fact_total
where abs(mart_total.total_revenue - fact_total.total_revenue) > 0.01
