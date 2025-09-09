//
// Functions required for helper-to-tcg to interface correctly with QEMU.
//
// Copyright (c) 2025 rev.ng Labs Srl.
//
// This work is licensed under the terms of the GNU GPL, version 2 or
// (at your option) any later version.
//
// See the LICENSE file in the top-level directory for details.
//

#pragma once

#include <stdint.h>

#include "base-structs.h"

struct CPUArchState;
using abi_ptr = uint32_t;

uint32_t cpu_ldub_data(CPUArchState *env, abi_ptr ptr);
uint32_t cpu_lduw_le_data(CPUArchState *env, abi_ptr ptr);
uint32_t cpu_ldl_le_data(CPUArchState *env, abi_ptr ptr);
uint64_t cpu_ldq_le_data(CPUArchState *env, abi_ptr ptr);

void cpu_stb_data(CPUArchState *env, abi_ptr ptr, uint32_t val);
void cpu_stw_le_data(CPUArchState *env, abi_ptr ptr, uint32_t val);
void cpu_stl_le_data(CPUArchState *env, abi_ptr ptr, uint32_t val);
void cpu_stq_le_data(CPUArchState *env, abi_ptr ptr, uint64_t val);

#define read_memory_xlen read_memory<32>
#define write_memory_xlen write_memory<32>

template <int N> void write_memory(XReg va, XReg value, uint32_t encoding = 0);
template <> void write_memory<8>(XReg va, XReg value, uint32_t encoding) {
    cpu_stb_data(NULL, va.value(), value.value());
}
template <> void write_memory<16>(XReg va, XReg value, uint32_t encoding) {
    cpu_stw_le_data(NULL, va.value(), value.value());
}
template <> void write_memory<32>(XReg va, XReg value, uint32_t encoding) {
    cpu_stl_le_data(NULL, va.value(), value.value());
}

template <int N> XReg read_memory(XReg va, uint32_t encoding = 0);
template <> XReg read_memory<8>(XReg va, uint32_t encoding) {
    return cpu_ldub_data(NULL, va.value());
}
template <> XReg read_memory<16>(XReg va, uint32_t encoding) {
    return cpu_lduw_le_data(NULL, va.value());
}
template <> XReg read_memory<32>(XReg va, uint32_t encoding) {
    return cpu_ldl_le_data(NULL, va.value());
}

void xqci_raise_IllegalInstruction();
__attribute__((annotate("immediate: 1"))) XReg
ann_get_and_validate_stack_pointer(XReg, int32_t) {}
XReg get_and_validate_stack_pointer(XReg, int32_t);
void xqci_set_mode_M();
void xqci_set_mode_S();
void xqci_set_mode_U();
bool xqci_implemented_U();
bool xqci_implemented_Xqccmp();
bool xqci_implemented_Zcmp();
bool xqci_implemented_Smdbltrp();
__attribute__((annotate("immediate: 0"))) void ann_xqci_syscall(int32_t func,
                                                                int32_t arg) {}
__attribute__((annotate("immediate: 0"))) void xqci_syscall(int32_t func, int32_t arg);

static void iss_syscall(XReg a, XReg b) { xqci_syscall(a.value(), b.value()); }

__attribute__((pure)) uint32_t xqci_get_gpr_xreg(XReg csrno) {
    return xqci_get_gpr(csrno.value());
}
