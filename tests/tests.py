import invoke


def simulate_command(module_name: str, top_level: str) -> str:
    return (f"MODULE={module_name} " +
            f"TOPLEVEL={top_level} " +
            f"SIM_BUILD={module_name}.work " +
            f"SIM_ARGS=--vcd={module_name}.work/waveform.vcd " +
            f"COCOTB_RESULTS_FILE={module_name}.work/results.xml " +
            f"make")


@invoke.task
def simple_tests(c: invoke.Context) -> None:
    c.run(simulate_command("simple_tests", "simple_adder"))


@invoke.task
def fifo_tests(c: invoke.Context) -> None:
    c.run(simulate_command("fifo_tests", "fifo"))