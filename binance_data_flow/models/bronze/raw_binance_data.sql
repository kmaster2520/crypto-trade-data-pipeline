{{ config(
    materialized = 'streaming_table',
    file_format = 'delta',
) }}

SELECT
  eventType,
  symbol,
  price,
  quantity,
  eventId,
  lambdaRequestId,
  timestamp
FROM STREAM(
    read_files(
      's3://greatestbucketever/binance/raw/',
      format => 'json',
      schema => 'eventType STRING, symbol STRING, price STRING, quantity STRING, eventId STRING, lambdaRequestId STRING, timestamp TIMESTAMP',
      multiLine => 'false',
      includeExistingFiles => 'true',
      ignoreCorruptFiles => 'true',
      recursiveFileLookup => 'true'
    )
);
