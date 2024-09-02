#!/bin/sh

[ ! -d build ] && exit

cp build/xqciu-16.decode submodules/xqci/target/riscv/xqci/
cp build/xqciu-32.decode submodules/xqci/target/riscv/xqci/
cp build/xqciu-48.decode submodules/xqci/target/riscv/xqci/
cp build/smrnmi-32.decode submodules/xqci/target/riscv/smrnmi/
cp build/xqccmp-16.decode submodules/xqci/target/riscv/xqccmp/

cp build/xqciu_tcg.c submodules/xqci/target/riscv/xqci/
cp build/xqciu_tcg.h submodules/xqci/target/riscv/xqci/
cp build/xqciu_trans.c.inc submodules/xqci/target/riscv/xqci/
cp build/xqci_csr.c submodules/xqci/target/riscv/xqci/
cp build/xqci_csr.h submodules/xqci/target/riscv/xqci/

cp build/xqccmp_tcg.c submodules/xqci/target/riscv/xqccmp/
cp build/xqccmp_tcg.h submodules/xqci/target/riscv/xqccmp/
cp build/xqccmp_trans.c.inc submodules/xqci/target/riscv/xqccmp/

cp build/smrnmi_tcg.c submodules/xqci/target/riscv/smrnmi
cp build/smrnmi_tcg.h submodules/xqci/target/riscv/smrnmi
cp build/smrnmi_trans.c.inc submodules/xqci/target/riscv/smrnmi
cp build/smrnmi_csr.c submodules/xqci/target/riscv/smrnmi
cp build/smrnmi_csr.h submodules/xqci/target/riscv/smrnmi

cp xqciu_tcg_manual.c.inc submodules/xqci/target/riscv/xqci/
cp xqci_helper.h submodules/xqci/target/riscv/xqci/

# Disas
cp build/riscv-xqci.c submodules/xqci/disas/
cp build/riscv-xqci.h submodules/xqci/disas/
cp build/riscv-xqci-16-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqci-32-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqci-48-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqci-trans.c.inc submodules/xqci/disas/

cp build/riscv-xqccmp.c submodules/xqci/disas/
cp build/riscv-xqccmp.h submodules/xqci/disas/
cp build/riscv-xqccmp-16-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqccmp-trans.c.inc submodules/xqci/disas/

cp build/riscv-smrnmi.c submodules/xqci/disas/
cp build/riscv-smrnmi.h submodules/xqci/disas/
cp build/riscv-smrnmi-32-decode.c.inc submodules/xqci/disas/
cp build/riscv-smrnmi-trans.c.inc submodules/xqci/disas/

# Testing
rm -r submodules/xqci/tests/tcg/riscv32/klee_io
rm -r submodules/xqci/tests/tcg/riscv32/Xqci
mkdir submodules/xqci/tests/tcg/riscv32/klee_io
cp -r build/klee/xqci/io submodules/xqci/tests/tcg/riscv32/klee_io/xqci/
cp -r build/klee/xqccmp/io submodules/xqci/tests/tcg/riscv32/klee_io/xqccmp/
cp -r build/klee/smrnmi/io submodules/xqci/tests/tcg/riscv32/klee_io/smrnmi/
cp -r submodules/riscv-unified-db/arch_overlay/qc_iu/inst/Xqci/ submodules/xqci/tests/tcg/riscv32/
cp -r submodules/riscv-unified-db/arch_overlay/qc_iu/inst/Xqccmp/ submodules/xqci/tests/tcg/riscv32/
cp -r submodules/riscv-unified-db/arch/inst/Smrnmi/ submodules/xqci/tests/tcg/riscv32/
cp scripts/assemble.py submodules/xqci/tests/tcg/riscv32/
cp scripts/c.py submodules/xqci/tests/tcg/riscv32/
cp scripts/common.py submodules/xqci/tests/tcg/riscv32/
