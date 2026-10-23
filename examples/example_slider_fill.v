module example_slider_fill (
  input wire clk,
  input wire [15:0] adc_in,
  output reg [31:0] pixel_matrix = 256'b0
);

  integer i;

  always @(posedge clk) begin
      pixel_matrix <= 256'b0;
      for (i = 0; (i < 256); i = i + 1) begin
        if ((i <= adc_in[7:0])) begin
          pixel_matrix[i:i] <= 1'b1;
        end
      end
  end
  

endmodule
