with stg as (
    select * from {{ ref('stg_transactions') }}
),

flagged as (
    select
        *,

        case
            when from_account = to_account then 1
            else 0
        end as is_same_account,

        case
            when receiving_currency != payment_currency then 1
            else 0
        end as is_currency_mismatch,

        abs(amount_received - amount_paid) as amount_discrepancy

    from stg
),

velocity as (
    select
        *,

        count(*) over (
            partition by from_account
            order by transaction_timestamp
            rows between 10 preceding and current row
        ) as txn_count_last_10_from_account,

        sum(amount_paid) over (
            partition by from_account
            order by transaction_timestamp
            rows between 10 preceding and current row
        ) as amount_sum_last_10_from_account

    from flagged
)

select * from velocity
