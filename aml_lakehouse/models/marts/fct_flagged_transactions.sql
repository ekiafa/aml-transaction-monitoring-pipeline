-- models/marts/fct_flagged_transactions.sql

with features as (
    select * from {{ ref('int_transaction_features') }}
),

scored as (
    select
        *,
        case
            when unique_senders_last_10 between 7 and 10 then 3
            when unique_senders_last_10 in (5, 6) then 2
            when unique_senders_last_10 = 4 then 1
            else 0
        end as risk_score
    from features
)

select
    *,
    case when risk_score >= 1 then 1 else 0 end as is_flagged
from scored