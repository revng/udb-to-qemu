#!/usr/bin/env python3

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
        prog='udb-to-decodetree.py',
        description='Convert UDB instruction encodings to QEMU decodetree input'
    )
    parser.add_argument('--inst-dir', required=True,
                        help='Path to extensions instruction directory in the UDB')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    encoding = {}
    operation = {}
    for file in sorted(os.listdir(args.inst_dir)):
        if not should_translate(file) and not should_decode_only(file):
            continue

        y = common.load_yaml_or_exit(os.path.join(args.inst_dir, file))
        op_name = re.sub(r'\.', r'_', y['name'])
        encoding[op_name] = y['encoding']
        operation[op_name] = y['operation()']

    # Collect sizes of instructions, and group them by size
    instruction_sizes = {}
    for name in encoding:
        size = len(encoding[name]['match'])
        if size not in instruction_sizes:
            instruction_sizes[size] = []
        instruction_sizes[size].append(name)

    # Look for instructions of the same size whose fixed bit patterns overlap.
    # Instructions which are separated by a runtime field need special
    # formatting in the decodetree input.
    for size in instruction_sizes:
        new_inst = {}
        overlapping = []

        N = len(instruction_sizes[size])
        for i0 in range(0, N):
            n0 = instruction_sizes[size][i0]
            fixed0 = encoding[n0]['match']
            p0 = int(re.sub(r'-', r'0', fixed0), 2)
            for i1 in range(i0+1, N):
                n1 = instruction_sizes[size][i1]
                fixed1 = encoding[n1]['match']
                p1 = int(re.sub(r'-', r'0', fixed1), 2)

                matches = True
                for j in range(0, size):
                    rj = size-1 - j
                    if fixed0[rj] == '1' and fixed1[rj] == '0' or \
                       fixed0[rj] == '0' and fixed1[rj] == '1':
                        matches = False
                        break

                if matches:
                    inserted = False
                    for o in overlapping:
                        if n0 in o:
                            o.add(n1)
                            inserted = True
                            break
                        if n1 in o:
                            o.add(n0)
                            inserted = True
                            break
                    if not inserted:
                        overlapping.append({n0, n1})

                if p0 == p1:
                    new_name = f'{n0}_{n1}'
                    new_inst[new_name] = [n0, n1]

        for o in overlapping:
            for e in o:
                instruction_sizes[size].remove(e)
            instruction_sizes[size].append(o)

    defs = {}
    formats = {}

    for size in instruction_sizes:
        for inst in instruction_sizes[size]:
            y = None
            inst_name = None

            group_formats = []

            if size not in defs:
                defs[size] = {}

            if size not in formats:
                formats[size] = []

            if isinstance(inst, set):
                for i in inst:
                    inst_name = i

                    pattern = encoding[i]['match']
                    pattern = re.sub(r'([-]+)', r' \1 ', pattern)
                    pattern = re.sub(r'-', r'.', pattern)

                    format = f"{inst_name} {pattern}"

                    if 'variables' in encoding[i]:
                        for v in encoding[i]['variables']:
                            ranges = []
                            names = []

                            for r in v['location'].split('|'):
                                if '-' in r:
                                    offsets = [int(s) for s in r.split('-')]
                                    start = offsets[1]
                                    length = offsets[0] - offsets[1] + 1
                                else:
                                    offset = int(r)
                                    length = 1
                                    start = offset

                                start += common.round_to_power_of_two(size) - size
                                ranges.append(f'{start}:{length}')
                                names.append(f'{start}_{length}')

                            name = f"{v['name']}_{'_'.join(names)}"
                            defs[size][name] = f"%{name} {' '.join(ranges)}"
                            format = format + f" {v['name']}=%{name}"

                    group_formats.append(format)

                formats[size].append(group_formats)

    for size in instruction_sizes:
        for inst in instruction_sizes[size]:
            if isinstance(inst, set):
                continue

            op = operation[inst]
            y = encoding[inst]
            inst_name = inst

            pattern = y['match']
            pattern = re.sub(r'([-]+)', r' \1 ', pattern)
            pattern = re.sub(r'-', r'.', pattern)

            if size not in defs:
                defs[size] = {}

            if size not in formats:
                formats[size] = []

            format = f"{inst_name} {pattern}"

            if 'variables' in y:
                for v in y['variables']:
                    ranges = []
                    names = []

                    # Sanity check
                    for subfield in v:
                        if subfield not in {
                                'name',
                                'not',
                                'location',
                                'sign_extend',
                                'left_shift'  # left shift is handled in trans_*()
                            }:
                            print(f'Unhandled field in variable {subfield}')
                            assert(False)

                    for i, r in enumerate(common.ranges_in_location(v['location'])):
                        start, length = r

                        sign_extend = ''
                        if i == 0 and ('sign_extend' in v or f'$signed({v["name"]})' in op):
                            sign_extend = 's'

                        start += common.round_to_power_of_two(size) - size
                        ranges.append(f'{start}:{sign_extend}{length}')
                        names.append(f'{start}_{sign_extend}{length}')

                    name = f"{v['name']}_{'_'.join(names)}"
                    defs[size][name] = f"%{name} {' '.join(ranges)}"
                    format = format + f" {v['name']}=%{name}"

            formats[size].append(format)

        for pattern_length in defs:
            with open(f'{args.out}-{pattern_length}.decode', 'w') as out:

                for name in defs[pattern_length]:
                    out.write(defs[pattern_length][name])
                    out.write('\n')

                for f in formats[pattern_length]:
                    if isinstance(f, list):
                        out.write('{\n')
                        for subf in f:
                            out.write('  ')
                            out.write(subf)
                            out.write('\n')
                        out.write('}\n')
                    else:
                        out.write(f)
                        out.write('\n')


if __name__ == '__main__':
    main()
