import invoke
import tests


def simulate_command(module_name: str, top_level: str) -> str:
    return (f"MODULE={module_name} " +
            f"TOPLEVEL={top_level} " +
            f"SIM_BUILD={module_name}.work " +
            f"SIM_ARGS=--vcd={module_name}.work/waveform.vcd " +
            f"COCOTB_RESULTS_FILE={module_name}.work/results.xml " +
            f"make")


@invoke.task
def clean(c: invoke.Context) -> None:
    c.run("rm -rf *.work")


@invoke.task
def simple_tests(c: invoke.Context) -> None:
    c.run(simulate_command("simple_tests", "simple_adder"))


@invoke.task
def fifo_tests(c: invoke.Context) -> None:
    c.run(simulate_command("fifo_tests", "fifo"))


@invoke.task(simple_tests, fifo_tests, default=True)
def run(c: invoke.Context) -> None:
    print("Run all the tests.")


ns = invoke.Collection()
tests_ns = invoke.Collection("tests")
tests_ns.add_task(simple_tests, "simple")
tests_ns.add_task(fifo_tests, "fifo")
ns.add_collection(tests_ns)
ns.add_task(run)
ns.add_task(clean)




