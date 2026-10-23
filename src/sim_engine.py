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
        self._is_compiling = False  # Engine lock to prevent double-triggering

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

        print(f"[DEBUG] Resolved iverilog path: {self.iverilog_path}")

    def cleanup_previous_process(self):
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)
        self.stdout_buffer = ""

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
        
        self.verilog_signals = parsed['outputs'] + [f"dut.{i}" for i in parsed['internals']]
        self.ui_signals = parsed['outputs'] + parsed['internals']
        
        tb += "    integer cmd_id;\n"
        tb += "    integer cmd_val;\n\n"
        
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
        """Fallback wrapper for main.py to prevent AttributeErrors."""
        verilog_code = ""
        
        # Robust read loop to handle OneDrive file locks
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
            
        # Pass the successfully read string to the new compiler
        self.compile_verilog_string(verilog_code)
    
    def compile_verilog_string(self, verilog_code):
        # 1. Debounce rapid double-triggers from the UI
        if getattr(self, '_is_compiling', False):
            return
        self._is_compiling = True

        try:
            self.cleanup_previous_process()

            # 2. Immediately check if we have valid code from memory
            if not verilog_code or not verilog_code.strip():
                self.log_message.emit("Canvas is empty. No hardware logic generated to compile.", "WARN")
                return

            parsed = self.parse_verilog_content(verilog_code)
            self.parsed_design.emit(parsed)
            
            # generate_embedded_testbench handles writing the string to auto_sandbox_tb.v
            self.generate_embedded_testbench(parsed, verilog_code)
            
            self.log_message.emit(f"Parsed and prepared inline harness for module: '{parsed['module_name']}'", "INFO")
            
            # 3. Synchronous compilation pass using the generated local file
            compile_proc = QProcess()
            compile_proc.start(self.iverilog_path, ["-g2012", "-o", "sim_build.vvp", "auto_sandbox_tb.v"])
            compile_proc.waitForFinished(5000)
            
            if compile_proc.exitCode() != 0:
                err = compile_proc.readAllStandardError().data().decode().strip()
                self.log_message.emit(f"Compilation Error:\n{err}", "ERROR")
                return
                
            # 4. Launch simulation backend
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
                            
                self.hardware_updated.emit(state_dict)
            else:
                self.log_message.emit(f"[Verilog] {line}", "INFO")

    def read_stderr(self):
        err = self.process.readAllStandardError().data().decode().strip()
        if err:
            self.log_message.emit(f"Engine Warning: {err}", "WARN")