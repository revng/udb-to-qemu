#!/usr/bin/env python3

#
# UDB to decode and disassembly C functions for inclusion into QEMU.
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
    parser.add_argument('--out-disas', required=True)
    parser.add_argument('--out-decode', required=True)
    args = parser.parse_args()


    instructions = {}
    for file in sorted(os.listdir(args.inst_dir)):
        if not should_translate(file) and not should_decode_only(file):
            continue

        y = common.load_yaml_or_exit(os.path.join(args.inst_dir, file))
        instructions[y['name']] = y

    with open(args.out_decode, 'w') as out:
        for inst in instructions:
            y = instructions[inst]
            name = y['name']
            op_name = re.sub(r'\.', r'_', name)
            out.write(f'static bool trans_{op_name}(DisasContext *ctx, arg_{op_name} *arg)\n')
            out.write('{\n')

            if name in common.system_only:
                 out.write('#ifdef CONFIG_USER_ONLY\n')
                 out.write('    return false;\n')
                 out.write('#else\n')

            out.write('#ifndef TARGET_RISCV32\n')
            out.write('    return false;\n')
            out.write('#else\n')

            extensions = []
            extensions_yaml = []
            if 'anyOf' in y['definedBy']:
                for e in y['definedBy']['anyOf']:
                    extensions_yaml.append(e)
            else:
                extensions_yaml.append(y['definedBy'])
            for e in extensions_yaml:
                if 'name' in e:
                    extensions.append(e['name'])
                else:
                    extensions.append(e)
            assert(len(extensions) > 0)
            print(f'{file} {extensions}')
            out.write(f'    if ({' && '.join([f"!ctx->cfg_ptr->ext_{e.lower()}" for e in extensions])}) {{\n')
            out.write(f'        return false;\n')
            out.write(f'    }}\n')

            str_args = []
            if 'variables' in y['encoding']:
                str_args = [f"arg->{v['name']}" for v in y['encoding']['variables']]
                for v in y['encoding']['variables']:
                    if 'not' in v:
                        not_values = v['not'] if isinstance(v['not'], list) else [v['not']]
                        conditions = [f"arg->{v['name']} == {n}" for n in not_values]
                        out.write(f"    if ({' || '.join(conditions)}) {{\n")
                        out.write( "        return false;\n")
                        out.write( "    }\n")
                    if 'left_shift' in v:
                        out.write(f"    arg->{v['name']} <<= {v['left_shift']};\n")

            out.write(f'    emit_{op_name}(ctx, tcg_env')
            if len(str_args) > 0:
                out.write(', ')
                out.write(', '.join(str_args))
            out.write(');\n')

            if 'jump_halfword' in y['operation()']:
                out.write('    gen_goto_tb(ctx, 0, ctx->cur_insn_len);\n');

            out.write('    return true;\n')

            out.write('#endif\n')

            if name in common.system_only:
                 out.write('#endif\n')

            out.write('}\n')

    with open(args.out_disas, 'w') as out:
        for inst in instructions:
            y = instructions[inst]
            name = y['name']
            op_name = re.sub(r'\.', r'_', name)
            out.write(f'static bool trans_{op_name}(rv_decode *dec, arg_{op_name} *arg)\n')
            out.write('{\n')

            if name in common.system_only:
                 out.write('#ifdef CONFIG_USER_ONLY\n')
                 out.write('    return false;\n')
                 out.write('#else\n')

            extensions = []
            extensions_yaml = []
            if 'anyOf' in y['definedBy']:
                for e in y['definedBy']['anyOf']:
                    extensions_yaml.append(e)
            else:
                extensions_yaml.append(y['definedBy'])
            for e in extensions_yaml:
                if 'name' in e:
                    extensions.append(e['name'])
                else:
                    extensions.append(e)
            assert(len(extensions) > 0)
            print(f'{file} {extensions}')
            out.write(f'    if ({' && '.join([f"!dec->cfg->ext_{e.lower()}" for e in extensions])}) {{\n')
            out.write(f'        return false;\n')
            out.write(f'    }}\n')

            str_args = []
            if 'variables' in y['encoding']:
                str_args = [f"arg->{v['name']}" for v in y['encoding']['variables']]
                for v in y['encoding']['variables']:
                    if 'not' in v:
                        not_values = v['not'] if isinstance(v['not'], list) else [v['not']]
                        conditions = [f"arg->{v['name']} == {n}" for n in not_values]
                        out.write(f"    if ({' || '.join(conditions)}) {{\n")
                        out.write( "        return false;\n")
                        out.write( "    }\n")
                    if 'left_shift' in v:
                        out.write(f"    arg->{v['name']} <<= {v['left_shift']};\n")

                used_fields = set()
                for v in y['encoding']['variables']:
                    remap_fields = {
                        'rlist' : 'uimm',
                        'slist' : 'uimm',
                        'shamt' : 'uimm',
                        'width_minus1' : 'imm1',
                        'r1s' : 'rs1',
                        'r2s' : 'rs2',
                        'simm' : 'imm1',
                        'simm1' : 'imm',
                        'simm2' : 'imm1',
                        'length' : 'imm1',
                        'spimm' : 'imm',
                    }
                    field = remap_fields[v['name']] if v['name'] in remap_fields else v['name']
                    if field in used_fields:
                        print(f'{name} field {field} used already in disas/')
                    used_fields.add(field)
                    if not common.var_is_imm(y['operation()'], name) and common.inst_is_compressed(y):
                        out.write(f"    dec->{field} = arg->{v['name']} + 8;\n")
                    else:
                        out.write(f"    dec->{field} = arg->{v['name']};\n")

            out.write(f'    dec->op = rv_op_{op_name};\n')
            out.write( '    return true;\n')

            if name in common.system_only:
                 out.write('#endif\n')

            out.write('}\n')

if __name__ == '__main__':
    main()
