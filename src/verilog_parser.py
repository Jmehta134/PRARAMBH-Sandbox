import os
import sys
import re
import tempfile
import xml.etree.ElementTree as ET
from pyverilog.vparser.parser import VerilogParser
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

DECLARED_SIGNALS = set()
codegen = ASTCodeGenerator()

def chain_xml_blocks(parent_stmt, block_list):
    if not block_list: return
    curr = block_list[0]
    parent_stmt.append(curr)
    for next_blk in block_list[1:]:
        nxt = ET.SubElement(curr, "next")
        nxt.append(next_blk)
        curr = next_blk

def parse_ast_to_expression(node):
    if node is None:
        return ET.Element("block", type="verilog_constant")
    
    node_type = type(node).__name__

    if node_type in ('Lvalue', 'Rvalue'):
        return parse_ast_to_expression(node.var)

    if node_type == 'Identifier':
        sig_name = node.name
        if sig_name in DECLARED_SIGNALS or sig_name.isidentifier():
            sig_blk = ET.Element("block", type="verilog_signal")
            ET.SubElement(sig_blk, "field", name="SIG").text = sig_name
            return sig_blk
        else:
            const_blk = ET.Element("block", type="verilog_constant")
            ET.SubElement(const_blk, "field", name="VAL").text = sig_name
            return const_blk

    elif node_type in ('IntConst', 'Number', 'Constant'):
        val_str = str(node.value)
        num_blk = ET.Element("block", type="verilog_numeric")
        w, b, v = "8", "d", val_str
        if "'" in val_str:
            parts = val_str.split("'")
            w = parts[0] if parts[0] else "32"
            if len(parts) > 1 and len(parts[1]) > 0:
                base_char = parts[1][0].lower()
                if base_char == 's': 
                    b = parts[1][1].lower() if len(parts[1]) > 1 else 'd'
                    v = parts[1][2:]
                else:
                    b = base_char
                    v = parts[1][1:]
        ET.SubElement(num_blk, "field", name="WIDTH").text = w
        ET.SubElement(num_blk, "field", name="BASE").text = b
        ET.SubElement(num_blk, "field", name="VAL").text = v
        return num_blk

    elif node_type in ('Pointer', 'Partselect'):
        slice_blk = ET.Element("block", type="verilog_slice")
        v_sig = ET.SubElement(slice_blk, "value", name="SIG")
        var_node = node.var if hasattr(node, 'var') else node
        v_sig.append(parse_ast_to_expression(var_node))
        
        idx_msb, idx_lsb = "0", "0"
        if hasattr(node, 'ptr'):
            idx_msb = idx_lsb = codegen.visit(node.ptr).strip()
        elif hasattr(node, 'msb') and hasattr(node, 'lsb'):
            idx_msb = codegen.visit(node.msb).strip()
            idx_lsb = codegen.visit(node.lsb).strip()
            
        ET.SubElement(slice_blk, "field", name="MSB").text = idx_msb
        ET.SubElement(slice_blk, "field", name="LSB").text = idx_lsb
        return slice_blk

    elif node_type == 'Concat':
        concat_blk = ET.Element("block", type="verilog_concat")
        if hasattr(node, 'list') and len(node.list) >= 2:
            v_a = ET.SubElement(concat_blk, "value", name="A")
            v_a.append(parse_ast_to_expression(node.list[0]))
            v_b = ET.SubElement(concat_blk, "value", name="B")
            v_b.append(parse_ast_to_expression(node.list[1]))
        return concat_blk

    elif node_type == 'Cond':
        mux_blk = ET.Element("block", type="verilog_mux")
        v_sel = ET.SubElement(mux_blk, "value", name="SEL")
        v_sel.append(parse_ast_to_expression(node.cond))
        v_in1 = ET.SubElement(mux_blk, "value", name="IN1")
        v_in1.append(parse_ast_to_expression(node.true_value))
        v_in0 = ET.SubElement(mux_blk, "value", name="IN0")
        v_in0.append(parse_ast_to_expression(node.false_value))
        return mux_blk

    elif node_type in ('Plus', 'Minus', 'Times', 'Divide', 'Eq', 'NotEq', 'GreaterThan', 'LessThan', 'GreaterEq', 'LessEq', 'Land', 'Lor', 'Sll', 'Srl', 'And', 'Or', 'Xor'):
        op_map = {
            'Plus': '+', 'Minus': '-', 'Times': '*', 'Divide': '/', 'Eq': '==', 'NotEq': '!=',
            'GreaterThan': '>', 'LessThan': '<', 'GreaterEq': '>=', 'LessEq': '<=',
            'Land': '&&', 'Lor': '||', 'Sll': '<<', 'Srl': '>>', 'And': '&', 'Or': '|', 'Xor': '^'
        }
        binop_blk = ET.Element("block", type="verilog_binop")
        v_a = ET.SubElement(binop_blk, "value", name="A")
        v_a.append(parse_ast_to_expression(node.left))
        ET.SubElement(binop_blk, "field", name="OP").text = op_map.get(node_type, '+')
        v_b = ET.SubElement(binop_blk, "value", name="B")
        v_b.append(parse_ast_to_expression(node.right))
        return binop_blk

    elif node_type in ('Ulnot', 'Not', 'Unot'):
        unop_blk = ET.Element("block", type="verilog_unop")
        ET.SubElement(unop_blk, "field", name="OP").text = "!"
        v_a = ET.SubElement(unop_blk, "value", name="A")
        v_a.append(parse_ast_to_expression(node.right if hasattr(node, 'right') else node.factor))
        return unop_blk

    const_blk = ET.Element("block", type="verilog_constant")
    ET.SubElement(const_blk, "field", name="VAL").text = codegen.visit(node).strip()
    return const_blk

