# I hate this. Please work.
import typing

import olm

from ..models.encryption import DeviceKeys, KeyObject, KeyUploadResponse
from ..models.lib import AnyData


if typing.TYPE_CHECKING:
    from ..core import MatrixCore


class Olm:
    def __init__(self, client: "MatrixCore"):
        self.client = client

        self.account = olm.Account()
        self.account.generate_one_time_keys(10)

    async def upload_keys(
            self,
            device_keys: DeviceKeys | None = None,
            fallback_keys: dict[str, str | KeyObject] | None = None,
            one_time_keys: dict[str, str | KeyObject] | None = None,
    ) -> KeyUploadResponse:
        """
        Uploads the given keys to the server.

        See: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3keysupload

        :param device_keys: Identity keys for the device. May be absent if no new identity keys are required.
        :param fallback_keys: Fallback keys for the device.
        :param one_time_keys: One-time keys for the device.
        """
        body = {}
        if device_keys is not None:
            body["device_keys"] = device_keys.model_dump(mode="json")
        if fallback_keys is not None:
            body["fallback_keys"] = AnyData.model_validate(fallback_keys).model_dump(mode="json")
        if one_time_keys is not None:
            body["one_time_keys"] = AnyData.model_validate(one_time_keys).model_dump(mode="json")
        return await self.client.http._post(
            self.client.http.construct_uri("_matrix", "client", "v3", "keys", "upload"),
            body,
            model=KeyUploadResponse
        )
