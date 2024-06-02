library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity simulation_handle_example is
end entity simulation_handle_example;

architecture behav of simulation_handle_example is
    signal a : std_logic := '1';
    signal b : std_logic_vector(3 downto 0) := "Z10U";
    type example_array_type is array(0 to 3) of std_logic_vector(3 downto 0);
    signal c : example_array_type := (others=>(others=>'0'));
    signal d : integer := 10;
    signal e : real := 4.5;
    signal f : string(1 to 5) := "hello";
begin

    delta_inst : entity work.delta_example;

    ex0_gen : if (TRUE) generate
        delta_inst : entity work.delta_example;
    end generate ex0_gen;

    ex1_gen : for i in 0 to 1 generate
        delta_inst : entity work.delta_example;
    end generate ex1_gen;

end architecture behav;