def parse_ast_statements(statements):
    blocks = []
    if not statements:
        return blocks

    for stmt in statements:
        if stmt is None:
            continue
            
        try:
            stmt_code = codegen.visit(stmt).strip()
            if stmt_code.startswith('$display') or stmt_code.startswith('$monitor'):
                task_type = "verilog_display" if stmt_code.startswith('$display') else "verilog_monitor"
                blk = ET.Element("block", type=task_type)
                
                match = re.search(r'\$(?:display|monitor)\s*\(\s*"(.*?)"\s*(?:,\s*(.*))?\)\s*;?$', stmt_code, re.DOTALL)
                if match:
                    fmt_str = match.group(1)
                    args_str = match.group(2) if match.group(2) else ""
                else:
                    fallback = re.search(r'\$(?:display|monitor)\s*\((.*)\)\s*;?$', stmt_code, re.DOTALL)
                    fmt_str = ""
                    args_str = fallback.group(1).strip() if fallback else ""
                    
                ET.SubElement(blk, "field", name="FORMAT").text = fmt_str
                ET.SubElement(blk, "field", name="ARGS").text = args_str
                blocks.append(blk)
                continue
        except Exception:
            pass

        stype = type(stmt).__name__

        if stype == 'NonblockingSubstitution':
            blk = ET.Element("block", type="verilog_nonblocking_assign")
            vl = ET.SubElement(blk, "value", name="LHS")
            vl.append(parse_ast_to_expression(stmt.left))
            vr = ET.SubElement(blk, "value", name="RHS")
            vr.append(parse_ast_to_expression(stmt.right))
            blocks.append(blk)

        elif stype == 'BlockingSubstitution':
            blk = ET.Element("block", type="verilog_blocking_assign")
            vl = ET.SubElement(blk, "value", name="LHS")
            vl.append(parse_ast_to_expression(stmt.left))
            vr = ET.SubElement(blk, "value", name="RHS")
            vr.append(parse_ast_to_expression(stmt.right))
            blocks.append(blk)

        elif stype == 'IfStatement':
            if_blk = ET.Element("block", type="verilog_if")
            v_cond = ET.SubElement(if_blk, "value", name="COND")
            v_cond.append(parse_ast_to_expression(stmt.cond))

            if stmt.true_statement:
                true_stmts = stmt.true_statement.statements if hasattr(stmt.true_statement, 'statements') else [stmt.true_statement]
                true_list = parse_ast_statements(true_stmts)
                if true_list:
                    s_then = ET.SubElement(if_blk, "statement", name="THEN")
                    chain_xml_blocks(s_then, true_list)

            if stmt.false_statement:
                false_stmts = stmt.false_statement.statements if hasattr(stmt.false_statement, 'statements') else [stmt.false_statement]
                false_list = parse_ast_statements(false_stmts)
                if false_list:
                    s_else = ET.SubElement(if_blk, "statement", name="ELSE")
                    chain_xml_blocks(s_else, false_list)

            blocks.append(if_blk)

        elif stype == 'CaseStatement':
            case_blk = ET.Element("block", type="verilog_case")
            v_expr = ET.SubElement(case_blk, "value", name="EXPR")
            v_expr.append(parse_ast_to_expression(stmt.comp))

            case_item_blocks = []
            for case_item in stmt.caselist:
                if case_item.cond is None:  
                    def_blk = ET.Element("block", type="verilog_default")
                    item_stmts = case_item.statement.statements if hasattr(case_item.statement, 'statements') else [case_item.statement]
                    def_inner = parse_ast_statements(item_stmts)
                    if def_inner:
                        s_do = ET.SubElement(def_blk, "statement", name="DO")
                        chain_xml_blocks(s_do, def_inner)
                    case_item_blocks.append(def_blk)
                else:
                    for cond_val in case_item.cond:
                        item_blk = ET.Element("block", type="verilog_case_item")
                        v_val = ET.SubElement(item_blk, "value", name="VAL")
                        v_val.append(parse_ast_to_expression(cond_val))
                        item_stmts = case_item.statement.statements if hasattr(case_item.statement, 'statements') else [case_item.statement]
                        item_inner = parse_ast_statements(item_stmts)
                        if item_inner:
                            s_do = ET.SubElement(item_blk, "statement", name="DO")
                            chain_xml_blocks(s_do, item_inner)
                        case_item_blocks.append(item_blk)

            if case_item_blocks:
                s_cases = ET.SubElement(case_blk, "statement", name="CASES")
                chain_xml_blocks(s_cases, case_item_blocks)

            blocks.append(case_blk)

        elif stype == 'ForStatement':
            for_blk = ET.Element("block", type="verilog_for")
            pre_str = codegen.visit(stmt.pre).strip().strip(';') if hasattr(stmt, 'pre') and stmt.pre else ""
            cond_str = codegen.visit(stmt.cond).strip().strip(';') if hasattr(stmt, 'cond') and stmt.cond else ""
            post_str = codegen.visit(stmt.post).strip().strip(';') if hasattr(stmt, 'post') and stmt.post else ""
            ET.SubElement(for_blk, "field", name="COND").text = f"{pre_str}; {cond_str}; {post_str}"
            
            loop_stmts = stmt.statement.statements if hasattr(stmt.statement, 'statements') else [stmt.statement]
            inner_blks = parse_ast_statements(loop_stmts)
            if inner_blks:
                s_do = ET.SubElement(for_blk, "statement", name="DO")
                chain_xml_blocks(s_do, inner_blks)
            blocks.append(for_blk)

        elif stype == 'DelayStatement':
            delay_blk = ET.Element("block", type="verilog_delay")
            ET.SubElement(delay_blk, "field", name="DELAY").text = str(getattr(stmt.delay, 'value', '10'))
            blocks.append(delay_blk)

        elif stype == 'Block':
            if hasattr(stmt, 'statements') and stmt.statements:
                blocks.extend(parse_ast_statements(stmt.statements))

    return blocks

