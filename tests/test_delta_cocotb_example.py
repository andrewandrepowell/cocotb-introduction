"""
Made specifically for the cocotb presentation to demonstrate simulator operation with cocotb.
"""
import cocotb
import cocotb.triggers as triggers
import cocotb_introduction.runner as runner


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


def test_delta_cocotb_example() -> None:
    """The only purpose of this test is to demonstrate how simulator works.
    See the cocotb presentation and the test itself for more information."""
    runner.run(hdl_toplevel="delta_cocotb_example", test_module="tests.test_delta_cocotb_example", work=f"delta_cocotb_example")


if __name__ == "__main__":
    test_delta_cocotb_example()
    pass