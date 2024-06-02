import cocotb
import cocotb.triggers as triggers
import cocotb.binary as binary


@cocotb.test()
async def simulation_handle_example(top):

    # Accessing simulation handles
    cocotb.log.info("Demonstrating how simulation handles can be accessed...")
    cocotb.log.info(f"top.a.value={top.a.value}")
    cocotb.log.info(f"top.delta_inst.a.value={top.delta_inst.a.value}")
    cocotb.log.info(f"top.ex0_gen.delta_inst.a.value={top.ex0_gen.delta_inst.a.value}")

    # https://github.com/cocotb/cocotb/issues/3540#issuecomment-1830049657
    # GHDL limitation
    # dir needs to be called on parent of a generator loop,
    # as well as the nested regions within the loop.
    dir(top)
    gen_loop = getattr(top, 'ex1_gen(0)')
    dir(gen_loop)
    dir(gen_loop.delta_inst)
    cocotb.log.info(f"top.ex1_gen(0).delta_inst.a.value={gen_loop.delta_inst.a.value}")

    # Accessing the value of a simulation handle is done with the "value" property.
    cocotb.log.info("Demonstrating how the values of simulation handles can be accessed...")
    top.a.value = 0
    cocotb.log.info(f"top.a.value={top.a.value}")
    await triggers.Edge(top.a)
    cocotb.log.info(f"top.a.value={top.a.value}")

    # Array elements can be accessed with the square-brackets.
    cocotb.log.info(f"top.c[1].value={top.c[1].value}")

    # Return type for logics is always BinaryValue.
    # It's recommended to convert from BinaryValue to either integer or binstr (binary value as string).
    a = top.a.value
    assert isinstance(a, binary.BinaryValue)
    cocotb.log.info(f"type(a)={type(a)}")
    cocotb.log.info(f"a.integer={a.integer}, type(a.integer)={type(a.integer)}")
    cocotb.log.info(f"a.binstr={a.binstr}, type(a.binstr)={type(a.binstr)}")

    # Unresolved logics can't be converted into integers.
    b = top.b.value
    cocotb.log.info(f"b={b}")
    assert isinstance(b, binary.BinaryValue)
    try:
        b.integer
    except ValueError as err:
        cocotb.log.info(err)

    # But they can be converted into binary strings.
    cocotb.log.info(f"b.binstr={b.binstr}")

    # Resolved logics can of course be converted into integers.
    top.b.value = 0b101
    cocotb.log.info(f"top.b.value={top.b.value}")
    dir(top.b) # GHDL limitation. Without this, Edge doesn't work on multibit handles.
    await triggers.Edge(top.b)
    cocotb.log.info(f"top.b.value.integer={top.b.value.integer}")

    # Len can be used to determine width of logics.
    cocotb.log.info("Demonstrating how the ranges of the simulation handles can be accessed...")
    cocotb.log.info(f"len(top.b)={len(top.b)}")

    # Range can be determined with _rang.
    # Be aware this property isn't intended for public access!
    cocotb.log.info(f"top.b._range={top.b._range}")

    # What about accessing bit-slices, integers, floats, and strings?
    # Well, not going to be shown in this example since I had trouble accessing these types myself!
    # Future problem to solve.
    # Integers can still be accessed, but it's inconsistent with Questa.
    # It appears integers with GHDL are treated the same as logics.








