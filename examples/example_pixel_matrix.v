// ============================================================================
// MODULE: example_pixel_matrix
// DESCRIPTION: Sweeps a vertical column of pixels horizontally across the matrix.
// ============================================================================
module example_pixel_matrix(
    input  wire         clk,
    output reg  [255:0] pixel_matrix = 256'b0
);
    reg [3:0] col_index = 4'd0;
    reg       dir       = 1'b0; // 0 = right, 1 = left

    integer row;

    always @(posedge clk) begin
        // Update horizontal column position (0 to 15)
        if (!dir) begin
            if (col_index == 4'd15)
                dir <= 1'b1; // Bounce left at right boundary
            else
                col_index <= col_index + 1'b1;
        end else begin
            if (col_index == 4'd0)
                dir <= 1'b0; // Bounce right at left boundary
            else
                col_index <= col_index - 1'b1;
        end

        // Light up all 16 rows at the active column coordinate
        pixel_matrix <= 256'b0;
        for (row = 0; row < 16; row = row + 1) begin
            pixel_matrix[(row * 16) + col_index] <= 1'b1;
        end
    end
endmodule