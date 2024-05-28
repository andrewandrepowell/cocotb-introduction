library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity simple_adder is
    generic (
        WIDTH : natural := 32);
    port (
        clk: in std_logic;
        rst: in std_logic;
        aData: in std_logic_vector(WIDTH-1 downto 0);
        bData: in std_logic_vector(WIDTH-1 downto 0);
        abValid: in std_logic;
        rData : out std_logic_vector(WIDTH-1 downto 0);
        rValid: out std_logic);
end entity simple_adder;

architecture rtl of simple_adder is
begin

    add_proc : process (clk)
    begin
        if (rising_edge(clk)) then
            if (rst/='0') then
                rValid <= '0';
            else
                rValid <= abValid;
            end if;
            rData <= std_logic_vector(unsigned(aData) + unsigned(bData));
        end if;
    end process add_proc;

end architecture rtl;
