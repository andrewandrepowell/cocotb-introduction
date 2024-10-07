import yaml
import pathlib
import typing


class RunnerDict(typing.TypedDict):
    """Represents all the configurations related to the cocotb runner."""
    simulator: str
    hdl_library: str
    vhdl_sources: typing.Sequence[str]


class ConfigDict(typing.TypedDict):
    """Represents the configurations for the repo stored as a yaml."""
    runner: RunnerDict


CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config.yaml"
with open(CONFIG_PATH, "r") as file:
    CONFIG = ConfigDict(yaml.safe_load(file))

