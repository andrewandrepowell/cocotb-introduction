"""
Made specifically for the cocotb presentation to demonstrate simulator operation with cocotb.
"""
import cocotb
import cocotb.triggers as triggers


@cocotb.test()
async def delta_example(top) -> None:
    cocotb.log.info(f"b={top.b.value}")
    await triggers.Edge(top.b)
    cocotb.log.info(f"b={top.b.value}")
    await triggers.Timer(5, "ns")
    top.a.value = 0
    await triggers.Timer(5, "ns")
    top.a.value = 1
    await triggers.Timer(5, "ns")
    cocotb.log.info(f"c={top.c.value}")
    await triggers.Edge(top.c)
    cocotb.log.info(f"c={top.c.value}")
    await triggers.Timer(5, "ns")
