from pydantic import BaseModel

from matrixcore import ClientEvent, ClientEventWithoutRoomID, StrippedStateEvent


class Event(BaseModel):
    content: dict
    type: str


class AccountData(BaseModel):
    """The private data created by this user."""

    events: list[Event] = None


class Presence(BaseModel):
    """The updates to the presence status of other users."""

    events: list[Event] = None


class Ephemeral(BaseModel):
    """
    The new ephemeral events in the room (events that aren’t recorded in the timeline or state of the room).
    In this version of the spec, these are typing notification and read receipt events.
    """

    events: list[Event] = None


class InvitedRoom(BaseModel):
    """Represents a room the user has been invited to, but not yet joined"""

    class InviteState(BaseModel):
        events: list[StrippedStateEvent] = None

    invite_state: InviteState = None


class JoinedRoom(BaseModel):
    """Represents a room the user has joined and is currently in"""

    account_data: AccountData = None
    state: list[ClientEventWithoutRoomID] = None
    ephemeral: Ephemeral = None
    summary: dict = None
    timeline: dict = None
    unread_notifications: dict = None
    unread_threads_notifications: dict = None


class KnockRoom(BaseModel):
    """Represents a room the user is now knocking to join"""


class LeftRooms(BaseModel):
    """Represents a room the user has left and is no longer a member of"""


class Rooms(BaseModel):
    invite: dict[str, InvitedRoom]
    """Rooms that the user has been invited to"""
    join: dict[str, JoinedRoom]
    """Rooms that the user has joined and is currently in"""
    knock: dict[str, KnockRoom]
    """Rooms that the user is now knocking to join"""
    leave: dict[str, LeftRooms]
    """Rooms that the user has left and is no longer a member of"""


class SyncResponse(BaseModel):
    """Response of /sync"""

    next_batch: str
    """The batch token to supply in the since param of the next /sync request."""
    device_one_time_keys_count: dict[str, int] = None
    """Information on end-to-end encryption keys"""
    account_data: AccountData = None
    """The global private data created by this user."""
