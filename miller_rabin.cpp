#include "miller_rabin.h"

#include <array>
#include <random>
#include <stdexcept>

using namespace std;

big_int modular_multiply_ordinary(const big_int& a, const big_int& b, const big_int& mod) {
    return (a * b).ordinary_mod(mod);
}

big_int modular_multiply_fast(const big_int& a, const big_int& b, const big_int& mod) {
    return big_int::fast_mod(a * b, mod);
}

big_int modular_power(big_int base, big_int exponent, const big_int& mod, bool use_fast_mod) {
    big_int result(1);
    base = use_fast_mod ? big_int::fast_mod(base, mod) : base.ordinary_mod(mod);

    while (!exponent.is_zero()) {
        if (exponent.is_odd()) {
            result = use_fast_mod ? modular_multiply_fast(result, base, mod)
                                  : modular_multiply_ordinary(result, base, mod);
        }
        exponent = exponent.div2();
        if (!exponent.is_zero()) {
            base = use_fast_mod ? modular_multiply_fast(base, base, mod)
                                : modular_multiply_ordinary(base, base, mod);
        }
    }

    return result;
}

bool miller_rabin(const big_int& n, bool use_fast_mod) {
    static const int witnesses[] = {2, 3, 5, 7, 11, 13, 17, 19, 23};

    if (n == big_int(2) || n == big_int(3)) {
        return true;
    }
    if (n < big_int(2) || !n.is_odd()) {
        return false;
    }

    for (int p : witnesses) {
        if (n == big_int(p)) {
            return true;
        }
        if (n.mod_int(p) == 0) {
            return false;
        }
    }

    big_int d = n - big_int(1);
    int s = 0;
    while (!d.is_odd()) {
        d = d.div2();
        ++s;
    }

    big_int n_minus_one = n - big_int(1);
    for (int a : witnesses) {
        big_int base(a);
        if (base >= n) {
            continue;
        }

        big_int x = modular_power(base, d, n, use_fast_mod);
        if (x == big_int(1) || x == n_minus_one) {
            continue;
        }

        bool witness_passed = false;
        for (int r = 1; r < s; ++r) {
            x = use_fast_mod ? modular_multiply_fast(x, x, n)
                             : modular_multiply_ordinary(x, x, n);
            if (x == n_minus_one) {
                witness_passed = true;
                break;
            }
        }

        if (!witness_passed) {
            return false;
        }
    }

    return true;
}

big_int generate_probable_prime(size_t bits) {
    if (bits < 2) {
        throw runtime_error("bit length must be at least 2");
    }

    static random_device rd;
    static mt19937_64 rng(rd());
    static const array<int, 10> small_primes = {3, 5, 7, 11, 13, 17, 19, 23, 29, 31};
    uniform_int_distribution<int> bit_dist(0, 1);

    while (true) {
        big_int candidate(0);
        for (size_t i = 0; i < bits; ++i) {
            int bit = 0;
            if (i == 0 || i == bits - 1) {
                bit = 1;
            } else {
                bit = bit_dist(rng);
            }

            candidate = candidate * 2;
            if (bit == 1) {
                candidate = candidate + big_int(1);
            }
        }

        bool divisible = false;
        for (int p : small_primes) {
            if (candidate == big_int(p)) {
                divisible = false;
                break;
            }
            if (candidate.mod_int(p) == 0) {
                divisible = true;
                break;
            }
        }
        if (divisible) {
            continue;
        }

        if (miller_rabin(candidate, true)) {
            return candidate;
        }
    }
}

big_int next_probable_prime(const big_int& n, bool use_fast_mod) {
    if (n < big_int(2)) {
        return big_int(2);
    }

    big_int candidate = n + big_int(1);
    if (candidate == big_int(2)) {
        return candidate;
    }
    if (!candidate.is_odd()) {
        candidate = candidate + big_int(1);
    }

    while (true) {
        if (miller_rabin(candidate, use_fast_mod)) {
            return candidate;
        }
        candidate = candidate + big_int(2);
    }
}

bool previous_probable_prime(const big_int& n, big_int& result, bool use_fast_mod) {
    if (n <= big_int(2)) {
        return false;
    }
    if (n == big_int(3)) {
        result = big_int(2);
        return true;
    }

    big_int candidate = n - big_int(1);
    if (candidate == big_int(2)) {
        result = candidate;
        return true;
    }
    if (!candidate.is_odd()) {
        candidate = candidate - big_int(1);
    }

    while (candidate >= big_int(3)) {
        if (miller_rabin(candidate, use_fast_mod)) {
            result = candidate;
            return true;
        }
        candidate = candidate - big_int(2);
    }

    return false;
}
