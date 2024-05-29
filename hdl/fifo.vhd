library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

-- register based design. only intended for small sizes.
entity fifo is
    generic (
        DEPTH : natural range 2 to integer'high := 16; -- depth of fifo
        ALMOST_FULL_DEPTH : natural range 2 to DEPTH := DEPTH; -- threshold indicating fifo is nearly full
        WIDTH : natural := 32); -- data width of fifo
    port (
        clk : in std_logic; -- clock
        rst : in std_logic; -- synchronous assert-high reset
        empty : out std_logic; -- indicates the fifo is empty
        full : out std_logic; -- indicates the fifo is full
        almost_full : out std_logic; -- indicates the fifo is almost full, as dictated by the ALMOST_FULL_DEPTH generic
        valid : in std_logic; -- indicates the input data is valid
        ack : in std_logic; -- indicates the output data is acknowledged
        data_in : in std_logic_vector(WIDTH-1 downto 0); -- input data
        data_out : out std_logic_vector(WIDTH-1 downto 0)); -- output data
end entity fifo;

architecture rtl of fifo is
    subtype pointer_type is natural range 0 to DEPTH-1;
    subtype data_type is std_logic_vector(WIDTH-1 downto 0);
    type memory_type is array(pointer_type) of data_type;
    signal wr_ptr, rd_ptr, amt_cntr : pointer_type;
    signal memory : memory_type;
    signal n_z, n_f, i_z, i_f, n_af, i_af : std_logic;
    signal valid_data, ack_data : std_logic;
begin

    n_z <= '1' when amt_cntr=1 else '0';
    n_f <= '1' when amt_cntr=DEPTH-2 else '0';
    n_af <= '1' when amt_cntr=ALMOST_FULL_DEPTH-2 else '0';

    i_z <= '1' when amt_cntr=0 else '0';
    i_f <= '1' when amt_cntr=DEPTH-1 else '0';
    i_af <= '1' when amt_cntr=ALMOST_FULL_DEPTH-1 else '0';

    valid_data <= not i_f and valid;
    ack_data <= not i_z and ack;

    amt_proc : process (clk)
    begin
        if rising_edge(clk) then
            if rst/='0' then
                amt_cntr <= 0;
            else
                if valid_data and not ack_data then
                    amt_cntr <= amt_cntr+1;
                elsif not valid_data and ack_data then
                    amt_cntr <= amt_cntr-1;
                end if;
            end if;
        end if;
    end process amt_proc;

    status_proc : process (clk)
    begin
        if rising_edge(clk) then
            if rst/='0' then
                full <= i_f;
                empty <= i_z;
                almost_full <= i_af;
            else
                if valid_data and not ack_data and i_z then
                    empty <= '0';
                elsif not valid_data and ack_data and n_z then
                    empty <= '1';
                end if;
                if valid_data and not ack_data and n_f then
                    full <= '1';
                elsif not valid_data and ack_data and i_f then
                    full <= '0';
                end if;
                if valid_data and not ack_data and n_af then
                    almost_full <= '1';
                elsif not valid_data and ack_data and i_f then
                    almost_full <= '0';
                end if;
            end if;
        end if;
    end process status_proc;

    ptr_proc : process (clk)
    begin
        if rising_edge(clk) then
            if rst/='0' then
                wr_ptr <= 0;
                rd_ptr <= 0;
            else
                if valid_data then
                    if wr_ptr=DEPTH-1 then
                        wr_ptr <= 0;
                    else
                        wr_ptr <= wr_ptr+1;
                    end if;
                end if;
                if ack_data then
                    if rd_ptr=DEPTH-1 then
                        rd_ptr <= 0;
                    else
                        rd_ptr <= rd_ptr+1;
                    end if;
                end if;
            end if;
        end if;
    end process ptr_proc;

    memory_proc : process (clk)
    begin
        if rising_edge(clk) then
            memory(wr_ptr) <= data_in;
        end if;
    end process memory_proc;

    data_out <= memory(rd_ptr);

end architecture rtl;