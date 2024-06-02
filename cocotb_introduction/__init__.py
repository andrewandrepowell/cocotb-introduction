import cocotb.triggers as triggers
import cocotb.handle as handle


async def reset(clk: handle.SimHandleBase, rst: handle.SimHandleBase, cycles: int=4) -> None:
    """Performs a simple synchronous reset."""

    rst.value = 1
    for _ in range(cycles):
        await triggers.RisingEdge(clk)
    rst.value = 0