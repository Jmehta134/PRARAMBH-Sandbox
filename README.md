# µP PRARAMBH Sandbox

A dynamic Verilog Interface built for debugging hardware modules to aid learning with the PRARAMBH Course. It seamlessly connects a PyQt5 user interface with eSim's backend i.e. Icarus Verilog  providing real-time register monitoring, auto-reset initialization, and interactive hardware testing.

## Prerequisites

1. **Python 3.8+** (Requires `PyQt5`)
2. **Icarus Verilog** (Sourced from FOSSEE eSim)
   * The system expects the `iverilog` and `vvp` executables at: `C:\FOSSEE\eSim\library\bin\iverilog\bin`
   * *Note: If your eSim installation is located elsewhere, update the toolchain paths inside `src/sim_engine.py`.*