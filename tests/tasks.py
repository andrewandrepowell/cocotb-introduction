import invoke


def simulate_command(module_name: str) -> str:
    return (f"MODULE={module_name} " +
            f"SIM_BUILD={module_name}.work " +
            f"SIM_ARGS=--vcd={module_name}.work/waveform.vcd " +
            f"COCOTB_RESULTS_FILE={module_name}.work/results.xml " +
            f"make")


@invoke.task
def clean(c: invoke.Context) -> None:
    c.run("rm -rf *.work")


@invoke.task
def simple_tests(c: invoke.Context) -> None:
    c.run(simulate_command("simple_tests"))


tests_namespace = invoke.Collection("tests")
tests_namespace.add_task(simple_tests)