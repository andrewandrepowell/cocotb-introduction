import cocotb
import cocotb.triggers as triggers
import cocotb.clock as clock


@cocotb.test()
async def test_bare_bones(top):
    """
    First test in cocotb.
    """

    aData = [1, 4, 3]
    bData = [1, 0, 2]
    rData = [a + b for a, b in zip(aData, bData)]

    cocotb.log.info(f"Running simple test with aData={aData} and bData={bData}")
    cocotb.log.info(f"The expected data should be rData={rData}")

    async def drive_reset():
        top.rst.value = 1
        for _ in range(2):
            await triggers.RisingEdge(top.clk)
        top.rst.value = 0


    async def drive_input():
        for a, b in zip(aData, bData):
            while True:
                await triggers.RisingEdge(top.clk)
                if top.rst.value.integer == 1:
                    top.abValid.value = 0
                else:
                    top.aData.value = a
                    top.bData.value = b
                    top.abValid.value = 1
                    cocotb.log.info(f"Wrote a={a} and b={b} into the adder.")
                    break
        await triggers.RisingEdge(top.clk)
        top.abValid.value = 0

    async def check_output():
        for expected in rData:
            while True:
                await triggers.RisingEdge(top.clk)
                if top.rst.value.integer == 0 and top.rValid.value.binstr == "1":
                    actual = top.rData.value.integer
                    cocotb.log.info(f"Read r={actual} from the adder.")
                    assert expected == actual, f"The expected value of {expected} does not equal the actual value {actual}!"
                    break


    cocotb.start_soon(clock.Clock(signal=top.clk, period=10, units="ns").start())
    cocotb.start_soon(drive_reset())
    wr_task = cocotb.start_soon(drive_input())
    await check_output()
    await wr_task

