-- Staging model for raw customer records.
-- Casts and cleans the all-text raw columns from raw.raw_customers.

with source as (

    select * from {{ source('raw', 'raw_customers') }}

),

renamed as (

    select
        cast(id as integer)                   as customer_id,
        trim(name)                            as customer_name,
        lower(trim(email))                    as email,
        cast(signup_date as date)             as signup_date,
        trim(country)                         as country

    from source

)

select * from renamed
