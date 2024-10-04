import cocotb
import cocotb.handle as handle
import cocotb.clock as clock
import cocotb.triggers as triggers
import pyuvm
import cocotb_introduction.validready as validready
import cocotb_introduction.messages as messages
import cocotb_introduction.queue as queue
from cocotb_introduction import reset
import typing
import random


WIDTH: int = cocotb.top.WIDTH.value
MASK = (1 << WIDTH) - 1


def adder_model(a: int, b: int) -> int:
    return (a + b) & MASK


async def random_wait(max_wait: int = 30) -> None:
    assert max_wait >= 0
    wait_time = random.randint(-50, max_wait)
    if wait_time < 0:
        return
    await triggers.Timer(wait_time, "ns")


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


class ABSeqItem(pyuvm.uvm_sequence_item):
    def __init__(self, name: str, data: ABData = ABData(0, 0)) -> None:
        super().__init__(name)
        assert 0 <= data.a <= MASK
        assert 0 <= data.b <= MASK
        self.data = data

    def randomize(self) -> None:
        self.data = ABData(random.randint(0, MASK), random.randint(0, MASK))

    def __eq__(self, other: typing.Any) -> bool:
        assert isinstance(other, type(self))
        return self.data == other.data and self.data == self.data

    def __repr__(self) -> str:
        return f"{type(self).__name__}(data={self.data})"


class RSeqItem(pyuvm.uvm_sequence_item):
    pass


class ABRandomSeq(pyuvm.uvm_sequence):
    def __init__(self, name: str, length: int = 16, max_wait: int = 100) -> None:
        super().__init__(name=name)
        self.length = length
        self.max_wait = max_wait

    async def body(self) -> None:
        for _ in range(self.length):
            ab_seq = ABSeqItem("ab_seq")
            await self.start_item(ab_seq)
            ab_seq.randomize()
            await self.finish_item(ab_seq)
            await random_wait(self.max_wait)


class RRandomSeq(pyuvm.uvm_sequence):
    def __init__(self, name: str, length: int = 16, max_wait: int = 100) -> None:
        super().__init__(name=name)
        self.length = length
        self.max_wait = max_wait

    async def body(self) -> None:
        for _ in range(self.length):
            r_seq = RSeqItem("r_seq")
            await self.start_item(r_seq)
            await self.finish_item(r_seq)
            await random_wait(self.max_wait)


class TestAllSeq(pyuvm.uvm_sequence):
    async def body(self):
        config_db = pyuvm.ConfigDB()
        ab_seqr = config_db.get(None, "", "AB_SEQR")
        r_seqr = config_db.get(None, "", "R_SEQR")
        ab_delay = config_db.get(None, "", "AB_DELAY")
        r_delay = config_db.get(None, "", "R_DELAY")
        length = config_db.get(None, "", "LENGTH")
        ab_seq = ABRandomSeq("ab_seq", length=length, max_wait=ab_delay)
        r_seq = RRandomSeq("r_seq", length=length, max_wait=r_delay)
        await triggers.Combine(
            cocotb.start_soon(ab_seq.start(ab_seqr)),
            cocotb.start_soon(r_seq.start(r_seqr)))


class RdDriver(pyuvm.uvm_driver):
    def build_phase(self) -> None:
        self.r_ap = pyuvm.uvm_analysis_port("r_ap", self)

    def start_of_simulation_phase(self) -> None:
        self.r_drv = validready.ValidReadyReadDriver(
            clk=cocotb.top.clk,
            rst=cocotb.top.rst,
            valid=cocotb.top.r_valid,
            ready=cocotb.top.r_ready,
            data=cocotb.top.r_Data)

    async def run_phase(self) -> None:
        r_msgs = queue.Queue[messages.ReadMessage]()

        async def perform_rd() -> None:
            while True:
                _: RSeqItem = await self.seq_item_port.get_next_item()
                self.seq_item_port.item_done()
                r_msg = self.r_drv.read()
                r_msgs.push(r_msg)
                await r_msg.started_wait()

        async def send_r() -> None:
            while True:
                r_msg = await r_msgs.pop_wait()
                r_act = await r_msg.processed_wait()
                self.r_ap.write(r_act)

        await triggers.Combine(
            cocotb.start_soon(perform_rd()),
            cocotb.start_soon(send_r()))


