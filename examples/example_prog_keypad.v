// ============================================================================
// MODULE: example_keypad
// DESCRIPTION: Captures 4 macro key presses and outputs logs to the console.
//
// INSTRUCTIONS FOR BINDING KEYPAD BUTTONS IN THE IDE:
// 1. Load this file in the Sandbox IDE.
// 2. Select "Programmable Keypad" in one of the split workspace panes.
// 3. Set the "TARGET INPUT PORT" dropdown to "key_in".
// 4. Click any of the first 4 buttons (Key 0, Key 1, Key 2, Key 3) on the 
//    keypad interface to inject values into the key_in [3:0] register!
// ============================================================================
module example_keypad(
    input wire       clk,
    input wire [3:0] key_in
);
    reg [3:0] prev_key = 4'd0;

    always @(posedge clk) begin
        if (key_in != prev_key && key_in != 4'd0) begin
            case (key_in)
                4'b0001: $display("[KEYPAD] Button 1 Pressed! (Val: 1)");
                4'b0010: $display("[KEYPAD] Button 2 Pressed! (Val: 2)");
                4'b0011: $display("[KEYPAD] Button 3 Pressed! (Val: 4)");
                4'b0100: $display("[KEYPAD] Button 4 Pressed! (Val: 8)");
                default: $display("[KEYPAD] Some Key Pressed! (Val: %d)", key_in);
            endcase
        end
        prev_key <= key_in;
    end
endmodule   