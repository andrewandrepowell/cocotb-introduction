import cocotb
from . import Queue
import cocotb.handle as handle
import cocotb.triggers as triggers
import typing


class ValidDriverMessage:
    """Represents a message that can be sent to the ValidDriver. Data is passed into the message.

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


class ValidMonitorMessage:
    def __init__(self, data: int) -> None:
        super().__init__()
        self._data = data

    @property
    def data(self) -> int:
        return self._data


class ValidDriver:
    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        data: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._message = Queue[ValidDriverMessage]()

        async def drive_valid_data() -> None:
            msg = None
            valid.value = 0
            while True:
                await triggers.RisingEdge(clk)
                if rst.value.binstr != "0":
                    valid.value = 0
                    assert msg is None, "Reset occurred during an oustanding transaction."
                    await triggers.FallingEdge(rst)
                else:
                    if msg is not None:
                        assert msg is not None
                        msg._process()
                        msg = None
                        valid.value = 0
                    if msg is None and not self._message.empty:
                        msg = self._message.pop()
                        msg._start()
                        data.value = msg.data
                        valid.value = 1
                    if msg is None and self._message.empty:
                        await triggers.First(triggers.Edge(rst), self._message.event)

        cocotb.start_soon(drive_valid_data())

    def write(self, data: int) -> ValidDriverMessage:
        msg = ValidDriverMessage(data)
        self._message.push(msg)
        return msg


class ValidMonitor:
    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        data: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._msg: typing.Optional[ValidMonitorMessage] = None
        self._evt = triggers.Event()

        async def observe_valid_data() -> None:
            while True:
                await triggers.RisingEdge(clk)
                if rst.value.binstr != "0":
                    self._msg = None
                else:
                    if valid.value.integer == 1:
                        self._msg = ValidMonitorMessage(data.value.integer)
                        self._evt.set()
                    else:
                        await triggers.First(triggers.Edge(rst), triggers.Edge(valid))

        cocotb.start_soon(observe_valid_data())

    @property
    def event(self) -> triggers.PythonTrigger:
        self._evt.clear()
        return self._evt.wait()

    @property
    def message(self) -> ValidMonitorMessage:
        assert self._msg is not None, "ValidMonitor.event must be awaited prior to retreiving a message."
        return self._msg

