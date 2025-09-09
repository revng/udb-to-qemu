#!/bin/sh

#
# Constants common across C++ code generated as both helper-to-tcg, and
# KLEE input.
#
# Copyright (c) 2025 rev.ng Labs Srl.
#
# This work is licensed under the terms of the GNU GPL, version 2 or
# (at your option) any later version.
#
# See the LICENSE file in the top-level directory for details.
#

clangpp=$1
klee=$2
dir=$3

klee_bc_dir=${dir}/bc
klee_out_dir=${dir}/out
klee_exes_dir=${dir}/exes
klee_io_dir=${dir}/io

[ ! -d ${klee_bc_dir} ] && mkdir ${klee_bc_dir}
[ ! -d ${klee_out_dir} ] && mkdir ${klee_out_dir}
[ ! -d ${klee_exes_dir} ] && mkdir ${klee_exes_dir}
[ ! -d ${klee_io_dir} ] && mkdir ${klee_io_dir}

for file in ${dir}/*.cpp; do
    no_ext=${file%.*}
    basename=${no_ext##*/}

    echo "  ${basename}"
    echo "    - Compiling klee .cpp input -> .bc"
    $clangpp $file -std=c++20 -emit-llvm -c -g -O0 -Xclang -disable-O0-optnone -I cpp-templates -I include -I build -o ${klee_bc_dir}/${basename}.bc

    echo "    - Running klee"
    $klee --external-calls=all \
          --only-output-states-covering-new \
          --libc=uclibc \
          --posix-runtime \
          --output-dir=${klee_out_dir}/${basename} \
          ${klee_bc_dir}/${basename}.bc \
          &> ${dir}/klee-out

    echo "    - Compiling test executable"
    $clangpp $file -std=c++20 -g -lkleeRuntest -I cpp-templates -I include -I build -o ${klee_exes_dir}/${basename}

    for test in ${klee_out_dir}/${basename}/*.ktest; do
        echo "    - Collecting test ${test}"
        KTEST_FILE=$test ./${klee_exes_dir}/${basename} >> ${klee_io_dir}/${basename}
    done
done

