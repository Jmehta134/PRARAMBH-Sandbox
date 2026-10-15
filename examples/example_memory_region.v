// =============================================================================
// DEMO: "Hello World!" & Live Counter inside SCRATCHPAD (0x0200 - 128 Bytes)
// =============================================================================
module top (
    input wire clk,
    input wire rst,
    output reg [15:0] current_addr, // 16-bit address bus targeting 0x0200 region
    output reg [7:0] current_data
);

    // 128-Byte Scratchpad Array (Mapped to 0x0200)
    reg [7:0] scratchpad [0:127];

    reg [3:0] step;
    reg [7:0] counter;
    reg       msg_done;

    integer i;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            step <= 4'd0;
            counter <= 8'h00;
            msg_done <= 1'b0;
            current_addr <= 16'h0200;
            current_data <= 8'h00;

            // Zero-fill scratchpad array on reset
            for (i = 0; i < 128; i = i + 1) begin
                scratchpad[i] <= 8'h00;
            end
        end else begin
            if (!msg_done) begin
                // --- PHASE 1: Write "Hello World!" into SCRATCHPAD (0x0200 - 0x020B) ---
                case (step)
                    4'd0:  begin scratchpad[0]  <= 8'h48; current_addr <= 16'h0200; current_data <= 8'h48; end // 'H'
                    4'd1:  begin scratchpad[1]  <= 8'h65; current_addr <= 16'h0201; current_data <= 8'h65; end // 'e'
                    4'd2:  begin scratchpad[2]  <= 8'h6C; current_addr <= 16'h0202; current_data <= 8'h6C; end // 'l'
                    4'd3:  begin scratchpad[3]  <= 8'h6C; current_addr <= 16'h0203; current_data <= 8'h6C; end // 'l'
                    4'd4:  begin scratchpad[4]  <= 8'h6F; current_addr <= 16'h0204; current_data <= 8'h6F; end // 'o'
                    4'd5:  begin scratchpad[5]  <= 8'h20; current_addr <= 16'h0205; current_data <= 8'h20; end // ' '
                    4'd6:  begin scratchpad[6]  <= 8'h57; current_addr <= 16'h0206; current_data <= 8'h57; end // 'W'
                    4'd7:  begin scratchpad[7]  <= 8'h6F; current_addr <= 16'h0207; current_data <= 8'h6F; end // 'o'
                    4'd8:  begin scratchpad[8]  <= 8'h72; current_addr <= 16'h0208; current_data <= 8'h72; end // 'r'
                    4'd9:  begin scratchpad[9]  <= 8'h6C; current_addr <= 16'h0209; current_data <= 8'h6C; end // 'l'
                    4'd10: begin scratchpad[10] <= 8'h64; current_addr <= 16'h020A; current_data <= 8'h64; end // 'd'
                    4'd11: begin 
                        scratchpad[11] <= 8'h21; // '!'
                        current_addr <= 16'h020B; 
                        current_data <= 8'h21; 
                        msg_done <= 1'b1; 
                    end
                    default: msg_done <= 1'b1;
                endcase
                step <= step + 1'b1;

            end else begin
                // --- PHASE 2: Write live counter into SCRATCHPAD Address 0x020D ---
                counter <= counter + 1'b1;
                scratchpad[8'h0D] <= counter + 1'b1;

                current_addr <= 16'h020D;
                current_data <= counter + 1'b1;
            end
        end
    end

endmodule