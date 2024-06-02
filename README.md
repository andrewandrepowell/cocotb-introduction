## Summary

cocotb-introduction is a set of reference tests and examples for developers who want to get started with cocotb for verification. The examples are referenced by the [cocotb-introduction presentation](). The tests are complete examples on what a full test might look like, including an example of functional coverage with cocotb_coverage and an UVM test with pyuvm.

## Dependencies

- **linux/WSL** - cocotb-introduction was originally developed over Windows WSL in order to utilize the Makefile flow of cocotb. Other Linux distros like Ubuntu should work just as well, but know that the contents of this repo were only tested on WSL.
- **python 3.11.7** - Python is needed to run cocotb and all other Python dependencies. [Information on how to install just python can be found here.](https://radwanelourhmati7.medium.com/installing-python-3-11-on-ubuntu-step-by-step-a46631d4e293) However, it is recommended to [install Anaconda 2024.02](https://docs.anaconda.com/free/anaconda/install/linux/) instead since it includes more Python distributions, none of those distributions are used by cocotb-introductions though.
- **poetry** - Python tool for configuring the Python virtual environment, including installing all the Python dependencies. Since poetry handles all the Python dependencies, they will not be listed in this README. Please see the pyproject.toml. [Information on how to install poetry can be found here.](https://python-poetry.org/docs/)
- **ghdl** - VHDL simulator used by all the tests and examples in cocotb-introduction. Recommended to build from source since `apt install ghdl` only installs older version of the simulator. [The repo can be cloned from here.](https://github.com/ghdl/ghd) [Instructions on how to build from source can be found here.](https://ghdl-rad.readthedocs.io/en/latest/getting/mcode.html)
- **gtkwave** - Waveform viewer. This is only needed to open the waveform.vcd waveform files produced by the simulations. [Windows install can be found here.](https://sourceforge.net/projects/gtkwave/files/gtkwave-3.3.90-bin-win64/gtkwave-3.3.90-bin-win64.zip/download)

##

Make sure all the dependencies are installed.

```
> git clone https://github.com/andrewandrepowell/cocotb-introduction
> cd cocotb-introduction
> poetry shell
> poetry install
<install output ommitted>
> cd tests
> inv --list
Available tasks:

  clean                   Removes all the working directories.
  run                     Runs all the tests and examples.
  test.adder              Verifies the adder.
  test.fifo               Verifies the fifo.
  tutorial.delta          The only purpose of this test is to demonstrate how simulator works.
  tutorial.delta-cocotb   The only purpose of this test is to demonstrate how simulator works with cocotb.
  tutorial.simple         Runs a simple test intended for tutorial purposes.

Default task: run
> inv run
```

## Helpful Links

- https://gotofritz.net/blog/creating-a-poetry-driven-python-project-template-with-cookiecutter/
- https://python-poetry.org/docs/basic-usage/
- https://www.freecodecamp.org/news/how-to-build-and-publish-python-packages-with-poetry/
- https://pipx.pypa.io/stable/installation/
- https://ghdl-rad.readthedocs.io/en/latest/getting/mcode.html
- https://docs.cocotb.org/en/stable/building.html # Definitely need a section going over the building arguments in the makefile.
- https://github.com/cocotb/cocotb/issues/3540#issuecomment-1830049657

## Dependencies

- python 3.11.7
- `pipx poetry` poetry is needed to configure the Python virtual environment and install Python dependencies
- `apt install make` cocotb can be optionally started with make files.
- `apt install gtkwave` gtkwave is the tool for viewing waveforms.
- `apt install ghdl` ghdl is the simulator. It's recommended to build from source. had some issues with the version downloaded from apt.
- `apt install gnat` needed by ghdl when built from source
- `apt install libz-dev` needed by ghdl when built from source

```
> cd cocotb_introduction
> poetry install
> poetry shellit
> cd tests
> invoke simple-tests
```