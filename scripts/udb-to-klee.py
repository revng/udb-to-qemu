#!/usr/bin/env python3


# UDB to C++ KLEE input.
#
# Copyright (c) 2025 rev.ng Labs Srl.
#
# This work is licensed under the terms of the GNU GPL, version 2 or
# (at your option) any later version.
#
# See the LICENSE file in the top-level directory for details.
#

import yaml
import argparse
import re
import os
import common


preamble = """
struct CPUArchState {
    void xqci_set_gpr_xreg(XReg csrno, XReg csrw) {
        X.regs[csrno.value()] = csrw;
    }

    XRegSet X;
    XReg pc;

    CPUArchState() {}
"""


klee_str_includes = """
struct RISCVCPU;
typedef struct RISCVCPU RISCVCPU;

#include <stdint.h>
#include <stddef.h>
#include <initializer_list>
#include <iterator>
#include <type_traits>
#include "tcg_global_mappings.h"

#include <klee-idl.h>
"""


def should_translate(name):
    return name not in {
        'qc.brev32.yaml',
        'qc.c.mienter.nest.yaml',
        'qc.c.mienter.yaml',
        'qc.c.mileaveret.yaml',
        'qc.c.sync.yaml',
        'qc.c.syncr.yaml',
        'qc.c.syncwf.yaml',
        'qc.c.syncwl.yaml',
        'qc.sync.yaml',
        'qc.syncr.yaml',
        'qc.syncwf.yaml',
        'qc.syncwl.yaml',
        'qc.csrrwr.yaml',
        'qc.csrrwri.yaml',
        'qc.inw.yaml',
        'qc.outw.yaml',
    }


def get_csrs(exts):
    csrs = {}
    for dir in exts.split(','):
        for file in sorted(os.listdir(dir)):
            if not file.endswith('.yaml'):
                continue
            y = common.load_yaml_or_exit(os.path.join(dir, file))
            csrs[y['name']] = y
    return csrs


def out_csr(out, csrs):
    for csr in csrs:
        if csr in {'time'}:
            continue
        csr_name = re.sub(r'\.', r'_', csr)
        out.write(f"const uint32_t {csr_name} = {
                  hex(csrs[csr]['address'])};\n")

    for csr in csrs:
        csr_name = re.sub(r'\.', r'_', csr)
        for field in csrs[csr]['fields']:
            mask = 0
            if 'location' in csrs[csr]['fields'][field]:
                loc_str = csrs[csr]['fields'][field]['location']
                for start, len in common.ranges_in_location(str(loc_str)):
                    mask |= ((1 << len) - 1) << start
                out.write(f"#define {csr_name.upper()}_{field} {hex(mask)}\n")
            elif 'location_rv32' in csrs[csr]['fields'][field]:
                loc_str = csrs[csr]['fields'][field]['location_rv32']
                for start, len in common.ranges_in_location(str(loc_str)):
                    mask |= ((1 << len) - 1) << start
                out.write(f"#define {csr_name.upper()}_{field} {hex(mask)}\n")
            elif 'location_rv64' in csrs[csr]['fields'][field]:
                loc_str = csrs[csr]['fields'][field]['location_rv64']
                for start, len in common.ranges_in_location(str(loc_str)):
                    mask |= ((1 << len) - 1) << start
                out.write(f"#define {csr_name.upper()}_{field} {hex(mask)}\n")


