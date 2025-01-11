from pydantic import Field

from .events import ClientEventWithoutRoomID, StrippedStateEvent
from .lib import CustomBaseModel

__all__ = (
    "GenericEvent",
    "SyncAccountData",
    "SyncPresenceData",
    "SyncEphemeralData",
    "SyncRoomStateData",
    "SyncRoomSummary",
    "SyncRoomNotificationCounts",
    "SyncRoomTimeline",
    "SyncToDeviceData",
    "SyncDeviceListsData",
    "SyncInvitedRoom",
    "SyncKnockedRoom",
    "SyncJoinedRoom",
    "SyncLeftRoom",
    "SyncResponseRooms",
    "SyncResponse",
)


class GenericEvent(CustomBaseModel):
    content: dict
    type: str


class SyncAccountData(CustomBaseModel):
    """The private data created by this user."""

    events: list[GenericEvent] = None


class SyncPresenceData(CustomBaseModel):
    """The updates to the presence status of other users."""

    events: list[GenericEvent] = None


class SyncEphemeralData(CustomBaseModel):
    """
    The new ephemeral events in the room (events that aren’t recorded in the timeline or state of the room).
    In this version of the spec, these are typing notification and read receipt events.
    """

    events: list[GenericEvent] = None


class SyncRoomStateData(CustomBaseModel):
    """represents the state of a room"""

    events: list[ClientEventWithoutRoomID]


class SyncRoomSummary(CustomBaseModel):
    """
    Represents a room summary
    """

    m_heroes: list[str] = Field(default=None, alias="m.heroes")
    """
    The users which can be used to generate a room name if the room does not have one. 
    Required if the room’s m.room.name or m.room.canonical_alias state events are unset or empty.

    This should be the first 5 members of the room, ordered by stream ordering, which are joined or invited. 
    The list must never include the client’s own user ID. When no joined or invited members are available, 
    this should consist of the banned and left users. More than 5 members may be provided, 
    however less than 5 should only be provided when there are less than 5 members to represent.
    
    When lazy-loading room members is enabled, the membership events for the heroes MUST be included in the state,
    unless they are redundant. When the list of users changes, the server notifies the client by sending a fresh list
    of heroes. If there are no changes since the last sync, this field may be omitted.
    """
    m_invited_member_count: int = Field(default=None, alias="m.invited_member_count")
    """
    The number of users with membership of invite. 
    If this field has not changed since the last sync, it may be omitted. Required otherwise.
    """
    m_joined_member_count: int = Field(default=None, alias="m.joined_member_count")
    """
    The number of users with membership of join, including the client’s own user ID. 
    If this field has not changed since the last sync, it may be omitted. Required otherwise.
    """


class SyncRoomNotificationCounts(CustomBaseModel):
    highlight_count: int = None
    """The number of unread notifications for this room with the highlight flag set."""
    notification_count: int = None
    """The total number of unread notifications for this room."""


class SyncRoomTimeline(CustomBaseModel):
    limit: bool = False
    prev_batch: str = None
    """
    A token that can be supplied to the from parameter of the /rooms/<room_id>/messages endpoint in order to
    retrieve earlier events. 
    If no earlier events are available, this property may be omitted from the response.
    """
    events: list[ClientEventWithoutRoomID]
    """List of events"""


class SyncToDeviceData(CustomBaseModel):
    """Information on the send-to-device messages for the client device."""

    class ToDeviceEvent(CustomBaseModel):
        content: dict
        """The content of this event. The fields in this object will vary depending on the type of event."""
        type: str
        """The type of event"""
        sender: str
        """The user ID of the sender"""

    events: list[ToDeviceEvent] = None


class SyncDeviceListsData(CustomBaseModel):
    changed: list[str] = None
    """
    List of users who have updated their device identity or cross-signing keys,
    or who now share an encrypted room with the client since the previous sync response.
    """
    left: list[str] = None
    """
    List of users with whom we do not share any encrypted rooms anymore since the previous sync response.
    """


class SyncInvitedRoom(CustomBaseModel):
    """Represents a room the user has been invited to, but not yet joined"""

    class InviteState(CustomBaseModel):
        events: list[StrippedStateEvent] = None

    invite_state: InviteState


class SyncJoinedRoom(CustomBaseModel):
    """Represents a room the user has joined and is currently in"""

    account_data: SyncAccountData = None
    state: SyncRoomStateData = None
    ephemeral: SyncEphemeralData = None
    summary: SyncRoomSummary = None
    timeline: SyncRoomTimeline = None
    unread_notifications: SyncRoomNotificationCounts = None
    unread_threads_notifications: SyncRoomNotificationCounts = None


class SyncKnockedRoom(CustomBaseModel):
    """Represents a room the user is now knocking to join"""

    class KnockState(CustomBaseModel):
        events: list[StrippedStateEvent] = None

    knock_state: KnockState


class SyncLeftRoom(CustomBaseModel):
    """Represents a room the user has left and is no longer a member of"""

    account_data: SyncAccountData = None
    state: SyncRoomStateData = None
    timeline: SyncRoomTimeline = None


class SyncResponseRooms(CustomBaseModel):
    # noinspection PyDataclass
    invite: dict[str, SyncInvitedRoom] = Field(default_factory=dict)
    """Rooms that the user has been invited to"""
    # noinspection PyDataclass
    join: dict[str, SyncJoinedRoom] = Field(default_factory=dict)
    """Rooms that the user has joined and is currently in"""
    # noinspection PyDataclass
    knock: dict[str, SyncKnockedRoom] = Field(default_factory=dict)
    """Rooms that the user is now knocking to join"""
    # noinspection PyDataclass
    leave: dict[str, SyncLeftRoom] = Field(default_factory=dict)
    """Rooms that the user has left and is no longer a member of"""


class SyncResponse(CustomBaseModel):
    """Response of /sync"""

    account_data: SyncAccountData = None
    """The global private data created by this user."""
    device_lists: SyncDeviceListsData = None
    """Information on end-to-end device updates, as specified in End-to-end encryption."""
    device_one_time_keys_count: dict[str, int] = None
    """Information on end-to-end encryption keys, as specified in End-to-end encryption."""
    next_batch: str
    """The batch token to supply in the since param of the next /sync request."""
    presence: SyncPresenceData = None
    """The updates to the presence status of other users."""
    rooms: SyncResponseRooms = Field(default_factory=SyncResponseRooms)
    """Updates to rooms."""
    to_device: SyncToDeviceData = None
    """Information on the send-to-device messages for the client device, as defined in Send-to-Device messaging."""
