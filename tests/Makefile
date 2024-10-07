# Shouldn't change
HDL_DIR = $(PWD)/../hdl
SIM ?= nvc
TOPLEVEL_LANG ?= vhdl
VHDL_SOURCES += $(HDL_DIR)/simple_adder.vhd
VHDL_SOURCES += $(HDL_DIR)/fifo.vhd
VHDL_SOURCES += $(HDL_DIR)/bfifo.vhd
VHDL_SOURCES += $(HDL_DIR)/delta_example.vhd
VHDL_SOURCES += $(HDL_DIR)/delta_cocotb_example.vhd
VHDL_SOURCES += $(HDL_DIR)/back_adder.vhd
VHDL_SOURCES += $(HDL_DIR)/simulation_handle_example.vhd

# Will change depending on test
TOPLEVEL ?= simple_adder # Toplevel module in HDL.
MODULE ?= simple_tests # Python test
SIM_BUILD ?= simple_tests.work # Working directory
SIM_ARGS ?= --wave=simple_tests.work/waveform.vcd # Simulation arguments.
COCOTB_RESULTS_FILE ?= simple_tests.work/results.xml # Results file

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim