import asyncio
import os
import logging
import time

import matrixcore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

client = matrixcore.MatrixCore(os.getenv("HOMESERVER", "https://matrix-client.matrix.org"))
client.http.access_token = os.environ["ACCESS_TOKEN"]
now = time.time()


@client.on("m.room.message")
async def on_message(room: matrixcore.Room, event: matrixcore.ClientEventWithoutRoomID):
    if event.origin_server_ts / 1000 < now:
        return
    content = matrixcore.Message.model_validate(event.content)
    print(f"[{room.name} at {event.origin_server_ts * 1000}] <{event.sender}>: {content.body}", end="\n\n")
    if content.body.startswith("!matrixcore test"):
        await room.send(
            "m.room.message",
            matrixcore.Message(
                body=f"Hello, {event.sender}!",
                msgtype="m.notice"
            )
        )
    elif content.body.startswith("!matrixcore ping"):
        latency = (time.time() * 1000 - event.origin_server_ts)
        age = event.unsigned.age
        lines = [f"Pong {event.sender}! Took {latency:,.0f} ms"]
        if age:
            lines.append(f"Server-side sent age: {age}ms")
        else:
            lines.append(f"Server sent no age.")
        await room.send(
            "m.room.message",
            matrixcore.Message(
                body="\n".join(lines),
                msgtype="m.notice"
            )
        )
    elif content.body.startswith("!matrixcore time"):
        origin_ts = event.origin_server_ts
        origin_ts_seconds = origin_ts / 1000
        current = time.time()
        lines = [
            f"Event received at {origin_ts_seconds} ({origin_ts})",
            f"Process started at {now} ({now * 1000})",
            f"Time is now {current} ({current * 1000})"
        ]
        await room.send(
            "m.room.message",
            {
                "body": "\n".join(lines),
                "msgtype": "m.notice",
                "m.mentions": {
                    "user_ids": [event.sender]
                }
            }
        )


async def main():
    await client.http.whoami()

    llm = matrixcore.RoomEventFilter(
        lazy_load_members=True,
        limit=100
    )
    sf = await client.http.upload_filter(
        matrixcore.Filter(
            room=matrixcore.RoomFilter(
                state=llm,
                timeline=llm
            )
        )
    )
    print("Logged in as", client.http.user_id)
    while True:
        logging.info("Next batch before sync: %s", client.next_batch)
        await client.sync(sf.filter_id)
        logging.info("Next batch after sync: %s", client.next_batch)


asyncio.run(main())
