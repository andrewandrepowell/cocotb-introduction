"""
Contains the ValidDriver and the ValidMonitor implementations.
"""
import cocotb
from .queue import Queue
from .messages import WriteMessage, MonitorMessage
import cocotb.handle as handle
import cocotb.triggers as triggers
import typing


class ValidDriver:
    """Writes messages to the valid interface."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        data: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._message = Queue[WriteMessage]()

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

    def write(self, data: int) -> WriteMessage:
        msg = WriteMessage(data)
        self._message.push(msg)
        return msg


class ValidMonitor:
    """Observes a valid interface."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        valid: handle.SimHandleBase,
        data: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._msg: typing.Optional[MonitorMessage] = None
        self._evt = triggers.Event()

        async def observe_valid_data() -> None:
            while True:
                await triggers.RisingEdge(clk)
                if rst.value.binstr != "0":
                    self._msg = None
                else:
                    if valid.value.integer == 1:
                        self._msg = MonitorMessage(data.value.integer)
                        self._evt.set()
                    else:
                        await triggers.First(triggers.Edge(rst), triggers.Edge(valid))

        cocotb.start_soon(observe_valid_data())

    @property
    def event(self) -> triggers.PythonTrigger:
        """Current task resumes when a new message is available on the monitor."""
        self._evt.clear()
        return self._evt.wait()

    @property
    def message(self) -> MonitorMessage:
        """The current message available on the monitor. Must await on the event first before accessing this property."""
        assert self._msg is not None, "ValidMonitor.event must be awaited prior to retreiving a message."
        return self._msg

