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
import datetime
import json
from typing import Union, Any, Type

from httpx import Response


__all__ = [
    "MatrixCoreException",
    "MatrixHTTPException",
    "NotAuthorised",
    "NotAuthorized",
    "Forbidden",
    "NotFound",
    "RateLimited",
    "InternalServerError",
]

from pydantic import BaseModel


class MatrixCoreException(Exception):
    """Base exceptions from which all MatrixCore errors stem."""


class BadResponse(MatrixCoreException):
    """Raised when a response model cannot be validated into its associated pydantic model"""

    def __init__(self, body: Any, model: Type[BaseModel]):
        self.body = body
        self.model = model
        # NOTE: this should only be raised alongside a pydantic validation error.


class MatrixHTTPException(MatrixCoreException):
    """Exception related to HTTP response errors from MatrixCore."""

    def __init__(self, response: Response | None = None, *, errcode: str, error: str, **kwargs):
        self.errcode = errcode
        self.error = error
        self.extra = kwargs or {}
        self.response = response

    @staticmethod
    def from_response(response: Response) -> Union["MatrixHTTPException", "RateLimited"]:
        """
        Creates a MatrixHTTPError from the given HTTP response object.

        :param response: HTTP response object
        :return: MatrixHTTPError
        """
        try:
            err_details = response.json()
            if not isinstance(err_details, dict):
                raise TypeError("err_details must be a dictionary, got %r" % type(err_details))
            err_details.setdefault("errcode", "M_UNKNOWN")
            err_details.setdefault("error", "no error text available")
        except json.JSONDecodeError:
            err_details = {
                "errcode": "M_UNKNOWN",
                "error": response.text,
            }

        special = {
            401: NotAuthorised,
            403: Forbidden,
            404: NotFound,
            429: RateLimited,
            500: InternalServerError,
        }
        for code in range(500, 600):
            special[code] = InternalServerError

        cls = MatrixHTTPException
        if response.status_code in special:
            cls = special[response.status_code]
        return cls(response, **err_details)


class NotAuthorised(MatrixHTTPException):
    """Represents a HTTP 401 error"""


NotAuthorized = NotAuthorised


class Forbidden(MatrixHTTPException):
    """Represents a HTTP 403 error"""


class NotFound(MatrixHTTPException):
    """Represents a HTTP 404 error"""


class RateLimited(MatrixHTTPException):
    """Represents a HTTP 429 error"""

    def __init__(self, response: Response | None = None, *, errcode: str, error: str, retry_after_ms: int, **kwargs):
        super().__init__(response, errcode=errcode, error=error)
        self._now = datetime.datetime.now(datetime.timezone.utc)
        self.retry_after_ms = retry_after_ms

    @property
    def retry_after(self) -> float:
        """After how many seconds this request should be retried."""
        return self.retry_after_ms / 1000

    @property
    def retry_at(self) -> datetime:
        """Returns the timezone-aware datetime when this request should be retried"""
        return self._now + datetime.timedelta(seconds=self.retry_after_ms)


class InternalServerError(MatrixHTTPException):
    """Represents a HTTP 500 error"""
