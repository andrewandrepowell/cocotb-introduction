library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity simple_adder is
    generic (
        WIDTH : natural := 32); -- width of adder
    port (
        clk: in std_logic; -- clock
        rst: in std_logic; -- synchronous assert-high reset
        aData: in std_logic_vector(WIDTH-1 downto 0); -- a input data
        bData: in std_logic_vector(WIDTH-1 downto 0); -- b input data
        abValid: in std_logic; -- Indicates a and b input data are valid
        rData : out std_logic_vector(WIDTH-1 downto 0); -- result output data
        rValid: out std_logic); -- Indicates the result data is valid
end entity simple_adder;

architecture rtl of simple_adder is
begin

    add_proc : process (clk)
    begin
        if rising_edge(clk) then
            if rst/='0' then
                rValid <= '0';
            else
                rValid <= abValid;
            end if;
            rData <= std_logic_vector(unsigned(aData) + unsigned(bData));
        end if;
    end process add_proc;

end architecture rtl;
