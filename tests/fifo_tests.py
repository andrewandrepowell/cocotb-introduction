import cocotb
import cocotb.clock as clock
import cocotb_introduction.fifo as fifo
from cocotb_introduction import reset
import typing


@cocotb.test()
async def test_basic(top):
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

    data = list(range(64))

    rd_msgs: typing.List[fifo.FifoReadMessage] = []
    for value in data:
        fifo_wr.write(value)
        rd_msgs.append(fifo_rd.read())

    for exp, msg in zip(data, rd_msgs):
        act = await msg.processedwait()
        cocotb.log.info(f"Comparing expected {exp} against actual {act}...")
        assert exp == act

    pass

