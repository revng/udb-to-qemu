#pragma once

#include <algorithm>
#include <bit>
#include <stdint.h>
#include <type_traits>

constexpr size_t xlen() { return 32; }

// clang-format off
template<int S> struct SizeSelector {};
template<> struct SizeSelector<1>  {using type = uint8_t;};
template<> struct SizeSelector<2>  {using type = uint8_t;};
template<> struct SizeSelector<4>  {using type = uint8_t;};
template<> struct SizeSelector<8>  {using type = uint8_t;};
template<> struct SizeSelector<16> {using type = uint16_t;};
template<> struct SizeSelector<32> {using type = uint32_t;};
template<> struct SizeSelector<64> {using type = uint64_t;};
// clang-format on

template <uint32_t N, bool S> class Bits;

struct BitRange {
    uint64_t value;
    uint64_t length;

    BitRange(uint32_t v, uint32_t l) : value(v), length(l) {}

    template <typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
    BitRange(T v)
        : value(static_cast<uint64_t>(v)),
          length(std::max(1, std::bit_width(static_cast<std::make_unsigned_t<T>>(v)))) {}

    template <uint32_t N, bool S> BitRange(Bits<N, S> &b) : value(b.value()), length(N) {}
};

BitRange operator>>(BitRange l, BitRange r) {
    r.value |= l.value << r.length;
    r.length += l.length;
    return r;
}

template <uint32_t N, bool S, uint32_t M, bool P>
constexpr Bits<N, S> maybe_sext_init(Bits<M, P> b);

template <uint32_t N, bool S = false> class __attribute__((packed)) Bits {
  public:
    using unsigned_type = typename SizeSelector<std::bit_ceil(N)>::type;
    using signed_type = std::make_signed_t<unsigned_type>;
    using type = typename std::conditional<S, signed_type, unsigned_type>::type;

    static constexpr type unsigned_max = ((uint64_t)-1) >> (64 - N);
    static constexpr type unsigned_min = 0;
    static constexpr type signed_max = unsigned_max >> 1;
    static constexpr type signed_min = unsigned_max ^ signed_max;
    static constexpr type max = (S) ? signed_max : unsigned_max;
    static constexpr type min = (S) ? signed_min : unsigned_min;

  private:
    type larger_value;

  public:
    Bits() : larger_value(0) {}

    template <typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
    Bits(T value) : larger_value(value) {}

    template <uint32_t M, bool P>
    Bits(Bits<M, P> b) : larger_value(maybe_sext_init<N, S, M, P>(b).value()) {}

    template <typename... Args>
        requires(sizeof...(Args) > 1)
    constexpr Bits(Args &&...r) {
        larger_value = (... >> BitRange(r)).value;
    }

    type value() const {
        return (N < 8 * sizeof(type)) ? larger_value & unsigned_max : larger_value;
    }

    explicit operator bool() const { return value() != 0; }

    explicit operator type() const { return value(); }

    Bits<1> operator[](size_t i) { return (larger_value >> i) & 1; }

    template <uint32_t M, bool T> Bits<1> operator[](Bits<M, T> reg) {
        return (larger_value >> reg.value()) & 1;
    }

    template <uint32_t b, uint32_t e> Bits<e - b + 1> range() {
        unsigned_type mask = ((unsigned_type)-1) >> (8 * sizeof(unsigned_type) - (e + 1));
        return {(larger_value & mask) >> b};
    }
};

template <typename T> Bits(T) -> Bits<8 * sizeof(T)>;

using XReg = Bits<32>;
using U32 = Bits<32>;
using Csr = Bits<32>;

struct XRegSet {
    XReg regs[32];

    XRegSet() {}

#ifdef KLEE_INPUT
    // defined in *-operators.h
    XReg &operator[](size_t i);

    XReg &operator[](XReg reg) { return operator[](reg.value()); }
#else
    // defined in *-operators.h
    XReg operator[](size_t i);

    XReg operator[](XReg reg) { return operator[](reg.value()); }
#endif
};
