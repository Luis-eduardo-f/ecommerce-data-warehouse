-- Staging model for raw order records.
-- Casts and cleans the all-text raw columns from raw.raw_orders.

with source as (

    select * from {{ source('raw', 'raw_orders') }}

),

renamed as (

    select
        cast(id as integer)                   as order_id,
        cast(customer_id as integer)          as customer_id,
        cast(order_date as date)              as order_date,
        lower(trim(status))                   as order_status

    from source

)

select * from renamed
