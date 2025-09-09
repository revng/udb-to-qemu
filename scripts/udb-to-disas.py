#!/usr/bin/env python3

#
# UDB to C code implementing disassemler glue in QEMU.
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


def should_decode_only(name):
    return name in common.decode_only


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


def main():
    parser = argparse.ArgumentParser(
        prog='udb-to-trans.py',
        description='Convert UDB instruction encodings to QEMU decodetree input'
    )
    parser.add_argument('--inst-dir', required=True,
                        help='Path to extensions instruction directory in the UDB')
    parser.add_argument('--out-c', required=True)
    parser.add_argument('--out-h', required=True)
    parser.add_argument('--trans-disas', required=True)
    parser.add_argument('--disas-name', required=True)
    parser.add_argument('--disas-sizes', required=True)
    args = parser.parse_args()

    instructions = {}
    for file in sorted(os.listdir(args.inst_dir)):
        if not should_translate(file) and not should_decode_only(file):
            continue

        y = common.load_yaml_or_exit(os.path.join(args.inst_dir, file))
        instructions[y['name']] = y

    with open(f'{args.out_h}', 'w') as out:
        out.write(f'#ifndef DISAS_RISCV_{args.disas_name.upper()}_H\n')
        out.write(f'#define DISAS_RISCV_{args.disas_name.upper()}_H\n')
        out.write('\n')
        out.write(f'extern const rv_opcode_data {
                  args.disas_name}_opcode_data[];\n')
        out.write(f'void decode_{args.disas_name}(rv_decode *, rv_isa);\n')
        out.write('\n')
        out.write('#endif\n')

    with open(f'{args.out_c}', 'w') as out:
        out.write('#include \"qemu/osdep.h\"\n')
        out.write('#include \"qemu/bitops.h\"\n')
        out.write('#include \"disas/riscv.h\"\n')
        out.write(f'#include \"disas/riscv-{args.disas_name}.h\"\n')
        out.write('\n')

        out.write('typedef enum {\n')
        for i, inst in enumerate(instructions):
            y = instructions[inst]
            variables = y['encoding']['variables'] if 'variables' in y['encoding'] else [
            ]
            op_name = re.sub(r'\.', r'_', y['name'])
            if i == 0:
                out.write(f'    rv_op_{op_name} = 1,\n')
            else:
                out.write(f'    rv_op_{op_name},\n')
        out.write(f'}} rv_{args.disas_name}_opcode;\n')
        out.write('\n')

        out.write(f'const rv_opcode_data {
                  args.disas_name}_opcode_data[] = {{\n')
        out.write(
            '    { "qc.illegal", rv_codec_illegal, rv_fmt_none, NULL, 0, 0, 0 },\n')
        for inst in instructions:
            y = instructions[inst]
            variables = y['encoding']['variables'] if 'variables' in y['encoding'] else [
            ]
            fmt_args = []
            for v in reversed(variables):
                fmt = {
                    'rd': '0',
                    'rs1': '1',
                    'rs2': '2',
                    'rs3': '6',
                    'r1s': '1',
                    'r2s': '2',
                    'uimm': 'k',
                    'shamt': 'k',
                    'shamt': 'k',
                    'rlist': 'k',
                    'slist': 'k',
                    'width_minus1': 'j',
                    'imm': 'i',
                    'simm': 'j',
                    'simm1': 'i',
                    'simm2': 'j',
                    'spimm': 'i',
                    'length': 'j',
                    'offset': 'Z',
                }
                if v['name'] not in fmt:
                    print(f"Unhandled variable fmt {v['name']}")
                    print(f"For inst:")
                    print(f"{y}")
                    continue

                fmt_args.append(fmt[v['name']])

            fmt_str = f"O\\t{','.join(fmt_args)}"
            name = y['name']
            out.write(
                f"    {{ \"{name}\", rv_codec_skip, \"{fmt_str}\", NULL, 0, 0, 0 }},\n")
        out.write("};\n")

        out.write("\n")

        sizes = [int(s) for s in args.disas_sizes.split(',')]

        for s in sizes:
            if s == 16 or s == 32:
                continue
            out.write(f'static uint64_t decode_{args.disas_name}_{
                      s}_impl_load_bytes(rv_decode *dec, uint64_t insn, int offset, int length)\n')
            out.write('{\n')
            out.write('    return 0;\n')
            out.write('}\n')

        for s in sizes:
            non_standard_size = (s != 16 and s != 32)
            if non_standard_size:
                out.write('#pragma GCC diagnostic push\n')
                out.write('#pragma GCC diagnostic ignored "-Wunused-function"\n')
            out.write(f'#include "riscv-{args.disas_name}-{s}-decode.c.inc"\n')
            if non_standard_size:
                out.write('#pragma GCC diagnostic pop\n')
        out.write(f'#include "{args.trans_disas}"\n')
        out.write('\n')

        out.write(f'void decode_{
                  args.disas_name}(rv_decode *dec, rv_isa isa) {{\n')
        out.write('    rv_inst inst = dec->inst;\n')
        out.write('    dec->op = rv_op_illegal;\n')
        out.write('    switch (dec->inst_length) {\n')
        for s in sizes:
            out.write(f'    case {int(s/8)}:\n')
            if s == 48:
                out.write(f'        inst <<= (64-48);\n')
            out.write(f'        decode_{args.disas_name}_{
                      s}_impl(dec, inst);\n')
            out.write('        break;\n')
        out.write('    }\n')
        out.write('}\n')


if __name__ == '__main__':
    main()
