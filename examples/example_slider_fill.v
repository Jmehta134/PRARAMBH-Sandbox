module example_slider_fill (
  input wire [15:0] adc_in
);

  initial begin
      $monitor("Slider changed to: (0x%h)", adc_in);
  end

endmodule
