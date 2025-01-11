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
import asyncio
import collections
import json
import logging
import sys
import typing
import uuid
from importlib.metadata import version as package_version
from typing import Any, Literal, Self, Type, TypeVar, overload
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from .errors import MatrixHTTPException
from .models import Any as AnyData
from .models import (
    ClientEvent,
    Empty,
    EventSendResponse,
    Filter,
    InvitedRoom,
    JoinResponse,
    KnockedRoom,
    LeftRoom,
    LoginFlows,
    LoginResponse,
    MRoomPowerLevels,
    ResolveRoomAliasResponse,
    StrippedStateEvent,
    SyncResponse,
    UserProfile,
    WhoAmI,
)
from .models.lib import FilterResponse
from .room import Room

T = TypeVar("T")
T_MODEL_TYPE = TypeVar("T_MODEL_TYPE", bound=Type[BaseModel])
T_MODEL_TYPE_COVAR = TypeVar("T_MODEL_TYPE_COVAR", covariant=True, bound=Type[BaseModel])


log = logging.getLogger(__name__)


class MatrixCoreHTTPClient:
    """
    Next generation client library HTTP backend
    """

    USER_AGENT = "NioBot+MatrixCore/0.0.0 (+https://pypi.org/p/nio-bot) python/{} httpx/{}".format(
        ".".join(map(str, sys.version_info[:3])),
        package_version("httpx"),
    )

    def __init__(
        self,
        homeserver_base_url: str,
    ):
        self.homeserver_base_url = homeserver_base_url
        self.client = httpx.AsyncClient(
            headers={"User-Agent": self.USER_AGENT},
            base_url=homeserver_base_url,
        )
        self.access_token: str | None = None
        self.user_id: str | None = None
        self.device_id: str | None = None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_):
        await self.close()

    @property
    def request_headers(self) -> dict[str, str]:
        h = {
            "User-Agent": self.USER_AGENT,
        }
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        log.debug("Produced headers: %r", h)
        return h

    @staticmethod
    def construct_uri(*parts: str | int, no_escape: bool = False, safe: str = None) -> str:
        """
        Constructs a URI (excluding base URL) to pass to a request.

        :param parts: Each part to join with a /. If no_escape is False, this will urlencode each part.
        :param no_escape: If true, automatic URL encoding is disabled.
        :param safe: Characters to not escape. Only used if no_escape is False.
        :return: URI (excluding base URL).
        """
        if not any(parts[0] == x for x in ("_matrix", "_synapse", "_dendrite", "_conduwuit")):  # note: inflexible!
            parts = ("_matrix", *parts)
        if no_escape:
            return "/" + "/".join(map(str, parts))
        else:
            constructed = [quote(x, safe=safe or "") for x in map(str, parts)]
            return "/" + "/".join(constructed)

    async def _get(
        self,
        uri: str,
        query_params: dict[str, Any] | None = None,
        extra_headers: dict[str, Any] | None = None,
        *,
        timeout: httpx.Timeout | float | int | None = None,
        model: T_MODEL_TYPE | None,
    ) -> T_MODEL_TYPE_COVAR:
        """
        Attempts to make a GET request with the given parameters.

        :param uri: URI to make a GET request.
        :param query_params: Query parameters to pass to the GET request.
        :param extra_headers: Extra headers to pass to the GET request.
        :param timeout: Override timeout for this request.
        :param model: The model to parse the response with. None to receive the raw JSON data.
        :return: The validated model
        """
        headers = self.request_headers
        if extra_headers:
            headers.update(extra_headers)
        kwargs = {"headers": headers}

        if query_params:
            kwargs["params"] = query_params
        if extra_headers is not None:
            kwargs["headers"] = extra_headers
        if timeout is not None:
            kwargs["timeout"] = timeout
        response = await self.client.get(uri, **kwargs)
        if response.status_code not in range(200, 300):
            raise MatrixHTTPException.from_response(response)

        data = response.json()
        if model is None:
            return data

        return model.model_validate(data)

    async def _post(
        self,
        uri: str,
        data: dict[str, Any] | bytes | None,
        query_params: dict[str, Any] | None = None,
        extra_headers: dict[str, Any] | None = None,
        *,
        timeout: httpx.Timeout | float | int | None = None,
        model: T_MODEL_TYPE,
    ) -> T_MODEL_TYPE_COVAR:
        """
        Attempts to make a POST request with the given parameters.

        :param uri: URI to make a POST request.
        :param query_params: Query parameters to pass to the POST request.
        :param extra_headers: Extra headers to pass to the POST request.
        :param data: Data to pass to the POST request.
        :param timeout: Override timeout for this request.
        :param model: The model to parse the response with. None to receive the raw JSON data.
        :return: The validated model
        """
        headers = self.request_headers
        if extra_headers:
            headers.update(extra_headers)
        kwargs = {"headers": headers}

        if query_params:
            kwargs["params"] = query_params
        if timeout is not None:
            kwargs["timeout"] = timeout
        if isinstance(data, bytes):
            kwargs["body"] = data
        elif isinstance(data, (dict, list)):
            kwargs["json"] = data

        response = await self.client.post(uri, **kwargs)
        if response.status_code not in range(200, 300):
            raise MatrixHTTPException.from_response(response)

        data = response.json()
        log.debug("Validating %r: %r", model, data)
        return model.model_validate(data)

    async def _put(
        self,
        uri: str,
        data: dict[str, Any] | bytes | None,
        query_params: dict[str, Any] | None = None,
        extra_headers: dict[str, Any] | None = None,
        *,
        timeout: httpx.Timeout | float | int | None = None,
        model: T_MODEL_TYPE,
    ) -> T_MODEL_TYPE_COVAR:
        """
        Attempts to make a PUT request with the given parameters.

        :param uri: URI to make a PUT request.
        :param query_params: Query parameters to pass to the PUT request.
        :param extra_headers: Extra headers to pass to the PUT request.
        :param data: Data to pass to the PUT request.
        :param timeout: Override timeout for this request.
        :param model: The model to parse the response with. None to receive the raw JSON data.
        :return: The validated model
        """
        headers = self.request_headers
        if extra_headers:
            headers.update(extra_headers)
        kwargs = {"headers": headers}

        if query_params:
            kwargs["params"] = query_params
        if timeout is not None:
            kwargs["timeout"] = timeout
        if isinstance(data, bytes):
            kwargs["body"] = data
        elif isinstance(data, (dict, list)):
            kwargs["json"] = data

        response = await self.client.put(uri, **kwargs)
        if response.status_code not in range(200, 300):
            raise MatrixHTTPException.from_response(response)

        data = response.json()
        return model.model_validate(data)

    def clear(self) -> Self:
        """Clears the current login state (i.e. null user_id, access_token, device_id, etc.)"""
        self.access_token = None
        self.device_id = None
        self.user_id = None
        return self

    async def close(self) -> None:
        """Shuts down the client, closing any open connections, and clearing any state."""
        await self.client.aclose()
        self.clear()

    async def decline_invite(self, room_id: str, reason: str = None) -> Empty:
        """
        Alias function for leave_room.
        """
        return await self.leave_room(room_id, reason)

    async def get_login_types(self) -> LoginFlows:
        """
        Fetches the supported login types for this server.

        :return: LoginFlows
        :raises RateLimited: This request was rate-limited.
        """
        return await self._get(self.construct_uri("client", "v3", "login"), model=LoginFlows)

    async def join_room(
        self,
        room_id_or_alias: str,
        vias: list[str] = None,
        reason: str = None,
    ) -> JoinResponse:
        """
        Joins a room via a room ID *or* alias.

        This function may take a long time to return and has the HTTP request timeout disabled.
        You should use asyncio.wait_for with a custom timeout to prevent this function from running for longer
        than is acceptable.

        :param room_id_or_alias: Room ID or alias to join.
        :param vias: List of server names to join through.
        :param reason: A reason for joining
        :return: JoinResponse - the result of joining. Includes a room ID.
        :raises NotAuthorised: You did not authenticate.
        :raises Forbidden: Your request to join was forbidden (e.g. user is banned, not invited, etc.)
        :raises RateLimited: This request was rate-limited.
        """
        if not room_id_or_alias.startswith(("!", "#")):
            raise ValueError("room_id_or_alias must start with '!' or '#'")
        uri = self.construct_uri("client", "v3", "join", room_id_or_alias)
        if vias:
            # This dirty trick allows us to pass the same query params multiple times, which
            # httpx traditionally does not seem to let us do.
            prepared_vias = []
            for server_name in vias:
                encoded = quote(server_name, safe="")
                prepared_vias += [
                    "via=" + encoded,
                    "server_name=" + encoded,
                ]
            uri += "?" + "&".join(prepared_vias)

        data = {"reason": reason} if reason else {}
        return await self._post(uri, data, timeout=httpx.Timeout(None), model=JoinResponse)

    @overload
    async def get_room_state(self, room_id: str) -> list[ClientEvent | StrippedStateEvent]: ...

    @overload
    async def get_room_state(self, room_id: str, event_type: str = None, state_key: str = None) -> dict[str, Any]: ...

    async def get_room_state(
        self, room_id: str, event_type: str = None, state_key: str = None
    ) -> list[ClientEvent | StrippedStateEvent] | dict[str, Any]:
        """
        Fetches all/a specific current state event(s) for a given room.

        :param room_id: The room ID to fetch state for.
        :param event_type: The specific event type to fetch. If not provided, fetches all state.
        :param state_key: The specific state key to fetch. If not provided, fetches all state.
        :return: A list of state events.
        :raises ValueError: You did not pass a room ID
        :raises NotAuthorised: You did not authenticate.
        :raises BadRequest: The request was malformed.
        :raises NotFound: The room was not found.
        """
        if not room_id.startswith("!"):
            raise ValueError("room_id must start with '!'")

        if event_type is None and state_key is None:  # fetch all state
            data = await self._get(self.construct_uri("client", "v3", "rooms", room_id, "state", safe="!:"), model=None)
            parsed = []
            for event in data:
                try:
                    e = ClientEvent.model_validate(event)
                    parsed.append(e)
                except ValidationError:
                    try:
                        e = StrippedStateEvent.model_validate(event)
                        parsed.append(e)
                    except ValidationError:
                        logging.warning("Failed to validate state event: %r", event)
            return parsed
        elif event_type and state_key is None:
            raise ValueError("You must provide a state_key if you provide an event_type")
        elif event_type is None and state_key:
            raise ValueError("You must provide an event_type if you provide a state_key")
        else:
            return await self._get(
                self.construct_uri("client", "v3", "rooms", room_id, "state", event_type, state_key, safe="!:"),
                model=None,
            )

    async def get_profile(self, user_id: str) -> UserProfile:
        """
        Fetches the profile for this user.

        :param user_id: The user ID to fetch the profile for.
        :return: The user's profile.
        :raises Forbidden: The user's homeserver will not disclose if they exist
        :raises NotFound: The user does not exist.
        """
        return await self._get(self.construct_uri("client", "v3", "profile", user_id), model=UserProfile)

    async def leave_room(self, room_id: str, reason: str = None) -> Empty:
        """
        Leaves a room (if the current user is in it), or declines an invitation to a room.

        :param room_id: The room ID to leave.
        :param reason: A reason for leaving. None to omit a reason.
        :return: Empty - the request was successful.
        :raises NotAuthorised: You did not authenticate.
        :raises RateLimited: This request was rate-limited.
        """
        if not room_id.startswith("!"):
            raise ValueError("room_id must start with '!'")

        uri = self.construct_uri("client", "v3", "rooms", room_id, "leave")
        data = {"reason": reason} if reason else {}
        return await self._post(uri, data, model=Empty)

    async def login(
        self,
        login_type: str,
        device_id: str = None,
        identifier: dict[Literal["type"] | str, Any] = None,
        initial_device_display_name: str = None,
        password: str = None,
        token: str = None,
    ) -> LoginResponse:
        """
        Performs a login with the given credentials.

        This function, if successful, will populate this client's login state.

        :param login_type: The type of login to perform. Usually "m.login.password".
        Can be fetched with `get_login_types`.
        :param device_id: ID of the client device. Auto-generated if not provided. Must be consistent!
        :param identifier: Identification information for a user
        :param initial_device_display_name: Initial device display name. Ignored for existing `device_id`s.
        :param password: Password for the user. Required when type is "m.login.password".
        :param token: Token for the user. Required when type is "m.login.token".
        :return: LoginResponse
        :raises BadRequest: Part of the request was invalid. For example, the login type may not be recognised.
        :raises Forbidden: The login attempt failed. This can include one of the following error codes:
        :raises RateLimited: This request was rate-limited.
        :raises ValueError: You provided malformed data.
        """
        payload = {"type": login_type}
        if device_id is not None:
            payload["device_id"] = device_id
        if initial_device_display_name is not None:
            payload["initial_device_display_name"] = initial_device_display_name
        if password is not None:
            payload["password"] = password
        if token is not None:
            payload["token"] = token
        if identifier is not None:
            if "type" not in identifier:
                raise ValueError("'type' is a required key in `identifier`")
            payload["identifier"] = identifier

        log.debug(payload)
        return await self._post(
            self.construct_uri("client", "v3", "login"),
            data=payload,
            model=LoginResponse
        )

    async def logout(self, all_devices: bool = False) -> Empty:
        """
        Invalidates the current session, requiring re-authentication for further requests.

        This function, if successful, will clear this client's login state.

        :param all_devices: If True, this function calls logout_all instead.
        :return: Empty - the request was successful.
        :raises NotAuthorised: The access token was invalid or not provided.
        """
        if all_devices:
            return await self.logout_all()
        r = await self._post(self.construct_uri("client", "v3", "logout"), None, model=Empty)
        self.clear()
        return r

    async def logout_all(self) -> Empty:
        """
        Invalidates all sessions for the authenticated user.

        This function, if successful, will clear this client's login state.

        :return: Empty - the request was successful.
        :raises NotAuthorised: The access token was invalid or not provided.
        """
        r = await self._post(self.construct_uri("client", "v3", "logout", "all"), None, model=Empty)
        self.clear()
        return r

    async def redact_event(
        self, room_id: str, event_id: str, reason: str = None, txn_id: str = None
    ) -> EventSendResponse:
        """
        Redacts an event in the given room.

        :param room_id: The room ID to redact the event in.
        :param event_id: The event ID to redact.
        :param reason: The reason for redacting the event.
        :param txn_id: The transaction ID for this event. If omitted, one will be generated. It is recommended that you
        omit this unless you know what you are doing.
        :return: EventSendResponse - the resulting m.room.redact timeline event's ID
        :raises NotAuthorised: You did not authenticate.
        :raises BadRequest: The request was malformed.
        """
        if not room_id.startswith("!"):
            raise ValueError("room_id must start with '!'")

        if not txn_id:
            txn_id = hash((room_id, event_id, reason, self.access_token))

        uri = self.construct_uri("client", "v3", "rooms", room_id, "redact", event_id, txn_id)
        data = {"reason": reason} if reason else {}
        return await self._post(uri, data, model=EventSendResponse)

    async def resolve_room_alias(self, room_alias: str) -> ResolveRoomAliasResponse:
        """
        Resolves a room alias to a room ID.

        :param room_alias: The room alias to resolve.
        :return: The room ID.
        :raises BadRequest: The given roomAlias is not a valid room alias.
        :raises NotFound: The given room alias does not exist.
        """
        if not room_alias.startswith("#"):
            raise ValueError("room_alias must start with '#'")
        return await self._get(
            self.construct_uri("client", "v3", "directory", "room", room_alias), model=ResolveRoomAliasResponse
        )

    async def send_event(
        self, room_id: str, event_type: str, body: BaseModel | dict, txn_id: str = None
    ) -> EventSendResponse:
        """
        Sends a single event in the given room.

        :param room_id: The room ID to send the event in.
        :param event_type: The type of event to send. Usually m.room.message.
        :param body: The body of the event to send.
        :param txn_id: The transaction ID for this event. If omitted, one will be generated. It is recommended that you
        omit this unless you know what you are doing.
        :return: EventSendResponse - the result of sending the event.
        :raises NotAuthorised: You did not authenticate.
        :raises BadRequest: The request was malformed.
        """
        if not room_id.startswith("!"):
            raise ValueError("room_id must start with '!'")

        if not isinstance(body, BaseModel):
            body = AnyData.model_validate(body)

        if not txn_id:
            txn_id = hash((body.model_dump_json(exclude_unset=True), room_id, event_type, self.access_token))

        uri = self.construct_uri("client", "v3", "rooms", room_id, "send", event_type, txn_id)
        data = body.model_dump(exclude_unset=True)
        return await self._put(uri, data, model=EventSendResponse)

    async def whoami(self) -> WhoAmI:
        """
        Fetches the data associated with the current access token.
        Can be used to fetch your own user ID.

        :return: WhoAmI
        :raises NotAuthorized: The token is not recognised
        :raises Forbidden: The appservice cannot masquerade as the user or has not registered them.
        :raises RateLimited: This request was rate-limited.
        """
        response: WhoAmI = await self._get(self.construct_uri("client", "v3", "account", "whoami"), model=WhoAmI)
        self.user_id = response.user_id
        if response.device_id:
            self.device_id = response.device_id
        return response

    async def sync(
        self,
        sync_filter: str | dict = None,
        full_state: bool = False,
        set_presence: str | None = None,
        since: str | None = None,
        timeout: int | None = 48,
    ) -> SyncResponse:
        """
        Syncs with the server
        """
        if not self.user_id:
            await self.whoami()
        query_params = {}
        if sync_filter:
            if isinstance(sync_filter, dict):
                sync_filter = json.dumps(sync_filter, separators=(",", ":"))
            query_params["filter"] = sync_filter
        if full_state is not None:
            query_params["full_state"] = json.dumps(full_state)
        if set_presence:
            query_params["set_presence"] = set_presence
        if since:
            query_params["since"] = since
        if timeout is not None and timeout > 0:
            query_params["timeout"] = timeout * 1000

        data: SyncResponse = await self._get(
            self.construct_uri("client", "v3", "sync"),
            query_params=query_params,
            timeout=httpx.Timeout(timeout),
            model=SyncResponse,
        )
        return data

    async def upload_filter(self, content: Filter) -> FilterResponse:
        """
        Uploads a filter to the server, returning the filter ID
        """
        if not self.user_id:
            raise ValueError("You must be logged in to do this.")
        response = await self._post(
            self.construct_uri("client", "v3", "user", self.user_id, "filter"),
            data=content.model_dump(exclude_unset=True, exclude_none=True),
            model=FilterResponse,
        )
        return response

    async def invite_user(self, room_id: str, user_id: str, reason: str = None) -> Empty:
        """
        Invites a user to a room.

        :param room_id: The room ID to invite the user to.
        :param user_id: The user ID to invite.
        :param reason: The reason for inviting the user.
        :return: Empty - the request was successful.
        """
        payload = {"user_id": user_id}
        if reason:
            payload["reason"] = reason
        return await self._post(
            self.construct_uri("client", "v3", "rooms", room_id, "invite"), data=payload, model=Empty
        )

    async def kick_user(self, room_id: str, user_id: str, reason: str = None) -> Empty:
        """
        Kicks a user from a room.

        :param room_id: The room ID to kick the user from.
        :param user_id: The user ID to kick.
        :param reason: The reason for kicking the user.
        :return: Empty - the request was successful.
        """
        payload = {"user_id": user_id}
        if reason:
            payload["reason"] = reason
        return await self._post(self.construct_uri("client", "v3", "rooms", room_id, "kick"), data=payload, model=Empty)

    async def ban_user(self, room_id: str, user_id: str, reason: str = None) -> Empty:
        """
        Bans a user from a room.

        :param room_id: The room ID to ban the user from.
        :param user_id: The user ID to ban.
        :param reason: The reason for banning the user.
        :return: Empty - the request was successful.
        """
        payload = {"user_id": user_id}
        if reason:
            payload["reason"] = reason
        return await self._post(self.construct_uri("client", "v3", "rooms", room_id, "ban"), data=payload, model=Empty)

    async def unban_user(self, room_id: str, user_id: str, reason: str = None) -> Empty:
        """
        Unbans a user from a room.

        :param room_id: The room ID to unban the user from.
        :param user_id: The user ID to unban.
        :param reason: The reason for unbanning the user.
        :return: Empty - the request was successful.
        """
        payload = {"user_id": user_id}
        if reason:
            payload["reason"] = reason
        return await self._post(
            self.construct_uri("client", "v3", "rooms", room_id, "unban"), data=payload, model=Empty
        )

    async def set_state(self, room_id: str, event_type: str, state_key: str, data: Any) -> EventSendResponse:
        """
        Sets a state event in the given room.

        :param room_id: The room ID to set the state event in.
        :param event_type: The type of event to set.
        :param state_key: The state key to set.
        :param data: The data to set.
        :return: EventSendResponse - the result of setting the state event.
        """
        if not room_id.startswith("!"):
            raise ValueError("room_id must start with '!'")
        if state_key:
            uri = self.construct_uri("client", "v3", "rooms", room_id, "state", event_type, state_key)
        else:
            uri = self.construct_uri("client", "v3", "rooms", room_id, "state", event_type)

        return await self._put(uri, data, model=EventSendResponse)

    async def create_room(
        self,
        *,
        name: str | None = None,
        topic: str | None = None,
        invite: list[str] = None,
        is_direct: bool = False,
        preset: typing.Literal["public_chat", "private_chat", "trusted_private_chat"] | None = None,
        room_alias: str | None = None,
        room_version: str | int | None = None,
        visibility: typing.Literal["public", "private"] | None = None,
        power_level_content_override: MRoomPowerLevels | None = None,
        creation_content: dict[typing.Literal["m.federate"] | str, bool | Any] | None = None,
        initial_state: list[dict[str, Any]] | None = None,
        unsupported_custom_room_id: str | None = None,
    ) -> JoinResponse:
        """
        Creates a room with the given parameters.

        Read: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3createroom

        :param name: The name of the room. Pass `None` to omit.
        :param topic: The topic of the room. Pass `None` to omit.
        :param invite: A list of user IDs to invite to the room. Pass `None` to omit.
        :param is_direct: If `True`, the room will be a direct chat. Defaults to `False`.
        :param preset: The preset for the room. Pass `None` to omit.
        :param room_alias: The alias for the room. Pass `None` to omit.
        :param room_version: The version of the room. Pass `None` to omit.
        :param visibility: The visibility of the room. Pass `None` to omit.
        :param power_level_content_override: The power level content override. Pass `None` to omit.
        :param creation_content: The creation content. Pass `None` to omit.
        :param initial_state: Any extra additional state events. Pass `None` to omit.
        :param unsupported_custom_room_id: The custom room ID. Pass `None` to omit.
        :return: JoinResponse - the result of creating the room.
        """
        payload = {}
        if creation_content is not None:
            payload["creation_content"] = creation_content
        if initial_state is not None:
            payload["initial_state"] = initial_state
        if invite is not None:
            payload["invite"] = invite
        payload["is_direct"] = is_direct
        if name is not None:
            payload["name"] = name
        if power_level_content_override:
            payload["power_level_content_override"] = power_level_content_override.model_dump(exclude_unset=True)
        if room_version is not None:
            payload["room_version"] = room_version
        if topic is not None:
            payload["topic"] = topic
        if visibility is not None:
            payload["visibility"] = visibility
        if preset is not None:
            payload["preset"] = preset
        if room_alias is not None:
            # Sanity check and make sure the user isn't passing a fully qualified room alias
            if room_alias.startswith("#") and ":" in room_alias:
                raise ValueError("room_alias must not be a fully qualified room alias, only the name part.")
            elif room_alias.startswith("#"):
                log.warning(
                    "You probably don't want your room alias to start with #, as this would result in the final "
                    "alias being ##youralias:yourhomeserver.com. If you want to create a room alias, pass the name. "
                    "Got: %r",
                    room_alias,
                )
            payload["room_alias_name"] = room_alias

        if unsupported_custom_room_id:
            if unsupported_custom_room_id.startswith("!"):
                raise ValueError("unsupported_custom_room_id must not start with '!'.")
            log.warning(
                "The 'unsupported_custom_room_id' parameter is not officially part of the Matrix specification and"
                " requires very specific homeserver support in order to work. Your request may not work as expected. "
                "Got: %r",
                unsupported_custom_room_id,
            )
            payload["room_id"] = unsupported_custom_room_id

        return await self._post(self.construct_uri("client", "v3", "createRoom"), data=payload, model=JoinResponse)


