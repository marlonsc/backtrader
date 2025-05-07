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
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Pattern,
    Tuple,
    Type,
    TypeVar,
    Union,
)

# This sort of sucks, but seems to be as good as it gets...
# This is essentially the same as re._pattern_type
RE_TYPE: Type[Pattern[Any]] = type(re.compile(""))

_Key = TypeVar("_Key")
_Value = TypeVar("_Value")
_T = TypeVar("_T")


class SON(Dict[_Key, _Value]):
    """SON data.
A subclass of dict that maintains ordering of keys and provides a
few extra niceties for dealing with SON. SON provides an API
similar to collections.OrderedDict."""

    __keys: List[Any]

"""__init__ function.

Args:
    data: Description of data

"""
        self,
        data: Optional[
            Union[Mapping[_Key, _Value], Iterable[Tuple[_Key, _Value]]]
        ] = None,
        **kwargs: Any,
    ) -> None:
        self.__keys = []
        dict.__init__(self)
        self.update(data)
        self.update(kwargs)

"""__new__ function.

Args:
    cls: Description of cls

Returns:
    Description of return value
"""
        cls: Type["SON[_Key, _Value]"], *args: Any, **kwargs: Any
    ) -> "SON[_Key, _Value]":
        instance = super(SON, cls).__new__(cls, *args, **kwargs)
        instance.__keys = []
        return instance

"""__repr__ function.

Returns:
    Description of return value
"""
        result = []
        for key in self.__keys:
            result.append("(%r, %r)" % (key, self[key]))
        return "SON([%s])" % ", ".join(result)

"""__setitem__ function.

Args:
    key: Description of key
    value: Description of value

"""
        if key not in self.__keys:
            self.__keys.append(key)
        dict.__setitem__(self, key, value)

"""__delitem__ function.

Args:
    key: Description of key

"""
        self.__keys.remove(key)
        dict.__delitem__(self, key)

"""copy function.

Returns:
    Description of return value
"""
        other: SON[_Key, _Value] = SON()
        other.update(self)
        return other

    # TODO this is all from UserDict.DictMixin. it could probably be made more
    # efficient.
    # second level definitions support higher levels
"""__iter__ function.

Returns:
    Description of return value
"""
        for k in self.__keys:
            yield k

"""has_key function.

Args:
    key: Description of key

Returns:
    Description of return value
"""
        return key in self.__keys

"""iterkeys function.

Returns:
    Description of return value
"""
        return self.__iter__()

    # fourth level uses definitions from lower levels
"""itervalues function.

Returns:
    Description of return value
"""
        for _, v in self.items():
            yield v

"""values function.

Returns:
    Description of return value
"""
        return [v for _, v in self.items()]

"""clear function.

"""
        self.__keys = []
        super(SON, self).clear()

    # type: ignore[override]
"""setdefault function.

Args:
    key: Description of key
    default: Description of default

Returns:
    Description of return value
"""
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default

"""pop function.

Args:
    key: Description of key

Returns:
    Description of return value
"""
        if len(args) > 1:
            raise TypeError(
                "pop expected at most 2 arguments, got " + repr(1 + len(args))
            )
        try:
            value = self[key]
        except KeyError:
            if args:
                return args[0]
            raise
        del self[key]
        return value

"""popitem function.

Returns:
    Description of return value
"""
        try:
            k, v = next(iter(self.items()))
        except StopIteration:
            raise KeyError("container is empty")
        del self[k]
        return (k, v)

    # type: ignore[override]
"""update function.

Args:
    other: Description of other

"""
        # Make progressively weaker assumptions about "other"
        if other is None:
            pass
        elif hasattr(other, "items"):
            for k, v in other.items():
                self[k] = v
        elif hasattr(other, "keys"):
            for k in other.keys():
                self[k] = other[k]
        else:
            for k, v in other:
                self[k] = v
        if kwargs:
            self.update(kwargs)

    # type: ignore[override]
"""get function.

Args:
    key: Description of key
    default: Description of default

Returns:
    Description of return value
"""
        self, key: _Key, default: Optional[Union[_Value, _T]] = None
    ) -> Union[_Value, _T, None]:
        try:
            return self[key]
        except KeyError:
            return default

    def __eq__(self, other: Any) -> bool:
"""Comparison to another SON is order-sensitive while comparison to a
        regular dictionary is order-insensitive."""
        """
        if isinstance(other, SON):
            return len(self) == len(other) and list(self.items()) == list(other.items())
        return self.to_dict() == other

"""__ne__ function.

Args:
    other: Description of other

Returns:
    Description of return value
"""
        return not self == other

"""__len__ function.

Returns:
    Description of return value
"""
        return len(self.__keys)

    def to_dict(self) -> Dict[_Key, _Value]:
        """Convert a SON document to a normal Python dictionary instance.
This is trickier than just *dict(...)* because it needs to be
recursive."""

"""transform_value function.

Args:
    value: Description of value

Returns:
    Description of return value
"""
            if isinstance(value, list):
                return [transform_value(v) for v in value]
            elif isinstance(value, _Mapping):
                return dict([(k, transform_value(v)) for k, v in value.items()])
            else:
                return value

        return transform_value(dict(self))

"""__deepcopy__ function.

Args:
    memo: Description of memo

Returns:
    Description of return value
"""
        out: SON[_Key, _Value] = SON()
        val_id = id(self)
        if val_id in memo:
            return memo[val_id]
        memo[val_id] = out
        for k, v in self.items():
            if not isinstance(v, RE_TYPE):
                v = copy.deepcopy(v, memo)
            out[k] = v
        return out
