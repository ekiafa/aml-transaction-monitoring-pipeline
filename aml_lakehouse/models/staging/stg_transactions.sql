with source as (
    select * from {{ source('aml_bronze', 'raw_transactions') }}
),

cleaned as (
    select
        to_timestamp(timestamp, 'yyyy/MM/dd HH:mm') as transaction_timestamp,
        from_bank,
        from_account,
        to_bank,
        to_account,
        amount_received,
        receiving_currency,
        amount_paid,
        payment_currency,
        payment_format,
        is_laundering,
        _ingested_at
    from source
)

select * from cleaned