import cocotb
import cocotb.clock as clock
import cocotb.handle as handle
import cocotb.triggers as triggers
import random
from cocotb_introduction import reset
import cocotb_introduction.valid as validmdl
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
    def value(self) -> ABData:
        return ABData(a=self._a.value.integer, b=self._b.value.integer)

    @value.setter
    def value(self, value: ABData) -> None:
        self._a.value = value.a
        self._b.value = value.b


@cocotb.test()
async def test_random(top: handle.SimHandleBase) -> None:
    ab_driver = validmdl.ValidDriver(
        clk=top.clk,
        rst=top.rst,
        valid=top.abValid,
        data=ABDataHandle(
            a=top.aData,
            b=top.bData))

    r_monitor = validmdl.ValidMonitor(
        clk=top.clk,
        rst=top.rst,
        valid=top.rValid,
        data=top.rData)

    width = top.WIDTH.value
    mask = (1 << width) - 1
    total = 256
    a_data = [value & mask for value in range(total)]
    b_data = [value & mask for value in range(total)]
    r_data = [ (a + b) & mask for a, b in zip(a_data, b_data)]

    async def drive_data() -> None:
        for a, b in zip(a_data, b_data):
            msg = ab_driver.write(ABData(a, b))
            wait = random.randint(-100, 50)
            if wait > 0:
                await triggers.Timer(wait, "ns")
            await msg.started_wait()

    async def check_data() -> None:
        for exp in r_data:
            await r_monitor.event
            act = r_monitor.message.data
            cocotb.log.info(f"Comparing expected {exp} against actual {act}...")
            assert exp == act

    cocotb.start_soon(clock.Clock(top.clk, 10, "ns").start())
    cocotb.start_soon(reset(top.clk, top.rst))
    await triggers.Combine(cocotb.start_soon(drive_data()), cocotb.start_soon(check_data()))