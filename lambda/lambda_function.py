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
            "data": "eyJlIjoiYWdnVHJhZGUiLCJFIjoxNzY0NzMxNzk5Nzg1LCJzIjoiQlRDVVNEVCIsImEiOjI5MzIxMzU2LCJwIjoiOTI1NTkuODMwMDAwMDAiLCJxIjoiMC4wMDEwODAwMCIsImYiOjMwOTM4NDI3LCJsIjozMDkzODQyNywiVCI6MTc2NDczMTc5OTc4NCwibSI6dHJ1ZSwiTSI6dHJ1ZX0=",
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
'''
Example Event (decoded):
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
    lambda_handler(EXAMPLE_EVENT, EventContext)
