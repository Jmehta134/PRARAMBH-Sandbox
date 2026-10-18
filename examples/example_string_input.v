module example_string_input (
  input wire clk,
  input wire [7:0] string_in
);

  reg [7:0] prev_string = 128'd0;

  always @(posedge clk) begin
      if (string_in != prev_string) begin
        $display("[STRING INJECTED] String: '%s' | Packed Hex: 0x%h", string_in, string_in);
        prev_string <= string_in;
      end
  end


endmodule
