#!/usr/bin/env python3

#
# Translation from UDB to C code adding CSR functionality to QEMU.
#
# Copyright (c) 2025 rev.ng Labs Srl.
#
# This work is licensed under the terms of the GNU GPL, version 2 or
# (at your option) any later version.
#
# See the LICENSE file in the top-level directory for details.
#

import common
import argparse
import os
import re


def main():
    parser = argparse.ArgumentParser(
        prog='udb-to-csr.py',
        description='Convert UDB descriptions of CSR fields to .c/.h files that can be included in a QEMU RISC-V frontend'
    )
    parser.add_argument('--inst-dir', required=True,
                        help='Path to extensions instruction directory in the UDB')
    parser.add_argument('--csr-dir', required=True,
                        help='Path to CSR directory in the UDB')
    parser.add_argument('--out-c', required=True)
    parser.add_argument('--out-h', required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()

    csrs = {}
    for file in sorted(os.listdir(args.csr_dir)):
        if not file.endswith('.yaml'):
            continue
        y = common.load_yaml_or_exit(os.path.join(args.csr_dir, file))
        csrs[y['name']] = y

    with open(args.out_c, 'w') as out:
        out.write('#include "qemu/osdep.h"\n')
        out.write('#include "cpu.h"\n')
        out.write('#include "cpu_vendorid.h"\n')
        out.write(f'#include "{args.name}-csr.h"\n')
        out.write('\n')

        for csr in csrs:
            csr_name = re.sub(r'\.', r'_', csr)

            # Output read/modify/write function
            out.write(f'static RISCVException rmw_{
                      csr_name}(CPURISCVState * env,\n')
            out.write('                              int csrno,\n')
            out.write('                              target_ulong *ret_val,\n')
            out.write('                              target_ulong new_val,\n')
            out.write('                              target_ulong wr_mask)\n')
            out.write('{\n')
            out.write('    if (ret_val) {\n')
            out.write(f'        *ret_val = env->{csr_name};\n')
            out.write('    }\n')
            out.write(
                f'    env->{csr_name} = (env->{csr_name} & ~wr_mask) | (new_val & wr_mask);\n')
            out.write('    return RISCV_EXCP_NONE;\n')
            out.write('}\n')

            # Output predicate function
            exts = common.get_anyof_extensions_from_yaml(csrs[csr])
            exts_cond = ' && '.join(
                [f"!riscv_cpu_cfg(env)->ext_{e.lower()}" for e in exts])
            out.write(f'static RISCVException pred_{
                      csr_name}(CPURISCVState * env,\n')
            out.write('                               int csrno)\n')
            out.write('{\n')
            out.write(
                f'    if (env->priv != PRV_{csrs[csr]['priv_mode']} || ({exts_cond})) {{\n')
            out.write(f'        return RISCV_EXCP_ILLEGAL_INST;\n')
            out.write(f'    }}\n')
            out.write('    return RISCV_EXCP_NONE;\n')
            out.write('}\n')

        out.write('const RISCVCSR xqci_csr_list[] = {\n')
        for csr in csrs:
            csr_name = re.sub(r'\.', r'_', csr)
            out.write('    {\n')
            out.write(f"    .csrno = CSR_{csr_name.upper()},\n")
            out.write(f"    .csr_ops = {{\"{csr_name}\", pred_{
                      csr_name}, NULL, NULL, rmw_{csr_name}}},\n")
            out.write('    },\n')
        out.write('}\n')

    with open(args.out_h, 'w') as out:
        out.write('\n')
        for csr in csrs:
            csr_name = re.sub(r'\.', r'_', csr)
            out.write(f"#define CSR_{csr_name.upper()} {
                      hex(csrs[csr]['address'])}\n")

        # TODO handling of rv32 rv64 not correct
        for csr in csrs:
            csr_name = re.sub(r'\.', r'_', csr)
            for field in csrs[csr]['fields']:
                mask = 0
                if 'location' in csrs[csr]['fields'][field]:
                    loc_str = csrs[csr]['fields'][field]['location']
                    for start, len in common.ranges_in_location(str(loc_str)):
                        mask |= ((1 << len) - 1) << start
                    out.write(f"#define {csr_name.upper()}_{
                              field} {hex(mask)}\n")
                elif 'location_rv32' in csrs[csr]['fields'][field]:
                    loc_str = csrs[csr]['fields'][field]['location_rv32']
                    for start, len in common.ranges_in_location(str(loc_str)):
                        mask |= ((1 << len) - 1) << start
                    out.write(f"#define {csr_name.upper()}_{
                              field} {hex(mask)}\n")
                elif 'location_rv64' in csrs[csr]['fields'][field]:
                    loc_str = csrs[csr]['fields'][field]['location_rv64']
                    for start, len in common.ranges_in_location(str(loc_str)):
                        mask |= ((1 << len) - 1) << start
                    out.write(f"#define {csr_name.upper()}_{
                              field} {hex(mask)}\n")

        out.write(f'void {args.name}_register_custom_csrs(RISCVCPU *cpu);\n')


if __name__ == '__main__':
    main()
