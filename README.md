# µP PRARAMBH - Dynamic Verilog Sandbox IDE

**µP PRARAMBH** is an industrial-themed, self-documenting Graphical User Interface (GUI) and simulation sandbox designed for Verilog education and rapid prototyping. Built with **Python (PyQt5)** and integrated directly with **eSim / Icarus Verilog (`iverilog`)**, it features real-time dynamic hardware introspection, AST signal parsing, and an on-the-fly testbench generation engine.

---

## 🛠️ Standard Port Naming Guide

To ensure your Verilog modules interface seamlessly with the Sandbox's visual tools (DIP switches, LED monitors, matrix displays, and interactive probes), follow these standard top-level port naming conventions in your Verilog header:

| Hardware Module | Expected Verilog Port Name | Size / Type | Description & Behavior |
| :--- | :--- | :--- | :--- |
| **Global Clock** | `clk` | `input` (1-bit) | Driven by the manual **PULSE** button or the **AUTO** clock engine on the top toolbar. |
| **Global Reset** | `rst` | `input` (1-bit) | Driven active-high (`1`) while pressing the **GLOBAL RST** button. |
| **Input Port A** | `port_a` | `input [7:0]` | Driven directly by the 8-bit DIP Switch bank **Port A** in the DIP & Hex I/O pane. |
| **Input Port B** | `port_b` | `input [7:0]` | Driven directly by the 8-bit DIP Switch bank **Port B** in the DIP & Hex I/O pane. |
| **Output Monitor** | `out_monitor` | `output [15:0]` | Read by the **16-bit Output Monitor** (LED row + Hex LCD display) in the DIP & Hex I/O pane. |
| **Pixel Matrix** | `pixel_matrix` | `output [255:0]` | Drives the **16x16 LED Matrix View**. Bit `0` corresponds to `(0,0)` and Bit `255` corresponds to `(15,15)`. |
| **Macro Keypad** | *Any input port* | `input` (Any width) | Detected automatically by AST parsing. Right-click any keycap to assign it to drive input ports such as `opcode`, `enable`, or `cmd`. |
| **Register Probe** | *Any internal variable* | `reg` / `wire` | Any internal module variable (e.g., `counter`, `state`, `accum`) is extracted automatically and populates the **Register Monitor** dropdowns. |

---

## 📋 Universal Top Module Template

Students can paste or write their designs using this standard module template. Any ports not required by a specific lab experiment can simply be left unused or assigned defaults.

```verilog
module top_sandbox (
    input clk,                      // Master clock
    input rst,                      // Active-high global reset
    input [7:0] port_a,             // DIP Switch Input Port A
    input [7:0] port_b,             // DIP Switch Input Port B
    input [7:0] opcode,             // Example input driven by Macro Keypad
    output reg [15:0] out_monitor,  // 16-Bit Output Monitor LEDs & Hex display
    output reg [255:0] pixel_matrix // 16x16 Pixel Matrix Display
);

    // --- Internal Registers (Inspectable via Register Monitor) ---
    reg [15:0] counter;
    reg [3:0]  state;

    // --- Student Logic ---
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter      <= 16'h0000;
            state        <= 4'd0;
            out_monitor  <= 16'h0000;
            pixel_matrix <= 256'b1;
        end else begin
            counter     <= counter + 1'b1;
            out_monitor <= port_a + port_b;
            pixel_matrix <= pixel_matrix << 1;
        end
    end

endmodule