module example_console (
  input wire clk,
  input wire rst
);

  reg [7:0] counter;

  always @(posedge clk or posedge rst) begin
      if (rst) begin
        counter <= 8'd0;
      end else begin
        counter <= (counter + 8'd1);
        $display("Clock Pulse: %d", counter);
      end
  end

  initial begin
      counter = 8'd0;
      $monitor("Counter changed to: (0x%h)", counter);
  end


endmodule
