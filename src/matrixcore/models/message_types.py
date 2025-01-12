import typing

from pydantic import Field

from ..media import MXCUri
from .lib import Any as AnyData
from .lib import CustomBaseModel, EventSendResponse

__all__ = (
    "MText",
    "MNotice",
    "MEmote",
    "MImage",
    "Mentions",
    "RelatesTo",
    "ImageInfo",
)


class Mentions(CustomBaseModel):
    """The mentions enabled for this message"""

    room: bool = None
    user_ids: list[str] = None


class RelatesTo(CustomBaseModel):
    """The relation to another event"""

    event_id: str = None
    in_reply_to: EventSendResponse = Field(None, alias="m.in_reply_to")
    rel_type: str = None


class ImageInfo(CustomBaseModel):
    """Metadata about the image, such as a thumbnail."""

    h: int = None
    """The height of the image in pixels."""
    w: int = None
    """The width of the image in pixels."""
    mimetype: str = None
    """The mimetype of the image, e.g. image/jpeg."""
    size: int = None
    """The size of the image in bytes."""
    thumbnail_info: "ImageInfo" = None
    """Metadata about a thumbnail of the image."""
    thumbnail_url: MXCUri = None
    """The URL to a thumbnail of the image."""


class MText(AnyData):
    """Represents the base m.text message."""

    msgtype: str = "m.text"
    """The type of this message"""
    body: str
    """The plain text body"""
    formatted_body: str = None
    """The formatted body"""
    format: str = None
    """The format of the formatted body. Usually org.matrix.custom.html"""
    m_mentions: Mentions = Field(None, alias="m.mentions")
    """The mentions enabled for this message"""
    m_relates_to: RelatesTo = Field(None, alias="m.relates_to")
    """The relation to another event"""


class MNotice(MText):
    """Represents a notice message, usually sent by bots."""

    msgtype: typing.Literal["m.notice"] = "m.notice"


class MEmote(MText):
    """Represents an emote message"""

    msgtype: typing.Literal["m.emote"] = "m.emote"


class MImage(MText):
    """Represents an image message"""

    msgtype: typing.Literal["m.image"] = "m.image"
    url: MXCUri
    """The URL to the image."""
    info: ImageInfo = None
    """Metadata about the image, such as a thumbnail."""
