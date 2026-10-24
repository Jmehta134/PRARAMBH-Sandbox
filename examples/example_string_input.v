module example_string_input (
  input wire [127:0] string_in
);

  initial begin
      $monitor("String: '%s' | Packed Hex: 0x%h", string_in, string_in);
  end

endmodule
