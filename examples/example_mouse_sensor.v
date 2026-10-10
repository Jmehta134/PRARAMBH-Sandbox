// ============================================================================
// MODULE: example_mouse_sensor
// DESCRIPTION: Tracks mouse direction inputs to move a single pixel in 2D space.
// INSTRUCTIONS: 
// 1. Open the MOUSE DIR and PICEL MATRIX pane.
// 2. switch the CLOCK ENGINE mode from "MANUAL" to "AUTO" ( Select frequency 16Hz ).
// ============================================================================
module example_mouse_sensor(
    input  wire         clk,
    input  wire  [7:0]  mouse_dir,
    output reg   [255:0] pixel_matrix = 256'b1 // Starts at top-left (0,0)
);
    reg [3:0] pos_x = 4'd0;
    reg [3:0] pos_y = 4'd0;

    always @(posedge clk) begin
        // Move Up (Bit 0, 1, 7)
        if ((mouse_dir[0] || mouse_dir[1] || mouse_dir[7]) && pos_y > 0)
            pos_y <= pos_y - 1'b1;
            
        // Move Down (Bit 3, 4, 5)
        if ((mouse_dir[3] || mouse_dir[4] || mouse_dir[5]) && pos_y < 15)
            pos_y <= pos_y + 1'b1;

        // Move Left (Bit 5, 6, 7)
        if ((mouse_dir[5] || mouse_dir[6] || mouse_dir[7]) && pos_x > 0)
            pos_x <= pos_x - 1'b1;

        // Move Right (Bit 1, 2, 3)
        if ((mouse_dir[1] || mouse_dir[2] || mouse_dir[3]) && pos_x < 15)
            pos_x <= pos_x + 1'b1;

        // Update single pixel at (pos_x, pos_y)
        pixel_matrix <= (256'b1 << ((pos_y * 16) + pos_x));
    end
endmodule