"""
Contains all the tests to verify the fifo.
Functional coverage is set up with cocotb_coverage, but only reporting.
More information on cocotb_coverage can be found in their official documentation.
"""
import cocotb
import cocotb.clock as clock
import cocotb.handle as handle
import cocotb.triggers as triggers
import cocotb_introduction
import cocotb_introduction.fifo as fifo
import cocotb_introduction.valid as valid
import cocotb_introduction.messages as messages
import cocotb_introduction.queue as queue
import cocotb_introduction.runner as runner
import cocotb_coverage.coverage as coverage
import typing
import random
import os
import pathlib
import itertools


class DUT_Testbench:
    """Contains all the essentials of the fifo testbench,
    including setting up the cover groups for functional coverage reporting.
    """

    def __init__(self, top: handle.SimHandleBase) -> None:
        super().__init__()

        #############################
        ## RECORD USEFUL PROPERTIES #
        #############################

        self.width: int = top.WIDTH.value
        self.mask = (1 << self.width) - 1

        #########################################
        ## CREATE THE DRIVERS USED BY THE TESTS #
        #########################################

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

        ###################################
        ## VERIFY DATA-RELATED OPERATIONS #
        ###################################

        wr_mon = valid.ValidMonitor(
            clk=top.clk,
            rst=top.rst,
            valid=top.valid,
            data=top.data_in)
        rd_mon = valid.ValidMonitor(
            clk=top.clk,
            rst=top.rst,
            valid=top.ack,
            data=top.data_out)
        wr_msgs = queue.Queue[messages.MonitorMessage]()
        rd_msgs = queue.Queue[messages.MonitorMessage]()

        async def observe(m: valid.ValidMonitor, q: queue.Queue[messages.MonitorMessage]) -> None:
            while True:
                await m.event
                q.push(m.message)


        async def check_data() -> None:
            log = cocotb.log.getChild("check_data")
            while True:
                exp = (await wr_msgs.pop_wait()).data
                act = (await rd_msgs.pop_wait()).data
                log.info(f"Comparing expected {exp} against actual {act}...")
                assert exp == act

        cocotb.start_soon(observe(wr_mon, wr_msgs))
        cocotb.start_soon(observe(rd_mon, rd_msgs))
        cocotb.start_soon(check_data())

        ################################
        ## COVERAGE RELATED OPERATIONS #
        ################################

        def coverage_rel_data(actual: int, bin: typing.Union[int, range]) -> bool:
            """Defines the rel function used to perform the determination on whether or
            not the actual data is in the corresponding bin."""
            if isinstance(bin, range):
                return actual in bin
            else:
                return actual == bin

        @coverage.coverage_section(
            coverage.CoverPoint(name="top.almost_full", xf=lambda almost_full, full, valid, data_in : almost_full, bins=[1, 0]),
            coverage.CoverPoint(name="top.full", xf=lambda almost_full, full, valid, data_in : full, bins=[1, 0]),
            coverage.CoverPoint(name="top.valid", xf=lambda almost_full, full, valid, data_in : valid, bins=[1, 0]),
            coverage.CoverPoint(name="top.data_in", xf=lambda almost_full, full, valid, data_in : data_in, bins=[0, range(1, self.mask), self.mask],
                                rel=coverage_rel_data),
            coverage.CoverCross(name="top.wr.cross_data", items=["top.valid", "top.data_in"], ign_bins=[(0, None)]),
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
            coverage.CoverPoint(name="top.data_out", xf=lambda empty, ack, data_out : data_out, bins=[0, range(1, self.mask), self.mask],
                                rel=coverage_rel_data),
            coverage.CoverCross(name="top.rd.cross_data", items=["top.ack", "top.data_out"], ign_bins=[(0, None)]),
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

        cocotb.start_soon(cover_wr())
        cocotb.start_soon(cover_rd())

        ####################
        ## CLOCK AND RESET #
        ####################

        cocotb.start_soon(cocotb_introduction.reset(top.clk, top.rst))
        cocotb.start_soon(clock.Clock(top.clk, 10, "ns").start())


@cocotb.test()
async def basic_test(top: handle.SimHandleBase):
    """Simple test to quickly verify the fifo."""

    tb = DUT_Testbench(top)
    total = 128
    data = [value & tb.mask for value in range(total)]

    for value in data:
        tb.fifo_wr.write(value)
        last_msg = tb.fifo_rd.read()

    await last_msg.processed_wait()
    await triggers.Timer(50, "ns")


@cocotb.test()
async def backpressure_test(top: handle.SimHandleBase):
    """Fill up fifo. Wait a while. And then empty it, while reading data."""

    tb = DUT_Testbench(top)
    total = 128
    data = [value & tb.mask for value in range(total)]

    for value in data:
        tb.fifo_wr.write(value)

    while top.full.value.binstr != '1':
        await triggers.Edge(top.full)

    await triggers.Timer(100, "ns")

    for _ in range(total):
        last_msg = tb.fifo_rd.read()
    await last_msg.processed_wait()
    await triggers.Timer(50, "ns")


@cocotb.test()
async def random_test(top: handle.SimHandleBase):
    """Write data into fifo at random intervals,
    while read data from fifo at random intervals.

    The rate at which data is written to faster than
    the rate which data is read."""

    tb = DUT_Testbench(top)
    total = 512
    data = [value & tb.mask for value in range(total)]

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
        for _ in range(total):
            msg = tb.fifo_rd.read()
            await random_wait(70)
            await msg.started_wait()
        await msg.processed_wait()
        await triggers.Timer(50, "ns")

    await triggers.Combine(
        cocotb.start_soon(write_data()),
        cocotb.start_soon(read_data()))


@cocotb.test()
async def report_coverage(top: handle.SimHandleBase) -> None:
    """Reports the coverage."""
    coverage_path = pathlib.Path(os.environ.get("WORK_DIR", "")) / "coverage.yaml"
    coverage.coverage_db.report_coverage(cocotb.log.info, bins=True)
    coverage.coverage_db.export_to_yaml(coverage_path.as_posix())


def test_fifo() -> None:
    """Verifies the fifo. Includes functional coverage with cocotb_coverage."""
    top_levels = ("fifo", "bfifo",)
    widths = (4, 8,)
    depths = (2, 32, 64,)
    af_depths = (2, 16, 32,)
    for top_level, width, depth, af_depth in itertools.product(top_levels, widths, depths, af_depths):
        if af_depth > depth:
            continue
        runner.run(
            hdl_toplevel=top_level,
            test_module="tests.test_fifo",
            work=f"{top_level}_tests_width_{width}_depth_{depth}_afdepth_{af_depth}",
            parameters={"WIDTH": width, "DEPTH": depth, "ALMOST_FULL_DEPTH": af_depth})


if __name__ == "__main__":
    test_fifo()
    pass