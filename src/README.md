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
