#!/usr/bin/env python3

import yaml
import argparse
import re
import subprocess
import os
import math
#from copy import deepcopy
import common


def main():
    parser = argparse.ArgumentParser(
        prog='cpp-csr',
        description='Emit CSR defintions for inclusion into pre-ll cpp code'
    )
    parser.add_argument('-o', '--out')
    parser.add_argument('--extensions', required=True)
    args = parser.parse_args()

    filename = f'cpp_csr_{os.path.basename(v).lower()}.h'
    with open(os.path.join(args.out, filename), 'w') as out:
        out_csrs(out, csrs)


if __name__ == '__main__':
    main()
