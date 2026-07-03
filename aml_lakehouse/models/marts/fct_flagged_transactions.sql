-- models/marts/fct_flagged_transactions.sql

with features as (
    select * from {{ ref('int_transaction_features') }}
),

scored as (
    select
        *,
        (
            is_same_account * 2 +
            is_currency_mismatch * 1 +
            case when amount_paid > 50000 then 2 else 0 end +
            case when txn_count_last_10_from_account >= 10 then 1 else 0 end
        ) as risk_score
    from features
)

select
    *,
    case when risk_score >= 3 then 1 else 0 end as is_flagged
from scored