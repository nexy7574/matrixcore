from typing import Any

from .lib import CustomBaseModel, AnyData


class KeyObject(CustomBaseModel):
    key: str
    """The key, encoded using unpadded base64."""
    signatures: dict[str, dict]
    """
     Signature for the device.
     Mapped from user ID to signature object, containing mapping from key signing identifier to the signature
     """


class DeviceKeys(CustomBaseModel):
    algorithms: list[str]
    """The encryption algorithms supported by this device."""
    device_id: str
    """The ID of the device these keys belong to. Must match the device ID used when logging in."""
    keys: dict[str, str]
    """
    Public identity keys. The names of the properties should be in the format <algorithm>:<device_id>.
    The keys themselves should be encoded as specified by the key algorithm.
    """
    signatures: dict[str, dict[str, str]]
    """
    Signatures for the device key object. A map from user ID, to a map from <algorithm>:<device_id> to the signature.
    """
    user_id: str
    """The ID of the user the device belongs to. Must match the user ID used when logging in."""


class DeviceInformation(DeviceKeys):
    unsigned: AnyData = None
    """
    Additional data added to the device key information by intermediate servers, and not covered by the signatures.
    """


class CrossSigningKey(CustomBaseModel):
    keys: dict[str, str]
    """
    The public key. The object must have exactly one property, whose name is in the form
    <algorithm>:<unpadded_base64_public_key>, and whose value is the unpadded base64 public key.
    """
    signatures: dict[str, dict[str, str]]
    """
    Signatures of the key, calculated using the process described at Signing JSON.
    Optional for the master key. Other keys must be signed by the user's master key.
    """
    usage: str
    """What the key is used for."""
    user_id: str
    """The ID of the user the key belongs to."""


class KeyQueryResponse(CustomBaseModel):
    device_keys: dict[str, DeviceInformation] = None
    failures: dict[str, dict] = None
    master_keys: dict[str, Any] = None
    self_signing_keys: dict[str, Any] = None
    user_signing_keys: dict[str, Any] = None


class KeyUploadResponse(CustomBaseModel):
    one_time_key_counts: dict[str, int]
    """
    For each key algorithm, the number of unclaimed one-time keys of that type currently held on the server
    for this device. If an algorithm is not listed, the count for that algorithm is to be assumed zero.
    """
