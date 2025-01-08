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

if typing.TYPE_CHECKING:
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
]


class Empty(BaseModel):
    """Represents an empty response body."""


class Any(BaseModel):
    """Represents a response body with no pre-defined content"""

    model_config = ConfigDict(extra="allow")


class RoomPredecessor(BaseModel):
    room_id: str
    """The previous room's room ID"""
    event_id: str
    """The previous room's last known event ID. Usually the m.room.tombstone event."""


class JoinResponse(BaseModel):
    """The result of joining a room"""

    room_id: str
    """The ID of the room that was joined"""


class EventSendResponse(BaseModel):
    """The result of sending an event"""

    event_id: str
    """The ID of the event that was sent"""


class LoginFlows(BaseModel):
    """The result of fetching supported login methods"""

    class LoginFlow(BaseModel):
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


class LoginResponse(BaseModel):
    """The result of logging in"""

    class DiscoveryInformation(BaseModel):
        class ServerInformation(BaseModel):
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


class WhoAmI(BaseModel):
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


class ResolveRoomAliasResponse(BaseModel):
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
