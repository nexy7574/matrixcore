# Copyright 2025 nexy7574 <https://github.com/nexy7574>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Requires: fastapi, uvicorn, matrixcore (obviously)
# Example usage (please don't use this in production):
#
# MATRIX_HOMESERVER=https://matrix-client.matrix.org \
# MATRIX_ACCESS_TOKEN=your_access-token \
# WEBHOOK_TOKEN=abcdefg \
# uvicorn server:app
import os
import uuid

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import matrixcore


# define the body that must be sent to the webhook
class WebhookPayload(BaseModel):
    identifier: uuid.UUID
    """A unique identifier for the service calling this webhook."""
    content: str
    """The content of this webhook that should be sent."""
    room: str
    """The room ID or alias of this webhook."""
    display_name: str | None = None
    """The display name override to send to matrix with this webhook, if any."""
    mention_room: bool = False
    """Whether to mention everyone in the destination room."""
    mention_users: list[str] | None = None
    """A list of User IDs to mention."""


security = HTTPBearer()
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")
MATRIX_HOMESERVER = os.getenv("MATRIX_HOMESERVER")
MATRIX_ACCESS_TOKEN = os.getenv("MATRIX_ACCESS_TOKEN")
if not WEBHOOK_TOKEN:
    raise ValueError("$WEBHOOK_TOKEN must be set")
if not MATRIX_HOMESERVER:
    raise ValueError("$MATRIX_HOMESERVER must be set")
if not MATRIX_ACCESS_TOKEN:
    raise ValueError("$MATRIX_ACCESS_TOKEN must be set")


def _authentication(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Require "Bearer {WEBHOOK_TOKEN}"
    if credentials.credentials != WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=401,
        )
    return credentials

authorisation = Depends(_authentication)


app = FastAPI(title="Webhook Server", description="Matrix Webhook API powered by MatrixCore.")
app.add_api_route("/", lambda: RedirectResponse("/docs"))

matrix_client = matrixcore.MatrixCore(MATRIX_HOMESERVER)
matrix_client.http.access_token = MATRIX_ACCESS_TOKEN  # required to send requests


@app.post("/send", dependencies=[authorisation], status_code=204)
async def send(payload: WebhookPayload):
    """Sends a payload"""
    event = {
        "body": payload.content,  # the text to send
        "msgtype": "m.notice",  # send it as a notice, a type specifically for automations.
        "m.mentions": {}
    }
    if payload.mention_room:
        event["m.mentions"]["room"] = True
        event["msgtype"] = "m.text"  # switch it to text to show that it is an urgent event.
    if payload.mention_users:
        event["m.mentions"]["user_ids"] = payload.mention_users.copy()

    # Now we can send the MSC4144 per-message profile, overriding the display name.
    if payload.display_name:
        # Keep in mind that only some clients implement MSC4144, so this won't display on all clients.
        event["com.beeper.per_message_profile"] = {
            "id": str(payload.identifier),
            "displayname": payload.display_name,
        }

    # Now, resolve the room if it is an alias.
    if payload.room.startswith("#"):
        try:
            room_res = await matrix_client.http.resolve_room_alias(payload.room)
        except matrixcore.NotFound:
            raise HTTPException(
                status_code=404,
                detail=f"The alias {payload.room!r} does not exist."
            )
        room_id = room_res.room_id
    elif payload.room.startswith("!"):  # ensure that if it's not an alias, it's valid room ID
        room_id = payload.room
    else:
        # Invalid input.
        raise HTTPException(
            status_code=400,
            detail="payload.room must be a qualified room ID or qualified room alias."
        )

    # Finally, send the event!
    await matrix_client.http.send_event(
        room_id,
        "m.room.message",
        event
    )
    # Note that if this fails, you will see a traceback in your console, and the HTTP requester
    # will just see "HTTP 500 Internal Server Error" in response.


# Run the program if we're in interactive mode
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
