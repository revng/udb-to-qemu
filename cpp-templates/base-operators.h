//
// Operators common across C++ code generated as both helper-to-tcg, and
// KLEE input. Defines arithmetic operators and includes checks for
// over-/underflow required for KLEE.
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
#include <type_traits>

#include "base-structs.h"

#ifdef OP_CHECK_OVERFLOW
bool overflow = false;
bool underflow = false;

#define OP_CHECK_WRAP(op, N, M, S, T, a, b)                                              \
    do {                                                                                 \
        using IntTy = std::conditional_t<std::max(N, M) < 64, int64_t, __int128>;        \
        using SmallType = Bits<std::max(N, M), S and T>;                                 \
        IntTy res = ((IntTy)a.value())op((IntTy)b.value());                              \
        if (res > SmallType::max) {                                                      \
            overflow = true;                                                             \
        }                                                                                \
        if (res < SmallType::min) {                                                      \
            underflow = true;                                                            \
        }                                                                                \
    } while (0)
#else
#define OP_CHECK_WRAP(op, N, M, S, T, a, b) /* nothing */
#endif

template <uint32_t ResN, uint32_t N, bool S>
Bits<ResN, S> extend_if_needed(const Bits<N, S> &b) {
    static_assert(ResN >= N);
    if constexpr (N < ResN and S) {
        return {signed_ext(b.value(), 0, N)};
    } else {
        return b;
    }
}

#define DEF_ARITH_OP(name, OP)                                                           \
    template <uint32_t N, uint32_t M, bool S, bool T, uint32_t L = std::max(N, M)>       \
    Bits<L, T and S> name(const Bits<N, S> l, const Bits<M, T> r) {                      \
        OP_CHECK_WRAP(OP, N, M, S, T, l, r);                                             \
        return {(extend_if_needed<L>(l).value() OP extend_if_needed<L>(r).value())};     \
    }                                                                                    \
    template <uint32_t N, bool S, typename IntT, uint32_t M = 8 * sizeof(IntT),          \
              bool T = std::is_signed_v<IntT>,                                           \
              typename = std::enable_if_t<std::is_integral_v<IntT>>>                     \
    Bits<std::max(N, M), T and S> name(const Bits<N, S> l, IntT i) {                     \
        return {l OP Bits<M, T>(i)};                                                     \
    }                                                                                    \
    template <uint32_t N, bool S, typename IntT, uint32_t M = 8 * sizeof(IntT),          \
              bool T = std::is_signed_v<IntT>,                                           \
              typename = std::enable_if_t<std::is_integral_v<IntT>>>                     \
    Bits<std::max(N, M), T and S> name(IntT i, const Bits<N, S> r) {                     \
        return {Bits<M, T>(i) OP r};                                                     \
    }

#define DEF_LSHIFT_OP(name, OP)                                                          \
    template <uint32_t N, uint32_t M, bool S, bool T, uint32_t L = std::max(N, M)>       \
    Bits<L, T and S> name(const Bits<N, S> l, const Bits<M, T> r) {                      \
        OP_CHECK_WRAP(OP, N, M, S, T, l, r);                                             \
        Bits<L, T and S> res =                                                           \
            (extend_if_needed<L>(l).value() OP extend_if_needed<L>(r).value());          \
        return (r.value() < L) ? res : 0;                                                \
    }                                                                                    \
    template <uint32_t N, bool S, typename IntT, uint32_t M = 8 * sizeof(IntT),          \
              bool T = std::is_signed_v<IntT>,                                           \
              typename = std::enable_if_t<std::is_integral_v<IntT>>>                     \
    Bits<std::max(N, M), T and S> name(const Bits<N, S> l, IntT i) {                     \
        return {l OP Bits<M, T>(i)};                                                     \
    }                                                                                    \
    template <uint32_t N, bool S, typename IntT, uint32_t M = 8 * sizeof(IntT),          \
              bool T = std::is_signed_v<IntT>,                                           \
              typename = std::enable_if_t<std::is_integral_v<IntT>>>                     \
    Bits<std::max(N, M), T and S> name(IntT i, const Bits<N, S> r) {                     \
        return {Bits<M, T>(i) OP r};                                                     \
    }

#define DEF_COND_OP(name, OP)                                                            \
    template <uint32_t N, uint32_t M, bool S, bool T, uint32_t L = std::max(N, M)>       \
    bool name(const Bits<N, S> &l, const Bits<M, T> &r) {                                \
        return extend_if_needed<8 * sizeof(typename Bits<N, S>::type)>(l)                \
            .value() OP extend_if_needed<8 * sizeof(typename Bits<M, T>::type)>(r)       \
            .value();                                                                    \
    }                                                                                    \
    template <uint32_t N, bool S, typename IntT, uint32_t M = 8 * sizeof(IntT),          \
              bool T = std::is_signed_v<IntT>,                                           \
              typename = std::enable_if_t<std::is_integral_v<IntT>>>                     \
    bool name(const Bits<N, S> l, IntT i) {                                              \
        return {l OP Bits<M, T>(i)};                                                     \
    }                                                                                    \
    template <uint32_t N, bool S, typename IntT, uint32_t M = 8 * sizeof(IntT),          \
              bool T = std::is_signed_v<IntT>,                                           \
              typename = std::enable_if_t<std::is_integral_v<IntT>>>                     \
    bool name(IntT i, const Bits<N, S> l) {                                              \
        return {Bits<M, T>(i) OP l};                                                     \
    }

DEF_ARITH_OP(operator+, +)
DEF_ARITH_OP(operator-, -)
DEF_ARITH_OP(operator*, *)
DEF_ARITH_OP(operator/, /)
DEF_ARITH_OP(operator%, %)
DEF_ARITH_OP(operator&, &)
DEF_ARITH_OP(operator|, |)
DEF_ARITH_OP(operator^, ^)
DEF_ARITH_OP(operator>>, >>)

DEF_LSHIFT_OP(operator<<, <<)

template <uint32_t N, bool S> Bits<N, S> operator~(const Bits<N, S> l) {
    return {~l.value()};
}
template <uint32_t N, bool S> Bits<N, S> operator-(const Bits<N, S> l) {
    return {-l.value()};
}

DEF_COND_OP(operator>, >)
DEF_COND_OP(operator<, <)
DEF_COND_OP(operator>=, >=)
DEF_COND_OP(operator<=, <=)
DEF_COND_OP(operator==, ==)
DEF_COND_OP(operator!=, !=)

template <uint32_t N, bool S> Bits<N, S> operator++(Bits<N, S> &l, int) {
    auto tmp = l;
    l = Bits<N, S>(l.value() + 1);
    return tmp;
}