def verilog_to_blockly_xml(verilog_code: str) -> str:
    global DECLARED_SIGNALS
    DECLARED_SIGNALS.clear()

    # --- STRICT TOP-LEVEL SANITIZATION ---
    mod_match = re.search(r'\bmodule\b.*?\bendmodule\b', verilog_code, re.DOTALL)
    if mod_match:
        verilog_code = mod_match.group(0)
    elif verilog_code.strip():
        verilog_code = f"module top_module;\n{verilog_code}\nendmodule"
    else:
        return '<xml xmlns="https://developers.google.com/blockly/xml"></xml>'

    init_vals = {}
    init_pattern = r'\b(input|output|inout|wire|reg|integer|parameter|localparam)\s+(?:signed\s+)?(?:\[[^\]]+\]\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;,)]+)'
    for match in re.finditer(init_pattern, verilog_code):
        init_vals[match.group(2)] = match.group(3).strip()

    strip_pattern = r'(\b(?:input|output|inout|wire|reg|integer)\s+(?:signed\s+)?(?:\[[^\]]+\]\s+)?[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^;,)]+([;,)])'
    clean_code = re.sub(strip_pattern, r'\1\2', verilog_code)

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    with open(os.devnull, 'w') as null_out:
        sys.stdout = null_out
        sys.stderr = null_out
        try:
            tmp_dir = tempfile.gettempdir()
            parser = VerilogParser(outputdir=tmp_dir)
            ast = parser.parse(clean_code)
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            import traceback
            error_details = traceback.format_exc().strip().split('\n')[-1]
            
            if 'before: "assign"' in error_details:
                return "PARSE_ERROR: You placed an 'assign' statement inside an 'always' block! In standard Verilog, 'assign' must go outside 'always'. Use procedural Assignment blocks (= or <=) inside 'always' instead."
                
            return f"PARSE_ERROR: Syntax or mapping failure near -> {error_details}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    xml_doc = ET.Element("xml", xmlns="https://developers.google.com/blockly/xml")
    mod_name = "top_module"

    module_def = None
    if hasattr(ast, 'description') and hasattr(ast.description, 'definitions'):
        for d in ast.description.definitions:
            if type(d).__name__ == 'ModuleDef':
                module_def = d
                mod_name = module_def.name
                break

    mod_block = ET.SubElement(xml_doc, "block", type="verilog_module", x="50", y="50")
    ET.SubElement(mod_block, "field", name="NAME").text = mod_name

    decl_blocks = []
    body_blocks = []

    def get_width_string(width_obj):
        if not width_obj: return "1"
        try:
            msb = int(getattr(width_obj.msb, 'value', 0))
            lsb = int(getattr(width_obj.lsb, 'value', 0))
            calc = abs(msb - lsb) + 1
            if calc <= 1: return "1"
            elif calc <= 2: return "2"
            elif calc <= 4: return "4"
            elif calc <= 8: return "8"
            elif calc <= 16: return "16"
            else: return "32"
        except Exception:
            return "8" 

    if module_def:
        if module_def.portlist and module_def.portlist.ports:
            for port in module_def.portlist.ports:
                if type(port).__name__ == 'Ioport':
                    decl = port.first
                    itype = type(decl).__name__
                    sig_name = decl.name
                    DECLARED_SIGNALS.add(sig_name)
                    second_type = type(port.second).__name__ if hasattr(port, 'second') and port.second else ''
                    
                    dir_type = "wire"
                    if itype == 'Input': dir_type = "input wire"
                    elif itype == 'Output': dir_type = "output reg" if second_type == 'Reg' else "output wire"
                    elif itype == 'Inout': dir_type = "inout wire"

                    width_val = get_width_string(getattr(decl, 'width', None))

                    blk = ET.Element("block", type="verilog_port")
                    ET.SubElement(blk, "field", name="DIR_TYPE").text = dir_type
                    ET.SubElement(blk, "field", name="WIDTH").text = width_val
                    ET.SubElement(blk, "field", name="NAME").text = sig_name
                    
                    # Parse INIT_VAL into value input element
                    init_expr = init_vals.get(sig_name, "")
                    if hasattr(decl, 'value') and decl.value is not None:
                        v_elem = ET.SubElement(blk, "value", name="INIT_VAL")
                        v_elem.append(parse_ast_to_expression(decl.value))
                    elif init_expr:
                        v_elem = ET.SubElement(blk, "value", name="INIT_VAL")
                        const_blk = ET.Element("block", type="verilog_constant")
                        ET.SubElement(const_blk, "field", name="VAL").text = init_expr
                        v_elem.append(const_blk)

                    decl_blocks.append(blk)

        if module_def.items:
            for item in module_def.items:
                itype = type(item).__name__

                if itype == 'Decl':
                    for decl_item in item.list:
                        dtype = type(decl_item).__name__
                        if dtype in ('Input', 'Output', 'Inout', 'Wire', 'Reg', 'Parameter', 'Localparam', 'Integer'):
                            sig_name = decl_item.name
                            DECLARED_SIGNALS.add(sig_name)

                            dir_type = "wire"
                            if dtype == 'Input': dir_type = "input wire"
                            elif dtype == 'Output': dir_type = "output reg"
                            elif dtype == 'Reg': dir_type = "reg"
                            elif dtype == 'Integer': dir_type = "integer"
                            elif dtype in ('Parameter', 'Localparam'): dir_type = "parameter"

                            width_val = get_width_string(getattr(decl_item, 'width', None))

                            blk = ET.Element("block", type="verilog_port")
                            ET.SubElement(blk, "field", name="DIR_TYPE").text = dir_type
                            ET.SubElement(blk, "field", name="WIDTH").text = width_val
                            ET.SubElement(blk, "field", name="NAME").text = sig_name
                            
                            init_expr = init_vals.get(sig_name, "")
                            if hasattr(decl_item, 'value') and decl_item.value is not None:
                                v_elem = ET.SubElement(blk, "value", name="INIT_VAL")
                                v_elem.append(parse_ast_to_expression(decl_item.value))
                            elif init_expr:
                                v_elem = ET.SubElement(blk, "value", name="INIT_VAL")
                                const_blk = ET.Element("block", type="verilog_constant")
                                ET.SubElement(const_blk, "field", name="VAL").text = init_expr
                                v_elem.append(const_blk)

                            decl_blocks.append(blk)

                elif itype == 'Always':
                    is_comb = False
                    clk_name = "clk"
                    
                    if hasattr(item, 'sens_list') and item.sens_list:
                        for sens in item.sens_list.list:
                            sens_str = str(sens.sig) if hasattr(sens, 'sig') else str(sens)
                            sens_type = getattr(sens, 'type', '')
                            
                            if sens_type == 'all' or '*' in sens_str:
                                is_comb = True
                            elif sens_type not in ('posedge', 'negedge'):
                                is_comb = True
                            else:
                                clean_sens = sens_str.replace('posedge ', '').replace('negedge ', '').strip()
                                if not ('rst' in clean_sens or 'reset' in clean_sens): 
                                    clk_name = clean_sens

                    blk_type = "verilog_always_comb" if is_comb else "verilog_always_ff"
                    ff_blk = ET.Element("block", type=blk_type)
                    
                    if not is_comb:
                        v_clk = ET.SubElement(ff_blk, "value", name="CLK")
                        clk_sig = ET.Element("block", type="verilog_signal")
                        ET.SubElement(clk_sig, "field", name="SIG").text = clk_name
                        v_clk.append(clk_sig)

                    inner_stmts = item.statement.statements if hasattr(item.statement, 'statements') else [item.statement]
                    inner_blks = parse_ast_statements(inner_stmts)
                    if inner_blks:
                        do_stmt = ET.SubElement(ff_blk, "statement", name="DO")
                        chain_xml_blocks(do_stmt, inner_blks)
                    body_blocks.append(ff_blk)

                elif itype == 'Initial':
                    init_blk = ET.Element("block", type="verilog_initial")
                    inner_stmts = item.statement.statements if hasattr(item.statement, 'statements') else [item.statement]
                    inner_blks = parse_ast_statements(inner_stmts)
                    if inner_blks:
                        s_do = ET.SubElement(init_blk, "statement", name="DO")
                        chain_xml_blocks(s_do, inner_blks)
                    body_blocks.append(init_blk)

                elif itype == 'Assign':
                    assign_blk = ET.Element("block", type="verilog_assign")
                    vl = ET.SubElement(assign_blk, "value", name="LHS")
                    vl.append(parse_ast_to_expression(item.left))
                    vr = ET.SubElement(assign_blk, "value", name="RHS")
                    vr.append(parse_ast_to_expression(item.right))
                    body_blocks.append(assign_blk)

                elif itype == 'InstanceList':
                    for inst in item.instances:
                        inst_blk = ET.Element("block", type="verilog_instantiate")
                        ET.SubElement(inst_blk, "field", name="MODULE_TYPE").text = item.module
                        ET.SubElement(inst_blk, "field", name="INST_NAME").text = inst.name
                        
                        mapping_str = ""
                        if hasattr(inst, 'portlist'):
                            mappings = []
                            for portarg in inst.portlist:
                                arg_str = getattr(portarg.argname, 'name', str(portarg.argname))
                                mappings.append(f".{portarg.portname}({arg_str})")
                            mapping_str = ", ".join(mappings)
                        ET.SubElement(inst_blk, "field", name="MAPPING").text = mapping_str
                        body_blocks.append(inst_blk)

    if decl_blocks:
        decl_stmt = ET.SubElement(mod_block, "statement", name="DECLARATIONS")
        chain_xml_blocks(decl_stmt, decl_blocks)

    if body_blocks:
        body_stmt = ET.SubElement(mod_block, "statement", name="BODY")
        chain_xml_blocks(body_stmt, body_blocks)

    return ET.tostring(xml_doc, encoding="unicode")