## Helpful Links

- https://gotofritz.net/blog/creating-a-poetry-driven-python-project-template-with-cookiecutter/
- https://python-poetry.org/docs/basic-usage/
- https://www.freecodecamp.org/news/how-to-build-and-publish-python-packages-with-poetry/
- https://pipx.pypa.io/stable/installation/
- https://ghdl-rad.readthedocs.io/en/latest/getting/mcode.html
- https://docs.cocotb.org/en/stable/building.html # Definitely need a section going over the building arguments in the makefile.

## Dependencies

- `apt install make` cocotb can be optionally started with make files.
- `apt install gtkwave` gtkwave is the tool for viewing waveforms.
- `apt install ghdl` ghdl is the simulator. It's recommended to build from source. had some issues with the version downloaded from apt.
- `apt install gnat` needed by ghdl
- `apt install libz-dev` needed by ghdl

```
> cd cocotb_introduction
> poetry install
> poetry shellit
> cd tests
> invoke simple-tests
```