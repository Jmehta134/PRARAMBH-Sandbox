module top_sandbox (
    input clk,                      // Master clock
    input rst,                      // Active-high global reset
    input [7:0] port_a,             // DIP Switch Input Port A
    input [7:0] port_b,             // DIP Switch Input Port B
    input [7:0] opcode,             // Example input driven by Macro Keypad
    output reg [15:0] out_monitor,  // 16-Bit Output Monitor LEDs & Hex display
    output reg [255:0] pixel_matrix // 16x16 Pixel Matrix Display
);

    // --- Internal Registers (Inspectable via Register Monitor) ---
    reg [15:0] counter;
    reg [3:0]  state;

    // --- Student Logic ---
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter      <= 16'h0000;
            state        <= 4'd0;
            out_monitor  <= 16'h0000;
            pixel_matrix <= 256'b1;
        end else begin
            counter     <= counter + 1'b1;
            out_monitor <= port_a + port_b;
            pixel_matrix <= pixel_matrix << 1;
        end
    end

endmodule