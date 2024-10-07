"""
Made specifically for the cocotb presentation to demonstrate simulator operation.
"""
import cocotb
import cocotb.triggers as triggers
import cocotb_introduction.runner as runner


@cocotb.test()
async def delta_example(top) -> None:
    await triggers.Timer(25, "ns")


def test_delta_example() -> None:
    """The only purpose of this test is to demonstrate how simulator works.
    See the cocotb presentation and the test itself for more information."""
    runner.run(hdl_toplevel="delta_example", test_module="tests.test_delta_example", work=f"delta_example")


if __name__ == "__main__":
    test_delta_example()
    pass