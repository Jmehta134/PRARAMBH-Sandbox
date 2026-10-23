module example_char_display (
  input wire clk,
  output reg [7:0] lcd_ir = 8'h00,
  output reg [7:0] lcd_dr = 8'h00,
  output reg lcd_rs = 1'b0,
  output reg lcd_en = 1'b0
);

  reg [1:0] state = 2'd0;

  always @(posedge clk) begin
      lcd_en <= !(lcd_en);
      if (lcd_en) begin
        case (state)
            2'd0: begin
            lcd_rs <= 1'b0;
            lcd_ir <= 8'h01;
            state <= 2'd1;
            end
            2'd1: begin
            lcd_rs <= 1'b1;
            lcd_dr <= 8'h41;
            state <= 2'd2;
            end
            2'd2: begin
            if ((lcd_dr >= 8'h7A)) begin
              lcd_dr <= 8'h41;
            end else begin
              lcd_dr <= (lcd_dr + 1'b1);
            end
            end
        endcase
      end
  end
  

endmodule
