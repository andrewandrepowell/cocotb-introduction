"""
Contains the definitions for the different types of messages
that can be passed to drivers and received from monitors.

The drivers follow a message-passing, object-oriented approach.
The idea is that the driver is responsible for a single interface,
directly interacting with the simulation handles of the interface and
carrying out all the necessary operations to fulfill the interface's protocol.

Separate tasks send messages to the driver in order to indirectly access the interface.
The message itself acts like communication medium between the separate task and the driver,
where the driver can even send data back to the separate task or receive more data, depending on the interface.
The driver is also responsible for dealing with the possibility of receiving multiple messages.
In this sense, the driver acts like server, providing clients a safe, simpler access to a resource, the interface.

The monitors behave differently. Instead of sending it messages,
separate tasks can get a reference to the latest message directly associated with the monitor.
The monitor's event property must be awaited on first to know when the message has been updated.
"""
import cocotb.triggers as triggers
import typing


class ReadNoData(BaseException):
    """Indicates no data is available yet on the ReadMessage."""
    pass


class WriteMessage:
    """Represents a message that can be sent to a WriteDriver. Data is passed into the message.

    Please note that in the context of the message's documentation,
    client refers to the task that's communicating with the driver through the message,
    whereas the driver itself is regarded as a server."""

    def __init__(self, data: int) -> None:
        super().__init__()
        self._data = data
        self._started = False
        self._processed = False
        self._event = triggers.Event()

    @property
    def event(self) -> triggers.PythonTrigger:
        """Current task resumes when a change occurs on the message."""
        self._event.clear()
        return self._event.wait()

    @property
    def started(self) -> bool:
        """Indicates back to the client task the message is getting processed."""
        return self._started

    @property
    def processed(self) -> bool:
        """Indicates back to the client task the message has gotten processed."""
        return self._processed

    @property
    def data(self) -> int:
        """The data associated with the message."""
        return self._data

    async def started_wait(self) -> None:
        """Current task resumes when the message is getting processed."""
        while not self.started:
            await self.event

    async def processed_wait(self) -> None:
        """Current task resumes when the message has gotten processed."""
        while not self.processed:
            await self.event

    def _start(self) -> None:
        """The driver calls this method in order to indicate back to the client the message is getting processed."""
        assert not self._started
        self._event.set()
        self._started = True

    def _process(self) -> None:
        """The driver calls this method in order to indicate back to the client the message has gotten processed."""
        assert not self._processed
        self._event.set()
        self._processed = True


class ReadMessage:
    """Represents a message that can be sent to a ReadDriver. Contains the data read from the driver.

    Please note that in the context of the message's documentation,
    client refers to the task that's communicating with the driver through the message,
    whereas the driver itself is regarded as a server."""

    def __init__(self) -> None:
        super().__init__()
        self._data: typing.Optional[int] = None
        self._started = False
        self._processed = False
        self._event = triggers.Event()

    @property
    def event(self) -> triggers.PythonTrigger:
        """Current task resumes when a change occurs on the message."""
        self._event.clear()
        return self._event.wait()

    @property
    def started(self) -> bool:
        """Indicates back to the client task the message is getting processed."""
        return self._started

    @property
    def processed(self) -> bool:
        """Indicates back to the client task the message has gotten processed."""
        return self._processed

    @property
    def data(self) -> int:
        """The data associated with the message."""
        if self._data is None:
            raise ReadNoData()
        return self._data

    async def started_wait(self) -> None:
        """Current task resumes when the message is getting processed."""
        while not self.started:
            await self.event

    async def processed_wait(self) -> int:
        """Current task resumes when the message has gotten processed. The read data is returned."""
        while not self.processed:
            await self.event
        return self.data

    def _start(self) -> None:
        """The driver calls this method in order to indicate back to the client the message is getting processed."""
        assert not self._started
        self._event.set()
        self._started = True

    def _process(self, data: int) -> None:
        """The driver calls this method in order to indicate back to the client the message has gotten processed."""
        assert not self._processed
        self._event.set()
        self._processed = True
        self._data = data


class MonitorMessage:
    """Represents a message a monitor can make available."""

    def __init__(self, data: int) -> None:
        super().__init__()
        self._data = data

    @property
    def data(self) -> int:
        """The data associated with the message."""
        return self._data