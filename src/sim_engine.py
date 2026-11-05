import sys
import os
import platform
import stat
import re
import time
from PyQt5.QtCore import QObject, QProcess, pyqtSignal
from PyQt5.QtWidgets import QApplication

class SimulationEngine(QObject):
    hardware_updated = pyqtSignal(dict)
    log_message = pyqtSignal(str, str)
    parsed_design = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        
        self.input_map = {}
        self.verilog_signals = []
        self.ui_signals = []
        self.stdout_buffer = ""
        self._is_compiling = False
        self.memory_updates = {}

        if getattr(sys, 'frozen', False):
            root_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            src_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.abspath(os.path.join(src_dir, ".."))

        system_os = platform.system().lower()

        if system_os == "windows":
            self.iverilog_path = os.path.join(root_dir, "bin", "windows", "bin", "iverilog.exe")
            self.vvp_path = os.path.join(root_dir, "bin", "windows", "bin", "vvp.exe")
        else:
            self.iverilog_path = os.path.join(root_dir, "bin", "linux", "bin", "iverilog")
            self.vvp_path = os.path.join(root_dir, "bin", "linux", "bin", "vvp")
            for binary in [self.iverilog_path, self.vvp_path]:
                if os.path.exists(binary):
                    st = os.stat(binary)
                    os.chmod(binary, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def cleanup_previous_process(self):
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)
        self.stdout_buffer = ""
        self.memory_updates.clear()

    def parse_verilog_content(self, verilog_code):
        clean_code = re.sub(r'//.*', '', verilog_code)
        clean_code = re.sub(r'/\*.*?\*/', '', clean_code, flags=re.DOTALL)
        
        mod_match = re.search(r'module\s+(\w+)', clean_code)
        module_name = mod_match.group(1) if mod_match else "top"
        
        inputs = re.findall(r'\binput\s+(?:wire\s+|reg\s+)?(?:\[.*?\]\s+)?(\w+)', clean_code)
        outputs = re.findall(r'\boutput\s+(?:wire\s+|reg\s+)?(?:\[.*?\]\s+)?(\w+)', clean_code)
        raw_internals = re.findall(r'\b(?:reg|wire|integer)\s+(?:\[.*?\]\s+)?(\w+)\s*[;,]', clean_code)
        
        internals = [sig for sig in set(raw_internals) if sig not in inputs and sig not in outputs]
        self.input_map = {name: idx for idx, name in enumerate(inputs)}
        
        return {
            "module_name": module_name,
            "inputs": inputs,
            "outputs": outputs,
            "internals": internals
        }

    def _find_matching_signal(self, all_sigs, candidates):
        """Case-insensitive search for memory control signals."""
        sig_map = {s.lower(): s for s in all_sigs}
        for cand in candidates:
            if cand.lower() in sig_map:
                return sig_map[cand.lower()]
        return None

    def generate_embedded_testbench(self, parsed, verilog_code):
        tb = "// Auto-generated Dynamic Testbench\n"
        tb += verilog_code + "\n\n"
        tb += "module auto_sandbox_tb;\n"
        
        for inp in parsed['inputs']:
            if inp in ['clk', 'rst']:
                tb += f"    reg {inp} = 0;\n"
            else:
                tb += f"    reg [511:0] {inp} = 0;\n"
            
        for out in parsed['outputs']:
            tb += f"    wire [511:0] {out};\n"
            
        tb += f"\n    {parsed['module_name']} dut (\n"
        ports = [f".{p}({p})" for p in parsed['inputs'] + parsed['outputs']]
        tb += "        " + ",\n        ".join(ports) + "\n    );\n\n"
        
        self.verilog_signals = parsed['inputs'] + parsed['outputs'] + [f"dut.{i}" for i in parsed['internals']]
        self.ui_signals = parsed['inputs'] + parsed['outputs'] + parsed['internals']
        
        tb += "    integer cmd_id;\n"
        tb += "    integer cmd_val;\n\n"

        # --- Flexible Memory Spy Injection ---
        all_sigs = parsed['inputs'] + parsed['outputs'] + parsed['internals']
        clk_sig = self._find_matching_signal(parsed['inputs'], ['clk', 'clock'])
        we_sig = self._find_matching_signal(all_sigs, ['we', 'write_en', 'wen', 'write', 'w_en'])
        addr_sig = self._find_matching_signal(all_sigs, ['addr', 'address', 'radr', 'wadr'])
        wdata_sig = self._find_matching_signal(all_sigs, ['wdata', 'data_in', 'din', 'data', 'writedata'])

        if clk_sig and we_sig and addr_sig and wdata_sig:
            def get_sig_path(sig):
                return f"dut.{sig}" if sig in parsed['internals'] else sig

            tb += "    // Embedded UI Memory Controller Spy\n"
            tb += f"    always @(posedge {get_sig_path(clk_sig)}) begin\n"
            tb += "        #1;\n"  # Settling delay after clock edge ensures proper signal reads
            tb += f"        if ({get_sig_path(we_sig)}) begin\n"
            tb += f"            $display(\"MEM_WRITE:%0d:%0d\", {get_sig_path(addr_sig)}, {get_sig_path(wdata_sig)});\n"
            tb += "            $fflush(32'h8000_0001);\n"
            tb += "        end\n"
            tb += "    end\n\n"
        
        tb += "    initial begin\n"
        if 'clk' in parsed['inputs']:
            tb += "        clk = 0;\n"
        if 'rst' in parsed['inputs']:
            tb += "        rst = 1; #5; clk = 1; #5; clk = 0; #5; rst = 0; #5;\n"
        else:
            tb += "        #20;\n"
            
        tb += '        $display("TESTBENCH_READY");\n'
        
        format_str = "UPDATE:" + ":".join(["%h" for _ in self.verilog_signals])
        vars_str = ", ".join(self.verilog_signals)
        if self.verilog_signals:
            tb += f'        $display("{format_str}", {vars_str});\n'
            
        tb += "        $fflush(32'h8000_0001);\n"
        tb += "        forever begin\n"
        tb += '            if ($fscanf(32\'h8000_0000, "%d %d", cmd_id, cmd_val) == 2) begin\n'
        
        for inp, idx in self.input_map.items():
            if inp == 'clk':
                tb += f'                if (cmd_id == {idx}) begin clk = 1; #5; clk = 0; #5; end\n'
            else:
                tb += f'                if (cmd_id == {idx}) {inp} = cmd_val;\n'
                
        tb += '                #1;\n'
        if self.verilog_signals:
            tb += f'                $display("{format_str}", {vars_str});\n'
        tb += "                $fflush(32'h8000_0001);\n"
        tb += "            end\n"
        tb += "        end\n"
        tb += "    end\n"
        tb += "endmodule\n"
        
        with open("auto_sandbox_tb.v", "w", encoding="utf-8") as f:
            f.write(tb)

    def compile_and_run(self, file_path):
        verilog_code = ""
        for attempt in range(15):
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        verilog_code = f.read()
                    if verilog_code.strip():
                        break
                except Exception:
                    pass
            QApplication.processEvents()
            time.sleep(0.1)
            
        if not verilog_code.strip():
            self.log_message.emit(f"Engine Error: Could not read {file_path} or file is empty.", "ERROR")
            return
            
        self.compile_verilog_string(verilog_code)
    
    def compile_verilog_string(self, verilog_code):
        if getattr(self, '_is_compiling', False):
            return
        self._is_compiling = True

        try:
            self.cleanup_previous_process()

            if not verilog_code or not verilog_code.strip():
                self.log_message.emit("Canvas is empty. No hardware logic generated to compile.", "WARN")
                return

            parsed = self.parse_verilog_content(verilog_code)
            self.parsed_design.emit(parsed)
            
            self.generate_embedded_testbench(parsed, verilog_code)
            
            self.log_message.emit(f"Parsed and prepared inline harness for module: '{parsed['module_name']}'", "INFO")
            
            compile_proc = QProcess()
            compile_proc.start(self.iverilog_path, ["-g2012", "-o", "sim_build.vvp", "auto_sandbox_tb.v"])
            compile_proc.waitForFinished(5000)
            
            if compile_proc.exitCode() != 0:
                err = compile_proc.readAllStandardError().data().decode().strip()
                self.log_message.emit(f"Compilation Error:\n{err}", "ERROR")
                return
                
            self.process.start(self.vvp_path, ["sim_build.vvp"])

        finally:
            self._is_compiling = False

    def send_command(self, signal_name, value):
        if self.process.state() == QProcess.Running:
            if signal_name in self.input_map:
                cmd_id = self.input_map[signal_name]
                self.process.write(f"{cmd_id} {value}\n".encode())
                self.process.waitForBytesWritten(100)

    def read_stdout(self):
        raw_bytes = self.process.readAllStandardOutput().data()
        self.stdout_buffer += raw_bytes.decode('utf-8', errors='ignore')
        
        while '\n' in self.stdout_buffer:
            line, self.stdout_buffer = self.stdout_buffer.split('\n', 1)
            line = line.strip()
            if not line:
                continue
            
            if line == "TESTBENCH_READY":
                self.log_message.emit("Simulation Engine active. Hardware synced.", "SUCCESS")
                # Fix 1: Zero-initialize BOTH 64-byte RAM and 128-byte ROM maps immediately on startup
                self.hardware_updated.emit({
                    'ram': {i: 0 for i in range(64)},
                    'rom': {i: 0 for i in range(128)}
                })

            elif line.startswith("MEM_WRITE:"):
                parts = line.split(':')
                try:
                    addr = int(parts[1].strip())
                    val = int(parts[2].strip())
                    self.memory_updates[addr] = val
                    # Fix 2: Emit a debug message so you visibly see intercepted writes in the console
                    # self.log_message.emit(f"Spy Intercepted Write: Addr 0x{addr:04X} = 0x{val:02X}", "INFO")
                except ValueError:
                    pass
                    
            elif line.startswith("UPDATE:"):
                parts = line.split(':')[1:]
                state_dict = {}
                for i, sig in enumerate(self.ui_signals):
                    if i < len(parts) and parts[i]:
                        try:
                            val = int(parts[i], 16)
                        except ValueError:
                            val = 0xEEEE 
                            
                        state_dict[sig] = val
                        if not sig.startswith("dut."):
                            state_dict[f"dut.{sig}"] = val 
                            
                # Fix 3: Safely route memory updates to RAM or ROM based on the absolute address
                if self.memory_updates:
                    ram_up = {}
                    rom_up = {}
                    for a, v in self.memory_updates.items():
                        if 0 <= a < 64:
                            ram_up[a] = v
                        elif 512 <= a < 512 + 128:  # 0x0200 = 512 (ROM start address)
                            rom_up[a - 512] = v     # Adjust to relative ROM offset for the UI
                        else:
                            ram_up[a] = v           # Fallback
                            
                    if ram_up: state_dict['ram'] = ram_up
                    if rom_up: state_dict['rom'] = rom_up
                    self.memory_updates.clear()
                            
                self.hardware_updated.emit(state_dict)
            else:
                self.log_message.emit(f"[Verilog] {line}", "INFO")

    def read_stderr(self):
        err = self.process.readAllStandardError().data().decode().strip()
        if err:
            self.log_message.emit(f"Engine Warning: {err}", "WARN")