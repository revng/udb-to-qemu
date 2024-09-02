#!/usr/bin/env python3

import argparse
import yaml
import re
import os
from operator import itemgetter
import common

def main():
    parser = argparse.ArgumentParser(
        prog='report',
        description='Generate report of handled instructions'
    )
    parser.add_argument('--prioritized')
    parser.add_argument('--inst-dir')
    parser.add_argument('--enabled')
    parser.add_argument('--io')
    parser.add_argument('--show')
    parser.add_argument('--diff')
    parser.add_argument('-o', '--out')
    args = parser.parse_args()

    max_prio = 100
    table_prio = []
    table_other = []
    if args.inst_dir:
        prio = {}
        if args.prioritized:
            with open(args.prioritized, 'r') as f:
                next(f)
                for line in f.readlines():
                    array = line.strip().split(';')
                    name = array[1].split(' ')[0]
                    prio[name] = array
        translated = ''
        if args.enabled:
            with open(args.enabled, 'r') as in_enabled:
                translated = in_enabled.read()

        num_inst = 0
        num_prio_inst = 0
        num_supported_prio_inst = 0
        num_supported_inst = 0

        instructions = {}
        manual_tcg_impl = set()
        for file in sorted(os.listdir(args.inst_dir)):
            with open(os.path.join(args.inst_dir, file), 'r') as f:
                try:
                    y = yaml.safe_load(f)
                    name = y['name']
                    op_name = re.sub(r'\.', r'_', name)
                    instructions[op_name] = y
                    if file in common.decode_only:
                        manual_tcg_impl.add(op_name)
                except yaml.YAMLError as e:
                    print(e)

        for prio_inst in prio:
            prio_name = prio[prio_inst][1].split(' ')[0]
            op_name = re.sub(r'\.', r'_', prio_name)
            if op_name not in instructions:
                print(f'{prio_name} not in instructions')

        for inst in instructions:
            num_inst += 1

            y = instructions[inst]
            name = y['name']
            op_name = inst

            num_tests = 0
            if args.io:
                path = os.path.join(args.io, name)
                if os.path.exists(path):
                    test_yaml = common.load_yaml_or_exit(path)
                    for test in test_yaml:
                        if 'has_jump' in test:
                            if test['has_jump']['valid_test_jump'] == 0:
                                continue
                        if 'has_valid_test_memop' in test and test['has_valid_test_memop'] == 0:
                            continue
                        num_tests += 1

            prioritized = name in prio

            p = max_prio
            if prioritized:
                if len(prio[name][5]) > 0:
                    p = int(prio[name][5])
                else:
                    p = 16

            supported = op_name in translated or op_name in manual_tcg_impl
            num_prio_inst += 1 if prioritized else 0;
            num_supported_inst += 1 if supported else 0
            num_supported_prio_inst += 1 if prioritized and supported else 0
            supported_str = '**yes**' if supported else 'no'
            num_tests_str = str(num_tests) if supported else '-'
            # Note p_str is either an int or a string.., string is used
            # for pretty printing of unprioritized instructions, and the
            # integer used to denote priority, and is used in sorting
            # instructions based on prio.
            p_str = '-' if p == 100 else p
            name_str = f'**`{name}`**'

            table_line = (p_str, name_str, supported_str, num_tests_str)
            if prioritized:
                table_prio.append(table_line)
            else:
                table_other.append(table_line)

        if args.out:
            with open(args.out, 'w') as f:
                f.write(str(num_supported_inst) + '\n')
                f.write(str(num_inst) + '\n')
                f.write(str(num_supported_prio_inst) + '\n')
                f.write(str(num_prio_inst) + '\n')
                table_prio = sorted(table_prio, key=itemgetter(0))
                for l in table_prio + table_other:
                    f.write(';'.join([str(e) for e in l]))
                    f.write('\n')

    if args.show:
        diff_lines = []
        if args.diff:
            with open(args.diff, 'r') as f:
                diff_lines = f.readlines()

        with open(args.show, 'r') as f:
            lines = f.readlines();

            if not args.diff:
                diff_lines = lines

            num_supported_inst = mark_str(lines[0].strip(), diff_lines[0].strip())
            num_inst = mark_str(lines[1].strip(), diff_lines[1].strip())
            num_supported_prio_inst = mark_str(lines[2].strip(), diff_lines[2].strip())
            num_prio_inst = mark_str(lines[3].strip(), diff_lines[3].strip())

            print(f"* Total instructions supported {num_supported_inst}/{num_inst}")
            print(f"* Prio. instructions supported {num_supported_prio_inst}/{num_prio_inst}")
            print("")

            print(f"|QEMU priority|Instruction|Supported?|Num. tests|")
            print(f"|---|---|---|---|")
            for l,d in zip(lines[4:], diff_lines[4:]):
                elements = l.strip().split(';')
                diff_elements = d.strip().split(';')
                print(f"|{'|'.join([mark_str(ee,dd) for ee,dd in zip(elements,diff_elements)])}|")

def mark_str(new_str, diff_str):
    return new_str if new_str == diff_str else f'=={new_str}=='

if __name__ == '__main__':
    main()
