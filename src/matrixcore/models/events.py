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
from pydantic import BaseModel, ConfigDict


__all__ = ["MRoomMessage"]


class MRoomMessage(BaseModel):
    """Represents the body of an m.room.message event"""

    model_config = ConfigDict(extra="allow")

    body: str
    msgtype: str
    format: str = None
    formatted_body: str = None


class MRoomName(BaseModel):
    """Represents the body of an m.room.name event"""

    name: str


class MRoomTopic(BaseModel):
    """Represents the body of an m.room.topic event"""

    topic: str


class MRoomAvatar(BaseModel):
    """Represents the body of an m.room.avatar event"""

    class AvatarInfo(BaseModel):
        class ThumbnailInfo(BaseModel):
            h: int = None
            w: int = None
            mimetype: str = None
            size: int = None

        h: int = None
        w: int = None
        mimetype: str = None
        size: int = None
        thumbnail_info: ThumbnailInfo = None
        thumbnail_url: str = None

    info: AvatarInfo = None
    url: str = None


class MRoomPinnedEvents(BaseModel):
    """Represents the body of an m.room.pinned_events event"""

    pinned: list[str]


class MRoomRedaction(BaseModel):
    """Represents the body of an m.room.redaction event"""

    reason: str = None
    redacts: str = None  # may be omitted in room versions <11
