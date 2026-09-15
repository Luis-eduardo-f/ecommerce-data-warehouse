-- mart_revenue_by_month: monthly revenue with trend analysis via window
-- functions (3-month moving average, month-over-month change).
-- Cancelled orders are excluded from revenue figures.

with fact as (

    select * from {{ ref('fact_orders') }}
    where order_status != 'cancelled'

),

monthly as (

    select
        date_trunc('month', order_date)::date as order_month,
        count(distinct order_id)               as order_count,
        sum(line_total)                        as monthly_revenue

    from fact
    group by 1

),

with_trends as (

    select
        order_month,
        order_count,
        monthly_revenue,

        round(
            avg(monthly_revenue) over (
                order by order_month
                rows between 2 preceding and current row
            ),
        2) as revenue_3mo_moving_avg,

        lag(monthly_revenue) over (order by order_month) as prior_month_revenue

    from monthly

)

select
    order_month,
    order_count,
    monthly_revenue,
    revenue_3mo_moving_avg,
    round(monthly_revenue - prior_month_revenue, 2) as revenue_mom_change,
    round(
        100.0 * (monthly_revenue - prior_month_revenue)
        / nullif(prior_month_revenue, 0),
    2) as revenue_mom_pct_change

from with_trends
order by order_month
