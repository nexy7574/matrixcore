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
import logging
import os
import typing
from enum import Enum
from fnmatch import fnmatch
from ipaddress import ip_address

from pydantic import BaseModel, ValidationError

from . import (
    MRoomAvatar,
    MRoomCanonicalAlias,
    MRoomCreate,
    MRoomEncryption,
    MRoomGuestAccess,
    MRoomHistoryVisibility,
    MRoomJoinRules,
    MRoomName,
    MRoomPowerLevels,
    MRoomTopic, MRoomMember, EventSendResponse,
)

if typing.TYPE_CHECKING:
    from .core import MatrixCore

from .media import MXCUri
from .models import ClientEvent, RoomPredecessor, StrippedStateEvent

log = logging.getLogger("matrixcore.room")
OVERRIDE_PL_CHECKS = os.getenv("MATRIXCORE_GLOBAL_ROOM_OVERRIDE_POWER_LEVEL_CHECKS", "False") in (
    "True",
    "true",
    "1",
    "yes",
    "on",
)


class GuestAccess(Enum):
    """The guest access level for the room."""

    FORBIDDEN = "forbidden"
    """Guests are not allowed to join the room."""
    CAN_JOIN = "can_join"
    """Guests are allowed to join the room."""


class JoinRule(Enum):
    """The rule for joining the room."""

    PUBLIC = "public"
    """anyone can join the room without any prior action."""
    INVITE = "invite"
    """a user must first receive an invite from someone already in the room in order to join."""
    KNOCK = "knock"
    """
    a user can request an invite to the room. They can be allowed (invited) or denied (kicked/banned) access.
    Otherwise, users need to be invited in.
    Only available in rooms which support knocking.
    """
    RESTRICTED = "restricted"
    """
    anyone able to satisfy at least one of the allow conditions is able to join the room without prior action.
    Otherwise, an invite is required.
    Only available in rooms which support the join rule.
    """
    KNOCK_RESTRICTED = "knock_restricted"
    """
    a user can request an invite using the same functions offered by the knock join rule,
    or can attempt to join having satisfied an allow condition per the restricted join rule.
    Only available in rooms which support the join rule.
    """
    PRIVATE = "private"
    """reserved without implementation. No significant meaning."""


class HistoryVisibility(Enum):
    """The visibility of the room's history."""

    WORLD_READABLE = "world_readable"
    """
    All events while this is the m.room.history_visibility value may be shared by any participating homeserver
    with anyone, regardless of whether they have ever joined the room.
    """
    SHARED = "shared"
    """
    Previous events are always accessible to newly joined members. All events in the room are accessible,
    even those sent when the member was not a part of the room.
    """
    INVITED = "invited"
    """
    Events are accessible to newly joined members from the point they were invited onwards. 
    Events stop being accessible when the member’s state changes to something other than invite or join.
    """
    JOINED = "joined"
    """
    Events are accessible to newly joined members from the point they joined the room onwards. 
    Events stop being accessible when the member’s state changes to something other than join.
    """


class ServerACLs(BaseModel):
    allow: list[str]
    """A list of explicitly allowed servers. Generally this is ["*"]."""
    deny: list[str]
    """A list of explicitly denied servers."""
    allow_ip_literals: bool
    """Whether to allow IP literals in the allow/deny lists."""

    def is_allowed(self, server_name: str) -> bool:
        """
        Checks that this ACL would permit the given server name.

        :param server_name: The server name to check.
        :return: Whether the server is allowed.
        """
        if self.allow_ip_literals is False:
            # 1. IP literals are checked first.
            try:
                ip_address(server_name)
                return False
            except ValueError:
                pass

        # 2. Deny list overrules allow list.
        if any((fnmatch(server_name, pattern) for pattern in self.deny)):
            return False

        # 3. Check if the server is explicitly allowed.
        if any((fnmatch(server_name, pattern) for pattern in self.allow)):
            return True

        # 4. If no rules match, deny access.
        return False


