// ============================================================================
// MODULE: example_gauge_adc
// DESCRIPTION: Smooth, continuous 12-bit triangular sweep (0x000 to 0xFFF).
//
// QUICK START INSTRUCTIONS FOR THE SANDBOX:
// 1. In one of the split workspace panes, select "Gauge ADC Out".
// 2. Set the "TARGET SIGNAL / REGISTER" dropdown in that pane to "gauge_out".
// 3. In the top header bar, switch the CLOCK ENGINE mode from "MANUAL" to "AUTO".
// 4. Set the clock frequency dropdown to "1 kHz (Fast)" to see the needle sweep!
// ============================================================================
module example_gauge_adc(
    input  wire        clk,
    output reg  [11:0] gauge_out = 12'h000
);
    // Direction Flag: 0 = Sweeping Up, 1 = Sweeping Down
    reg dir = 1'b0;

    // 12-Bit Increment Step Size (128 decimal)
    parameter STEP = 12'h080;

    always @(posedge clk) begin
        if (!dir) begin
            // Sweeping Up towards 12-Bit Max (0xFFF)
            if (gauge_out >= (12'hFFF - STEP)) begin
                gauge_out <= 12'hFFF;
                dir       <= 1'b1; // Reached top, reverse direction
            end else begin
                gauge_out <= gauge_out + STEP;
            end
        end else begin
            // Sweeping Down towards 12-Bit Min (0x000)
            if (gauge_out <= STEP) begin
                gauge_out <= 12'h000;
                dir       <= 1'b0; // Reached bottom, reverse direction
            end else begin
                gauge_out <= gauge_out - STEP;
            end
        end
    end
endmodule