def main():
    parser = argparse.ArgumentParser(
        prog='udb-to-klee',
        description='Convert UDB instruction definitions to C++, \
                     intended as input to KLEE for test generation'
    )
    parser.add_argument('-o', '--out', required=True, help='Output C++ file')
    parser.add_argument('--inst-dir', required=True,
                        help='Path to extensions instruction directory in the UDB')
    parser.add_argument('--csrs',
                        help='Comma separated list of CSR directories in the UDB which instruction definitions depend on')
    parser.add_argument('--helper-to-tcg-translated',
                        help='Path to output from helper-to-tcg of list of instructions which were successfully translated to TCG')
    args = parser.parse_args()

    csrs = get_csrs(args.csrs)

    translated = ''
    with open(args.helper_to_tcg_translated, 'r') as f:
        translated = f.read()

    for file in sorted(os.listdir(args.inst_dir)):
        if not should_translate(file):
            continue

        klee_file = os.path.join(args.out, os.path.splitext(file)[0]) + '.cpp'
        with open(os.path.join(args.inst_dir, file), 'r') as f:

            y = None
            try:
                y = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f'Error: {e}')
                continue
            name = y['name']
            op_name = re.sub(r'\.', r'_', name)
            if len(translated) > 0 and not op_name in translated:
                continue

            with open(klee_file, 'w') as out:
                out.write('#include <klee/klee.h>\n')
                out.write(f'#define INST_SIZE {int(len(y['encoding']['match'])/8)}')
                out.write(klee_str_includes)

                out_csr(out, csrs)

                out.write(preamble)


                vars = []
                var_names = []
                if 'variables' in y['encoding']:
                    for v in y['encoding']['variables']:
                        s = common.var_size(v)
                        cs = common.bit_to_c_size(s)
                        if common.var_is_imm(y['operation()'], v['name']):
                            vars.append(f'Bits<{s}> ' + v['name'])
                        else:
                            vars.append(f'uint{cs}_t ' + v['name'])
                        var_names.append(v['name'])
                out.write('\n')

                out.write(f"void {re.sub(r'\.', r'_', name)}({', '.join(vars)}) {{\n")
                op = y['operation()']
                op = common.op_to_cpp(op, csrs, True)
                out.write(op)
                out.write('}\n')

                out.write("};\n")

                out.write('int main() {\n')
                out.write('CPUArchState cpu;\n')
                out.write('for (int i = 0; i < 32; ++i) {\n')
                out.write('    cpu.X[i] = 0;\n')
                out.write('}\n')
                out.write('cpu.X[2] = 0x2800;\n')
                call_args = []
                variables = common.variables(y)
                print_info = {}
                op = y['operation()']
                for i, v in enumerate(variables):
                    name = v['name']

                    is_imm = common.var_is_imm(op, name)

                    var_size = common.var_size(v) if is_imm else 32
                    cs = common.bit_to_c_size(var_size) if is_imm else 32

                    if is_imm:
                        imm_name = f'imm_{name}'
                        out.write(f'uint{cs}_t {imm_name};\n')
                        out.write(f'klee_make_symbolic(&{imm_name}, sizeof({imm_name}), "{imm_name}");\n')
                        if 'sign_extend' in v or f'$signed({v["name"]})' in op:
                            out.write(f"{imm_name} = sextract{cs}({imm_name}, 0, {var_size});\n")
                        if 'left_shift' in v:
                            out.write(f"{imm_name} <<= {v['left_shift']};\n")
                        out.write(f'Bits<{var_size}> {name}({imm_name});\n')
                        print_info[name] = ('imm', 0, False)
                        call_args.append(name)

                    elif 'rd' not in name:
                        out.write(f'uint{cs}_t {name};\n')
                        out.write(f'klee_make_symbolic(&{name}, sizeof({name}), "{name}");\n')
                        compressed_offset = 8 if common.var_is_compressed(op, name) else 0
                        offset = i+1+compressed_offset
                        print_info[name] = ('reg', offset, False)
                        out.write(f'cpu.X[{offset}] = {name};\n')
                        call_args.append(str(i+1))

                    else:
                        out.write(f'uint{cs}_t {name};\n')
                        out.write(f'klee_make_symbolic(&{name}, sizeof({name}), "{name}");\n')
                        compressed_offset = 8 if common.var_is_compressed(op, name) else 0
                        offset = i+1+compressed_offset
                        print_info[name] = ('reg', offset, True)
                        out.write(f'cpu.X[{offset}] = {name};\n')
                        call_args.append(str(i+1))

                    if 'not' in v:
                        not_strs = []
                        not_values = v['not'] if isinstance(v['not'], list) else [v['not']]
                        for n in not_values:
                            not_strs.append(f'({name} != {n})')
                        out.write(f'klee_assume({" && ".join(not_strs)});\n')

                for i, v in enumerate(variables):
                    name = v['name']
                    is_imm = common.var_is_imm(y['operation()'], name)
                    var_size = common.var_size(v) if is_imm else 32
                    if var_size < 32 or var_size > 32 and var_size < 64:
                        out.write(f'klee_assume({name} <= ((1ul << {var_size})-1));\n')

                out.write(f"cpu.{op_name}({', '.join(call_args)}")
                out.write(');\n')

                out.write('printf("- variables:\\n");\n')
                for name in print_info:
                    kind, offset, is_output = print_info[name]
                    out.write(f'printf("  - name: \\\"{name}\\\"\\n");\n')
                    if kind == 'reg':
                        out.write(f'printf("    in: %u\\n", {name});\n')
                    elif kind == 'imm':
                        out.write(f'printf("    in: %u\\n", {name}.value());\n')
                    else:
                        assert(False)

                    if is_output and kind == 'reg':
                        out.write(f'printf("    out: %u\\n", cpu.X[{offset}].value());\n')

                out.write('printf("  overflow: %u\\n", overflow);\n')
                out.write('printf("  underflow: %u\\n", underflow);\n')
                out.write('if (has_jump) {\n')
                out.write('    printf("  has_jump:\\n");\n')
                out.write('    printf("    valid_test_jump: %u\\n", has_valid_test_jump);\n')
                out.write('    printf("    jump_pc_offset: %u\\n", jump_pc_offset);\n')
                out.write('}\n')
                out.write('if (has_load) {\n')
                out.write('    printf("  has_valid_test_memop: %u\\n", has_valid_test_memop);\n')
                out.write('    printf("  has_load:\\n");\n')
                out.write('    for (auto &P : rmemory) {\n')
                out.write('        printf("  - address: %u\\n", P.first);\n')
                out.write('        printf("    value: %u\\n", P.second.value);\n')
                out.write('        printf("    size: %u\\n", P.second.size);\n')
                out.write('    }\n')
                out.write('}\n')
                out.write('if (has_store) {\n')
                out.write('    printf("  has_valid_test_memop: %u\\n", has_valid_test_memop);\n')
                out.write('    printf("  has_store:\\n");\n')
                out.write('    for (auto &P : wmemory) {\n')
                out.write('        printf("  - address: %u\\n", P.first);\n')
                out.write('        printf("    value: %u\\n", P.second.value);\n')
                out.write('        printf("    size: %u\\n", P.second.size);\n')
                out.write('    }\n')
                out.write('}\n')
                out.write("return 0;\n")
                out.write('}\n')
                out.flush()


if __name__ == '__main__':
    main()
