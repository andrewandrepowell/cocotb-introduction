import cocotb
import cocotb.clock as clock
import cocotb.handle as handle
import cocotb.triggers as triggers
import cocotb_introduction.fifo as fifo
from cocotb_introduction import reset, Queue
import typing
import random
import dataclasses


@dataclasses.dataclass(frozen=True)
class Testbench:
    """Contains all the essentials of the fifo testbench."""
    width: int
    mask: int
    fifo_wr: fifo.FifoWriteDriver
    fifo_rd: fifo.FifoReadDriver


def prepare_testbench(top: handle.SimHandleBase) -> Testbench:
    """Quickly spin up a testbench to verify the fifo."""

    width = top.WIDTH.value
    mask = (1 << width) - 1

    fifo_wr = fifo.FifoWriteDriver(
        clk=top.clk,
        rst=top.rst,
        almost_full=top.almost_full,
        full=top.full,
        valid=top.valid,
        data_in=top.data_in,
        DEPTH=top.DEPTH.value,
        ALMOST_FULL_DEPTH=top.ALMOST_FULL_DEPTH.value)
    fifo_rd = fifo.FifoReadDriver(
        clk=top.clk,
        rst=top.rst,
        empty=top.empty,
        ack=top.ack,
        data_out=top.data_out)

    cocotb.start_soon(reset(top.clk, top.rst))
    cocotb.start_soon(clock.Clock(top.clk, 10, "ns").start())

    return Testbench(width=width, mask=mask, fifo_wr=fifo_wr, fifo_rd=fifo_rd)


@cocotb.test()
async def test_basic(top: handle.SimHandleBase):
    """Simple test to quickly verify the fifo."""

    tb = prepare_testbench(top)
    data = [value & tb.mask for value in range(64)]

    rd_msgs: typing.List[fifo.FifoReadMessage] = []
    for value in data:
        tb.fifo_wr.write(value)
        rd_msgs.append(tb.fifo_rd.read())

    for exp, msg in zip(data, rd_msgs):
        act = await msg.processed_wait()
        cocotb.log.info(f"Comparing expected {exp} against actual {act}...")
        assert exp == act


@cocotb.test()
async def test_backpressure(top: handle.SimHandleBase):
    """Fill up fifo. Wait a while. And then empty it, while reading data."""

    tb = prepare_testbench(top)
    data = [value & tb.mask for value in range(64)]

    for value in data:
        tb.fifo_wr.write(value)

    while top.full.value.binstr != '1':
        await triggers.Edge(top.full)

    await triggers.Timer(100, "ns")

    rd_msgs: typing.List[fifo.FifoReadMessage] = []
    for _ in data:
        rd_msgs.append(tb.fifo_rd.read())

    for exp, rd_msg in zip(data, rd_msgs):
        act = await rd_msg.processed_wait()
        cocotb.log.info(f"Comparing expected {exp} against actual {act}...")
        assert exp == act


@cocotb.test()
async def test_random(top: handle.SimHandleBase):
    """Write data into fifo at random intervals,
    while read data from fifo at random intervals.

    The rate at which data is written to faster than
    the rate which data is read."""

    tb = prepare_testbench(top)
    rd_queue = Queue[fifo.FifoReadMessage]()
    data = [value & tb.mask for value in range(256)]

    async def random_wait(max_time: float):
        wait = random.randint(-50, max_time)
        if wait > 0:
            await triggers.Timer(wait, "ns")

    async def write_data():
        for value in data:
            msg = tb.fifo_wr.write(value)
            await random_wait(50)
            await msg.started_wait()

    async def read_data():
        for _ in data:
            msg = tb.fifo_rd.read()
            rd_queue.push(msg)
            await random_wait(70)
            await msg.started_wait()

    async def check_data():
        for exp in data:
            msg = await rd_queue.pop_wait()
            act = await msg.processed_wait()
            cocotb.log.info(f"Comparing expected {exp} against actual {act}...")
            assert exp == act

    await triggers.Combine(
        cocotb.start_soon(write_data()),
        cocotb.start_soon(read_data()),
        cocotb.start_soon(check_data()))



