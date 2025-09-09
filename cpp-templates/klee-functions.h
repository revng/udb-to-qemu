//
// Functions required for C++ input to interface correctly with KLEE.
// Provides dummy branches for load, stores, and jumps to enable test
// test generation.
//
// Copyright (c) 2025 rev.ng Labs Srl.
//
// This work is licensed under the terms of the GNU GPL, version 2 or
// (at your option) any later version.
//
// See the LICENSE file in the top-level directory for details.
//

#pragma once

#include <assert.h>
#include <stdint.h>
#include <unordered_map>

#include "base-structs.h"

struct MemoryOp {
    uint32_t value;
    uint8_t size;
};

static bool has_jump = false;
static bool has_store = false;
static bool has_load = false;
static bool has_valid_test_jump = false;
static bool has_valid_test_memop = false;
static int jump_pc_offset = 0;
static std::unordered_map<uint32_t, MemoryOp> wmemory;
static std::unordered_map<uint32_t, MemoryOp> rmemory;
static const uint32_t read_pattern = 0x12345678;
static uint32_t number_of_reads = 0;

#define read_memory_xlen read_memory<32>
#define write_memory_xlen write_memory<32>

template <int N> void write_memory(XReg va, XReg value, uint32_t encoding = 0);
template <> void write_memory<8>(XReg va, XReg value, uint32_t encoding) {
    has_store = true;
    if (va.value() >= 0x1000 && va.value() <= 0x2ff8 && value.value() != 0) {
        has_valid_test_memop = true;
        wmemory[va.value()] = {value.value() & 0xff, 8};
    }
}
template <> void write_memory<16>(XReg va, XReg value, uint32_t encoding) {
    has_store = true;
    if (va.value() >= 0x1000 && va.value() <= 0x2ff8 && value.value() != 0) {
        has_valid_test_memop = true;
        wmemory[va.value()] = {value.value() & 0xffff, 16};
    }
}
template <> void write_memory<32>(XReg va, XReg value, uint32_t encoding) {
    has_store = true;
    if (va.value() >= 0x1000 && va.value() <= 0x2ff8 && value.value() != 0) {
        has_valid_test_memop = true;
        wmemory[va.value()] = {value.value() & 0xffffffff, 32};
    }
}

template <int N> XReg read_memory(XReg va, uint32_t encoding = 0);
template <> XReg read_memory<8>(XReg va, uint32_t encoding) {
    has_load = true;
    ++number_of_reads;
    uint32_t value = number_of_reads * read_pattern;
    if (va.value() >= 0x1000 && va.value() <= 0x2ff8) {
        has_valid_test_memop = true;
        rmemory[va.value()] = {value & 0xff, 8};
    }
    return rmemory[va.value()].value;
}
template <> XReg read_memory<16>(XReg va, uint32_t encoding) {
    has_load = true;
    ++number_of_reads;
    uint32_t value = number_of_reads * read_pattern;
    if (va.value() >= 0x1000 && va.value() <= 0x2ff8) {
        has_valid_test_memop = true;
        rmemory[va.value()] = {value & 0xffff, 16};
    }
    return rmemory[va.value()].value;
}
template <> XReg read_memory<32>(XReg va, uint32_t encoding) {
    has_load = true;
    ++number_of_reads;
    uint32_t value = number_of_reads * read_pattern;
    if (va.value() >= 0x1000 && va.value() <= 0x2ff8) {
        has_valid_test_memop = true;
        rmemory[va.value()] = {value & 0xffffffff, 32};
    }
    return rmemory[va.value()].value;
}

uint64_t xqci_current_pc() { return 0; }

void xqci_jump_pcrel(int imm) {
    has_jump = true;
    jump_pc_offset = imm;
    if (imm == INST_SIZE + 4) {
        // Skip current instruction + next 4-byte wide jump
        has_valid_test_jump = true;
    } else if (imm == -4) {
        // Jump backwards to previous 4-byte wide jump
        has_valid_test_jump = true;
    }
}

void xqci_jump(XReg pc, int imm) { has_jump = true; }

struct CPUArchState;

int32_t xqci_csrr(CPUArchState *, int32_t csrno) { return 0; }

int32_t xqci_csrr_field(CPUArchState *, int32_t csrno, int32_t field) { return 0; }

void xqci_csrw(CPUArchState *, int32_t csrno, int32_t csrw) {}

void xqci_csrw_field(CPUArchState *, int32_t csrno, int32_t field, int32_t value) {}

#define DEF_SEXTRACT(size)                                                               \
    static int##size##_t sextract##size(uint##size##_t value, int start, int length) {   \
        assert(start >= 0 && length > 0 && length <= size - start);                      \
        return ((int##size##_t)(value << (size - length - start))) >> (size - length);   \
    }

DEF_SEXTRACT(8)
DEF_SEXTRACT(16)
DEF_SEXTRACT(32)
DEF_SEXTRACT(64)

void xqci_raise_IllegalInstruction() {}
XReg get_and_validate_stack_pointer(XReg a, int32_t i) { return a; }
void xqci_set_mode_M() {}
void xqci_set_mode_S() {}
void xqci_set_mode_U() {}
bool xqci_implemented_U() { return true; }
bool xqci_implemented_Xqccmp() { return true; }
bool xqci_implemented_Zcmp() { return true; }
/* Implemented in a default rv32 QEMU machine */
bool xqci_implemented_Smdbltrp() { return true; }
void xqci_syscall(int a, int b) {}

static void iss_syscall(XReg a, XReg b) { xqci_syscall(a.value(), b.value()); }
