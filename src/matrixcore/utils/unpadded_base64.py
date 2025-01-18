import base64


__all__ = ("ub64encode", "ub64decode")


def ub64encode(data: bytes, urlsafe: bool = False) -> str:
    """
    Encodes the given data as an unpadded base64 encoded string.

    :param data: The data to encode.
    :param urlsafe: Whether to encode with urlsafe base64 encoding.
    :return: The encoded data.
    """
    caller = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    result = caller(data)
    return result.rstrip(b'=').decode()


def ub64decode(data: str) -> bytes:
    """
    Decodes the given data as an unpadded base64 encoded string.

    :param data: The data to decode.
    :return: The decoded data.
    """
    data = data.encode("ascii")
    data += b"=" * (4 - (len(data) % 4))
    return base64.b64decode(data)
