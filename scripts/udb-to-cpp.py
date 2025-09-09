#!/usr/bin/env python3

#
# UDB to C++ translation, used as input for helper-to-tcg.
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
import subprocess
import os
import math
from copy import deepcopy
import common

h2tcg_str_includes = """
struct RISCVCPU;
typedef struct RISCVCPU RISCVCPU;

#include <stdint.h>
#include <stddef.h>
#include <initializer_list>
#include <iterator>
#include <type_traits>
#include "tcg_global_mappings.h"

#include <h2tcg-idl.h>
"""

preamble = """
struct CPUArchState {
    void xqci_set_gpr_xreg(XReg csrno, XReg csrw) {
        X.regs[csrno.value()] = csrw;
    }

    XRegSet X;
    XReg pc;

    CPUArchState() {}
"""


postamble = """
struct TCGv {};
TCGv cpu_gpr[32];
TCGv cpu_pc;
__attribute__((used))
cpu_tcg_mapping tcg_global_mappings[] = {
    cpu_tcg_map_array(CPUArchState, cpu_gpr, X, NULL),
    cpu_tcg_map(CPUArchState, cpu_pc, pc, NULL)
};
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
        prog='udb-to-cpp',
        description='Convert UDB instruction definitions to C++, \
                     intended as input to helper-to-tcg'
    )
    parser.add_argument('-o', '--out', required=True, help='Output C++ file')
    parser.add_argument('--inst-dir', required=True,
                        help='Path to extensions instruction directory in the UDB')
    parser.add_argument('--csrs',
                        help='Comma separated list of CSR directories in the UDB which instruction definitions depend on')
    args = parser.parse_args()

    csrs = get_csrs(args.csrs) if args.csrs else {}

    with open(args.out, 'w') as out:
        out.write(h2tcg_str_includes)

        out_csr(out, csrs)

        out.write(preamble)

        for file in sorted(os.listdir(args.inst_dir)):
            if not should_translate(file):
                continue

            with open(os.path.join(args.inst_dir, file), 'r') as f:
                try:
                    y = yaml.safe_load(f)
                    vars = []
                    if 'variables' in y['encoding']:
                        for v in y['encoding']['variables']:
                            s = common.var_size(v)
                            cs = common.bit_to_c_size(s)
                            if common.var_is_imm(y['operation()'], v['name']):
                                vars.append(f'Bits<{s}> ' + v['name'])
                            else:
                                vars.append(f'uint{cs}_t ' + v['name'])
                    imm_vars = ', '.join([str(i+1)
                                         for i in range(0, len(vars))])
                    name = y['name']
                    out.write('\n')
                    out.write('__attribute__((used))\n')
                    out.write(
                        f'__attribute__((annotate ("immediate: {imm_vars}")))\n')
                    out.write(
                        '__attribute__((annotate ("helper-to-tcg")))\n')
                    out.write(f"void {re.sub(r'\.', r'_', name)}({
                              ', '.join(vars)}) {{\n")
                    op = y['operation()']
                    op = common.op_to_cpp(op, csrs)
                    out.write(op)
                    out.write('}\n')
                except yaml.YAMLError as e:
                    print(e)
        out.write("};\n")
        out.write(postamble)


if __name__ == '__main__':
    main()
