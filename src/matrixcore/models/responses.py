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
from .events import ClientEvent
from .lib import CustomBaseModel

__all__ = [
    "RoomMessagesResponse",
]


class RoomMessagesResponse(CustomBaseModel):
    chunk: list[ClientEvent]
    """
    A list of room events. The order depends on the dir parameter. For dir=b events will be in reverse-chronological
    order, for dir=f in chronological order.
    (The exact definition of chronological is dependent on the server implementation.)

    Note that an empty chunk does not necessarily imply that no more events are available.
    Clients should continue to paginate until no end property is returned.
    """
    end: str = None
    """
    A token corresponding to the end of chunk. This token can be passed back to this endpoint to request further events.

    If no further events are available (either because we have reached the start of the timeline,
    or because the user does not have permission to see any more events), this property is omitted from the response.
    """
    start: str
    """A token corresponding to the start of chunk. This will be the same as the value given in from."""
    state: list[ClientEvent] = None
    """
    A list of state events relevant to showing the chunk. For example,
    if lazy_load_members is enabled in the filter then this may contain the membership events for the senders of
    events in the chunk.

    Unless include_redundant_members is true, the server may remove membership events which would have already been
    sent to the client in prior calls to this endpoint, assuming the membership of those members has not changed.
    """
