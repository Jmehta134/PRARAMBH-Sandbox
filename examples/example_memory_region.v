module memory_auto_demo (
    input  wire       clk,
    input  wire       rst,
    
    // Outputs monitored by the Python memory spy
    output reg        we,
    output reg  [5:0] addr,
    output reg  [7:0] wdata,
    output reg  [7:0] rdata
);

    reg [7:0] ram [0:63];

    initial begin
        we    = 1'b1;
        addr  = 6'd0;
        wdata = 8'h10;
    end

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            addr  <= 6'd0;
            wdata <= 8'h10;
            we    <= 1'b1;
        end else begin
            we    <= 1'b1;
            addr  <= addr + 1'b1;   // Automatically step through addresses
            wdata <= wdata + 1'b1;   // Automatically increment data values

            // Write to RAM
            if (we) begin
                ram[addr] <= wdata;
            end
            
            rdata <= ram[addr];
        end
    end

endmodule