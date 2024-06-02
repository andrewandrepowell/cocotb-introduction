import invoke
import typing
import itertools


def simulate_command(module_name: str, top_level: str, work_dir: typing.Optional[str] = None, sim_args: typing.Optional[str] = None) -> str:
    """Runs the specified cocotb test with make."""
    if work_dir is None:
        work_dir = f"{module_name}.work"
    else:
        work_dir = f"{work_dir}.work"
    return (f"MODULE={module_name} " +
            f"TOPLEVEL={top_level} " +
            f"SIM_BUILD={work_dir} " +
            f"WORK_DIR={work_dir} " +
            f"SIM_ARGS=\"--vcd={work_dir}/waveform.vcd " +
            ("" if sim_args is None else f"{sim_args} ") + "\" " +
            f"COCOTB_RESULTS_FILE={work_dir}/results.xml " +
            f"make")


@invoke.task
def clean(c: invoke.Context) -> None:
    """Removes all the working directories."""
    c.run("rm -rf *.work")


@invoke.task
def simple_tests(c: invoke.Context) -> None:
    """Runs a simple test intended for tutorial purposes.
    See the cocotb presentation and the test itself for more information."""
    c.run(simulate_command("simple_tests", "simple_adder"))


@invoke.task
def adder_tests(c: invoke.Context) -> None:
    """Verifies the adder."""
    widths = (2, 4, 8)
    for width in widths:
        c.run(simulate_command(
            module_name="adder_tests",
            top_level="simple_adder",
            work_dir=f"adder_tests_width_{width}",
            sim_args=f"-gWIDTH={width}"))


@invoke.task
def back_adder_tests(c: invoke.Context) -> None:
    """Verifies the adder with back pressure."""
    widths = (16, 32,)
    for width in widths:
        c.run(simulate_command(
            module_name="back_adder_tests",
            top_level="back_adder",
            work_dir=f"back_adder_tests_width_{width}",
            sim_args=f"-gWIDTH={width}"))


@invoke.task
def fifo_tests(c: invoke.Context) -> None:
    """Verifies the fifo."""
    widths = (4, 8,)
    depths = (2, 32, 64,)
    af_depths = (2, 16, 32,)
    for width, depth, af_depth in itertools.product(widths, depths, af_depths):
        if af_depth > depth:
            continue
        c.run(simulate_command(
            module_name="fifo_tests",
            top_level="fifo",
            work_dir=f"fifo_tests_width_{width}_depth_{depth}_afdepth_{af_depth}",
            sim_args=f"-gWIDTH={width} -gDEPTH={depth} -gALMOST_FULL_DEPTH={af_depth}"))


@invoke.task
def delta_example(c: invoke.Context) -> None:
    """The only purpose of this test is to demonstrate how simulator works.
    See the cocotb presentation and the test itself for more information."""
    c.run(simulate_command("delta_example", "delta_example"))


@invoke.task
def delta_cocotb_example(c: invoke.Context) -> None:
    """The only purpose of this test is to demonstrate how simulator works with cocotb.
    See the cocotb presentation and the test itself for more information."""
    c.run(simulate_command("delta_cocotb_example", "delta_cocotb_example"))


@invoke.task(
    fifo_tests,
    adder_tests,
    back_adder_tests,
    simple_tests,
    delta_example,
    delta_cocotb_example,
    default=True
)
def run(c: invoke.Context) -> None:
    """Runs all the tests and examples."""
    print("Run all the tests.")


ns = invoke.Collection()
tests_ns = invoke.Collection("test")
tests_ns.add_task(fifo_tests, "fifo")
tests_ns.add_task(adder_tests, "adder")
tests_ns.add_task(back_adder_tests, "back-adder")
tutorial_ns = invoke.Collection("tutorial")
tutorial_ns.add_task(simple_tests, "simple")
tutorial_ns.add_task(delta_example, "delta")
tutorial_ns.add_task(delta_cocotb_example, "delta-cocotb")
ns.add_collection(tests_ns)
ns.add_collection(tutorial_ns)
ns.add_task(run)
ns.add_task(clean)




