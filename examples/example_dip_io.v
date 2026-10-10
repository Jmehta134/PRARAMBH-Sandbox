// ============================================================================
// MODULE: example_dip_hex_io
// DESCRIPTION: Maps 8-bit DIP switch inputs directly to 16-bit Hex displays.
// ============================================================================
module example_dip_hex_io(
    input  wire [7:0]  port_a,
    input  wire [7:0]  port_b,
    output wire [15:0] out_monitor
);
    // Concatenates Port A and Port B to drive the 16-bit hardware readout
    assign out_monitor = {port_a, port_b};
endmodule