# Copyright 2009-present MongoDB, Inc.
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
"""Tools for creating and manipulating SON, the Serialized Ocument Notation.
Regular dictionaries can be used instead of SON objects, but not when the order
of keys is important. A SON object can be used just like a normal Python
dictionary."""

import copy
import re
from collections.abc import Mapping as _Mapping

# This sort of sucks, but seems to be as good as it gets...
# This is essentially the same as re._pattern_type
RE_TYPE = type(re.compile(""))


class SON(dict):
    """SON data.
A subclass of dict that maintains ordering of keys and provides a
few extra niceties for dealing with SON. SON provides an API
similar to collections.OrderedDict."""

    def __init__(self, data=None, **kwargs):
"""Args::
    data: (Default value = None)"""
        """"""
        instance = super(SON, cls).__new__(cls, *args, **kwargs)
        instance.__keys = []
        return instance

    def __repr__(self):
""""""
"""Args::
    key: 
    value:"""
    value:"""
        if key not in self.__keys:
            self.__keys.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
"""Args::
    key:"""
""""""
""""""
"""Args::
    key:"""
""""""
""""""
""""""
""""""
"""Args::
    key: 
    default: (Default value = None)"""
    default: (Default value = None)"""
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default

    def pop(self, key, *args):
"""Args::
    key:"""
""""""
"""Args::
    other: (Default value = None)"""
"""Args::
    key: 
    default: (Default value = None)"""
    default: (Default value = None)"""
        try:
            return self[key]
        except KeyError:
            return default

    def __eq__(self, other):
"""Comparison to another SON is order-sensitive while comparison to a
regular dictionary is order-insensitive.

Args::
    other:"""
    other:"""
        if isinstance(other, SON):
            return len(self) == len(other) and list(self.items()) == list(other.items())
        return self.to_dict() == other

    def __ne__(self, other):
"""Args::
    other:"""
""""""
        """Convert a SON document to a normal Python dictionary instance.
This is trickier than just *dict(...)* because it needs to be
recursive."""

        def transform_value(value):
"""Args::
    value:"""
"""Args::
    memo:"""
    memo:"""
        out = SON()
        val_id = id(self)
        if val_id in memo:
            return memo.get(val_id)
        memo[val_id] = out
        for k, v in self.items():
            if not isinstance(v, RE_TYPE):
                v = copy.deepcopy(v, memo)
            out[k] = v
        return out
