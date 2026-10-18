// ============================================================================
// MODULE: example_mouse_sensor
// DESCRIPTION: Tracks mouse direction inputs to move a single pixel in 2D space.
// ============================================================================
module example_mouse_sensor(
    input  wire        clk,
    input  wire  [7:0] mouse_dir,
    output reg [255:0] pixel_matrix = 256'b1 
);
    reg [3:0] pos_x = 4'd0;
    reg [3:0] pos_y = 4'd0;

    // Flattening the logic into dedicated wires for a cleaner parser AST
    wire move_up    = mouse_dir[0] | mouse_dir[1] | mouse_dir[7];
    wire move_down  = mouse_dir[3] | mouse_dir[4] | mouse_dir[5];
    wire move_left  = mouse_dir[5] | mouse_dir[6] | mouse_dir[7];
    wire move_right = mouse_dir[1] | mouse_dir[2] | mouse_dir[3];

    always @(posedge clk) begin
        if (move_up && (pos_y > 4'd0)) begin
            pos_y <= pos_y - 4'd1;
        end
            
        if (move_down && (pos_y < 4'd15)) begin
            pos_y <= pos_y + 4'd1;
        end

        if (move_left && (pos_x > 4'd0)) begin
            pos_x <= pos_x - 4'd1;
        end

        if (move_right && (pos_x < 4'd15)) begin
            pos_x <= pos_x + 4'd1;
        end

        // Concatenation replaces the need for (pos_y * 16) + pos_x
        pixel_matrix <= (256'b1 << {pos_y, pos_x});
    end
endmodule