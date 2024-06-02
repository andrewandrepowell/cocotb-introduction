library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity delta_cocotb_example is
end entity delta_cocotb_example;

architecture behav of delta_cocotb_example is
    signal a, b, c: std_logic;
begin

    c <= a and b;

    run_proc : process
    begin
        b <= '0';
        wait for 15 ns;
        b <= '1';
        wait;
    end process run_proc;

end architecture behav;