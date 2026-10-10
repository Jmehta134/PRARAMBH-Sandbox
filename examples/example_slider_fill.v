// ============================================================================
// MODULE: example_slider_fill
// DESCRIPTION: Progressive LED fill level controlled by the Slider ADC input.
// INSTRUCTIONS: 
// 1. Select the target input port as "adc_in".
// 2. Set the clock to auto.
// ============================================================================
module example_slider_fill(
    input  wire         clk,
    input  wire  [15:0] adc_in,        // Expecting range 0x0000 (0) to 0x00FF (255)
    output reg   [255:0] pixel_matrix = 256'b0
);
    integer i;

    always @(posedge clk) begin
        pixel_matrix <= 256'b0;
        
        // Turn on pixels proportional to the slider position
        for (i = 0; i < 256; i = i + 1) begin
            if (i <= adc_in[7:0]) begin
                pixel_matrix[i] <= 1'b1;
            end
        end
    end
endmodule