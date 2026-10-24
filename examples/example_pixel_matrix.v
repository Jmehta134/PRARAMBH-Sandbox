module row_flasher (
    input  wire clk,
    output reg [255:0] pixel_matrix = 256'b0
);

    always @(posedge clk) begin
      pixel_matrix[15:0]    <= ~pixel_matrix[15:0];    // Toggle Row 0  (Top)
      pixel_matrix[127:112] <= ~pixel_matrix[127:112]; // Toggle Row 7  (Middle)
      pixel_matrix[255:240] <= ~pixel_matrix[255:240]; // Toggle Row 15 (Bottom)
    end
endmodule