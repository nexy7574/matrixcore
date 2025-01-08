import typing

from pydantic import AnyUrl, UrlConstraints, validate_call


class MXCUriObject(AnyUrl):
    """URL type for mxc:// URLs specifically."""

    _constraints = UrlConstraints(allowed_schemes=["mxc"], host_required=True)


MXCUri = typing.Annotated[str, MXCUriObject]
"""Annotated type for mxc:// URLs. that returns a string instead of a URL Object."""


class Media:
    def __init__(self, server_name: str, media_id: str):
        self.server_name = server_name
        self.media_id = media_id

    def as_uri(self) -> str:
        return f"mxc://{self.server_name}/{self.media_id}"

    @classmethod
    @validate_call
    def from_uri(cls, uri: MXCUri):
        """
        Constructs a Media object from a mxc:// URI.

        :param uri: The mxc:// URI to parse.
        """
        server_name, media_id = uri[6:].split("/", 1)[1:]
        return cls(server_name, media_id)
