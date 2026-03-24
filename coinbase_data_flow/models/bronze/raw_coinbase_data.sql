{{ config(
    materialized = 'streaming_table',
    file_format = 'delta',
    liquid_cluster_by = ['tradeTime', 'symbol'],
    post_hook = "DELETE FROM {{ this }} WHERE tradeTime < CURRENT_DATE() - INTERVAL '90 DAYS'"
) }}

SELECT
    eventType,
    symbol,
    CAST(price AS DECIMAL(18, 8)),
    CAST(quantity AS DECIMAL(18, 8)),
    tradeId,
    side,
    tradeTime
FROM STREAM(
    read_files(
      's3://greatestbucketever/coinbase/raw/',
      format => 'json',
      schema => 'eventType STRING, symbol STRING, price STRING, quantity STRING, tradeId STRING, side STRING, tradeTime TIMESTAMP',
      multiLine => 'false',
      includeExistingFiles => 'true',
      ignoreCorruptFiles => 'true',
      recursiveFileLookup => 'true'
    )
);
