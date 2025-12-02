#!/bin/sh

#
# Copies over all relevant artifacts into the QEMU subproject.
#
# Copyright (c) 2025 rev.ng Labs Srl.
#
# This work is licensed under the terms of the GNU GPL, version 2 or
# (at your option) any later version.
#
# See the LICENSE file in the top-level directory for details.
#

[ ! -d build ] && exit

cp build/xqci-16.decode submodules/xqci/target/riscv/xqci/
cp build/xqci-32.decode submodules/xqci/target/riscv/xqci/
cp build/xqci-48.decode submodules/xqci/target/riscv/xqci/
cp build/xqccmp-16.decode submodules/xqci/target/riscv/xqccmp/

cp build/xqci-tcg.c submodules/xqci/target/riscv/xqci/
cp build/xqci-tcg.h submodules/xqci/target/riscv/xqci/
cp build/xqci-trans-decode.c.inc submodules/xqci/target/riscv/xqci/
cp build/xqci-csr.c submodules/xqci/target/riscv/xqci/
cp build/xqci-csr.h submodules/xqci/target/riscv/xqci/

cp build/xqccmp-tcg.c submodules/xqci/target/riscv/xqccmp/
cp build/xqccmp-tcg.h submodules/xqci/target/riscv/xqccmp/
cp build/xqccmp-trans-decode.c.inc submodules/xqci/target/riscv/xqccmp/

cp xqci-tcg-manual.c.inc submodules/xqci/target/riscv/xqci/
cp xqci-helper.h submodules/xqci/target/riscv/xqci/

# Disas
cp build/riscv-xqci.c submodules/xqci/disas/
cp build/riscv-xqci.h submodules/xqci/disas/
cp build/riscv-xqci-16-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqci-32-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqci-48-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqci-trans-disas.c.inc submodules/xqci/disas/

cp build/riscv-xqccmp.c submodules/xqci/disas/
cp build/riscv-xqccmp.h submodules/xqci/disas/
cp build/riscv-xqccmp-16-decode.c.inc submodules/xqci/disas/
cp build/riscv-xqccmp-trans-disas.c.inc submodules/xqci/disas/

# Testing
rm -r submodules/xqci/tests/tcg/riscv32/klee_io
rm -r submodules/xqci/tests/tcg/riscv32/Xqci
mkdir submodules/xqci/tests/tcg/riscv32/klee_io
cp -r build/klee/xqci/io submodules/xqci/tests/tcg/riscv32/klee_io/xqci/
cp -r build/klee/xqccmp/io submodules/xqci/tests/tcg/riscv32/klee_io/xqccmp/
cp -r submodules/riscv-unified-db/spec/custom/isa/qc_iu/inst/Xqci/ submodules/xqci/tests/tcg/riscv32/
cp -r submodules/riscv-unified-db/spec/custom/isa/qc_iu/inst/Xqccmp/ submodules/xqci/tests/tcg/riscv32/
cp scripts/assemble.py submodules/xqci/tests/tcg/riscv32/
cp scripts/c.py submodules/xqci/tests/tcg/riscv32/
cp scripts/common.py submodules/xqci/tests/tcg/riscv32/
