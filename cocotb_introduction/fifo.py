import cocotb.triggers as triggers
import cocotb
import typing
from . import Queue
import cocotb.handle as handle


class FifoReadNoData(BaseException):
    pass


class FifoWriteMessage:
    """Represents a message that can be sent to the FifoWriteDriver."""

    def __init__(self, data: int) -> None:
        super().__init__()
        self._data = data
        self._started = False
        self._processed = False
        self._event = triggers.Event()

    @property
    def event(self) -> triggers.PythonTrigger:
        self._event.clear()
        return self._event.wait()

    @property
    def started(self) -> bool:
        return self._started

    @property
    def processed(self) -> bool:
        return self._processed

    @property
    def data(self) -> int:
        return self._data

    def start(self) -> None:
        assert not self._started
        self._event.set()
        self._started = True

    def process(self) -> None:
        assert not self._processed
        self._event.set()
        self._processed = True


class FifoReadMessage:
    """Represents a message that can be sent to the FifoReadDriver. Contains the data read from the fifo."""

    def __init__(self) -> None:
        super().__init__()
        self._data: typing.Optional[int] = None
        self._started = False
        self._processed = False
        self._event = triggers.Event()

    @property
    def event(self) -> triggers.PythonTrigger:
        return self._event.wait()

    @property
    def started(self) -> bool:
        return self._started

    @property
    def processed(self) -> bool:
        return self._processed

    @property
    def data(self) -> int:
        if self._data is None:
            raise FifoReadNoData()
        return self._data

    def start(self) -> None:
        assert not self._started
        self._event.set()
        self._started = True

    def process(self, data: int) -> None:
        assert not self._processed
        self._event.set()
        self._processed = True
        self._data = data

    async def processedwait(self) -> int:
        while not self.processed:
            self._event.clear()
            await self.event
        return self.data


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

        async def operation() -> None:
            counter = 0
            counter_end = DEPTH - ALMOST_FULL_DEPTH
            valid.value = 0

            await triggers.RisingEdge(clk)
            while True:
                if rst.value.binstr != "0":
                    valid.value = 0
                    counter = 0
                    await triggers.Edge(rst)
                    await triggers.RisingEdge(clk)
                elif almost_full.value.integer == 0 or counter != counter_end:
                    if self._messages.empty:
                        await triggers.First(triggers.Edge(rst), self._messages.event)
                        await triggers.RisingEdge(clk)
                    else:
                        if almost_full.value.integer == 1:
                            counter = 0
                        else:
                            counter += 1
                        valid.value = 1
                        message = self._messages.pop()
                        message.start()
                        data_in.value = message.data
                        await triggers.RisingEdge(clk)
                        message.process()
                        valid.value = 0
                else:
                    await triggers.First(triggers.Edge(rst), triggers.Edge(almost_full))

        cocotb.start_soon(operation())

    def write(self, data: int) -> FifoWriteMessage:
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

        async def operation() -> None:
            ack.value = 0
            await triggers.RisingEdge(clk)
            while True:
                if rst.value.binstr != "0":
                    ack.value = 0
                    await triggers.FallingEdge(rst)
                    await triggers.RisingEdge(clk)
                elif empty.value.integer == 0 and self._messages.empty:
                    await triggers.First(triggers.Edge(rst), self._messages.event)
                    await triggers.RisingEdge(clk)
                elif empty.value.integer == 0 and not self._messages.empty:
                    ack.value = 1
                    message = self._messages.pop()
                    message.start()
                    await triggers.RisingEdge(clk)
                    message.process(data_out.value.integer)
                    ack.value = 0
                else:
                    await triggers.First(triggers.Edge(rst), triggers.Edge(empty))

        cocotb.start_soon(operation())

    def read(self) -> FifoReadMessage:
        message = FifoReadMessage()
        self._messages.push(message)
        return message
