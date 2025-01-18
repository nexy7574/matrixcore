import json
try:
    import orjson
except ImportError:
    orjson = None

import typing


__all__ = (
    "INT_MAX",
    "INT_MIN",
    "ENCODING",
    "SEPARATORS",
    "canonical_json_encode"
)
INT_MAX = (2**53) - 1
INT_MIN = -(2**53) - 1
ENCODING = "utf-8"
SEPARATORS = (',', ':')


def _validate(data: typing.Any) -> typing.Any:
    if isinstance(data, int):
        if data < INT_MIN or data > INT_MAX:
            raise ValueError("Cannot serialize {!r} - must be in the range of {!s]-{!s}".format(data, INT_MIN, INT_MAX))
        return data
    elif isinstance(data, float):
        raise TypeError("Cannot serialize floats into canonical JSON.")
    elif isinstance(data, dict):
        for key, value in data.copy().items():
            data[key] = _validate(value)
    elif isinstance(data, (list, tuple, set, frozenset)):
        return list(map(_validate, data))
    return data


def canonical_json_encode(data: typing.Any) -> bytes:
    """
    Performs canonical JSON encoding.
    """
    if orjson is not None:
        return orjson.dumps(
            data,
            None,
            orjson.OPT_SORT_KEYS | orjson.OPT_STRICT_INTEGER
        )
    data = _validate(data)
    return json.dumps(data, separators=SEPARATORS, ensure_ascii=False, sort_keys=True).encode()


# FFR: Sign JSON with olm.Account.sign_json
