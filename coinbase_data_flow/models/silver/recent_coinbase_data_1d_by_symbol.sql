{{ config(
    materialized = 'incremental',
    incremental_strategy = 'insert_overwrite',
    cluster_by = ['symbol']
) }}

SELECT
    symbol,
    COUNT(*) as totalTrades,
    MAX(tradeTime) as latestTradeTime,
    MIN(tradeTime) AS earliestTradeTime
FROM
    {{ ref('recent_coinbase_data_1d') }}
GROUP BY
    symbol
