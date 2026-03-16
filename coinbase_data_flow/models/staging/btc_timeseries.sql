{{ config(materialized='view') }}

SELECT
    CAST(price AS DECIMAL(18, 8)),
    CAST(quantity AS DECIMAL(18, 8)),
    tradeTime
FROM
    {{ ref('raw_coinbase_data') }}
WHERE
    eventType = 'market_trades'
    and symbol = 'BTC-USD'
    and tradeTime >= current_timestamp() - INTERVAL 90 DAY
    and tradeTime >= '2026-03-16'