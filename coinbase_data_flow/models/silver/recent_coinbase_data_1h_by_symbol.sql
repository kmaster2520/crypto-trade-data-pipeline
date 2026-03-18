{{ config(materialized='incremental') }}

SELECT
    symbol,
    COUNT(*) as total,
    MAX(tradeTime) as latestTradeTime
FROM
    {{ ref('raw_coinbase_data') }}
WHERE
    tradeTime >= current_timestamp() - INTERVAL 1 HOUR
GROUP BY
    symbol
