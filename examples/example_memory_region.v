module top (
  input wire clk,
  input wire rst,
  output reg [15:0] current_addr,
  output reg [7:0] current_data
);

  // Corrected memory map declaration: 128 addresses, 8-bits wide each
  reg [7:0] scratchpad [0:127];
  reg [3:0] step;
  reg msg_done;
  integer i;

  always @(posedge clk or posedge rst) begin
      if (rst) begin
        step <= 4'd0;
        msg_done <= 1'b0;
        current_addr <= 16'h0200;
        current_data <= 8'h00;
        
        // Clean array indexing without slice syntax
        for (i = 0; i < 128; i = i + 1) begin
          scratchpad[i] <= 8'h00;
        end
      end else begin
        if (!msg_done) begin
          case (step)
              4'd0: begin
                scratchpad[0] <= 8'h48; // 'H'
                current_addr <= 16'h0200;
                current_data <= 8'h48;
              end
              4'd1: begin
                scratchpad[1] <= 8'h65; // 'e'
                current_addr <= 16'h0201;
                current_data <= 8'h65;
              end
              4'd2: begin
                scratchpad[2] <= 8'h6C; // 'l'
                current_addr <= 16'h0202;
                current_data <= 8'h6C;
              end
              4'd3: begin
                scratchpad[3] <= 8'h6C; // 'l'
                current_addr <= 16'h0203;
                current_data <= 8'h6C;
              end
              4'd4: begin
                scratchpad[4] <= 8'h6F; // 'o'
                current_addr <= 16'h0204;
                current_data <= 8'h6F;
              end
              4'd5: begin
                msg_done <= 1'b1;
              end
              default: begin
                msg_done <= 1'b1;
              end
          endcase
          
          if (!msg_done) begin
              step <= step + 4'd1;
          end
        end
      end
  end

endmodule