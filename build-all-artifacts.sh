#!/bin/sh

#
# Main script to build all artifacts required for a QEMU frontend.
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
llvm_config=$3

rudb_dir=submodules/riscv-unified-db

klee_xqci=build/klee/xqci
klee_xqccmp=build/klee/xqccmp
klee_smrnmi=build/klee/smrnmi

xqci_inst_dir=${rudb_dir}/spec/custom/isa/qc_iu/inst/Xqci
xqci_csr_dir=${rudb_dir}/spec/custom/isa/qc_iu/csr/Xqci

xqccmp_inst_dir=${rudb_dir}/spec/custom/isa/qc_iu/inst/Xqccmp

smrnmi_inst_dir=${rudb_dir}/spec/std/isa/inst/Smrnmi
smrnmi_csr_dir=${rudb_dir}/spec/std/isa/csr/Smrnmi

base_csr_dir=${rudb_dir}/spec/std/isa/csr

[ ! -d build ] && mkdir build

[ ! -d ${klee_xqci} ] && mkdir -p ${klee_xqci}
[ ! -d ${klee_xqccmp} ] && mkdir -p ${klee_xqccmp}
[ ! -d ${klee_smrnmi} ] && mkdir -p ${klee_smrnmi}

echo "Building helper-to-tcg:"
sh build-helper-to-tcg.sh $llvm_config

echo "Generating:"
echo "  - helper-to-tcg cpp input for Xqci"
./scripts/udb-to-cpp.py \
    --csrs "${xqci_csr_dir},${smrnmi_csr_dir},${base_csr_dir}" \
    --inst-dir ${xqci_inst_dir} \
    -o build/xqci.cpp 

echo "  - helper-to-tcg cpp input for Xqccmp"
./scripts/udb-to-cpp.py \
    --csrs "${base_csr_dir}" \
    --inst-dir ${xqccmp_inst_dir} \
    -o build/xqccmp.cpp 

echo "  - helper-to-tcg cpp input for Smrnmi"
./scripts/udb-to-cpp.py \
    --csrs "${smrnmi_csr_dir},${base_csr_dir}" \
    --inst-dir ${smrnmi_inst_dir} \
    -o build/smrnmi.cpp 

echo "Building CSR fields for Xqci"
./scripts/udb-to-csr.py \
    --inst-dir=${xqci_inst_dir} \
    --csr-dir=${xqci_csr_dir} \
    --out-c=build/xqci-csr.c \
    --out-h=build/xqci-csr.h \
    --name=xqci

echo "Building CSR fields for Smrnmi"
./scripts/udb-to-csr.py \
    --inst-dir=${smrnmi_inst_dir} \
    --csr-dir=${smrnmi_csr_dir} \
    --out-c=build/smrnmi-csr.c \
    --out-h=build/smrnmi-csr.h \
    --name=smrnmi

echo "Compiling helper-to-tcg input -> .ll for Xqci"
$clangpp build/xqci.cpp -emit-llvm -std=c++20 -c -O3 -I cpp-templates -I include -o build/xqci.ll
echo "Compiling helper-to-tcg input -> .ll for Xqccmp"
$clangpp build/xqccmp.cpp -emit-llvm -std=c++20 -c -O3 -I cpp-templates -I include -o build/xqccmp.ll
echo "Compiling helper-to-tcg input -> .ll for Smrnmi"
$clangpp build/smrnmi.cpp -emit-llvm -std=c++20 -c -O3 -I cpp-templates -I include -o build/smrnmi.ll

echo "Running helper-to-tcg for Xqci"
./build/helper-to-tcg build/xqci.ll \
    --forward-context \
    --allow-decl-call \
    --output-source build/xqci-tcg.c \
    --output-header build/xqci-tcg.h \
    --output-enabled build/xqci-tcg-enabled \
    --output-log build/xqci-tcg-log \
    --tcg-global-mappings=tcg_global_mappings \
    --mmu-index-function=_mmu \
    --temp-vector-block=_vector \
    --static-output \
    &> build/helper-to-tcg-out-xqci

echo "Running helper-to-tcg for Xqccmp"
./build/helper-to-tcg build/xqccmp.ll \
    --forward-context \
    --allow-decl-call \
    --output-source build/xqccmp-tcg.c \
    --output-header build/xqccmp-tcg.h \
    --output-enabled build/xqccmp-tcg-enabled \
    --output-log build/xqccmp-tcg-log \
    --tcg-global-mappings=tcg_global_mappings \
    --mmu-index-function=_mmu \
    --temp-vector-block=_vector \
    --static-output \
    &> build/helper-to-tcg-out-xqccmp

