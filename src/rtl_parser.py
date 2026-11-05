import subprocess
import os
import sys
import shutil
import xml.etree.ElementTree as ET

def get_tool_path(tool_name: str) -> str:
    """
    Resolves executable path:
    1. Local bin/<platform>/bin/ FIRST for bundled deployment.
    2. System PATH second (shutil.which) as a fallback.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if sys.platform.startswith('win'):
        platform_dir = os.path.join(base_dir, "bin", "windows", "bin")
        candidates = [f"{tool_name}.exe", f"{tool_name}.cmd", f"{tool_name}.bat", tool_name]
    else:
        platform_dir = os.path.join(base_dir, "bin", "linux", "bin")
        candidates = [tool_name]

    for cand in candidates:
        local_path = os.path.join(platform_dir, cand)
        if os.path.exists(local_path):
            return local_path

    system_path = shutil.which(tool_name)
    if system_path:
        return system_path

    return tool_name


def post_process_svg_for_qt(svg_path: str):
    """
    Post-process netlistsvg output for Qt QSvgRenderer.

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

        # ---------------------------------------------------------
        # PASS 1: Preserve the existing Qt-compatible styling
        # ---------------------------------------------------------
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
                except ValueError:
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

        # ---------------------------------------------------------
        # PASS 2: Correct labels on mux/demux/split/join components
        # ---------------------------------------------------------
        # Build parent relationships so each text element can be
        # associated with its actual netlistsvg component.
        parents = {}

        for parent in root.iter():
            for child in parent:
                parents[child] = parent

        target_types = {
            "mux",
            "pmux",
            "demux",
            "split",
            "join",
        }

        adjusted = 0

        for elem in root.iter():
            if elem.tag.split("}")[-1] != "text":
                continue

            # Only adjust labels attached to the relevant components.
            ancestor = parents.get(elem)
            component = None

            while ancestor is not None:
                component_type = ancestor.attrib.get(
                    f"{{{NET_NS}}}type"
                )

                if component_type is not None:
                    component = ancestor
                    break

                ancestor = parents.get(ancestor)

            if component is None:
                continue

            component_type = component.attrib.get(
                f"{{{NET_NS}}}type"
            )

            if component_type not in target_types:
                continue

            label = "".join(elem.itertext()).strip()

            if not label:
                continue

            # Check if one-to-many (demux, split) or many-to-one (mux, pmux, join)
            if component_type in ("demux", "split"):
                # Position on the right side
                elem.set("x", "7")
                elem.set("text-anchor", "start")
            else:
                # Position on the left side
                elem.set("x", "-7")
                elem.set("text-anchor", "end")

            elem.set("y", "-7")
            
            # Make the label bold as requested
            elem.set("font-weight", "bold")

            # Keep bit-range labels compact.
            if ":" in label and len(label) < 12:
                elem.set("font-size", "7px")
            else:
                elem.set("font-size", "7.5px")

            elem.set("font-family", "Arial, sans-serif")
            elem.set("fill", "#111111")

            # White outline masks the wire behind nearby text,
            # making labels easier to read without moving the wire.
            elem.set("stroke", "#FFFFFF")
            elem.set("stroke-width", "2")
            elem.set("paint-order", "stroke")
            elem.set("stroke-linejoin", "round")

            adjusted += 1

        # IMPORTANT:
        # Do not resize rectangles, move component bodies, or change
        # wire paths as part of label correction.

        tree.write(
            svg_path,
            encoding="utf-8",
            xml_declaration=True
        )

    except Exception as e:
        # Keep the original schematic generation workflow intact.
        print(f"SVG post-processing warning: {e}")

def generate_rtl_svg(verilog_code: str, output_svg="rtl_view.svg") -> str:
    """
    Compiles Verilog to an RTL SVG schematic using Yosys and netlistsvg.
    Returns the SVG file path or an error string starting with RTL_ERROR:.
    """
    if not verilog_code.strip():
        return "RTL_ERROR: Verilog source code is empty."

    base_dir = os.path.dirname(os.path.abspath(__file__))
    v_file = os.path.join(base_dir, "temp_design.v")
    json_file = os.path.join(base_dir, "temp_netlist.json")
    
    yosys_bin = get_tool_path("yosys")
    netlistsvg_bin = get_tool_path("netlistsvg")

    if not shutil.which(yosys_bin) and not os.path.exists(yosys_bin):
        return "RTL_ERROR: 'yosys' binary not found in bin/ directory or system PATH."
        
    if not shutil.which(netlistsvg_bin) and not os.path.exists(netlistsvg_bin):
        return "RTL_ERROR: 'netlistsvg' binary not found in bin/ directory or system PATH."

    try:
        with open(v_file, "w") as f:
            f.write(verilog_code)
            
        use_shell = sys.platform.startswith('win')

        # 1. Yosys Synthesis to JSON
        yosys_cmd = [
            yosys_bin, 
            "-p", 
            f"hierarchy -auto-top; proc; opt; write_json {json_file}", 
            v_file
        ]
        result_yosys = subprocess.run(yosys_cmd, capture_output=True, text=True, shell=use_shell)
        if result_yosys.returncode != 0:
            err = result_yosys.stderr or result_yosys.stdout
            return f"RTL_ERROR: Yosys Synthesis Failed.\n\n{err}"
        
        if not os.path.exists(json_file):
            return "RTL_ERROR: Yosys completed but generated no JSON netlist."

        # 2. Netlistsvg Rendering to SVG
        svg_cmd = [netlistsvg_bin, json_file, "-o", output_svg]
        result_svg = subprocess.run(svg_cmd, capture_output=True, text=True, shell=use_shell)
        if result_svg.returncode != 0:
            err = result_svg.stderr or result_svg.stdout
            return f"RTL_ERROR: Netlistsvg Rendering Failed.\n\n{err}"
        
        if not os.path.exists(output_svg) or os.path.getsize(output_svg) == 0:
            return "RTL_ERROR: Generated SVG schematic file is missing or empty."

        # 3. Post-process attributes for Qt QSvgRenderer compatibility
        post_process_svg_for_qt(output_svg)

        return output_svg
        
    except Exception as e:
        return f"RTL_ERROR: Toolchain Execution Error.\n\n{str(e)}"
    finally:
        for temp_path in (v_file, json_file):
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except OSError: pass