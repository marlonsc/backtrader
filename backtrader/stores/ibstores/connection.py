"""Event-driven socket connection."""

import asyncio

from eventkit import Event
from ib_insync.util import getLoop


class Connection(asyncio.Protocol):
    """Event-driven socket connection.
Events:
* ``hasData`` (data: bytes):
Emits the received socket data.
* ``disconnected`` (msg: str):
Is emitted on socket disconnect, with an error message in case
of error, or an empty string in case of a normal disconnect."""

    def __init__(self):
""""""
""""""
        """

        :param host:
        :param port:

        """
        if self.transport:
            # wait until a previous connection is finished closing
            self.disconnect()
            await self.disconnected
        self.reset()
        loop = getLoop()
        self.transport, _ = await loop.create_connection(lambda: self, host, port)

    def disconnect(self):
""""""
""""""
"""Args::
    msg:"""
"""Args::
    exc:"""
"""Args::
    data:"""
    data:"""
        self.hasData.emit(data)
