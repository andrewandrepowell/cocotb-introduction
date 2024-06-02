"""
Contains the FifoWriteDriver and the FifoReadDriver implementations.
"""
import cocotb.triggers as triggers
import cocotb
from .messages import WriteMessage, ReadMessage
from .queue import Queue
import cocotb.handle as handle


class FifoWriteDriver:
    """Writes data to the fifo."""

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
        self._messages = Queue[WriteMessage]()
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

    def write(self, data: int) -> WriteMessage:
        """Submit a write message to the driver."""
        message = WriteMessage(data)
        self._messages.push(message)
        return message


class FifoReadDriver:
    """Reads data from the fifo."""

    def __init__(
        self,
        clk: handle.SimHandleBase,
        rst: handle.SimHandleBase,
        empty: handle.SimHandleBase,
        ack: handle.SimHandleBase,
        data_out: handle.SimHandleBase
    ) -> None:
        super().__init__()
        self._messages = Queue[ReadMessage]()
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

    def read(self) -> ReadMessage:
        """Submit a read message to the driver."""
        message = ReadMessage()
        self._messages.push(message)
        return message
