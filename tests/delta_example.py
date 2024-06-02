"""
Made specifically for the cocotb presentation to demonstrate simulator operation.
"""
import cocotb
import cocotb.triggers as triggers


@cocotb.test()
async def delta_example(top) -> None:
    await triggers.Timer(25, "ns")
