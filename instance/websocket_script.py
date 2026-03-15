import asyncio
import os
import sys

import websockets
import json

import boto3


'''
Example Event:
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

base64: eyJlIjoiYWdnVHJhZGUiLCJFIjoxNzY0NzMxNzk5Nzg1LCJzIjoiQlRDVVNEVCIsImEiOjI5MzIxMzU2LCJwIjoiOTI1NTkuODMwMDAwMDAiLCJxIjoiMC4wMDEwODAwMCIsImYiOjMwOTM4NDI3LCJsIjozMDkzODQyNywiVCI6MTc2NDczMTc5OTc4NCwibSI6dHJ1ZSwiTSI6dHJ1ZX0=
'''



async def begin_stream(count=10):
    url = "wss://stream.binance.us:9443/ws"

    partition_key = "BTCUSDT"
    stream_types = [
        f"{partition_key.lower()}@aggTrade",
    ]

    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": stream_types,
        "id": 1
    }

    unsubscribe_message = {
        "method": "UNSUBSCRIBE",
        "params": stream_types,
        "id": 999
    }

    region = os.getenv("AWS_REGION", "us-east-1")
    kinesis_client = boto3.client('kinesis', region)

    async with websockets.connect(url) as ws:

        print(f"Subscribing to websocket")
        await ws.send(json.dumps(subscribe_message))
        subscribe_response = await ws.recv()
        print(subscribe_response) # stringified json

        try:
            for i in range(count):
                res = await ws.recv()
                print(res)
                kinesis_client.put_record(
                    StreamName="raw-trade-data",
                    Data=res.encode('ascii'),
                    PartitionKey=partition_key
                )
        except KeyboardInterrupt:
            print("keyboard interrupt")
        except Exception as e:
            print(e)
        finally:
            print(f"Unsubscribing to websocket")
            await ws.send(json.dumps(unsubscribe_message))
            unsubscribe_response = await ws.recv()
            print(unsubscribe_response)

if __name__ == "__main__":
    count = int(sys.argv[1])
    asyncio.run(begin_stream(count=count))
