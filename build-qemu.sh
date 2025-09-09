#!/bin/sh

#
# Helper script to build riscv32 QEMU binaries with user and
# system mode support.
#
# Copyright (c) 2025 rev.ng Labs Srl.
#
# This work is licensed under the terms of the GNU GPL, version 2 or
# (at your option) any later version.
#
# See the LICENSE file in the top-level directory for details.
#

set -e

build_qemu=build/qemu
qemu=$(realpath ./submodules/xqci/)

[ ! -d build ] && mkdir build
[ ! -d ${build_qemu} ] && mkdir ${build_qemu}

cd ${build_qemu} && ${qemu}/configure \
    --target-list="riscv32-linux-user riscv32-softmmu" \
    --disable-kvm \
    --disable-tools \
    --disable-libnfs \
    --disable-vde \
    --disable-gnutls \
    --disable-cap-ng \
    --disable-capstone \
    -Dvhost_user=disabled \
    -Dxkbcommon=disabled \
    && make -j8
