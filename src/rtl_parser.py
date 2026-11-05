import os
import sys
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


# -----------------------------------------------------------------------------
# Tool discovery
# -----------------------------------------------------------------------------

def _platform_folder() -> str:
    """Return the bundled platform folder name."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    return ""


def _application_roots():
    """
    Return likely application roots in source and PyInstaller deployments.

    In a PyInstaller onedir build, add-data files are normally placed under
    sys._MEIPASS (for example, Sandbox/_internal). In a source checkout this
    module may live either in the project root or in src/.
    """
    roots = []
    seen = set()

    def add(path):
        if not path:
            return
        path = os.path.abspath(path)
        if path not in seen and os.path.isdir(path):
            seen.add(path)
            roots.append(path)

    add(getattr(sys, "_MEIPASS", None))

    module_dir = os.path.dirname(os.path.abspath(__file__))
    current = module_dir
    # Covers RTLparser.py in the repository root, src/, or a shallow package.
    for _ in range(4):
        add(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    executable_dir = os.path.dirname(os.path.abspath(sys.executable))
    add(executable_dir)
    add(os.path.join(executable_dir, "_internal"))

    return roots


def _bundled_tool_directories():
    """Yield platform-specific bundled bin directories, in priority order."""
    platform_folder = _platform_folder()
    if not platform_folder:
        return

    for root in _application_roots():
        yield os.path.join(root, "bin", platform_folder, "bin")


def get_tool_path(tool_name: str) -> str:
    """
    Resolve a bundled tool first, then fall back to the system PATH.

    Expected bundled layout:

        bin/windows/bin/yosys.exe
        bin/windows/bin/node.exe
        bin/windows/bin/netlistsvg/node_modules/netlistsvg/bin/netlistsvg.js

        bin/linux/bin/yosys
        bin/linux/bin/node
        bin/linux/bin/netlistsvg/node_modules/netlistsvg/bin/netlistsvg.js

    For "netlistsvg", this function returns the bundled JavaScript CLI entry
    point when it exists. generate_rtl_svg() then launches it with bundled Node.
    """
    key = os.path.basename(str(tool_name)).lower()
    is_windows = sys.platform.startswith("win")

    for tool_dir in _bundled_tool_directories() or []:
        if key in ("netlistsvg", "netlistsvg.js"):
            candidates = [
                os.path.join(
                    tool_dir,
                    "netlistsvg",
                    "node_modules",
                    "netlistsvg",
                    "bin",
                    "netlistsvg.js",
                ),
                # Compatibility with the earlier netlistsvg_pkg directory name.
                os.path.join(
                    tool_dir,
                    "netlistsvg_pkg",
                    "node_modules",
                    "netlistsvg",
                    "bin",
                    "netlistsvg.js",
                ),
            ]
        elif key in ("yosys", "yosys.exe"):
            candidates = [os.path.join(tool_dir, "yosys.exe" if is_windows else "yosys")]
        elif key in ("node", "node.exe"):
            candidates = [os.path.join(tool_dir, "node.exe" if is_windows else "node")]
        else:
            candidates = [os.path.join(tool_dir, tool_name)]

        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

    # System fallback. Netlistsvg may be an executable, a .cmd shim on Windows,
    # or a console script on Linux. The launcher handles these cases.
    system_path = shutil.which(tool_name)
    return system_path or ""


# -----------------------------------------------------------------------------
# Process execution helpers
# -----------------------------------------------------------------------------

def _powershell_quote(value: str) -> str:
    """Quote a value as a PowerShell single-quoted string literal."""
    return "'" + str(value).replace("'", "''") + "'"


def _run_direct(command, cwd=None, env=None):
    """Run a command without a shell, except for Windows .cmd/.bat shims."""
    executable = str(command[0])

    if sys.platform.startswith("win") and executable.lower().endswith((".cmd", ".bat")):
        command_line = subprocess.list2cmdline([str(item) for item in command])
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        return subprocess.run(
            [comspec, "/d", "/c", command_line],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            env=env,
            shell=False,
        )

    return subprocess.run(
        [str(item) for item in command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
        env=env,
        shell=False,
    )


def _suite_root_for_yosys(yosys_path: str):
    """Return the OSS CAD Suite root for a bundled .../bin/yosys executable."""
    if not yosys_path:
        return None

    absolute = os.path.abspath(yosys_path)
    bin_dir = os.path.dirname(absolute)
    if os.path.basename(bin_dir).lower() != "bin":
        return None

    suite_root = os.path.dirname(bin_dir)
    if not os.path.isdir(suite_root):
        return None
    return suite_root


def _run_yosys(command, yosys_path: str, cwd=None):
    """
    Run Yosys with the official OSS CAD Suite environment when bundled.

    The suite documents environment.ps1 for PowerShell on Windows and
    environment for Linux/macOS. These scripts set PATH and suite-specific
    variables needed by helper binaries and data files.
    """
    suite_root = _suite_root_for_yosys(yosys_path)

    if suite_root and sys.platform.startswith("win"):
        environment_ps1 = os.path.join(suite_root, "environment.ps1")
        if os.path.isfile(environment_ps1):
            powershell = shutil.which("powershell.exe") or shutil.which("powershell") or "powershell.exe"

            script_lines = [
                "$ErrorActionPreference = 'Stop'",
                ". " + _powershell_quote(environment_ps1),
                "& " + " ".join(_powershell_quote(part) for part in command),
                "exit $LASTEXITCODE",
                "",
            ]

            script_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".ps1",
                    prefix="rtlparser_yosys_",
                    encoding="utf-8-sig",
                    delete=False,
                ) as script_file:
                    script_file.write("\n".join(script_lines))
                    script_path = script_file.name

                return subprocess.run(
                    [
                        powershell,
                        "-NoLogo",
                        "-NoProfile",
                        "-NonInteractive",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        script_path,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=cwd,
                    shell=False,
                )
            finally:
                if script_path and os.path.exists(script_path):
                    try:
                        os.remove(script_path)
                    except OSError:
                        pass

        # Older suite distributions may provide environment.bat only.
        environment_bat = os.path.join(suite_root, "environment.bat")
        if os.path.isfile(environment_bat):
            command_line = subprocess.list2cmdline([str(item) for item in command])
            batch_command = 'call "' + environment_bat + '" >nul && ' + command_line
            comspec = os.environ.get("COMSPEC", "cmd.exe")
            return subprocess.run(
                [comspec, "/d", "/c", batch_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                shell=False,
            )

    if suite_root and sys.platform.startswith("linux"):
        environment_script = os.path.join(suite_root, "environment")
        if os.path.isfile(environment_script):
            bash = shutil.which("bash") or "bash"
            # $1 is the environment script; after sourcing it, shift so "$@"
            # contains only the Yosys command and its arguments.
            return subprocess.run(
                [
                    bash,
                    "-c",
                    'source "$1" && shift && exec "$@"',
                    "rtlparser",
                    environment_script,
                    *[str(item) for item in command],
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                shell=False,
            )

    # PATH-based Yosys or a suite without an environment script.
    run_env = os.environ.copy()
    if suite_root:
        suite_bin = os.path.join(suite_root, "bin")
        run_env["PATH"] = suite_bin + os.pathsep + run_env.get("PATH", "")

    return _run_direct(command, cwd=cwd, env=run_env)


def _process_error(result) -> str:
    """Return useful subprocess diagnostics, including stdout when needed."""
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    if stdout and stderr:
        return stderr + "\n\nStandard output:\n" + stdout
    return stderr or stdout or f"Process exited with code {result.returncode}."


def _yosys_quote(path: str) -> str:
    """Quote an absolute path for use inside a Yosys command script."""
    normalized = os.path.abspath(path).replace("\\", "/")
    if '"' in normalized:
        raise ValueError('A file path used by Yosys cannot contain a double-quote character.')
    return '"' + normalized + '"'


# -----------------------------------------------------------------------------
# SVG post-processing for Qt
# -----------------------------------------------------------------------------

def post_process_svg_for_qt(svg_path: str):
    """
    Post-process Netlistsvg output for Qt QSvgRenderer.

    Label fix:
    - Keep component geometry and wires unchanged.
    - Move mux/join port labels away from component borders to the left.
    - Move demux/split port labels away from component borders to the right.
    - Make labels bold.
    - Position labels above their associated input wires.
    - Add a white text outline to improve readability over wires.
    - Do not resize rectangles or change wire connectivity.
    """
    if not os.path.exists(svg_path):
        return

    try:
        SVG_NS = "http://www.w3.org/2000/svg"
        NET_NS = "https://github.com/nturley/netlistsvg"

        ET.register_namespace("", SVG_NS)
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

        tree = ET.parse(svg_path)
        root = tree.getroot()

        # PASS 1: Preserve the existing Qt-compatible styling.
        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            elem_class = elem.attrib.get("class", "")

            if tag == "g":
                if "net" in elem_class:
                    elem.set("stroke", "#000000")
                    elem.set("stroke-width", "1.2")
                    elem.set("fill", "none")

            elif tag == "path":
                fill_val = elem.attrib.get("fill", "").lower()

                if (
                    fill_val in ("none", "")
                    or "net" in elem_class
                    or "wire" in elem_class
                    or "bus" in elem_class
                ):
                    elem.set("fill", "none")
                    elem.set("stroke", "#000000")
                    elem.set("stroke-linecap", "butt")
                    elem.set("stroke-linejoin", "miter")

                    if "bus" in elem_class:
                        elem.set("stroke-width", "1.8")
                    else:
                        elem.set("stroke-width", "1.2")
                else:
                    elem.set("fill", "#000000")
                    elem.set("stroke", "none")

            elif tag == "line":
                elem.set("stroke", "#000000")
                elem.set("stroke-width", "1.2")
                elem.set("stroke-linecap", "butt")

            elif tag in ("rect", "polygon"):
                if elem.attrib.get("fill") != "none":
                    elem.set("fill", "#F8F9FA")

                elem.set("stroke", "#222222")
                elem.set("stroke-width", "1.2")

            elif tag == "circle":
                try:
                    r_val = float(elem.attrib.get("r", "0"))
                except (TypeError, ValueError):
                    r_val = 0

                if r_val <= 4 or "dot" in elem_class or "junc" in elem_class:
                    elem.set("fill", "#000000")
                    elem.set("stroke", "none")
                else:
                    elem.set("fill", "#FFFFFF")
                    elem.set("stroke", "#222222")
                    elem.set("stroke-width", "1.2")

            elif tag in ("text", "tspan"):
                elem.set("font-family", "Arial, sans-serif")
                elem.set("stroke", "none")

                if "portlabel" in elem_class or "pin" in elem_class:
                    elem.set("font-size", "7.5px")
                    elem.set("fill", "#333333")
                    elem.set("font-weight", "normal")

                elif "nodelabel" in elem_class or "title" in elem_class:
                    elem.set("font-size", "10px")
                    elem.set("fill", "#000000")
                    elem.set("font-weight", "bold")

                else:
                    if "font-size" not in elem.attrib:
                        elem.set("font-size", "8.5px")

                    if "fill" not in elem.attrib:
                        elem.set("fill", "#000000")

        # PASS 2: Correct labels on mux/demux/split/join components.
        parents = {}
        for parent in root.iter():
            for child in parent:
                parents[child] = parent

        target_types = {"mux", "pmux", "demux", "split", "join"}

        for elem in root.iter():
            if elem.tag.split("}")[-1] != "text":
                continue

            ancestor = parents.get(elem)
            component = None

            while ancestor is not None:
                component_type = ancestor.attrib.get(f"{{{NET_NS}}}type")
                if component_type is not None:
                    component = ancestor
                    break
                ancestor = parents.get(ancestor)

            if component is None:
                continue

            component_type = component.attrib.get(f"{{{NET_NS}}}type")
            if component_type not in target_types:
                continue

            label = "".join(elem.itertext()).strip()
            if not label:
                continue

            if component_type in ("demux", "split"):
                elem.set("x", "7")
                elem.set("text-anchor", "start")
            else:
                elem.set("x", "-7")
                elem.set("text-anchor", "end")

            elem.set("y", "-7")
            elem.set("font-weight", "bold")

            if ":" in label and len(label) < 12:
                elem.set("font-size", "7px")
            else:
                elem.set("font-size", "7.5px")

            elem.set("font-family", "Arial, sans-serif")
            elem.set("fill", "#111111")
            elem.set("stroke", "#FFFFFF")
            elem.set("stroke-width", "2")
            elem.set("paint-order", "stroke")
            elem.set("stroke-linejoin", "round")

        tree.write(svg_path, encoding="utf-8", xml_declaration=True)

    except Exception as exc:
        # Do not fail an otherwise successful schematic generation because
        # optional SVG styling could not be applied.
        print(f"SVG post-processing warning: {exc}")


# -----------------------------------------------------------------------------
# Main RTL-to-SVG entry point
# -----------------------------------------------------------------------------

def generate_rtl_svg(verilog_code: str, output_svg="rtl_view.svg") -> str:
    """
    Compile Verilog/SystemVerilog into an SVG schematic using Yosys + Netlistsvg.

    Returns the output SVG path on success, or an error string beginning with
    RTL_ERROR: on failure.
    """
    if not isinstance(verilog_code, str) or not verilog_code.strip():
        return "RTL_ERROR: Verilog source code is empty."

    yosys_bin = get_tool_path("yosys")
    netlistsvg_tool = get_tool_path("netlistsvg")

    if not yosys_bin or not os.path.isfile(yosys_bin) and not shutil.which(yosys_bin):
        return (
            "RTL_ERROR: Yosys was not found. Expected the bundled executable under "
            "bin/windows/bin or bin/linux/bin, or a Yosys executable on PATH."
        )

    if not netlistsvg_tool or not os.path.isfile(netlistsvg_tool) and not shutil.which(netlistsvg_tool):
        return (
            "RTL_ERROR: Netlistsvg was not found. Install the bundled Netlistsvg "
            "package under the platform bin directory or add netlistsvg to PATH."
        )

    is_bundled_js = netlistsvg_tool.lower().endswith(".js")
    if is_bundled_js:
        node_bin = get_tool_path("node")
        if not node_bin:
            return "RTL_ERROR: The bundled Netlistsvg JavaScript file was found, but Node.js was not found."
        netlistsvg_command_prefix = [node_bin, netlistsvg_tool]
    else:
        netlistsvg_command_prefix = [netlistsvg_tool]

    try:
        output_svg_path = os.path.abspath(os.fspath(output_svg))
        output_directory = os.path.dirname(output_svg_path)
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

        # Unique temporary files avoid collisions when multiple schematic
        # generations happen concurrently (for example, from separate tabs).
        with tempfile.TemporaryDirectory(prefix="prarambh_rtl_") as temp_dir:
            verilog_file = os.path.join(temp_dir, "design.v")
            json_file = os.path.join(temp_dir, "netlist.json")

            with open(verilog_file, "w", encoding="utf-8", newline="\n") as source_file:
                source_file.write(verilog_code)

            yosys_script = (
                f"read_verilog -sv {_yosys_quote(verilog_file)}; "
                "hierarchy -auto-top; "
                "proc; "
                "opt; "
                f"write_json {_yosys_quote(json_file)}"
            )

            yosys_command = [yosys_bin, "-p", yosys_script]
            result_yosys = _run_yosys(yosys_command, yosys_bin)

            if result_yosys.returncode != 0:
                details = _process_error(result_yosys)
                return f"RTL_ERROR: Yosys synthesis failed.\n\n{details}"

            if not os.path.isfile(json_file) or os.path.getsize(json_file) == 0:
                details = _process_error(result_yosys)
                extra = f"\n\nYosys output:\n{details}" if details else ""
                return "RTL_ERROR: Yosys completed but generated no JSON netlist." + extra

            svg_command = netlistsvg_command_prefix + [json_file, "-o", output_svg_path]
            result_svg = _run_direct(svg_command)

            if result_svg.returncode != 0:
                details = _process_error(result_svg)
                return f"RTL_ERROR: Netlistsvg rendering failed.\n\n{details}"

            if not os.path.isfile(output_svg_path) or os.path.getsize(output_svg_path) == 0:
                details = _process_error(result_svg)
                extra = f"\n\nNetlistsvg output:\n{details}" if details else ""
                return "RTL_ERROR: Generated SVG schematic file is missing or empty." + extra

        # The temporary Verilog and JSON files have been removed at this point.
        post_process_svg_for_qt(output_svg_path)
        return output_svg_path

    except Exception as exc:
        return f"RTL_ERROR: Toolchain execution error.\n\n{type(exc).__name__}: {exc}"
