module example_pixel_matrix (
  input wire clk,
  output reg [31:0] pixel_matrix = 256'b0
);

  reg [3:0] col_index = 4'd0;
  reg dir = 1'b0;
  integer row;

  always @(posedge clk) begin
      if (!(dir)) begin
        if ((col_index == 4'd15)) begin
          dir <= 1'b1;
        end else begin
          col_index <= (col_index + 1'b1);
        end
      end else begin
        if ((col_index == 4'd0)) begin
          dir <= 1'b0;
        end else begin
          col_index <= (col_index - 1'b1);
        end
      end
      pixel_matrix <= 256'b0;
      for (row = 0; (row < 16); row = row + 1) begin
        pixel_matrix[(row * 16 + col_index):(row * 16 + col_index)] <= 1'b1;
      end
  end
  

endmodule
