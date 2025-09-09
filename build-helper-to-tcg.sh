#!/bin/sh

#
# Script to build helper-to-tcg as a separate project.
#
# Copyright (c) 2025 rev.ng Labs Srl.
#
# This work is licensed under the terms of the GNU GPL, version 2 or
# (at your option) any later version.
#
# See the LICENSE file in the top-level directory for details.
#

set -e

llvm_config_path=$1

[ ! -d build ] && mkdir build

meson setup build submodules/helper-to-tcg/subprojects/helper-to-tcg/ -Dllvm_config_path=${llvm_config_path}
meson compile -C build
