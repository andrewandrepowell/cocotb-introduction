##

Make sure all the dependencies are installed.

```
> git clone https://github.com/andrewandrepowell/cocotb-introduction
> cd cocotb-introduction
> poetry install
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