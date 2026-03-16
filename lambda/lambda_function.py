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
            "data": "eyJ0eXBlIjoidGlja2VyIiwic2VxdWVuY2UiOjEyNDIxODk2NjE3MywicHJvZHVjdF9pZCI6IkJUQy1VU0QiLCJwcmljZSI6IjczODQwLjkzIiwib3Blbl8yNGgiOiI3MTgzMi4wMSIsInZvbHVtZV8yNGgiOiIxMjE1My4yMzYxMDk2MCIsImxvd18yNGgiOiI3MTMyOC4wMSIsImhpZ2hfMjRoIjoiNzQ1NDcuNSIsInZvbHVtZV8zMGQiOiIzMDA2MDcuODI0ODI1ODkiLCJiZXN0X2JpZCI6IjczODQwLjkyIiwiYmVzdF9iaWRfc2l6ZSI6IjAuMDAwNTAwMDAiLCJiZXN0X2FzayI6IjczODQwLjkzIiwiYmVzdF9hc2tfc2l6ZSI6IjAuMDQxNDA3MDgiLCJzaWRlIjoiYnV5IiwidGltZSI6IjIwMjYtMDMtMTZUMTc6MzY6NDYuNjAzMzY4WiIsInRyYWRlX2lkIjo5ODE2OTczMDgsImxhc3Rfc2l6ZSI6IjAuMDA0NTQzIn0=",
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
  "type": "ticker",
  "sequence": 124218966173,
  "product_id": "BTC-USD",
  "price": "73840.93",
  "open_24h": "71832.01",
  "volume_24h": "12153.23610960",
  "low_24h": "71328.01",
  "high_24h": "74547.5",
  "volume_30d": "300607.82482589",
  "best_bid": "73840.92",
  "best_bid_size": "0.00050000",
  "best_ask": "73840.93",
  "best_ask_size": "0.04140708",
  "side": "buy",
  "time": "2026-03-16T17:36:46.603368Z",
  "trade_id": 981697308,
  "last_size": "0.004543"
}

'''


def lambda_handler(event, context):

    print("Event: " + json.dumps(event))
    transformed_records = []

    for evt in event.get("records", []):
        item_b64 = evt.get("data", "")
        partition_key = evt.get("kinesisRecordMetadata", {}).get("partitionKey", "")
        try:
            item_string = base64.b64decode(item_b64.encode("ascii")).decode("ascii")
            item = json.loads(item_string)
        except binascii.Error as exc:
            print(exc)
            continue
        except json.JSONDecodeError as exc:
            print(exc)
            continue

        processed_item = {}

        # BINANCE
        if item.get("e"):
            event_time = int(item.get("E")) // 1000
            if not event_time:
                continue

            processed_item = {
                "eventType": item.get("e", ""),
                "symbol": item.get("s", "(none)"),
                "price": item.get("p", "0.0"),
                "quantity": item.get("q", "0.0"),
                "eventId": item.get("a", 0),
                "lambdaRequestId": context.aws_request_id,
                "timestamp": datetime.fromtimestamp(event_time, tz=timezone.utc).isoformat()
            }

        # COINBASEs
        elif item.get("type"):
            event_time = item.get("time")
            if not event_time:
                continue

            processed_item = {
                "eventType": item.get("type", ""),
                "symbol": item.get("product_id", "(none)"),
                "price": item.get("price", "0.0"),
                "quantity": item.get("last_size", "0.0"),
                "eventId": item.get("trade_id", 0),
                "lambdaRequestId": context.aws_request_id,
                "timestamp": event_time
            }

        else:
            continue

        print(partition_key)
        print(json.dumps(processed_item))

        transformed_records.append({
            "recordId": evt.get("recordId", ""),
            "result": "Ok",
            "data": base64.b64encode(json.dumps(processed_item).encode("ascii")).decode("ascii")
        })
        print()

    return {
        "records": transformed_records
    }


if __name__ == "__main__":
    class EventContext:
        aws_request_id = "d"
    print(lambda_handler(EXAMPLE_EVENT, EventContext))