class WrDriver(pyuvm.uvm_driver):
    def start_of_simulation_phase(self) -> None:
        self.ab_drv = validready.ValidReadyWriteDriver(
            clk=cocotb.top.clk,
            rst=cocotb.top.rst,
            valid=cocotb.top.ab_valid,
            ready=cocotb.top.ab_ready,
            data=ABDataHandle(
                a=cocotb.top.a_data,
                b=cocotb.top.b_data))

    async def run_phase(self) -> None:
        while True:
            ab_seq: ABSeqItem = await self.seq_item_port.get_next_item()
            ab_msg = self.ab_drv.write(ab_seq.data)
            self.seq_item_port.item_done()
            await ab_msg.started_wait()


class Monitor(pyuvm.uvm_component):
    def build_phase(self) -> None:
        self.ab_ap = pyuvm.uvm_analysis_port("ab_ap", self)
        self.ab_mon = validready.ValidReadyMonitor(
            clk=cocotb.top.clk,
            rst=cocotb.top.rst,
            valid=cocotb.top.ab_valid,
            ready=cocotb.top.ab_ready,
            data=ABDataHandle(
                a=cocotb.top.a_data,
                b=cocotb.top.b_data))

    async def run_phase(self) -> None:
        while True:
            await self.ab_mon.event
            ab_msg = self.ab_mon.message
            self.ab_ap.write(ab_msg.data)


class Scoreboard(pyuvm.uvm_component):
    def build_phase(self) -> None:
        self.ab_get_port = pyuvm.uvm_get_port("ab_get_port", self)
        self.r_get_port = pyuvm.uvm_get_port("r_get_port", self)
        self.ab_fifo = pyuvm.uvm_tlm_analysis_fifo("ab_fifo", self)
        self.r_fifo = pyuvm.uvm_tlm_analysis_fifo("r_fifo", self)
        self.ab_export = self.ab_fifo.analysis_export
        self.r_export = self.r_fifo.analysis_export

    def connect_phase(self) -> None:
        self.ab_get_port.connect(self.ab_fifo.get_export)
        self.r_get_port.connect(self.r_fifo.get_export)

    def check_phase(self):
        while self.ab_get_port.can_get() and self.r_get_port.can_get():
            success, ab_exp = typing.cast(typing.Tuple[bool, ABData], self.ab_get_port.try_get())
            assert success
            success, r_act = typing.cast(typing.Tuple[bool, int], self.r_get_port.try_get())
            assert success
            r_exp = adder_model(ab_exp.a, ab_exp.b)
            self.logger.info(f"Comparing r_exp={r_exp} against r_act={r_act}. r_exp was derived from ab_exp={ab_exp}.")
            assert r_act == r_exp


class Environment(pyuvm.uvm_env):

    def start_of_simulation_phase(self) -> None:
        cocotb.start_soon(clock.Clock(cocotb.top.clk, 10, "ns").start())
        cocotb.start_soon(reset(cocotb.top.clk, cocotb.top.rst))

    def build_phase(self) -> None:
        config_db = pyuvm.ConfigDB()
        config_db.set(None, "*", "LENGTH", 64)
        config_db.set(None, "*", "AB_DELAY", 50)
        config_db.set(None, "*", "R_DELAY", 60)
        self.ab_seqr = pyuvm.uvm_sequencer("ab_seqr", self)
        self.r_seqr = pyuvm.uvm_sequencer("r_seqr", self)
        config_db.set(None, "*", "AB_SEQR", self.ab_seqr)
        config_db.set(None, "*", "R_SEQR", self.r_seqr)
        self.wr_drv = WrDriver("wr_drv", self)
        self.rd_drv = RdDriver("rd_drv", self)
        self.mon = Monitor("mon", self)
        self.sb = Scoreboard("sb", self)

    def connect_phase(self) -> None:
        self.wr_drv.seq_item_port.connect(self.ab_seqr.seq_item_export)
        self.rd_drv.seq_item_port.connect(self.r_seqr.seq_item_export)
        self.mon.ab_ap.connect(self.sb.ab_export)
        self.rd_drv.r_ap.connect(self.sb.r_export)


@pyuvm.test()
class Test(pyuvm.uvm_test):
    def build_phase(self) -> None:
        self.env = Environment("env", self)

    def end_of_elaboration_phase(self) -> None:
        self.test_all = TestAllSeq("test_all")

    async def run_phase(self) -> None:
        self.raise_objection()
        await self.test_all.start()
        self.drop_objection()