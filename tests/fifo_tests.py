"""
Contains all the tests to verify the fifo.
Functional coverage is set up with cocotb_coverage, but only reporting.
"""
import cocotb
import cocotb.clock as clock
import cocotb.handle as handle
import cocotb.triggers as triggers
import cocotb_introduction.fifo as fifo
import cocotb_introduction.messages as messages
from cocotb_introduction import reset
import cocotb_introduction.queue as queue
import cocotb_coverage.coverage as coverage
import typing
import random
import enum
import os
import pathlib


class CoverageStates(enum.Enum):
    """Extra coverage states to represent a group of values in a cover point."""

    MID_VALUE = enum.auto()
    """Represents every value apart from the lowest and highest."""


class Testbench:
    """Contains all the essentials of the fifo testbench,
    including setting up the cover groups for functional coverage reporting.
    """

    def __init__(self, top: handle.SimHandleBase) -> None:
        super().__init__()
        self.width: int = top.WIDTH.value
        self.mask = (1 << self.width) - 1
        self.fifo_wr = fifo.FifoWriteDriver(
            clk=top.clk,
            rst=top.rst,
            almost_full=top.almost_full,
            full=top.full,
            valid=top.valid,
            data_in=top.data_in,
            DEPTH=top.DEPTH.value,
            ALMOST_FULL_DEPTH=top.ALMOST_FULL_DEPTH.value)
        self.fifo_rd = fifo.FifoReadDriver(
            clk=top.clk,
            rst=top.rst,
            empty=top.empty,
            ack=top.ack,
            data_out=top.data_out)


        def coverage_rel_data(actual: int, bin: typing.Union[int, CoverageStates]) -> bool:
            """Defines the rel function used to perform the determination on whether or
            not the actual data is in the corresponding bin."""
            if isinstance(bin, CoverageStates):
                if bin == CoverageStates.MID_VALUE:
                    return actual > 0 and actual < self.mask
                else:
                    return False
            else:
                return actual == bin

        @coverage.coverage_section(
            coverage.CoverPoint(name="top.almost_full", xf=lambda almost_full, full, valid, data_in : almost_full, bins=[1, 0]),
            coverage.CoverPoint(name="top.full", xf=lambda almost_full, full, valid, data_in : full, bins=[1, 0]),
            coverage.CoverPoint(name="top.valid", xf=lambda almost_full, full, valid, data_in : valid, bins=[1, 0]),
            coverage.CoverPoint(name="top.data_in", xf=lambda almost_full, full, valid, data_in : data_in, bins=[0, CoverageStates.MID_VALUE, self.mask],
                                rel=coverage_rel_data),
            coverage.CoverCross(name="top.wr.cross_data", items=["top.valid", "top.data_in"], ign_bins=[(1, None)]),
            coverage.CoverCross(name="top.wr.cross_status", items=["top.almost_full", "top.full", "top.valid"], ign_bins=[(None, 1, 1), (0, 1, None)]))
        def sample_write(
            almost_full: int,
            full: int,
            valid: int,
            data_in: int
        ) -> None:
            """Defines the cover group for the fifo write interface."""
            pass

        @coverage.coverage_section(
            coverage.CoverPoint(name="top.empty", xf=lambda empty, ack, data_out : empty, bins=[1, 0]),
            coverage.CoverPoint(name="top.ack", xf=lambda empty, ack, data_out : ack, bins=[1, 0]),
            coverage.CoverPoint(name="top.data_out", xf=lambda empty, ack, data_out : data_out, bins=[0, CoverageStates.MID_VALUE, self.mask],
                                rel=coverage_rel_data),
            coverage.CoverCross(name="top.rd.cross_data", items=["top.ack", "top.data_out"], ign_bins=[(1, None)]),
            coverage.CoverCross(name="top.rd.cross_status", items=["top.empty", "top.ack"], ign_bins=[(1, 1)]))
        def sample_read(
            empty: int,
            ack: int,
            data_out: int
        ) -> None:
            """Defines the cover group for the fifo read interface."""
            pass

        async def cover_wr() -> None:
            """This coroutine is the sampler for the sample_write cover group."""
            while True:
                await triggers.RisingEdge(top.clk)
                if top.rst.value.binstr != "0":
                    await triggers.FallingEdge(top.rst)
                else:
                    # If data_in is unassigned, use 0 instead.
                    try:
                        data_in = top.data_in.value.integer
                    except ValueError:
                        data_in = 0
                    almost_full = top.almost_full.value.integer
                    full = top.full.value.integer
                    valid = top.valid.value.integer
                    assert not (almost_full == 0 and full == 1), "impossible state"
                    assert not (full == 1 and valid == 1), "impossible state"
                    sample_write(almost_full, full, valid, data_in)
                    await triggers.First(triggers.Edge(top.almost_full), triggers.Edge(top.full), triggers.Edge(top.valid), triggers.Edge(top.data_in))

        async def cover_rd() -> None:
            """This coroutine is the sampler for the sample_read cover group."""
            while True:
                await triggers.RisingEdge(top.clk)
                if top.rst.value.binstr != "0":
                    await triggers.FallingEdge(top.rst)
                else:
                    try:
                        data_out = top.data_out.value.integer
                    except ValueError:
                        data_out = 0
                    empty = top.empty.value.integer
                    ack = top.ack.value.integer
                    assert not (empty == 1 and ack == 1), "impossible state"
                    sample_read(empty, ack, data_out)
                    await triggers.First(triggers.Edge(top.empty), triggers.Edge(top.ack), triggers.Edge(top.data_out))


        cocotb.start_soon(reset(top.clk, top.rst))
        cocotb.start_soon(clock.Clock(top.clk, 10, "ns").start())
        cocotb.start_soon(cover_wr())
        cocotb.start_soon(cover_rd())


@cocotb.test()
async def test_basic(top: handle.SimHandleBase):
    """Simple test to quickly verify the fifo."""

    tb = Testbench(top)
    data = [value & tb.mask for value in range(64)]

    rd_msgs: typing.List[messages.ReadMessage] = []
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

    tb = Testbench(top)
    data = [value & tb.mask for value in range(64)]

    for value in data:
        tb.fifo_wr.write(value)

    while top.full.value.binstr != '1':
        await triggers.Edge(top.full)

    await triggers.Timer(100, "ns")

    rd_msgs: typing.List[messages.ReadMessage] = []
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

    tb = Testbench(top)
    rd_queue = queue.Queue[messages.ReadMessage]()
    data = [value & tb.mask for value in range(512)]

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


@cocotb.test()
async def report_coverage(top: handle.SimHandleBase) -> None:
    """Reports the coverage."""
    coverage_path = pathlib.Path(os.environ["WORK_DIR"]) / "coverage.yaml"
    coverage.coverage_db.report_coverage(cocotb.log.info, bins=True)
    coverage.coverage_db.export_to_yaml(coverage_path.as_posix())

