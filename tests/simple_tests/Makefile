# Makefile
HDL_DIR=$(PWD)/../../hdl

# Configs
SIM ?= ghdl
TOPLEVEL_LANG ?= vhdl
SIM_ARGS ?= --vcd=waveform.vcd

VHDL_SOURCES += $(HDL_DIR)/simple_adder.vhd

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = simple_adder

# MODULE is the basename of the Python test file
MODULE = simple_tests

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim