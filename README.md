# cocotb-introduction

## Summary

cocotb-introduction is a set of reference tests and examples for developers who need examples on how to use cocotb for verification. The examples are referenced by the [cocotb-introduction presentation](https://docs.google.com/presentation/d/1zugOCcWV_SXj0Bq5WKZequVLZ3Uh8_YhImmvimYsgEc/edit?usp=sharing). The tests are complete examples on what a full test might look like, including an example of functional coverage with cocotb_coverage and an UVM test with pyuvm.

## Dependencies

- **linux/WSL** - cocotb-introduction was originally developed over Windows WSL in order to utilize the Makefile flow of cocotb. Other Linux distros like Ubuntu should work just as well, but know that the contents of this repo were only tested on WSL.
- **python 3.11.7** - Python is needed to run cocotb and all other Python dependencies. [Information on how to install just python can be found here.](https://radwanelourhmati7.medium.com/installing-python-3-11-on-ubuntu-step-by-step-a46631d4e293) However, it is recommended to [install Anaconda 2024.02](https://docs.anaconda.com/free/anaconda/install/linux/) instead since it includes more Python distributions, none of those distributions are used by cocotb-introductions though.
- **poetry** - Python tool for configuring the Python virtual environment, including installing all the Python dependencies, such as cocotb itself. Since poetry handles all the Python dependencies, they will not be listed in this README. Please see the pyproject.toml. [Information on how to install poetry can be found here.](https://python-poetry.org/docs/)
- **nvc** - Open source VHDL simulator used by all the tests and examples in cocotb-introduction. The simulator can be cloned / built from https://github.com/nickg/nvc.
- **gtkwave** - Waveform viewer. This is only needed to open the waveform.vcd waveform files produced by the simulations. [Windows install can be found here.](https://sourceforge.net/projects/gtkwave/files/gtkwave-3.3.90-bin-win64/gtkwave-3.3.90-bin-win64.zip/download)

## Usage

Make sure all the aforementioned dependencies are installed.

```
> git clone https://github.com/andrewandrepowell/cocotb-introduction
> cd cocotb-introduction
> poetry shell
> poetry install
<install output ommitted>
> cd tests
> ls | grep "^test\_.*\.py$" # Lists all the possible tests and examples, which are the python modules prefixed with 'test_'.
test_adder.py
test_back_adder.py
test_back_adder_uvm.py
test_delta_cocotb_example.py
test_delta_example.py
test_fifo.py
test_simple.py
test_simulation_handle_example.py
>
> # The following demonstrates how to run the tests with the cocotb.runner.
> pytest # Runs all the tests with no logging.
> pytest -s # Runs all the tests, but logs are printed to standard output.
> LOG_ENABLE=1 pytest # Runs all the tests, but logs are stored in log files within each tests work directory.
> pytest test_<specific test>.py -s # Runs a specific test with pytest.
> python test_<specific test>.py # Runs a specific test with just python.
>
> # The following demonstrates how to run the tests with the invoke app and cocotb Makefile.
> # Please note that the invoke approach to running tests is deprecated and will eventually be removed once there's support for wavefile.
> inv --list generation with cocotb.runner configured for NVC.
Available tasks:

  clean                   Removes all the working directories.
  run                     Runs all the tests and examples.
  test.adder              Verifies the adder.
  test.back-adder         Verifies the adder with back pressure.
  test.back-adder-uvm     Verifies the adder with back pressure, using pyuvm.
  test.fifo               Verifies the fifo. Includes functional coverage with cocotb_coverage.
  tutorial.delta          The only purpose of this test is to demonstrate how simulator works.
  tutorial.delta-cocotb   The only purpose of this test is to demonstrate how simulator works with cocotb.
  tutorial.handle         Demonstrates how cocotb's simulation handles work.
  tutorial.simple         Runs a simple test intended for tutorial purposes.

Default task: run
> inv run
```
