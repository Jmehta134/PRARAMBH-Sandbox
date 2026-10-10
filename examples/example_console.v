// ============================================================================
// MODULE: example_console
// DESCRIPTION: Demonstrates console output using $display and $monitor.
// ============================================================================
module example_console(
    input wire clk
);
    reg [7:0] counter = 8'd0;

    // $monitor triggers automatically whenever counter changes value
    initial begin
        $monitor("Counter changed to: %d (0x%h)", counter, counter);
    end

    // $display triggers synchronously on every clock pulse
    always @(posedge clk) begin
        counter <= counter + 1'b1;
        $display("Clock Pulse: %d", counter);
    end
endmodule