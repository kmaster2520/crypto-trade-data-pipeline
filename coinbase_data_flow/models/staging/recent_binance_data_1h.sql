{{ config(materialized='view') }}

SELECT
    tradeTime,
    CAST(price AS DECIMAL(18, 8)),
FROM
    {{ ref('raw_coinbase_data') }}
WHERE
    tradeTime >= current_timestamp() - INTERVAL 90 DAY
