import typing
import zoneinfo

from .media import MXCUri

if typing.TYPE_CHECKING:
    from .core import MatrixCore


class User:
    """
    Represents a global user on Matrix.
    """

    def __init__(self, user_id: str, *, client: "MatrixCore"):
        self._client = client
        self.user_id = user_id
        """The user's fully qualified user ID"""

        self.global_display_name: MXCUri | None = None
        self.global_avatar_url: MXCUri | None = None

        self.unstable_msc4133_profile: dict[str, str | typing.Any] | None = None
        """
        The key:value pairs of the MSC4133 profile.
        
        See: https://github.com/matrix-org/matrix-spec-proposals/pull/4133
        """
        self.unstable_msc4175_timezone: zoneinfo.ZoneInfo | None = None
        """
        The timezone of this user.
        
        See: https://github.com/matrix-org/matrix-spec-proposals/pull/4175
        """

    @property
    def localpart(self) -> str:
        """This user's localpart.

        I.e. @localpart:server.tld -> localpart"""
        return self.user_id.split(":")[0][1:]

    @property
    def homeserver(self) -> str:
        """This user's homeserver.

        I.e. @localpart:server.tld -> server.tld"""
        return self.user_id.split(":")[1]

    async def fetch_profile(self):
        """Fetches the user's profile."""
        profile = await self._client.http.get_profile(self.user_id)
        self.global_display_name = profile.get("displayname")
        self.global_avatar_url = profile.get("avatar_url")