class Room:
    """
    Represents a room in Matrix.
    """

    def __init__(self, room_id: str, *, client: "MatrixCore"):
        self.id = room_id
        """The room's unique !ID:example.org."""
        self._client = client

        # All of these variables below are set by the `set_state` method.
        # Only overwrite them yourself if you know what you're doing.
        self.room_version: int = 1
        """The room's version."""
        self.creator: str = ""
        """This room's creator user ID, if available."""
        self.name: str | None = None
        """The room's name, if available. Prefer `display_name`."""
        self.topic: str | None = None
        """The room's topic, if available."""
        self.federated: bool = True
        """Whether the room is federated or not. Defaults to True if unavailable."""
        self.canonical_alias: str | None = None
        """The room's canonical alias, if available."""
        self.alt_aliases: list[str] = []
        """The room's alternative aliases, if available."""
        self.predecessor: RoomPredecessor | None = None
        """The room's predecessor, if available."""
        self.guest_access: GuestAccess = GuestAccess.FORBIDDEN
        """The room's guest access level."""
        self.join_rule: JoinRule = JoinRule.PRIVATE
        """The room's join rule."""
        self.join_conditions: list[str] | None = None
        """The conditions for joining the room, if it is restricted."""
        self.history_visibility: HistoryVisibility = HistoryVisibility.SHARED
        """The room's visibility for historical events."""
        self.avatar: MXCUri | None = None
        """The room's avatar, if set."""
        self.encrypted: bool = True
        """Whether the room is encrypted or not."""
        self.type: str | None = None
        """The room's custom type, if any."""
        self.server_acls: ServerACLs | None = None
        """The ACLs for this room"""
        self.power_levels: MRoomPowerLevels | None = None
        """The power levels for this room"""
        # Here we use the parsed event body as it has some utility functions. Normally we'd wrap it.
        self.members: dict[str, MRoomMember] = {}
        """
        All of the members in the room.
        """

        self.raw_state: dict[tuple[str, str], ClientEvent] = {}
        """
        All of the raw state events for this room.
        
        This dictionary stores events in the format: {(event_type, state_key): event}.
        You may want to use `Room.get_state` to get query this object easier.
        """
        self.override_local_power_level_checks: bool = OVERRIDE_PL_CHECKS
        """
        Choose to override local power level checks for the current user when sending requests.
        
        This is not recommended unless you know what you're doing.
        Tip: This can be set with the `MATRIXCORE_GLOBAL_ROOM_OVERRIDE_POWER_LEVEL_CHECKS=yes` environment variable.
        """

    def __str__(self):
        return self.id

    def __repr__(self):
        return (
            "<Room id={0.id!r} name={0.name!r} version={0.room_version} federated={0.federated} encrypted={0.encrypted}"
            " creator={0.creator!r} type={0.type} guest_access={0.guest_access} join_rule={0.join_rule} "
            "history_visibility={0.history_visibility} avatar={0.avatar!r} canonical_alias={0.canonical_alias!r}>"
        ).format(self)

    def get_members(self, membership_state: typing.Literal["join", "leave", "knock", "ban"] | None = "join") -> list:
        """
        Gets all the members in the room matching the given membership state.

        By default, this function calculates all the *joined* members.

        :param membership_state: The membership state to filter by. If None, returns all members, regardless of state.
        :return: A list of user IDs.
        """

    @staticmethod
    def _create_state_event_from_payload(payload: dict) -> ClientEvent | StrippedStateEvent:
        """
        Creates a state event from a raw payload.

        :param payload: The raw state event payload.
        :return: The state event.
        """
        if "room_id" in payload and "event_id" in payload:
            return ClientEvent.model_validate(payload)
        elif "content" in payload and "sender" in payload and "type" in payload:
            return StrippedStateEvent.model_validate(payload)
        raise ValueError("Invalid state event payload.")

    @classmethod
    async def get(cls, room_id_or_alias: str, *, client: "MatrixCore") -> "Room":
        """
        Get a room by its ID or alias.

        :param room_id_or_alias: The room's ID or alias.
        :param client: The client to use to get the room.
        :return: The resolved room
        :raises ValueError: If the room ID or alias is invalid.
        """
        if room_id_or_alias.startswith("#"):
            room_id = (await client.http.resolve_room_alias(room_id_or_alias)).room_id
        elif room_id_or_alias.startswith("!"):
            room_id = room_id_or_alias
        else:
            raise ValueError("Invalid room ID or alias. Must start with ! or #.")

        self = cls(room_id, client=client)
        state = await self.fetch_state()
        for event in state:
            self.process_state_event(event)
        return self

    async def leave(self, reason: str = None) -> None:
        """
        Leaves the current room.

        :param reason: The reason for leaving the room if any.
        """
        await self._client.http.leave_room(self.id, reason)

    @typing.overload
    async def fetch_state(self) -> list[ClientEvent | StrippedStateEvent]:
        """
        Get all state events for this room.

        This method is an API call. You may desire the `Room.raw_state` attribute instead.
        """
        ...

    @typing.overload
    async def fetch_state(self, event_type: str, state_key: str) -> dict[str, typing.Any]:
        """
        Get a specific state event for this room.
        """
        ...

    async def fetch_state(
        self, event_type: str = None, state_key: str = None
    ) -> list[ClientEvent | StrippedStateEvent] | dict[str, typing.Any]:
        """
        Gets all the current state events for the room.

        This method is an API call. You may desire the `Room.raw_state` attribute instead.

        :return: A list of unparsed state events.
        """
        if event_type is not None and state_key is None:
            raise ValueError('You must provide a state key to fetch. Don\'t forget, empty state keys are "", not None.')
        elif event_type is None and state_key is not None:
            raise ValueError("You must provide an event type to fetch with a state key.")

        if event_type is None or state_key is None:
            # Fetch all events
            return await self._client.http.get_room_state(self.id)
        else:
            # Fetch specific event
            return await self._client.http.get_room_state(self.id, event_type, state_key)

    def process_state_event(self, event: ClientEvent | StrippedStateEvent) -> typing.Self:
        """
        Processes a state event and sets the appropriate attributes.
        """
        match event.type:
            case "m.room.create":
                content = MRoomCreate.model_validate(event.content)
                self.room_version = content.room_version
                self.creator = content.creator or event.sender  # room v11+ has no creator field
                self.federated = content.federate
                self.predecessor = content.predecessor
                self.type = content.type
            case "m.room.name":
                content = MRoomName.model_validate(event.content)
                self.name = content.name
            case "m.room.topic":
                content = MRoomTopic.model_validate(event.content)
                self.topic = content.topic
            case "m.room.encryption":
                MRoomEncryption.model_validate(event.content)
                # There's nothing useful here, if this event exists, the room is encrypted. However, we should reject
                # the event if it does not pass validation. In this case, an error will be raised.
                self.encrypted = True
            case "m.room.avatar":
                content = MRoomAvatar.model_validate(event.content)
                self.avatar = content.url
            case "m.room.canonical_alias":
                content = MRoomCanonicalAlias.model_validate(event.content)
                self.canonical_alias = content.alias
                self.alt_aliases = content.alt_aliases
            case "m.room.guest_access":
                content = MRoomGuestAccess.model_validate(event.content)
                self.guest_access = GuestAccess(content.guest_access)
            case "m.room.join_rules":
                content = MRoomJoinRules.model_validate(event.content)
                self.join_rule = JoinRule(content.join_rule)
                self.join_conditions = content.allow
            case "m.room.history_visibility":
                content = MRoomHistoryVisibility.model_validate(event.content)
                self.history_visibility = HistoryVisibility(content.history_visibility)
            case "m.room.server_acl":
                self.server_acls = ServerACLs.model_validate(event.content)
            case "m.room.power_levels":
                content = MRoomPowerLevels.model_validate(event.content)
                self.power_levels = content
            case "m.room.member":
                content = MRoomMember.model_validate(event.content)
                self.members[event.state_key or event.sender] = content
            case _:
                log.debug("Unrecognised state event while processing %s: %r", self.id, event)

        key = (event.type, event.state_key)
        self.raw_state[key] = event
        return self

    async def send(self, event_type: str, event: BaseModel | dict) -> EventSendResponse:
        """
        Sends a message to the room.

        :param event_type: The event type to send.
        :param event: The event to send.
        :return: The response from the server.
        """
        return await self._client.http.send_event(self.id, event_type, event)
