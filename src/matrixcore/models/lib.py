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
import typing
import zoneinfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..media import MXCUri

__all__ = [
    "Empty",
    "Any",
    "EventSendResponse",
    "JoinResponse",
    "LoginFlows",
    "LoginResponse",
    "WhoAmI",
    "RoomPredecessor",
    "ResolveRoomAliasResponse",
    "UserProfile",
    "Filter",
    "RoomFilter",
    "RoomEventFilter",
    "EventFilter",
    "CustomBaseModel"
]

class CustomBaseModel(BaseModel):
    """A custom base model that adds some utilities."""

    def flattened(self, sep: str = ".") -> dict[str, typing.Any]:
        """
        Flattens the event into a dictionary where the keys are the full path to the value

        Example:
            {"foo": {"bar": "baz"}} -> {"foo.bar": "baz"}

        :param sep: The separator to use between keys. Defaults to period.
        :return: The flattened dictionary.
        """
        def flatten(d, parent_key=''):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        return flatten(self.model_dump(mode="python"))


class Empty(CustomBaseModel):
    """Represents an empty response body."""


class Any(CustomBaseModel):
    """Represents a response body with no pre-defined content"""

    model_config = ConfigDict(extra="allow")


class RoomPredecessor(CustomBaseModel):
    room_id: str
    """The previous room's room ID"""
    event_id: str
    """The previous room's last known event ID. Usually the m.room.tombstone event."""


class JoinResponse(CustomBaseModel):
    """The result of joining a room"""

    room_id: str
    """The ID of the room that was joined"""


class EventSendResponse(CustomBaseModel):
    """The result of sending an event"""

    event_id: str
    """The ID of the event that was sent"""


class LoginFlows(CustomBaseModel):
    """The result of fetching supported login methods"""

    class LoginFlow(CustomBaseModel):
        get_login_token: bool = None
        """
        If type is m.login.token, an optional field to indicate to the unauthenticated client that the homeserver 
        supports the POST /login/get_token endpoint. 
        Note that supporting the endpoint does not necessarily indicate that the user attempting to log in will 
        be able to generate such a token.
        """
        type: str
        """The login type. This is supplied as the type when logging in."""

    flows: list[LoginFlow]
    """The homeserver's supported login types"""


class LoginResponse(CustomBaseModel):
    """The result of logging in"""

    class DiscoveryInformation(CustomBaseModel):
        class ServerInformation(CustomBaseModel):
            base_url: str
            """The base URL for this server"""

        m_homeserver: ServerInformation = Field(..., alias="m.homeserver")
        """The base URL for the homeserver for client-server connections."""
        m_identity_server: ServerInformation = Field(..., alias="m.identity_server")
        """The base URL for the identity server for client-server connections."""

    access_token: str
    """An access token for the account. This access token can then be used to authorize other requests."""
    device_id: str
    """
    ID of the logged-in device. Will be the same as the corresponding parameter in the request, if one was specified.
    """
    expires_in_ms: int = None
    """
    The lifetime of the access token, in milliseconds. Once the access token has expired a new access token can be 
    obtained by using the provided refresh token. 
    If no refresh token is provided, the client will need to re-log in to obtain a new access token.
    If not given, the client can assume that the access token will not expire.
    """
    refresh_token: int = None
    """
    A refresh token for the account. This token can be used to obtain a new access token when it expires by calling 
    the /refresh endpoint.
    """
    user_id: str
    """
    The fully-qualified Matrix ID for the account.
    """
    well_known: DiscoveryInformation = None
    """Optional client configuration provided by the server."""


class WhoAmI(CustomBaseModel):
    """
    The result of the whoami request

    Spec version: v1.13
    """

    device_id: str = None
    """Device ID associated with the access token."""
    is_guest: bool = None
    """When true, the user is a Guest User. When not present or false, the user is presumed to be a non-guest user."""
    user_id: str
    """The user ID that owns the access token."""


class ResolveRoomAliasResponse(CustomBaseModel):
    """The result of resolving a room alias"""

    room_id: str
    """The room ID that corresponds to the alias"""
    servers: list[str]
    """The servers that are aware of the room ID"""


class UserProfile(Any):
    """
    Represents a user's profile.

    Note: This function supports MSC4133 and MSC4175. Profile keys not explicitly defined here are still stored
    in the dataclass.
    """

    model_config = ConfigDict(extra="allow")
    avatar_url: typing.Optional["MXCUri"] = None
    """The user's avatar URL"""
    displayname: str | None = None
    """The user's display name"""

    unstable_msc4175_timezone: zoneinfo.ZoneInfo | None = None

    @classmethod
    @field_validator("unstable_msc4175_timezone", mode="before")
    def is_valid_timezone(cls, value: Any) -> zoneinfo.ZoneInfo:
        """Validates that the given value is a timezone that exists"""
        try:
            return zoneinfo.ZoneInfo(str(value))
        except (ModuleNotFoundError, zoneinfo.ZoneInfoNotFoundError):
            raise ValueError(f"Invalid timezone: {value}")


