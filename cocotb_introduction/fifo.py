"""
Contains the FifoWriteDriver and the FifoReadDriver implementations.

The drivers follow a message-passing, object-oriented approach.
The idea is that the driver is responsible for a single interface,
directly interacting with the simulation handles of the interface and
carrying out all the necessary operations to fulfill the interface's protocol.

Separate tasks send messages to the driver in order to indirectly access the interface.
The message itself acts like communication medium between the separate task and the driver,
where the driver can even send data back to the separate task or receive more data, depending on the interface.
The driver is also responsible for dealing with the possibility of receiving multiple messages.
In this sense, the driver acts like server, providing clients a safe, simpler access to a resource, the interface.

For example, calling the read method on a FifoReadDriver sends a message to the FifoReadDriver, requesting data.
The FifoReadDriver will receive the message, issue

"""
import cocotb.triggers as triggers
import cocotb
import typing
from . import Queue
import cocotb.handle as handle


class FifoReadNoData(BaseException):
    """Indicates no data is available yet on the FifoReadMessage."""
    pass


class FifoWriteMessage:
    """Represents a message that can be sent to the FifoWriteDriver. Data is passed into the message.

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


class FifoReadMessage:
    """Represents a message that can be sent to the FifoReadDriver. Contains the data read from the fifo.

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
            raise FifoReadNoData()
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


class FifoWriteDriver:
    """Writes messages to the fifo."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        almost_full: handle.SimHandleBase,
        full: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        data_in: handle.SimHandleBase,
        DEPTH: int,
        ALMOST_FULL_DEPTH: int
    ) -> None:
        super().__init__()
        self._messages = Queue[FifoWriteMessage]()
        msg = None
        msg_evt = triggers.Event()
        cnt = 0
        cnt_end = DEPTH - ALMOST_FULL_DEPTH
        cnt_evt = triggers.Event()

        async def drive_cnt() -> None:
            nonlocal msg, cnt
            while True:
                await triggers.RisingEdge(clk)
                await triggers.NullTrigger() # Reschedules the task; need to make sure drive_data always occurs first
                if rst.value.binstr != "0":
                    cnt = 0
                    await triggers.FallingEdge(rst)
                else:
                    if almost_full.value.integer == 0:
                        cnt = 0
                        cnt_evt.set()
                        await triggers.RisingEdge(almost_full)
                    elif msg is not None and cnt != cnt_end:
                        cnt += 1
                        cnt_evt.set()

        async def drive_valid() -> None:
            nonlocal msg, cnt
            while True:
                valid.value = int((almost_full.value.binstr == "0" or cnt != cnt_end) and msg is not None)
                msg_evt.clear()
                cnt_evt.clear()
                await triggers.First(triggers.Edge(almost_full), msg_evt.wait(), cnt_evt.wait())

        async def drive_data() -> None:
            nonlocal msg, cnt
            while True:
                await triggers.RisingEdge(clk)
                if rst.value.binstr != "0":
                    assert msg is None, "Reset occurred during outstanding message"
                    await triggers.FallingEdge(rst)
                else:
                    if (almost_full.value.integer == 0 or cnt != cnt_end) and msg is not None:
                        msg._process()
                        msg = None
                        msg_evt.set()
                    if msg is None and not self._messages.empty:
                        msg = self._messages.pop()
                        data_in.value = msg.data
                        msg._start()
                        msg_evt.set()
                    if msg is not None and almost_full.value.integer == 1 and cnt == cnt_end:
                        cnt_evt.clear()
                        await triggers.First(triggers.Edge(rst), triggers.Edge(almost_full), cnt_evt.wait())
                    elif msg is None and self._messages.empty:
                        await triggers.First(triggers.Edge(rst), self._messages.event)

        cocotb.start_soon(drive_valid())
        cocotb.start_soon(drive_data())
        cocotb.start_soon(drive_cnt())

    def write(self, data: int) -> FifoWriteMessage:
        """Submit a write message to the driver."""
        message = FifoWriteMessage(data)
        self._messages.push(message)
        return message


class FifoReadDriver:
    """Reads messages from the fifo."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        empty: handle.SimHandleBase,
        ack: handle.SimHandleBase,
        data_out: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._messages = Queue[FifoReadMessage]()
        msg = None
        msg_evt = triggers.Event()

        async def drive_ack() -> None:
            nonlocal msg
            while True:
                ack.value = int(empty.value.binstr == "0" and msg is not None)
                msg_evt.clear()
                await triggers.First(triggers.Edge(empty), msg_evt.wait())

        async def drive_data() -> None:
                nonlocal msg
                while True:
                    await triggers.RisingEdge(clk)
                    if rst.value.binstr != "0":
                        assert msg is None, "Reset occurred during outstanding message"
                        await triggers.FallingEdge(rst)
                    else:
                        if empty.value.integer == 0 and msg is not None:
                            msg._process(data_out.value.integer)
                            msg = None
                            msg_evt.set()
                        if msg is None and not self._messages.empty:
                            msg = self._messages.pop()
                            msg._start()
                            msg_evt.set()
                        if msg is not None and empty.value.integer == 1:
                            await triggers.First(triggers.Edge(rst), triggers.Edge(empty))
                        elif msg is None and self._messages.empty:
                            await triggers.First(triggers.Edge(rst), self._messages.event)

        cocotb.start_soon(drive_ack())
        cocotb.start_soon(drive_data())

    def read(self) -> FifoReadMessage:
        """Submit a read message to the driver."""
        message = FifoReadMessage()
        self._messages.push(message)
        return message
