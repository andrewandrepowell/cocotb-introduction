import cocotb
import cocotb.triggers as triggers
import cocotb.binary as binary
import cocotb.types as types
import cocotb.handle as handle
import cocotb_introduction.runner as runner


@cocotb.test()
async def simulation_handle_example(top):

    cocotb.log.info("The following examples are applicable to logics (e.g. std_logic, std_logic_vector, etc).")

    cocotb.log.info("Demonstrating how the values of simulation handles can be accessed...")
    top.a.value = 0
    cocotb.log.info(f"top.a.value={top.a.value}")
    await triggers.Edge(top.a)
    cocotb.log.info(f"top.a.value={top.a.value}")

    cocotb.log.info("Demonstrating how to utilize BinaryValue, the return type when reading the value property of a simulation handle.")
    a = top.a.value
    assert isinstance(a, binary.BinaryValue)
    cocotb.log.info(f"type(a)={type(a)}")
    cocotb.log.info(f"a.integer={a.integer}, type(a.integer)={type(a.integer)}")
    cocotb.log.info(f"a.binstr={a.binstr}, type(a.binstr)={type(a.binstr)}")
    # It's worth pointing out BinaryValues can also be written to a simulation handle's value property.

    cocotb.log.info("Demonstrating how to access instantiations within a component using the dot operator...")
    cocotb.log.info(f"top.delta_inst.a.value={top.delta_inst.a.value}")

    cocotb.log.info("Dot operation can also be applied to generator blocks...")
    cocotb.log.info(f"top.ex0_gen.delta_inst.a.value={top.ex0_gen.delta_inst.a.value}")

    cocotb.log.info("Demonstrating how to access array elemnents with the square brackets...")
    cocotb.log.info(f"top.c[1].value={top.c[1].value}")

    cocotb.log.info("Demonstrating how to access generator loops with the square brackets...")
    cocotb.log.info(f"top.ex1_gen[1].delta_inst.a.value={top.ex1_gen[1].delta_inst.a.value}")

    cocotb.log.info("The Python len operator can be used to determine the length of a logic.")
    for i in range(len(top.b)):
        cocotb.log.info(f"top.b[{i}].value.binstr={top.b[i].value.binstr}")

    cocotb.log.info("LogicArrays can be used instead of BinaryValue for much easier slicing.")
    la = types.LogicArray(top.b.value)
    cocotb.log.info(f"la={la}")
    cocotb.log.info(f"la[2:0]={la[2:0]}")
    cocotb.log.info(f"la[3:1]={la[3:1]}")

    cocotb.log.info("The range can also be acquired from a simulation handle if it's a logic array.")
    cocotb.log.info("Be careful, the Python convention is that properties prefixed with an underscore are intended for internal use, however it's currently the only way to get the range.")
    def GetRange(h: handle.ModifiableObject) -> types.Range | None:
        if h._range:
            assert len(h._range) == 2
            return types.Range(h._range[0], 'to' if h._range[0] < h._range[1] else 'downto', h._range[1])
        else:
            return None
    cocotb.log.info(f"top.a._range={top.a._range}")
    cocotb.log.info(f"top.b._range={top.b._range}")
    cocotb.log.info(f"GetRange(top.a)={GetRange(top.a)}")
    cocotb.log.info(f"GetRange(top.b)={GetRange(top.b)}")

    cocotb.log.info("Unresolved logics can't be converted into integers.")
    b = top.b.value
    cocotb.log.info(f"b={b}")
    assert isinstance(b, binary.BinaryValue)
    try:
        b.integer
    except ValueError as err:
        cocotb.log.info(err)

    cocotb.log.info(f"But they can be converted into binary strings.")
    cocotb.log.info(f"b.binstr={b.binstr}")

    cocotb.log.info(f"Resolved logics can of course be converted into integers.")
    top.b.value = 0b101
    cocotb.log.info(f"top.b.value={top.b.value}")
    await triggers.Edge(top.b)
    cocotb.log.info(f"top.b.value.integer={top.b.value.integer}")

    cocotb.log.info(f"Aside from logics, reals, strings, and integers can also be accessed from cocotb...")

    cocotb.log.info("Integer access...")
    cocotb.log.info(f"type(top.d.value)={type(top.d.value)}")
    top.d.value = 3333
    cocotb.log.info(f"top.d.value={top.d.value}")
    await triggers.Edge(top.d)
    cocotb.log.info(f"top.d.value={top.d.value}")

    cocotb.log.info("Real access...")
    cocotb.log.info(f"type(top.e.value)={type(top.e.value)}")
    top.e.value = 1.3
    cocotb.log.info(f"top.e.value={top.d.value}")
    await triggers.Edge(top.e)
    cocotb.log.info(f"top.d.value={top.e.value}")

    cocotb.log.info("String access...")
    cocotb.log.info(f"type(top.f.value)={type(top.f.value)}")
    top.f.value = "what?" # Can't set more characters than what the signal's constraints allow.
    cocotb.log.info(f"top.f.value={top.f.value.decode()}")
    await triggers.Edge(top.f)
    cocotb.log.info(f"top.d.value={top.f.value.decode()}")


def test_simulation_handle_example() -> None:
    """Demonstrates how cocotb's simulation handles work.
    See the cocotb presentation and the test itself for more information."""
    runner.run(hdl_toplevel="simulation_handle_example", test_module="tests.test_simulation_handle_example", work=f"simulation_handle_example")


if __name__ == "__main__":
    test_simulation_handle_example()
    pass