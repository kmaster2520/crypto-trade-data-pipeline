{{ config(materialized='incremental') }}

SELECT
    symbol,
    price
    tradeTime
FROM
    {{ ref('raw_coinbase_data') }}
WHERE
    tradeTime >= current_timestamp() - INTERVAL 1 HOUR
