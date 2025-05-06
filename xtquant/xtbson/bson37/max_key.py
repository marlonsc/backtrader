# Copyright 2010-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Representation for the MongoDB internal MaxKey type."""

from typing import Any


class MaxKey(object):
    """MongoDB internal MaxKey type."""

    __slots__ = ()

    _type_marker = 127

    def __getstate__(self) -> Any:
""":rtype: Any"""
        """
        return {}

    def __setstate__(self, state: Any) -> None:
"""Args::
    state:"""
"""Args::
    other:"""
""":rtype: int"""
        """
        return hash(self._type_marker)

    def __ne__(self, other: Any) -> bool:
"""Args::
    other:"""
"""Args::
    other:"""
"""Args::
    dummy:"""
"""Args::
    dummy:"""
"""Args::
    other:"""
""""""
        return "MaxKey()"
