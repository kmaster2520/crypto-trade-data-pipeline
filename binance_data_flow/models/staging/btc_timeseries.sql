{{ config(materialized='view') }}

SELECT
    CAST(price AS DECIMAL(18, 8)),
    CAST(quantity AS DECIMAL(18, 8)),
    timestamp
FROM
    {{ ref('raw_binance_data')}}
WHERE
    eventType = 'aggTrade'
    and symbol = 'BTCUSDT'
    and timestamp >= current_timestamp() - INTERVAL 90 DAY