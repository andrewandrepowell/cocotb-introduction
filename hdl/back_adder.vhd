library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity back_adder is
    generic (
        WIDTH : natural := 32); -- width of adder
    port (
        clk: in std_logic; -- clock
        rst: in std_logic; -- synchronous assert-high reset
        a_data: in std_logic_vector(WIDTH-1 downto 0); -- a input data
        b_data: in std_logic_vector(WIDTH-1 downto 0); -- b input data
        ab_valid: in std_logic; -- Indicates a and b input data are valid
        ab_ready: out std_logic; -- Indicates the adder is ready for more data
        r_data : out std_logic_vector(WIDTH-1 downto 0); -- result output data
        r_valid: out std_logic;  -- Indicates the result data is valid
        r_ready: in std_logic); -- Indicates the connected interface is ready for the data
end entity back_adder;

architecture rtl of back_adder is
    subtype a_range is natural range WIDTH-1 downto 0;
    subtype b_range is natural range 2*WIDTH-1 downto WIDTH;
    subtype ab_range is natural range 2*WIDTH-1 downto 0;
    signal ab_empty, ab_full, ab_ack, r_almost_full, r_empty, adder_valid : std_logic;
    signal ab_word, adder_word : std_logic_vector(ab_range);
    signal adder_data : std_logic_vector(WIDTH-1 downto 0);
begin

    ab_ready <= not ab_full;
    ab_word(a_range) <= a_data;
    ab_word(b_range) <= b_data;

    ab_fifo_inst : entity work.fifo
        generic map (
            DEPTH => 3,
            ALMOST_FULL_DEPTH => 3,
            WIDTH => 2*WIDTH)
        port map (
            clk => clk,
            rst => rst,
            empty => ab_empty,
            full => ab_full,
            almost_full => open,
            valid => ab_valid and ab_ready,
            ack => ab_ack,
            data_in => ab_word,
            data_out => adder_word);

    ab_ack <= not ab_empty and not r_almost_full;

    adder_inst : entity work.simple_adder
        generic map (
            WIDTH => WIDTH)
        port map (
            clk => clk,
            rst => rst,
            aData => adder_word(a_range),
            bData => adder_word(b_range),
            abValid => ab_ack,
            rData => adder_data,
            rValid => adder_valid);

    r_fifo_inst : entity work.fifo
        generic map (
            DEPTH => 4,
            ALMOST_FULL_DEPTH => 3,
            WIDTH => WIDTH)
        port map (
            clk => clk,
            rst => rst,
            empty => r_empty,
            full => open,
            almost_full => r_almost_full,
            valid => adder_valid,
            ack => r_ready and r_valid,
            data_in => adder_data,
            data_out => r_data);

    r_valid <= not r_empty;

end architecture rtl;