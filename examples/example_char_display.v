// ============================================================================
// MODULE: example_char_display
// DESCRIPTION: Clears the LCD display first, then streams ASCII characters.
// ============================================================================
module example_char_display(
    input  wire       clk,
    output reg  [7:0] lcd_ir = 8'h00,
    output reg  [7:0] lcd_dr = 8'h00,
    output reg        lcd_rs = 1'b0, // Start in Instruction Mode (RS=0)
    output reg        lcd_en = 1'b0
);
    reg [1:0] state  = 2'd0;

    always @(posedge clk) begin
        lcd_en <= ~lcd_en; // Pulse Enable on alternating cycles

        if (lcd_en) begin
            case (state)
                // STATE 0: Send Clear Display Command (RS = 0, IR = 0x01)
                2'd0: begin
                    lcd_rs <= 1'b0; // Instruction Mode
                    lcd_ir <= 8'h01; // 0x01 = Clear Display & Reset Cursor
                    state  <= 2'd1;
                end

                // STATE 1: Switch to Data Mode & Set Initial Character 'A' (0x41)
                2'd1: begin
                    lcd_rs <= 1'b1; // Data Mode
                    lcd_dr <= 8'h41; // ASCII 'A'
                    state  <= 2'd2;
                end

                // STATE 2: Continuously Stream ASCII Characters
                2'd2: begin
                    if (lcd_dr >= 8'h7A) // 'z'
                        lcd_dr <= 8'h41; // Reset to 'A'
                    else
                        lcd_dr <= lcd_dr + 1'b1;
                end
            endcase
        end
    end
endmodule