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
    if content.body.lower().startswith("!matrixcore "):
        args = content.body.split(" ")[1:]
        match args[0]:
            case "ping":
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
            case "time":
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
            case "dm":
                response_event = await room.send(
                    "m.room.message",
                    {
                        "body": "DMing you!",
                        "msgtype": "m.notice",
                        "m.mentions": {
                            "user_ids": [event.sender]
                        }
                    }
                )
                room_id = await client.http.create_room(
                    preset="trusted_private_chat",
                    invite=[event.sender],
                    visibility="private",
                    is_direct=True
                )
                dm_room = await matrixcore.Room.get(room_id.room_id, client=client)
                await dm_room.send(
                    "m.room.message",
                    {
                        "body": "Hello!",
                        "msgtype": "m.text"
                    }
                )
                await dm_room.leave("Goodbye!")
                await room.send(
                    "m.room.message",
                    {
                        "body": "* I sent you a DM!",
                        "msgtype": "m.notice",
                        "m.new_content": {
                            "body": "I sent you a DM!",
                            "msgtype": "m.notice"
                        },
                        "m.relates_to": {
                            "rel_type": "m.replace",
                            "event_id": response_event.event_id
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
        await client.sync(sf.filter_id)


asyncio.run(main())
