import cocotb
import cocotb.clock as clock
import cocotb.handle as handle
import cocotb.triggers as triggers
import random
from cocotb_introduction import reset
import cocotb_introduction.validready as validready
import cocotb_introduction.messages as messages
import cocotb_introduction.queue as queue
import typing


class ABData(typing.NamedTuple):
    a: int
    b: int


class ABDataHandle:
    def __init__(self, a: handle.SimHandleBase, b: handle.SimHandleBase) -> None:
        super().__init__()
        self._a = a
        self._b = b

    @property
    def integer(self) -> ABData:
        return ABData(a=self._a.value.integer, b=self._b.value.integer)

    @property
    def value(self) -> typing.Self:
        return self

    @value.setter
    def value(self, value: ABData) -> None:
        self._a.value = value.a
        self._b.value = value.b


class Testbench:
    def __init__(self, top: handle.SimHandleBase) -> None:
        super().__init__()
        self.width: int = top.WIDTH.value
        self.mask = (1 << self.width) - 1
        wr_interface = validready.ValidReadyInterface(
            clk=top.clk,
            rst=top.rst,
            valid=top.ab_valid,
            ready=top.ab_ready,
            data=ABDataHandle(
                a=top.a_data,
                b=top.b_data)
        )
        rd_interface = validready.ValidReadyInterface(clk=top.clk,
            rst=top.rst,
            valid=top.r_valid,
            ready=top.r_ready,
            data=top.r_data)
        self.wr_driver = validready.ValidReadyWriteDriver(**wr_interface)
        self.rd_driver = validready.ValidReadyReadDriver(**rd_interface)

        wr_monitor = validready.ValidReadyMonitor(**wr_interface)
        rd_monitor = validready.ValidReadyMonitor(**rd_interface)
        wr_msgs = queue.Queue[messages.WriteMessage]()
        rd_msgs = queue.Queue[messages.WriteMessage]()

        async def monitor_wr() -> None:
            while True:
                await wr_monitor.event
                wr_msgs.push(wr_monitor.message)

        async def monitor_rd() -> None:
            while True:
                await rd_monitor.event
                rd_msgs.push(rd_monitor.message)

        async def check_data() -> None:
            log = cocotb.log.getChild("check_data")
            while True:
                while not wr_msgs.empty and not rd_msgs.empty:
                    wr_msg = wr_msgs.pop()
                    rd_msg = rd_msgs.pop()
                    ab_data = typing.cast(ABData, wr_msg.data)
                    exp = (ab_data.a + ab_data.b) & self.mask
                    act = rd_msg.data
                    log.info(f"Comparing expected {exp} against actual {act}...")
                    assert exp == act
                await triggers.First(wr_msgs.event, rd_msgs.event)


        cocotb.start_soon(clock.Clock(top.clk, 10, "ns").start())
        cocotb.start_soon(reset(top.clk, top.rst))
        cocotb.start_soon(monitor_wr())
        cocotb.start_soon(monitor_rd())
        cocotb.start_soon(check_data())


@cocotb.test()
async def test_basic(top: handle.SimHandleBase):
    """Simple test to quickly verify the fifo."""

    tb = Testbench(top)
    total = 16
    a_data = [random.randint(0, tb.mask) for _ in range(total)]
    b_data = [random.randint(0, tb.mask) for _ in range(total)]

    last_rd = None
    for a, b in zip(a_data, b_data):
        tb.wr_driver.write(ABData(a, b))
        last_rd = tb.rd_driver.read()

    await last_rd.processed_wait()
    await triggers.ReadOnly()


@cocotb.test()
async def test_backpressure(top: handle.SimHandleBase):
    """Fill up adder. Wait a while. And the continue."""

    tb = Testbench(top)
    total = 16
    a_data = [random.randint(0, tb.mask) for _ in range(total)]
    b_data = [random.randint(0, tb.mask) for _ in range(total)]

    for a, b in zip(a_data, b_data):
        tb.wr_driver.write(ABData(a, b))

    while top.ab_ready.value.binstr != '0':
        await triggers.Edge(top.ab_ready)

    await triggers.Timer(100, "ns")

    for _ in range(total):
        last_rd = tb.rd_driver.read()

    await last_rd.processed_wait()
    await triggers.ReadOnly()


@cocotb.test()
async def test_random(top: handle.SimHandleBase):
    """Write data into adder at random intervals,
    while read result from adder at random intervals.

    The rate at which data is written is faster than
    the rate which data is read."""

    tb = Testbench(top)
    total = 16
    a_data = [random.randint(0, tb.mask) for _ in range(total)]
    b_data = [random.randint(0, tb.mask) for _ in range(total)]

    async def random_wait(max_time: float):
        wait = random.randint(-50, max_time)
        if wait > 0:
            await triggers.Timer(wait, "ns")

    async def write_data():
        for a, b in zip(a_data, b_data):
            msg = tb.wr_driver.write(ABData(a, b))
            await random_wait(50)
            await msg.started_wait()

    async def read_data():
        for _ in range(total):
            msg = tb.rd_driver.read()
            await random_wait(70)
            await msg.started_wait()
        await msg.processed_wait()
        await triggers.ReadOnly()

    await triggers.Combine(
        cocotb.start_soon(write_data()),
        cocotb.start_soon(read_data()))