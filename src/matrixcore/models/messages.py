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
import typing

from pydantic import BaseModel


__all__ = (
    "Message",
    "FormattedMessage",
)


class Message(BaseModel):
    """Base class for all message types"""
    body: typing.Any
    """The plain-text message body"""
    msgtype: str
    """The message type"""


class FormattedMessage(Message):
    """A formatted text message"""
    msgtype: typing.Literal["m.text"] = "m.text"
    format: str = None
    formatted_body: str = None