echo "Running helper-to-tcg for Smrnmi"
./build/helper-to-tcg build/smrnmi.ll \
    --forward-context \
    --allow-decl-call \
    --output-source build/smrnmi-tcg.c \
    --output-header build/smrnmi-tcg.h \
    --output-enabled build/smrnmi-tcg-enabled \
    --output-log build/smrnmi-tcg-log \
    --tcg-global-mappings=tcg_global_mappings \
    --mmu-index-function=_mmu \
    --temp-vector-block=_vector \
    --static-output \
    &> build/helper-to-tcg-out-smrnmi

echo "Generating KLEE input:"
./scripts/udb-to-klee.py \
    --csrs "${xqci_csr_dir},${smrnmi_csr_dir},${base_csr_dir}" \
    --inst-dir ${xqci_inst_dir} \
    --helper-to-tcg-translated build/xqci-tcg.h \
    --out ${klee_xqci}

./scripts/udb-to-klee.py \
    --csrs "${base_csr_dir}" \
    --inst-dir ${xqccmp_inst_dir} \
    --helper-to-tcg-translated build/xqccmp-tcg.h \
    --out ${klee_xqccmp}

./scripts/udb-to-klee.py \
    --csrs "${smrnmi_csr_dir},${base_csr_dir}" \
    --inst-dir ${smrnmi_inst_dir} \
    --helper-to-tcg-translated build/smrnmi-tcg.h \
    --out ${klee_smrnmi}

echo "Generating QEMU decodetree input:"
./scripts/udb-to-decodetree.py \
    --inst-dir ${xqci_inst_dir} \
    --out build/xqci \

./scripts/udb-to-decodetree.py \
    --inst-dir ${xqccmp_inst_dir} \
    --out build/xqccmp

./scripts/udb-to-decodetree.py \
    --inst-dir ${smrnmi_inst_dir} \
    --out build/smrnmi

echo "Generating QEMU decodetree translation functions"
./scripts/udb-to-trans.py \
    --inst-dir ${xqci_inst_dir} \
    --out-decode build/xqci-trans-decode.c.inc \
    --out-disas build/riscv-xqci-trans-disas.c.inc

./scripts/udb-to-trans.py \
    --inst-dir ${xqccmp_inst_dir} \
    --out-decode build/xqccmp-trans-decode.c.inc \
    --out-disas build/riscv-xqccmp-trans-disas.c.inc

./scripts/udb-to-trans.py \
    --inst-dir ${smrnmi_inst_dir} \
    --out-decode build/smrnmi-trans-decode.c.inc \
    --out-disas build/riscv-smrnmi-trans-disas.c.inc

echo "Generating QEMU disas glue files"
./scripts/udb-to-disas.py \
    --inst-dir ${xqci_inst_dir} \
    --disas-name xqci \
    --disas-sizes "16,32,48" \
    --trans-disas riscv-xqci-trans-disas.c.inc \
    --out-c build/riscv-xqci.c \
    --out-h build/riscv-xqci.h

./scripts/udb-to-disas.py \
    --inst-dir ${xqccmp_inst_dir} \
    --disas-name xqccmp \
    --disas-sizes "16" \
    --trans-disas riscv-xqccmp-trans-disas.c.inc \
    --out-c build/riscv-xqccmp.c \
    --out-h build/riscv-xqccmp.h

./scripts/udb-to-disas.py \
    --inst-dir ${smrnmi_inst_dir} \
    --disas-name smrnmi \
    --disas-sizes "32" \
    --trans-disas riscv-smrnmi-trans-disas.c.inc \
    --out-c build/riscv-smrnmi.c \
    --out-h build/riscv-smrnmi.h

#echo "Running klee"
sh build-tests.sh $clangpp $klee ${klee_xqci}
sh build-tests.sh $clangpp $klee build/klee/xqccmp
sh build-tests.sh $clangpp $klee build/klee/smrnmi

#echo "Assembling tests"
#sh assemble-tests.sh ${xqci_inst_dir} ${klee_xqci}
#sh assemble-tests.sh ${xqccmp_inst_dir} build/klee/xqccmp
#sh assemble-tests.sh ${smrnmi_inst_dir} build/klee/smrnmi

./scripts/decodetree-disas.py --static-decode='decode_xqci_16_impl' build/xqci-16.decode --insnwidth=16 > build/riscv-xqci-16-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_xqci_32_impl' build/xqci-32.decode --insnwidth=32 > build/riscv-xqci-32-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_xqci_48_impl' build/xqci-48.decode --varinsnwidth=64 > build/riscv-xqci-48-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_xqccmp_16_impl' build/xqccmp-16.decode --insnwidth=16 > build/riscv-xqccmp-16-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_smrnmi_32_impl' build/smrnmi-32.decode --insnwidth=32 > build/riscv-smrnmi-32-decode.c.inc
