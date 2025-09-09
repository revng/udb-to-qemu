//
// Functions common across C++ code generated as both helper-to-tcg, and
// KLEE input.
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
#include <stddef.h>
#include <stdint.h>
#include <type_traits>

#include "base-structs.h"

template <typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
__attribute__((always_inline)) constexpr std::make_signed_t<T>
signed_ext(T value, int start, int length) {
    constexpr size_t size = 8 * sizeof(T);
    assert(start >= 0 && length > 0 && length <= size - start);
    return ((std::make_signed_t<T>)(value << (size - length - start))) >> (size - length);
}

uint32_t creg2reg(uint32_t index) { return 0b01000 | (index & 0b111); }

template <uint32_t N, bool S> void delay(Bits<N, S> imm) {}

template <uint32_t N, bool S>
__attribute__((always_inline)) constexpr Bits<N, true> _signed(Bits<N, S> b) {
    using T = typename Bits<N, S>::type;
    if constexpr (N < 8 * sizeof(T)) {
        return {
            static_cast<typename Bits<N, true>::type>(signed_ext<T>(b.value(), 0, N))};
    } else {
        return {static_cast<typename Bits<N, true>::type>(b.value())};
    }
}

template <uint32_t N, bool S, uint32_t M, bool P>
__attribute__((always_inline)) constexpr Bits<N, S> maybe_sext_init(Bits<M, P> b) {
    using T = typename Bits<N, S>::type;
    if constexpr (M < N && P) {
        return {static_cast<T>(signed_ext<T>(b.value(), 0, M))};
    } else {
        return {static_cast<T>(b.value())};
    }
}

template <typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
__attribute__((always_inline)) constexpr std::make_signed_t<T> _signed(T t) {
    return t;
}

template <uint32_t count, uint32_t N, bool S>
__attribute__((always_inline)) constexpr Bits<count * N, S> repeat(const Bits<N, S> b) {
    typename Bits<count * N, S>::type res = 0;
    typename Bits<count * N, S>::type pattern = b.value();
    for (uint32_t i = 0; i < count; ++i) {
        res |= (pattern << i * N);
    }
    return {res};
}

__attribute__((always_inline)) uint32_t sext(const XReg i, const XReg len) {
    uint32_t res = ((int32_t)(i.value() << (32 - len.value()))) >> (32 - len.value());
    return (len.value() >= xlen()) ? i.value() : res;
}

__attribute__((always_inline)) uint32_t highest_set_bit(const XReg i) {
    return 31 - __builtin_clz(i.value());
}

__attribute__((always_inline)) uint32_t lowest_set_bit(const XReg i) {
    return 1 + __builtin_ctz(i.value());
}

Csr direct_csr_lookup(Bits<32> no) { return no; }

struct CPUArchState;

__attribute__((annotate("immediate: 0"))) void ann_xqci_jump_pcrel(int imm) {}
__attribute__((annotate("immediate: 0"))) void xqci_jump_pcrel(int imm);
__attribute__((annotate("returns-immediate"))) uint64_t ann_xqci_current_pc() {
    return 0;
}
__attribute__((annotate("returns-immediate"))) uint64_t xqci_current_pc();

__attribute__((annotate("immediate: 1"))) void ann_xqci_jump(XReg pc, int imm) {}
__attribute__((annotate("immediate: 1"))) void xqci_jump(XReg pc, int imm);

__attribute__((annotate("immediate: 1"))) int32_t ann_xqci_csrr(CPUArchState *,
                                                                int32_t csrno) {
    return 0;
}
__attribute__((annotate("immediate: 1"))) int32_t xqci_csrr(CPUArchState *,
                                                            int32_t csrno);

__attribute__((annotate("immediate: 1"))) void
ann_xqci_csrw(CPUArchState *, int32_t csrno, int32_t csrw) {}
__attribute__((annotate("immediate: 1"))) void xqci_csrw(CPUArchState *, int32_t csrno,
                                                         int32_t csrw);