class EventFilter(CustomBaseModel):
    limit: int = Field(default=None, gt=0)
    not_senders: list[str] = None
    """
    A list of sender IDs to exclude. If this list is absent then no senders are excluded.
    A matching sender will be excluded even if it is listed in the 'senders' filter.
    """
    not_types: list[str] = None
    """
    A list of event types to exclude. If this list is absent then no event types are excluded.
    A matching type will be excluded even if it is listed in the 'types' filter.
    A ‘*’ can be used as a wildcard to match any sequence of characters.
    """
    senders: list[str] = None
    """A list of senders IDs to include. If this list is absent then all senders are included."""
    types: list[str] = None
    """
    A list of event types to include. If this list is absent then all event types are included.
    A '*' can be used as a wildcard to match any sequence of characters.
    """


class RoomEventFilter(CustomBaseModel):
    contains_url: bool | None = None
    """
    If true, includes only events with a url key in their content. If false, excludes those events.
    If omitted, url key is not considered for filtering.
    """
    include_redundant_members: bool = False
    """
    If true, sends all membership events for all events, even if they have already been sent to the client.
    Does not apply unless lazy_load_members is true. See Lazy-loading room members for more information.
    Defaults to false.
    """
    lazy_load_members: bool = False
    """
    If true, enables lazy-loading of membership events. See Lazy-loading room members for more information.
    Defaults to false.
    """
    limit: int = Field(default=None, gt=0)
    """
    The maximum number of events to return, must be an integer greater than 0.

    Servers should apply a default value, and impose a maximum value to avoid resource exhaustion.
    """
    not_rooms: list[str] = None
    """
    A list of room IDs to exclude. If this list is absent then no rooms are excluded
    A matching room will be excluded even if it is listed in the 'rooms' filter.
    """
    not_senders: list[str] = None
    """
    A list of sender IDs to exclude. If this list is absent then no senders are excluded.
    A matching sender will be excluded even if it is listed in the 'senders' filter.
    """
    not_types: list[str] = None
    """
    A list of event types to exclude. If this list is absent then no event types are excluded.
    A matching type will be excluded even if it is listed in the 'types' filter.
    A ‘*’ can be used as a wildcard to match any sequence of characters.
    """
    rooms: list[str] = None
    """A list of room IDs to include. If this list is absent then all rooms are included."""
    senders: list[str] = None
    """A list of senders IDs to include. If this list is absent then all senders are included."""
    types: list[str] = None
    """
    A list of event types to include. If this list is absent then all event types are included.
    A '*' can be used as a wildcard to match any sequence of characters.
    """
    unread_thread_notifications: bool = False
    """If true, enables per-thread notification counts. Only applies to the /sync endpoint. Defaults to false."""


class RoomFilter(CustomBaseModel):
    include_leave: bool = False
    """Include rooms that the user has left in the sync, default false"""
    not_rooms: list[str] = None
    """
    A list of room IDs to exclude. If this list is absent then no rooms are excluded.
    A matching room will be excluded even if it is listed in the 'rooms' filter.
    This filter is applied before the filters in ephemeral, state, timeline or account_data
    """
    rooms: list[str] = None
    """
    A list of room IDs to include. If this list is absent then all rooms are included.
    This filter is applied before the filters in ephemeral, state, timeline or account_data
    """
    account_data: RoomEventFilter = None
    """The per user account data to include for rooms."""
    ephemeral: RoomEventFilter = None
    """
    The ephemeral events to include for rooms. 
    These are the events that appear in the ephemeral property in the /sync response.
    """
    state: RoomEventFilter = None
    """The state events to include for rooms."""
    timeline: RoomEventFilter = None
    """The message and state update events to include for rooms."""


class Filter(CustomBaseModel):
    event_fields: list[str] = None
    """
    List of event fields to include. If this list is absent then all fields are included.
    The entries are dot-separated paths for each property to include. So [‘content.body’] will include the ‘body’
    field of the ‘content’ object. A server may include more fields than were requested.
    """
    event_format: typing.Literal["client", "federation"] = "client"
    account_data: EventFilter = None
    presence: EventFilter = None
    room: RoomFilter = None


class FilterResponse(CustomBaseModel):
    filter_id: str
