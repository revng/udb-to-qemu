#!/bin/sh

set -e

llvm_config_path=$1

[ ! -d build ] && mkdir build

meson setup build submodules/helper-to-tcg/subprojects/helper-to-tcg/ -Dllvm_config_path=${llvm_config_path}
meson compile -C build
