"""
The two tests "test_bare_bones" and "test_bare_bones_commentless" demonstrate
all the basics of cocotb.

The first test, "test_bare_bones", consists of comments that explain each major facet of the test,
whereas the "test_bare_bones_commentless" is the same test but without comments.
"""
import cocotb
import cocotb.triggers as triggers
import cocotb.clock as clock


# The cocotb.test decorator marks a coroutine function--a Python function qualified with
# "async"--as a cocotb test, and as such, will get picked up by cocotb's regression manager to run.
#
# The cocotb.test decorator can take several arguments in order to implement the following
# features.
#   - timeout
#   - expect a failure
#   - skip the test
#
# The marked coroutine function must take a single input, the "top" simulation handle.
# Simulation handles represent the objects within the HDL itself, such as nets and modules.
# The "top" simulation handle starts at the TOPLEVEL specified in the corresponding Makefile.
# The naming convention of each simulation handle is dictated for the simulator, NOT THE HDL.
#
@cocotb.test()
async def test_bare_bones(top):
    """
    First test in cocotb.

    This test demonstrates all the basic features of cocotb.
    The test doesn't try to leverage any advance reuse at all but
    instead attempts to demonstrate how a quickly a cocotb test can be
    spawn up without having much background in Python.
    """

    # Create some data. Random data can easily be created instead.
    # rData is created ahead of time in order to verify the adder.
    aData = [1, 4, 3]
    bData = [1, 0, 2]
    rData = [a + b for a, b in zip(aData, bData)]

    # Cocotb relies on the Python logger, to which a reference can be found under
    # the cocotb module.
    #
    # The same logger can be acquired from logging.getLogger("cocotb").
    cocotb.log.info(f"Running simple test with aData={aData} and bData={bData}")
    cocotb.log.info(f"The expected data should be rData={rData}")

    # Coroutine functions can be defined at any point.
    # However, they don't do anything until told to.
    # In other words, the drive_reset, drive_input, and
    # check_output don't perform any operations until later directed.

    async def drive_reset():
        """Drives the reset for a few cycles."""

        # Note how the "rst" simulation handle is referenced from "top".
        # "top" refers to "simple_adder", the TOPLEVEL, whereas "rst" is
        # a signal directly under the "top". If there were instantiations of
        # other components defined under "top", access to their signals is done
        # the same way.
        #
        # Setting and getting values to and from a simulation handle is acheived via
        # the "value" property.
        #
        # Getting a value from a simulation returns a cocotb.binary.BinaryValue.
        # It's highly recommended to convert the BinaryValue to either an integer
        # with the ".integer" property (".signed_integer" is signed) or a string
        # with ".binstr".
        top.rst.value = 1

        # This for-loop waits for 2 clock cycles before deasserting the reset.
        for _ in range(2):

            # All triggers give control back to the scheduler and are associated.
            # with a condition that determines when the coroutine should resume its operation.
            # The RisingEdge trigger's condition is the "transition of 0 to 1".
            #
            # CRITICAL: One of the major implications of a cooperative scheduling system is that
            #           each coroutine must give up its control in order for either the simulator
            #           to continue or another scheduled coroutine (i.e. a task) to continue.
            #           So, if a coroutine does not either await on a trigger, await on another coroutine with a
            #           trigger nested within, or simply end, then the simulation will freeze indefinitely.
            await triggers.RisingEdge(top.clk)

        # Reset is deasserted.
        top.rst.value = 0

    # The information explained in the first coroutine are applicable
    # to both the drive_input and check_output coroutines.

    async def drive_input():
        """Drives the input with data."""

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
        """Checks the output for correctness."""

        for expected in rData:
            while True:
                await triggers.RisingEdge(top.clk)
                if top.rst.value.integer == 0 and top.rValid.value.integer == 1:
                    actual = top.rData.value.integer
                    cocotb.log.info(f"Read r={actual} from the adder.")
                    assert expected == actual, f"The expected value of {expected} does not equal the actual value {actual}!"
                    break


    # cocotb.start_soon schedules a coroutine. Scheduled coroutines, called tasks, run
    # along side of other scheduled coroutines--such as the test itself--and the
    # simulator.
    #
    # In order for nonactive tasks to run, the current task must give up control by
    # either awaiting on a trigger, awaiting on a coroutine with a nested trigger, or end.
    #
    # The clock, drive_reset, and drive_input are all scheduled since they all need to run
    # at the same time.
    #
    # cocotb.start_soon returns the task, which optionally can be awaited later, indicating the task
    # is done.
    cocotb.start_soon(clock.Clock(signal=top.clk, period=10, units="ns").start())
    cocotb.start_soon(drive_reset())
    cocotb.start_soon(drive_input())

    # If a coroutine is instead awaited on, it's effectively treated like a function.
    # Please note that no simulation time has passed yet, since a trigger hasn't been awaited on!
    await check_output()


@cocotb.test()
async def test_bare_bones_commentless(top):
    """
    Same test as the bare_bones one, but all the comments
    are removed so that the test itself is clearer.
    """
    aData = [1, 4, 3]
    bData = [1, 0, 2]
    rData = [a + b for a, b in zip(aData, bData)]

    cocotb.log.info(f"Running simple test with aData={aData} and bData={bData}")
    cocotb.log.info(f"The expected data should be rData={rData}")

    async def drive_reset():
        """Drives the reset for a few cycles."""

        top.rst.value = 1
        for _ in range(2):
            await triggers.RisingEdge(top.clk)
        top.rst.value = 0

    async def drive_input():
        """Drives the input with data."""

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
        """Checks the output for correctness."""

        for expected in rData:
            while True:
                await triggers.RisingEdge(top.clk)
                if top.rst.value.integer == 0 and top.rValid.value.integer == 1:
                    actual = top.rData.value.integer
                    cocotb.log.info(f"Read r={actual} from the adder.")
                    assert expected == actual, f"The expected value of {expected} does not equal the actual value {actual}!"
                    break

    cocotb.start_soon(clock.Clock(signal=top.clk, period=10, units="ns").start())
    cocotb.start_soon(drive_reset())
    cocotb.start_soon(drive_input())
    await check_output()