__attribute__((annotate("immediate: 1,2"))) void
ann_xqci_csrw_field(CPUArchState *, int32_t csrno, int32_t field, int32_t value) {}
__attribute__((annotate("immediate: 1,2"))) void
xqci_csrw_field(CPUArchState *, int32_t csrno, int32_t field, int32_t value);

__attribute__((annotate("immediate: 1,2"))) int32_t ann_xqci_csrr_field(CPUArchState *,
                                                                        int32_t csrno,
                                                                        int32_t field) {
    return 0;
}
__attribute__((annotate("immediate: 1,2"))) int32_t xqci_csrr_field(CPUArchState *,
                                                                    int32_t csrno,
                                                                    int32_t field);

__attribute__((annotate("immediate: 0"))) uint32_t ann_xqci_get_gpr(int32_t i) {
    return 0;
}
__attribute__((pure)) uint32_t xqci_get_gpr(int32_t i);

template <uint32_t N, bool S> XReg maybe_sext_xreg(Bits<N, S> b) {
    if constexpr (N < 32) {
        using T = typename Bits<N, S>::type;
        if constexpr (S and N < 8 * sizeof(T)) {
            return signed_ext<uint32_t>(b.value(), 0, N);
        } else {
            return b;
        }
    } else {
        return b;
    }
}

template <uint32_t N, bool S> void xqci_jump_pcrel_bits(Bits<N, S> imm) {
    xqci_jump_pcrel(imm.value());
}

int32_t xqci_csrr_xreg(CPUArchState *env, XReg csrno) {
    return xqci_csrr(env, csrno.value());
}

void xqci_csrw_xreg(CPUArchState *env, XReg csrno, XReg csrw) {
    xqci_csrw(env, csrno.value(), csrw.value());
}

void csr_sw_write(CPUArchState *env, Csr no, Bits<32> v) {
    return xqci_csrw_xreg(env, no, v);
}

int32_t csr_sw_read(CPUArchState *env, Csr no) { return xqci_csrr_xreg(env, no); }

int32_t xqci_csrr_field_xreg(CPUArchState *env, int32_t csrno, int32_t field) {
    return xqci_csrr_field(env, csrno, field);
}

void xqci_csrw_field_xreg(CPUArchState *env, int32_t csrno, int32_t field, XReg value) {
    return xqci_csrw_field(env, csrno, field, value.value());
}

template <uint32_t N, uint32_t M, bool S, bool T,
          typename ResT = Bits<std::max(N, M) + 1, S and T>>
ResT wide_add(const Bits<N, S> l, const Bits<M, T> r) {
    return ResT(l) + ResT(r);
}

template <uint32_t N, bool S, typename T,
          typename = std::enable_if_t<std::is_integral_v<T>>>
auto wide_add(const Bits<N, S> l, T t) {
    return wide_add(l, Bits{t});
}

template <uint32_t N, bool S, typename T,
          typename = std::enable_if_t<std::is_integral_v<T>>>
auto wide_add(T t, const Bits<N, S> r) {
    return wide_add(Bits{t}, r);
}

template <uint32_t N, uint32_t M, bool S, bool T,
          typename ResT = Bits<std::max(N, M) + 1, S and T>>
ResT wide_sub(const Bits<N, S> l, const Bits<M, T> r) {
    return ResT(l) - ResT(r);
}

template <uint32_t N, bool S, typename T,
          typename = std::enable_if_t<std::is_integral_v<T>>>
auto wide_sub(const Bits<N, S> l, T t) {
    return wide_sub(l, Bits{t});
}

template <uint32_t N, bool S, typename T,
          typename = std::enable_if_t<std::is_integral_v<T>>>
auto wide_sub(T t, const Bits<N, S> r) {
    return wide_sub(Bits{t}, r);
}

template <int64_t amount, uint32_t N, bool S, typename ResT = Bits<N + amount, S>>
ResT wide_shl(Bits<N, S> l) {
    return ResT(l) << amount;
}
