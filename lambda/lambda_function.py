import base64
import binascii
import json
from datetime import datetime, timezone


'''
dir(context)
[
'__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', 
'__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', 
'__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', 
'__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 

'_epoch_deadline_time_in_ms', 'aws_request_id', 'client_context', 'function_name', 
'function_version', 'get_remaining_time_in_millis', 'identity', 'invoked_function_arn', 
'log', 'log_group_name', 'log_stream_name', 'memory_limit_in_mb', 'tenant_id'
]
'''


EXAMPLE_EVENT = {
    "invocationId": "085d3401-c076-4054-b657-2a1c01dd107c",
    "sourceKinesisStreamArn": "arn:aws:kinesis:us-east-1:391262527903:stream/raw-trade-data",
    "deliveryStreamArn": "arn:aws:firehose:us-east-1:391262527903:deliverystream/KDS-S3-trade-data",
    "region": "us-east-1",
    "records": [
        {
            "recordId": "shardId-00000000000200000000000000000000000000000000000000000000000000000000000000000000000049669534775090560008083220088837278296638367081844178978000000000000",
            "approximateArrivalTimestamp": 1765030657336,
            #"data": "eyJlIjoiYWdnVHJhZGUiLCJFIjoxNzY0NzMxNzk5Nzg1LCJzIjoiQlRDVVNEVCIsImEiOjI5MzIxMzU2LCJwIjoiOTI1NTkuODMwMDAwMDAiLCJxIjoiMC4wMDEwODAwMCIsImYiOjMwOTM4NDI3LCJsIjozMDkzODQyNywiVCI6MTc2NDczMTc5OTc4NCwibSI6dHJ1ZSwiTSI6dHJ1ZX0=",
            "data": "eyJjaGFubmVsIjoibWFya2V0X3RyYWRlcyIsInRpbWVzdGFtcCI6IjIwMjYtMDMtMTZUMjA6MzM6MjQuNzk5MTE3MjAzWiIsInNlcXVlbmNlX251bSI6MTAsImV2ZW50cyI6W3sidHlwZSI6InVwZGF0ZSIsInRyYWRlcyI6W3sicHJvZHVjdF9pZCI6IkJUQy1VU0QiLCJ0cmFkZV9pZCI6Ijk4MTgwNDk1NSIsInByaWNlIjoiNzQwNDAiLCJzaXplIjoiMC4wMDAwODQyNCIsInRpbWUiOiIyMDI2LTAzLTE2VDIwOjMzOjI0Ljc2MzQ5NVoiLCJzaWRlIjoiU0VMTCJ9LHsicHJvZHVjdF9pZCI6IkJUQy1VU0QiLCJ0cmFkZV9pZCI6Ijk4MTgwNDk1NCIsInByaWNlIjoiNzQwMzcuNTYiLCJzaXplIjoiMC4wMDAxMTc3NSIsInRpbWUiOiIyMDI2LTAzLTE2VDIwOjMzOjI0LjcyMzA2MloiLCJzaWRlIjoiU0VMTCJ9LHsicHJvZHVjdF9pZCI6IkJUQy1VU0QiLCJ0cmFkZV9pZCI6Ijk4MTgwNDk1MyIsInByaWNlIjoiNzQwMzciLCJzaXplIjoiMC4wMDAxNDk3IiwidGltZSI6IjIwMjYtMDMtMTZUMjA6MzM6MjQuNzIzMDYyWiIsInNpZGUiOiJTRUxMIn1dfV19",
            "kinesisRecordMetadata": {
                "sequenceNumber": "49669534775090560008083220088837278296638367081844178978",
                "subsequenceNumber": 0,
                "partitionKey": "BTCUSDT-aggTrade",
                "shardId": "shardId-000000000002",
                "approximateArrivalTimestamp": 1765030657336
            }
        }
    ]
}

'''
Example Event (decoded):
BINANCE
{
    "e":"aggTrade",
    "E":1764731799785,
    "s":"BTCUSDT",
    "a":29321356,
    "p":"92559.83000000",
    "q":"0.00108000",
    "f":30938427,
    "l":30938427,
    "T":1764731799784,
    "m":true,
    "M":true
}

COINBASE
{
  "channel": "market_trades",
  "timestamp": "2026-03-16T20:33:24.799117203Z",
  "sequence_num": 10,
  "events": [
    {
      "type": "update",
      "trades": [
        {
          "product_id": "BTC-USD",
          "trade_id": "981804955",
          "price": "74040",
          "size": "0.00008424",
          "time": "2026-03-16T20:33:24.763495Z",
          "side": "SELL"
        },
        {
          "product_id": "BTC-USD",
          "trade_id": "981804954",
          "price": "74037.56",
          "size": "0.00011775",
          "time": "2026-03-16T20:33:24.723062Z",
          "side": "SELL"
        },
        {
          "product_id": "BTC-USD",
          "trade_id": "981804953",
          "price": "74037",
          "size": "0.0001497",
          "time": "2026-03-16T20:33:24.723062Z",
          "side": "SELL"
        }
      ]
    }
  ]
}

'''


def lambda_handler(event, context):

    print("Event: " + json.dumps(event))
    transformed_records = []

    for evt in event.get("records", []):
        item_b64 = evt.get("data", "")
        #partition_key = evt.get("kinesisRecordMetadata", {}).get("partitionKey", "")
        try:
            item_string = base64.b64decode(item_b64.encode("ascii")).decode("ascii")
            item = json.loads(item_string)
        except binascii.Error as exc:
            print(exc)
            continue
        except json.JSONDecodeError as exc:
            print(exc)
            continue

        # COINBASE
        if item.get("channel") == "market_trades":
            if not item.get("timestamp"):
                continue

            event_type = item.get("channel", "")
            for item_event in item.get("events", []):
                for trade in item_event.get("trades", []):
                    processed_item = {
                        "eventType": event_type,
                        "symbol": trade.get("product_id", ""),
                        "price": trade.get("price", "0.0"),
                        "quantity": trade.get("size", "0.0"),
                        "tradeId": trade.get("trade_id", "0"),
                        "side": trade.get("side", ""),
                        "tradeTime": trade.get("time", "")
                    }

                    transformed_records.append({
                        "recordId": evt.get("recordId", ""),
                        "result": "Ok",
                        "data": base64.b64encode(json.dumps(processed_item).encode("ascii")).decode("ascii")
                    })

        else:
            continue

    return {
        "records": transformed_records
    }


if __name__ == "__main__":
    class EventContext:
        aws_request_id = "d"
    print(lambda_handler(EXAMPLE_EVENT, EventContext))
