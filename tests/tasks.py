import invoke
import invoke.exceptions as exceptions
import typing
import itertools
import sys
import pathlib
import bs4


class SimulationFailure(BaseException):
    """Represents a simulation failure"""
    pass


def run_simulation(c: invoke.Context, module_name: str, top_level: str, work_dir: typing.Optional[str] = None, sim_args: typing.Optional[str] = None) -> None:
    """Creates the command for the specified cocotb test with make."""

    # Determine work directory.
    if work_dir is None:
        work_dir = f"{module_name}.work"
    else:
        work_dir = f"{work_dir}.work"

    # Create the paths
    work_path = pathlib.Path(work_dir)
    if not work_path.exists():
        work_path.mkdir()
    waveform_path = work_path / "waveform.vcd"
    results_path = work_path / "results.xml"
    error_path = work_path / "error.log"

    # Create the simulation command and run the test.
    command = (f"MODULE={module_name} " +
        f"TOPLEVEL={top_level} " +
        f"SIM_BUILD={work_path.as_posix()} " +
        f"WORK_DIR={work_path.as_posix()} " +
        f"SIM_ARGS=\"--wave={waveform_path.as_posix()} " +
        ("" if sim_args is None else f"{sim_args} ") + "\" " +
        f"COCOTB_RESULTS_FILE={results_path.as_posix()} " +
        f"make " +
        f"2>{error_path.as_posix()}")

    # Run command. Catch any errors and dump the logs.
    try:
        result = c.run(command)

        # Check error code.
        # This really shouldn't happen since the run
        # should throw a Failure upon failures.
        if result.return_code != 0:
            raise SimulationFailure()

        # Check to see if resutls xml exists.
        if not (results_path.exists() and results_path.is_file()):
            raise SimulationFailure()

        # Check to see if the results file has any failures in it.
        with open(results_path, "r") as file:
            raw_results = file.read()
        bs_results = bs4.BeautifulSoup(raw_results, "xml")
        failures = bs_results.find_all("failure")
        if len(failures) > 0:
            raise SimulationFailure()

    except (exceptions.Failure, SimulationFailure):
        # Dump the error log if failure.
        print(f"TEST FAILURE DETECTED! Dumping error log as well...", file=sys.stderr)
        c.run(f"cat {error_path.as_posix()} >&2")
        raise


@invoke.task
def clean(c: invoke.Context) -> None:
    """Removes all the working directories."""
    c.run("rm -rf *.work")


@invoke.task
def simple_tests(c: invoke.Context) -> None:
    """Runs a simple test intended for tutorial purposes.
    See the cocotb presentation and the test itself for more information."""
    run_simulation(c, "test_simple", "simple_adder")


@invoke.task
def adder_tests(c: invoke.Context) -> None:
    """Verifies the adder."""
    widths = (2, 4, 8)
    for width in widths:
        run_simulation(
            c=c,
            module_name="test_adder",
            top_level="simple_adder",
            work_dir=f"adder_tests_width_{width}",
            sim_args=f"-gWIDTH={width}")


@invoke.task
def back_adder_tests(c: invoke.Context) -> None:
    """Verifies the adder with back pressure."""
    widths = (16, 32,)
    for width in widths:
        run_simulation(
            c=c,
            module_name="test_back_adder",
            top_level="back_adder",
            work_dir=f"back_adder_tests_width_{width}",
            sim_args=f"-gWIDTH={width}")


@invoke.task
def back_adder_uvm(c: invoke.Context) -> None:
    """Verifies the adder with back pressure, using pyuvm."""
    widths = (16,)
    for width in widths:
        run_simulation(
            c=c,
            module_name="test_back_adder_uvm",
            top_level="back_adder",
            work_dir=f"back_adder_uvm_width_{width}",
            sim_args=f"-gWIDTH={width}")


@invoke.task
def fifo_tests(c: invoke.Context) -> None:
    """Verifies the fifo. Includes functional coverage with cocotb_coverage."""
    top_levels = ("fifo", "bfifo",)
    widths = (4, 8,)
    depths = (2, 32, 64,)
    af_depths = (2, 16, 32,)
    for top_level, width, depth, af_depth in itertools.product(top_levels, widths, depths, af_depths):
        if af_depth > depth:
            continue
        run_simulation(
            c=c,
            module_name="test_fifo",
            top_level=top_level,
            work_dir=f"{top_level}_tests_width_{width}_depth_{depth}_afdepth_{af_depth}",
            sim_args=f"-gWIDTH={width} -gDEPTH={depth} -gALMOST_FULL_DEPTH={af_depth}")


@invoke.task
def delta_example(c: invoke.Context) -> None:
    """The only purpose of this test is to demonstrate how simulator works.
    See the cocotb presentation and the test itself for more information."""
    run_simulation(c, "test_delta_example", "delta_example")


@invoke.task
def delta_cocotb_example(c: invoke.Context) -> None:
    """The only purpose of this test is to demonstrate how simulator works with cocotb.
    See the cocotb presentation and the test itself for more information."""
    run_simulation(c, "test_delta_example", "delta_cocotb_example")


@invoke.task
def simulation_handle_example(c: invoke.Context) -> None:
    """Demonstrates how cocotb's simulation handles work.
    See the cocotb presentation and the test itself for more information."""
    run_simulation(c, "test_simulation_handle_example", "simulation_handle_example")


@invoke.task(
    fifo_tests,
    adder_tests,
    back_adder_tests,
    back_adder_uvm,
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
tests_ns.add_task(back_adder_uvm, "back-adder-uvm")
tutorial_ns = invoke.Collection("tutorial")
tutorial_ns.add_task(simple_tests, "simple")
tutorial_ns.add_task(delta_example, "delta")
tutorial_ns.add_task(delta_cocotb_example, "delta-cocotb")
tutorial_ns.add_task(simulation_handle_example, "handle")
ns.add_collection(tests_ns)
ns.add_collection(tutorial_ns)
ns.add_task(run)
ns.add_task(clean)




