#!/bin/sh

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
