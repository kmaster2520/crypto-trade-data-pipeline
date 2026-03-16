{{ config(
    materialized = 'streaming_table',
    file_format = 'delta',
    liquid_cluster_by = ['tradeTime', 'symbol']
) }}

SELECT
  *
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
