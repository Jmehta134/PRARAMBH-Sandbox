module example_dip_hex_io (
  input wire [7:0] port_a,
  input wire [7:0] port_b,
  output wire [15:0] out_monitor
);

  assign out_monitor = {port_a, port_b};

endmodule
