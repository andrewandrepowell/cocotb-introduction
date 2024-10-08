import cocotb.runner
import pathlib
import itertools
import os
import shutil
import typing
from . import config


def run(hdl_toplevel: str, test_module: str, work: str, parameters: typing.Mapping[str, typing.Any] | None = None) -> None:
    """Wraps around the cocotb runner to encapsulate operations that need to be common for every test.
    parameters refers to overloading/setting generics of the design."""

    # Unfortunately, it doesn't seem to be possible to log and print to standard out at the same time.
    # For now, the following environmental variable will be used to switch logging on/off.
    log_enable = os.environ.get("LOG_ENABLE", config.CONFIG.get("log_enable", None)) in ("1", "true", "True", "TRUE", True)

    # Prepare working directory.
    work_path = pathlib.Path(work + ".work")
    if work_path.exists():
        shutil.rmtree(work_path.as_posix())
    work_path.mkdir(parents=True)

    # Pull configurations from yaml.
    runner_config = config.CONFIG['runner']
    runner = cocotb.runner.get_runner(simulator_name=runner_config['simulator'])
    sources = list(cocotb.runner.VHDL(source) for source in
                   itertools.chain.from_iterable(config.CONFIG_PATH.parent.glob(source) for source in runner_config['vhdl_sources']))

    # Build the HDL using the cocotb runner.
    runner.build(
        hdl_library=runner_config['hdl_library'],
        sources=sources,
        build_dir=work_path,
        log_file=work_path / "build.log" if log_enable else None,
        always=True,
        waves=False, # Unfortunately, waves is not yet supported, using the cocotb.runner. Waves can be generated with the Makefile approach, however.
    )

    # Run the test with cocotb runner.
    runner.test(
        test_module=test_module,
        hdl_toplevel=hdl_toplevel,
        hdl_toplevel_library=runner_config['hdl_library'],
        log_file=work_path / "sim.log" if log_enable else None,
        test_dir=work_path,
        parameters=parameters)
