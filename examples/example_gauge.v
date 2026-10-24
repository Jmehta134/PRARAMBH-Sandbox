module example_gauge_adc (
    input wire clk,
    output reg [11:0] gauge_out
);

    reg dir;
    parameter STEP = 12'h080;

    initial begin
        gauge_out = 12'h000;
        dir = 1'b0;
    end

    always @(posedge clk) begin
        gauge_out <= gauge_out + STEP;
    end

endmodule