#!/bin/sh

clangpp=$1
klee=$2
rudb_dir=$3
llvm_config=$4

klee_xqci=build/klee/xqci
klee_xqccmp=build/klee/xqccmp
klee_smrnmi=build/klee/smrnmi

xqci_inst_dir=${rudb_dir}/arch_overlay/qc_iu/inst/Xqci
xqci_csr_dir=${rudb_dir}/arch_overlay/qc_iu/csr/Xqci

xqccmp_inst_dir=${rudb_dir}/arch_overlay/qc_iu/inst/Xqccmp

smrnmi_inst_dir=${rudb_dir}/arch/inst/Smrnmi
smrnmi_csr_dir=${rudb_dir}/arch/csr/Smrnmi

base_csr_dir=${rudb_dir}/arch/csr

[ ! -d build ] && mkdir build

[ ! -d ${klee_xqci} ] && mkdir -p ${klee_xqci}
[ ! -d ${klee_xqccmp} ] && mkdir -p ${klee_xqccmp}
[ ! -d ${klee_smrnmi} ] && mkdir -p ${klee_smrnmi}

echo "Building helper-to-tcg:"
sh build-helper-to-tcg.sh $llvm_config

echo "Generating:"
echo "  - helper-to-tcg cpp input for Xqci"
python scripts/yaml-to-cpp.py \
    --csrs "${xqci_csr_dir},${smrnmi_csr_dir},${base_csr_dir}" \
    -o build/xqciu.cpp ${xqci_inst_dir}

echo "  - helper-to-tcg cpp input for Xqccmp"
python scripts/yaml-to-cpp.py \
    --csrs "${base_csr_dir}" \
    -o build/xqccmp.cpp ${xqccmp_inst_dir}

echo "  - helper-to-tcg cpp input for Smrnmi"
python scripts/yaml-to-cpp.py \
    --csrs "${smrnmi_csr_dir},${base_csr_dir}" \
    -o build/smrnmi.cpp ${smrnmi_inst_dir}

echo "Building CSR fields for Xqci"
./scripts/csr.py --inst-dir=${xqci_inst_dir} --csr-dir=${xqci_csr_dir} --out-c=build/xqci_csr.c --out-h=build/xqci_csr.h --name=xqci
echo "Building CSR fields for Smrnmi"
./scripts/csr.py --inst-dir=${smrnmi_inst_dir} --csr-dir=${smrnmi_csr_dir} --out-c=build/smrnmi_csr.c --out-h=build/smrnmi_csr.h --name=smrnmi

echo "Compiling helper-to-tcg input -> .ll for Xqci"
$clangpp build/xqciu.cpp -emit-llvm -c -g -O3 -I include -o build/xqciu.ll
echo "Compiling helper-to-tcg input -> .ll for Xqccmp"
$clangpp build/xqccmp.cpp -emit-llvm -c -g -O3 -I include -o build/xqccmp.ll
echo "Compiling helper-to-tcg input -> .ll for Smrnmi"
$clangpp build/smrnmi.cpp -emit-llvm -c -g -O3 -I include -o build/smrnmi.ll

echo "Running helper-to-tcg for Xqci"
./build/helper-to-tcg build/xqciu.ll \
    --output-source build/xqciu_tcg.c \
    --output-header build/xqciu_tcg.h \
    --output-enabled build/xqciu_tcg_enabled \
    --output-log build/xqciu_tcg_log \
    --tcg-global-mappings=tcg_global_mappings \
    --mmu-index-function=_mmu \
    --temp-vector-block=_vector \
    --static-output \
    &> build/helper-to-tcg-out-xqci
echo "Running helper-to-tcg for Xqccmp"
./build/helper-to-tcg build/xqccmp.ll \
    --output-source build/xqccmp_tcg.c \
    --output-header build/xqccmp_tcg.h \
    --output-enabled build/xqccmp_tcg_enabled \
    --output-log build/xqccmp_tcg_log \
    --tcg-global-mappings=tcg_global_mappings \
    --mmu-index-function=_mmu \
    --temp-vector-block=_vector \
    --static-output \
    &> build/helper-to-tcg-out-xqccmp
echo "Running helper-to-tcg for Smrnmi"
./build/helper-to-tcg build/smrnmi.ll \
    --output-source build/smrnmi_tcg.c \
    --output-header build/smrnmi_tcg.h \
    --output-enabled build/smrnmi_tcg_enabled \
    --output-log build/smrnmi_tcg_log \
    --tcg-global-mappings=tcg_global_mappings \
    --mmu-index-function=_mmu \
    --temp-vector-block=_vector \
    --static-output \
    &> build/helper-to-tcg-out-smrnmi

echo "Generating:"
echo "  - klee cpp input"
echo "  - qemu decodetree input"
echo "  - qemu decodetree translation functions"
echo "  - qemu decodetree disas functions"
python scripts/yaml-to-cpp.py \
    --output-klee ${klee_xqci} \
    --output-trans build/xqciu_trans.c.inc \
    --output-decode build/xqciu \
    --output-decode-extra-functions build/xqciu-decode-extra \
    --output-disas build/riscv-xqci \
    --disas-name xqci \
    --disas-sizes "16,32,48" \
    --input-enabled build/xqciu_tcg.h \
    --csrs "${xqci_csr_dir},${smrnmi_csr_dir},${base_csr_dir}" \
    ${xqci_inst_dir}
python scripts/yaml-to-cpp.py \
    --output-klee ${klee_xqccmp} \
    --output-trans build/xqccmp_trans.c.inc \
    --output-decode build/xqccmp \
    --output-decode-extra-functions build/xqccmp-decode-extra \
    --output-disas build/riscv-xqccmp \
    --disas-name xqccmp \
    --disas-sizes "16" \
    --input-enabled build/xqccmp_tcg.h \
    --csrs "${base_csr_dir}" \
    ${xqccmp_inst_dir}
python scripts/yaml-to-cpp.py \
    --output-klee ${klee_smrnmi} \
    --output-trans build/smrnmi_trans.c.inc \
    --output-decode build/smrnmi \
    --output-decode-extra-functions build/smrnmi-decode-extra \
    --output-disas build/riscv-smrnmi \
    --disas-name smrnmi \
    --disas-sizes "32" \
    --input-enabled build/smrnmi_tcg.h \
    --csrs "${smrnmi_csr_dir},${base_csr_dir}" \
    ${smrnmi_inst_dir}

echo "Running klee"
sh build-tests.sh $clangpp $klee ${klee_xqci}
sh build-tests.sh $clangpp $klee build/klee/xqccmp
sh build-tests.sh $clangpp $klee build/klee/smrnmi

echo "Assembling tests"
sh assemble-tests.sh ${xqci_inst_dir} ${klee_xqci}
sh assemble-tests.sh ${xqccmp_inst_dir} build/klee/xqccmp
sh assemble-tests.sh ${smrnmi_inst_dir} build/klee/smrnmi

./scripts/decodetree-disas.py --static-decode='decode_xqci_16_impl' build/xqciu-16.decode --insnwidth=16 > build/riscv-xqci-16-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_xqci_32_impl' build/xqciu-32.decode --insnwidth=32 > build/riscv-xqci-32-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_xqci_48_impl' build/xqciu-48.decode --varinsnwidth=64 > build/riscv-xqci-48-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_xqccmp_16_impl' build/xqccmp-16.decode --insnwidth=16 > build/riscv-xqccmp-16-decode.c.inc
./scripts/decodetree-disas.py --static-decode='decode_smrnmi_32_impl' build/smrnmi-32.decode --insnwidth=32 > build/riscv-smrnmi-32-decode.c.inc
