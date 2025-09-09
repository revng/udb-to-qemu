//
// Operators required for C++ input to interface correctly with KLEE.
//
// Copyright (c) 2025 rev.ng Labs Srl.
//
// This work is licensed under the terms of the GNU GPL, version 2 or
// (at your option) any later version.
//
// See the LICENSE file in the top-level directory for details.
//

#pragma once

#include <stddef.h>

#include "base-structs.h"

XReg &XRegSet::operator[](size_t i) { return regs[i]; }
