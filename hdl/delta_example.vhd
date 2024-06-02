library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity delta_example is
end entity delta_example;

architecture behav of delta_example is
    signal a, b, c: std_logic;
begin

    c <= a and b;

    run_proc : process
    begin
        a <= '0';
        b <= '0';
        wait for 10 ns;
        a <= '1';
        wait for 5 ns;
        b <= '1';
        wait;
    end process run_proc;

end architecture behav;