import asyncio
import os
import sys

import websockets
import json

import boto3

# defaults
KINESIS_STREAM_NAME = "raw-trade-data"
SYMBOL = "BTC-USD"


async def process_websocket_response(*, res, kinesis_client, kinesis_stream_name):
    try:
        message = json.loads(res)
        channel = message.get("channel", "")
        if not channel:
            return

        events = message.get("events", [])
        if not events:
            return

        batch_records = []
        for event in events:
            trades = event.get("trades", [])
            if not trades:
                continue

            for trade in trades:
                trade["channel"] = message.get("channel", "")
                encoded_data = json.dumps(trade).encode("utf-8")
                batch_records.append({
                    "Data": encoded_data,
                    "PartitionKey": trade.get("product_id") or SYMBOL
                })

        if len(batch_records) > 0:
            await asyncio.to_thread(
                kinesis_client.put_records,
                StreamName=kinesis_stream_name,
                Records=batch_records
            )
    except json.JSONDecodeError as e:
        print('json decode error: ' + str(e))
    except Exception as e:
        print('message handling error: ' + str(e))


async def begin_stream(*, symbol, kinesis_stream_name):
    url = "wss://advanced-trade-ws.coinbase.com"

    subscribe_message = {
        "type": "subscribe",
        "channel": "market_trades",
        "product_ids": symbol.split(",")
    }

    unsubscribe_message = {
        "type": "unsubscribe",
        "channel": subscribe_message["channel"],
        "product_ids": subscribe_message["product_ids"]
    }

    region = os.getenv("AWS_REGION", "us-east-1")
    kinesis_client = boto3.client('kinesis', region)

    async with websockets.connect(url) as ws, asyncio.TaskGroup() as tg:
        print(f"Subscribing to websocket, using symbol: {symbol}")
        try:
            await ws.send(json.dumps(subscribe_message))
            while True:
                res = await ws.recv()
                tg.create_task(
                    process_websocket_response(
                        res=res,
                        kinesis_client=kinesis_client,
                        kinesis_stream_name=kinesis_stream_name
                    )
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
    if len(sys.argv) >= 2:
        SYMBOL = str(sys.argv[1])
    if len(sys.argv) >= 3:
        KINESIS_STREAM_NAME = str(sys.argv[2])
    asyncio.run(begin_stream(symbol=SYMBOL, kinesis_stream_name=KINESIS_STREAM_NAME))
