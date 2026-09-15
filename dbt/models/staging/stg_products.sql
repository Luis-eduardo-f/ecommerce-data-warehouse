-- Staging model for raw product records.
-- Casts and cleans the all-text raw columns from raw.raw_products.

with source as (

    select * from {{ source('raw', 'raw_products') }}

),

renamed as (

    select
        cast(id as integer)                   as product_id,
        trim(name)                            as product_name,
        trim(category)                        as category,
        cast(unit_price as numeric(10, 2))    as unit_price

    from source

)

select * from renamed
