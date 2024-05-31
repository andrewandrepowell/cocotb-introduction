import invoke
import typing
import itertools


def simulate_command(module_name: str, top_level: str, work_dir: typing.Optional[str] = None, sim_args: typing.Optional[str] = None) -> str:
    if work_dir is None:
        work_dir = f"{module_name}.work"
    else:
        work_dir = f"{work_dir}.work"
    return (f"MODULE={module_name} " +
            f"TOPLEVEL={top_level} " +
            f"SIM_BUILD={work_dir} " +
            f"SIM_ARGS=--vcd={work_dir}/waveform.vcd " +
            ("" if sim_args is None else f"SIM_ARGS={sim_args} ") +
            f"COCOTB_RESULTS_FILE={work_dir}/results.xml " +
            f"make")


@invoke.task
def clean(c: invoke.Context) -> None:
    c.run("rm -rf *.work")


@invoke.task
def simple_tests(c: invoke.Context) -> None:
    c.run(simulate_command("simple_tests", "simple_adder"))


@invoke.task
def fifo_tests(c: invoke.Context) -> None:
    widths = (4, 8,)
    depths = (32, 64,)
    af_depths = (16, 32,)
    for width, depth, af_depth in itertools.product(widths, depths, af_depths):
        if af_depth > depth:
            continue
        c.run(simulate_command(
            module_name="fifo_tests",
            top_level="fifo",
            work_dir=f"fifo_tests_width_{width}_depth_{depth}_afdepth_{af_depth}",
            sim_args=f"\"-gWIDTH={width} -gDEPTH={depth} -gALMOST_FULL_DEPTH={af_depth}\""))


@invoke.task(simple_tests, fifo_tests, default=True)
def run(c: invoke.Context) -> None:
    print("Run all the tests.")


ns = invoke.Collection()
tests_ns = invoke.Collection("test")
tests_ns.add_task(simple_tests, "simple")
tests_ns.add_task(fifo_tests, "fifo")
ns.add_collection(tests_ns)
ns.add_task(run)
ns.add_task(clean)




