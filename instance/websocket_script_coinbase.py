import asyncio
import os
import sys

import websockets
import json

import boto3


'''
Example Event:
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

base64: 
'''



async def begin_stream():
    url = "wss://advanced-trade-ws.coinbase.com"

    partition_key = "BTC-USD"

    subscribe_message = {
        "type": "subscribe",
        "channel": "market_trades",
        "product_ids": [partition_key]
    }

    unsubscribe_message = {
        "type": "unsubscribe",
        "channel": subscribe_message["channel"],
        "product_ids": subscribe_message["product_ids"]
    }

    region = os.getenv("AWS_REGION", "us-east-1")
    kinesis_client = boto3.client('kinesis', region)

    async with websockets.connect(url) as ws:

        print(f"Subscribing to websocket")
        await ws.send(json.dumps(subscribe_message))

        try:
            while True:
                res = await ws.recv()
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
    asyncio.run(begin_stream())
