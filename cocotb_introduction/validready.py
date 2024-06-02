"""
Contains the definitions for ValidReadyWriteDriver, ValidReadyReadDriver, and ValidReadyMonitor.

It should be noted the valid-ready interface is simply a watered down version of the AXI-Lite interface,
where there's only clk, rst, data, valid, and ready. The rst is assert-on-high.
"""
import cocotb.triggers as triggers
import cocotb
import typing
from .queue import Queue
from .messages import WriteMessage, ReadMessage, MonitorMessage
import cocotb.handle as handle


class ValidReadyInterface(typing.TypedDict):
    """Represents all the signals of a valid-ready interface."""
    clk: handle.SimHandleBase
    rst: handle.SimHandleBase
    valid: handle.SimHandleBase
    ready: handle.SimHandleBase
    data: handle.SimHandleBase


class ValidReadyWriteDriver:
    """Writes data to the valid-ready interface."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        ready: handle.SimHandleBase,
        data: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._messages = Queue[WriteMessage]()

        async def drive_valid_data() -> None:
            valid.value = 0
            msg = None
            while True:
                await triggers.RisingEdge(clk)
                if rst.value.binstr != "0":
                    assert msg is None, "Reset occurred during oustanding transaction."
                    valid.value = 0
                    await triggers.FallingEdge(rst)
                else:
                    if msg is not None and ready.value.integer == 1:
                        msg._process()
                        msg = None
                        valid.value = 0
                        pass
                    if msg is None and not self._messages.empty:
                        msg = self._messages.pop()
                        msg._start()
                        data.value = msg.data
                        valid.value = 1
                    if msg is None and self._messages.empty:
                        await triggers.First(triggers.Edge(rst), self._messages.event)
                    elif msg is not None and ready.value.integer == 0:
                        await triggers.First(triggers.Edge(rst), triggers.Edge(ready))

        cocotb.start_soon(drive_valid_data())

    def write(self, data: int) -> WriteMessage:
        """Submit a write message to the driver."""
        message = WriteMessage(data)
        self._messages.push(message)
        return message


class ValidReadyReadDriver:
    """Reads data from the valid-ready interface."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        ready: handle.SimHandleBase,
        data: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._messages = Queue[ReadMessage]()

        async def drive_ready() -> None:
            msg = None
            ready.value = 0
            while True:
                await triggers.RisingEdge(clk)
                if rst.value.binstr != "0":
                    assert msg is None, "Reset occurred on outstanding transaction."
                    ready.value = 0
                    await triggers.FallingEdge(rst)
                else:
                    if msg is not None and valid.value.integer == 1:
                        msg._process(data.value.integer)
                        msg = None
                        ready.value = 0
                    if msg is None and not self._messages.empty:
                        msg = self._messages.pop()
                        msg._start()
                        ready.value = 1
                    if msg is None and self._messages.empty:
                        await triggers.First(triggers.Edge(rst), self._messages.event)
                    elif msg is not None and valid.value.integer == 0:
                        await triggers.First(triggers.Edge(rst), triggers.Edge(valid))

        cocotb.start_soon(drive_ready())

    def read(self) -> ReadMessage:
        """Submit a read message to the driver."""
        message = ReadMessage()
        self._messages.push(message)
        return message


class ValidReadyMonitor:
    """Observes a valid-ready interface."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        ready: handle.SimHandleBase,
        data: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._msg: typing.Optional[MonitorMessage] = None
        self._evt = triggers.Event()

        async def observe_valid_ready_intf() -> None:
            while True:
                await triggers.RisingEdge(clk)
                if rst.value.binstr != "0":
                    pass
                else:
                    if valid.value.integer == 1 and ready.value.integer == 1:
                        self._msg = MonitorMessage(data.value.integer)
                        self._evt.set()
                    else:
                        await triggers.First(triggers.Edge(rst), triggers.Edge(valid), triggers.Edge(ready))

        cocotb.start_soon(observe_valid_ready_intf())

    @property
    def event(self) -> triggers.PythonTrigger:
        """Current task resumes when a new message is available on the monitor."""
        self._evt.clear()
        return self._evt.wait()

    @property
    def message(self) -> MonitorMessage:
        assert self._msg is not None, "ValidMonitor.event must be awaited prior to retreiving a message."
        return self._msg