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
        if (!dir) begin
            if (gauge_out >= (12'hFFF - STEP)) begin
                gauge_out <= 12'hFFF;
                dir <= 1'b1;
            end else begin
                gauge_out <= gauge_out + STEP;
            end
        end else begin
            if (gauge_out <= STEP) begin
                gauge_out <= 12'h000;
                dir <= 1'b0;
            end else begin
                gauge_out <= gauge_out - STEP;
            end
        end
    end

endmodule