class MatrixCore:
    """
    Next generation matrix client library
    """

    def __init__(
        self,
        homeserver_base_url: str,
        *,
        event_cache_size: int = 5000,
    ):
        self.http = MatrixCoreHTTPClient(homeserver_base_url)
        self._sync_lock = asyncio.Lock()

        self.next_batch = None
        self.invited_rooms: dict[str, InvitedRoom] = {}
        self.knocked_rooms: dict[str, KnockedRoom] = {}
        self.joined_rooms: dict[str, Room] = {}
        self.left_rooms: dict[str, LeftRoom] = {}

        self.event_handlers: dict[str, list] = {}
        self._pending_callbacks: list[asyncio.Task[Any]] = []
        self.event_cache = collections.deque(maxlen=event_cache_size)

    def _remove_room_from_register(self, room_id: str) -> str:
        x = self.invited_rooms.pop(room_id, None)
        y = x or self.knocked_rooms.pop(room_id, None)
        z = y or self.joined_rooms.pop(room_id, None)
        a = z or self.left_rooms.pop(room_id, None)

        if a:
            return "leave"
        if z:
            return "join"
        if y:
            return "knock"
        if x:
            return "invite"
        return "unknown"

    def dispatch(self, event: str, *data: Any, **kdata: Any) -> None:
        """
        Dispatches an event to any internal listeners.

        :param event: The event to dispatch. E.g. m.room.message, room_join
        :param data: The data to send.
        :param kdata: The data to send.
        :return: None
        """
        tasks = []
        for callback in self.event_handlers.get(event, []):
            task = asyncio.create_task(callback(*data, **kdata), name=f"callback_{event}_{uuid.uuid4().hex}")
            task.add_done_callback(lambda t: self._pending_callbacks.remove(t))
            tasks.append(task)
        self._pending_callbacks += tasks

    def on(self, event_name: str):
        """Registers an event listener callback for :name"""

        def wrapper(func):
            self.event_handlers.setdefault(event_name, [])
            if func in self.event_handlers[event_name]:
                raise ValueError(f"{event_name} already registered {func}.")
            self.event_handlers[event_name].append(func)
            return func

        return wrapper

    def process_sync(self, data: SyncResponse):
        room_states = {}
        if not data.rooms:
            self.next_batch = data.next_batch
            return data
        if data.rooms.invite:
            for room_id, room in data.rooms.invite.items():
                if room_id not in self.invited_rooms:
                    prev_state = self._remove_room_from_register(room_id)
                    self.invited_rooms[room_id] = room
                    room_states[room_id] = (prev_state, "invite")
                    self.dispatch("room_invite", room)

        if data.rooms.knock:
            for room_id, room in data.rooms.knock.items():
                if room_id not in self.knocked_rooms:
                    prev_state = self._remove_room_from_register(room_id)
                    self.knocked_rooms[room_id] = room
                    room_states[room_id] = (prev_state, "knock")
                    self.dispatch("room_knock", room)

        if data.rooms.join:
            for room_id, joined_room in data.rooms.join.items():
                if room_id not in self.joined_rooms:
                    prev_state = self._remove_room_from_register(room_id)
                    room_obj = Room(room_id, client=self)
                    if joined_room.summary:
                        room_obj.summary = joined_room.summary
                    room_states[room_id] = (prev_state, "join")
                    self.joined_rooms[room_id] = room_obj
                    self.dispatch("room_join", room_obj)
                else:
                    room_obj = self.joined_rooms[room_id]

                if joined_room.state:
                    for event in joined_room.state.events:
                        room_obj.process_state_event(event)
                        self.event_cache.append(event)
                        self.dispatch(event.type, room_obj, event)
                if joined_room.timeline:
                    for event in joined_room.timeline.events:
                        self.event_cache.append(event)
                        self.dispatch(event.type, room_obj, event)

        if data.rooms.leave:
            for room_id, left_room in data.rooms.leave.items():
                if room_id not in self.left_rooms:
                    prev_state = self._remove_room_from_register(room_id)
                    self.left_rooms[room_id] = left_room
                    room_states[room_id] = (prev_state, "leave")
                    self.dispatch("room_leave", left_room)
        self.next_batch = data.next_batch

    async def sync(self, sync_filter: Filter | str) -> SyncResponse:
        """Syncs with the server"""
        if isinstance(sync_filter, Filter):
            sync_filter = (await self.http.upload_filter(sync_filter)).filter_id
        data = await self.http.sync(sync_filter, timeout=None if self.next_batch is None else 48, since=self.next_batch)
        self.dispatch("sync", data)

        async with self._sync_lock:
            self.process_sync(data)

        return data

    def get_cached_event(self, event_id: str) -> ClientEvent | StrippedStateEvent | None:
        for event in self.event_cache:
            if event.event_id == event_id:
                return event
        return None

    async def password_login(
        self,
        user_id: str,
        password: str,
        device_id: str = None,
    ) -> LoginResponse:
        res = await self.http.login(
            "m.login.password",
            device_id=device_id,
            identifier={"type": "m.id.user", "user": user_id},
            password=password,
        )
        self.http.access_token = res.access_token
        self.http.user_id = res.user_id
        self.http.device_id = res.device_id
        return res
