# Copyright 2015-present MongoDB, Inc.
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
"""Tools for representing raw BSON documents.

Inserting and Retrieving RawBSONDocuments
=========================================

Example: Moving a document between different databases/collections

.. doctest::

  >>> import bson
  >>> from pymongo import MongoClient
  >>> from .raw_bson import RawBSONDocument
  >>> client = MongoClient(document_class=RawBSONDocument)
  >>> client.drop_database('db')
  >>> client.drop_database('replica_db')
  >>> db = client.db
  >>> result = db.test.insert_many([{'_id': 1, 'a': 1},
  ...                               {'_id': 2, 'b': 1},
  ...                               {'_id': 3, 'c': 1},
  ...                               {'_id': 4, 'd': 1}])
  >>> replica_db = client.replica_db
  >>> for doc in db.test.find():
  ...    print(f"raw document: {doc.raw}")
  ...    print(f"decoded document: {bson.decode(doc.raw)}")
  ...    result = replica_db.test.insert_one(doc)
  raw document: b'...'
  decoded document: {'_id': 1, 'a': 1}
  raw document: b'...'
  decoded document: {'_id': 2, 'b': 1}
  raw document: b'...'
  decoded document: {'_id': 3, 'c': 1}
  raw document: b'...'
  decoded document: {'_id': 4, 'd': 1}

For use cases like moving documents across different databases or writing binary
blobs to disk, using raw BSON documents provides better speed and avoids the
overhead of decoding or encoding BSON.
"""

from collections.abc import Mapping as _Mapping

from . import _get_object_size, _raw_to_dict
from .codec_options import _RAW_BSON_DOCUMENT_MARKER
from .codec_options import DEFAULT_CODEC_OPTIONS as DEFAULT
from .son import SON


class RawBSONDocument(_Mapping):
    """Representation for a MongoDB document that provides access to the raw
    BSON bytes that compose it.

    Only when a field is accessed or modified within the document does
    RawBSONDocument decode its bytes.


    """

    __slots__ = ("__raw", "__inflated_doc", "__codec_options")
    _type_marker = _RAW_BSON_DOCUMENT_MARKER

    def __init__(self, bson_bytes, codec_options=None):
        """Create a new :class:`RawBSONDocument`

        :class:`RawBSONDocument` is a representation of a BSON document that
        provides access to the underlying raw BSON bytes. Only when a field is
        accessed or modified within the document does RawBSONDocument decode
        its bytes.

        :class:`RawBSONDocument` implements the ``Mapping`` abstract base
        class from the standard library so it can be used like a read-only
        ``dict``::


        :Parameters:
          - `bson_bytes`: the BSON bytes that compose this document
          - `codec_options` (optional): An instance of
            :class:`~bson.codec_options.CodecOptions` whose ``document_class``
            must be :class:`RawBSONDocument`. The default is
            :attr:`DEFAULT_RAW_BSON_OPTIONS`.

        .. versionchanged:: 3.8
          :class:`RawBSONDocument` now validates that the ``bson_bytes``
          passed in represent a single bson document.

        .. versionchanged:: 3.5
          If a :class:`~bson.codec_options.CodecOptions` is passed in, its
          `document_class` must be :class:`RawBSONDocument`.

        :param bson_bytes:
        :param codec_options:  (Default value = None)

        >>> from . import encode
            >>> raw_doc = RawBSONDocument(encode({'_id': 'my_doc'}))
            >>> raw_doc.raw
            b'...'
            >>> raw_doc['_id']
            'my_doc'
        """
        self.__raw = bson_bytes
        self.__inflated_doc = None
        # Can't default codec_options to DEFAULT_RAW_BSON_OPTIONS in signature,
        # it refers to this class RawBSONDocument.
        if codec_options is None:
            codec_options = DEFAULT_RAW_BSON_OPTIONS
        elif codec_options.document_class is not RawBSONDocument:
            raise TypeError(
                "RawBSONDocument cannot use CodecOptions with document class %s"
                % (codec_options.document_class,)
            )
        self.__codec_options = codec_options
        # Validate the bson object size.
        _get_object_size(bson_bytes, 0, len(bson_bytes))

    @property
    def raw(self):
        """The raw BSON bytes composing this document."""
        return self.__raw

    def items(self):
        """Lazily decode and iterate elements in this document."""
        return self.__inflated.items()

    @property
    def __inflated(self):
        """ """
        if self.__inflated_doc is None:
            # We already validated the object's size when this document was
            # created, so no need to do that again.
            # Use SON to preserve ordering of elements.
            self.__inflated_doc = _inflate_bson(self.__raw, self.__codec_options)
        return self.__inflated_doc

    def __getitem__(self, item):
        """

        :param item:

        """
        return self.__inflated[item]

    def __iter__(self):
        """ """
        return iter(self.__inflated)

    def __len__(self):
        """ """
        return len(self.__inflated)

    def __eq__(self, other):
        """

        :param other:

        """
        if isinstance(other, RawBSONDocument):
            return self.__raw == other.raw
        return NotImplemented

    def __repr__(self):
        """ """
        return "RawBSONDocument(%r, codec_options=%r)" % (
            self.raw,
            self.__codec_options,
        )


def _inflate_bson(bson_bytes, codec_options):
    """Inflates the top level fields of a BSON document.

    :Parameters:
      - `bson_bytes`: the BSON bytes that compose this document
      - `codec_options`: An instance of
        :class:`~bson.codec_options.CodecOptions` whose ``document_class``
        must be :class:`RawBSONDocument`.

    :param bson_bytes:
    :param codec_options:

    """
    # Use SON to preserve ordering of elements.
    return _raw_to_dict(bson_bytes, 4, len(bson_bytes) - 1, codec_options, SON())


DEFAULT_RAW_BSON_OPTIONS = DEFAULT.with_options(document_class=RawBSONDocument)
"""The default :class:`~bson.codec_options.CodecOptions` for
:class:`RawBSONDocument`.
"""
