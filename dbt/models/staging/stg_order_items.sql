-- Staging model for raw order item records.
-- Casts and cleans the all-text raw columns from raw.raw_order_items.

with source as (

    select * from {{ source('raw', 'raw_order_items') }}

),

renamed as (

    select
        cast(id as integer)                   as order_item_id,
        cast(order_id as integer)             as order_id,
        cast(product_id as integer)           as product_id,
        cast(quantity as integer)             as quantity,
        cast(unit_price as numeric(10, 2))    as unit_price

    from source

)

select * from renamed
