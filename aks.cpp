#include "aks.h"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <vector>

#include "miller_rabin.h"

using namespace std;

namespace {

big_int reduce_mod(const big_int& value, const big_int& mod) {
    return big_int::fast_mod(value, mod);
}

big_int power_with_limit(const big_int& base, int exponent, const big_int& limit) {
    big_int result(1);
    big_int limit_plus_one = limit + big_int(1);

    for (int i = 0; i < exponent; ++i) {
        result = result * base;
        if (result > limit) {
            return limit_plus_one;
        }
    }

    return result;
}

big_int power_of_two(size_t exponent) {
    big_int result(1);
    for (size_t i = 0; i < exponent; ++i) {
        result = result * 2;
    }
    return result;
}

bool is_perfect_power(const big_int& n) {
    size_t bits = n.bit_length();
    if (bits <= 1) {
        return false;
    }

    for (int exponent = 2; exponent <= static_cast<int>(bits); ++exponent) {
        size_t root_bits = (bits + static_cast<size_t>(exponent) - 1) / static_cast<size_t>(exponent);
        big_int low(2);
        big_int high = power_of_two(root_bits);

        while (low <= high) {
            big_int mid = (low + high).div2();
            big_int mid_power = power_with_limit(mid, exponent, n);

            if (mid_power == n) {
                return true;
            }

            if (mid_power < n) {
                low = mid + big_int(1);
            } else {
                if (mid == big_int(0)) {
                    break;
                }
                high = mid - big_int(1);
            }
        }
    }

    return false;
}

int find_smallest_r(const big_int& n, size_t max_k) {
    for (int r = 2;; ++r) {
        int n_mod_r = n.mod_int(r);
        if (gcd(n_mod_r, r) != 1) {
            continue;
        }

        long long current = 1 % r;
        bool found_small_order = false;

        for (size_t k = 1; k <= max_k; ++k) {
            current = (current * n_mod_r) % r;
            if (current == 1) {
                found_small_order = true;
                break;
            }
        }

        if (!found_small_order) {
            return r;
        }
    }
}

int euler_phi(int n) {
    int result = n;
    int value = n;

    for (int p = 2; 1LL * p * p <= value; ++p) {
        if (value % p != 0) {
            continue;
        }
        while (value % p == 0) {
            value /= p;
        }
        result -= result / p;
    }

    if (value > 1) {
        result -= result / value;
    }

    return result;
}

vector<big_int> polynomial_multiply_mod(
    const vector<big_int>& left,
    const vector<big_int>& right,
    int r,
    const big_int& mod) {

    vector<big_int> result(static_cast<size_t>(r), big_int(0));

    for (int i = 0; i < r; ++i) {
        if (left[static_cast<size_t>(i)].is_zero()) {
            continue;
        }

        for (int j = 0; j < r; ++j) {
            if (right[static_cast<size_t>(j)].is_zero()) {
                continue;
            }

            int index = (i + j) % r;
            big_int term = modular_multiply_fast(
                left[static_cast<size_t>(i)],
                right[static_cast<size_t>(j)],
                mod);
            result[static_cast<size_t>(index)] =
                reduce_mod(result[static_cast<size_t>(index)] + term, mod);
        }
    }

    return result;
}

vector<big_int> polynomial_power_mod(vector<big_int> base, big_int exponent, int r, const big_int& mod) {
    vector<big_int> result(static_cast<size_t>(r), big_int(0));
    result[0] = big_int(1);

    while (!exponent.is_zero()) {
        if (exponent.is_odd()) {
            result = polynomial_multiply_mod(result, base, r, mod);
        }

        exponent = exponent.div2();
        if (!exponent.is_zero()) {
            base = polynomial_multiply_mod(base, base, r, mod);
        }
    }

    return result;
}

bool check_polynomial_identity(const big_int& n, int r, int a) {
    vector<big_int> base(static_cast<size_t>(r), big_int(0));
    base[0] = reduce_mod(big_int(a), n);
    base[1 % r] = big_int(1);

    vector<big_int> lhs = polynomial_power_mod(base, n, r, n);
    vector<big_int> rhs(static_cast<size_t>(r), big_int(0));

    rhs[0] = reduce_mod(big_int(a), n);
    int xn_index = n.mod_int(r);
    rhs[static_cast<size_t>(xn_index)] =
        reduce_mod(rhs[static_cast<size_t>(xn_index)] + big_int(1), n);

    return lhs == rhs;
}

}  // namespace

bool aks_primality_test(const big_int& n) {
    if (n == big_int(2) || n == big_int(3)) {
        return true;
    }
    if (n < big_int(2) || !n.is_odd()) {
        return false;
    }
    if (is_perfect_power(n)) {
        return false;
    }

    size_t log2_n = max<size_t>(1, n.bit_length());
    size_t max_k = log2_n * log2_n;
    int r = find_smallest_r(n, max_k);

    for (int a = 2; a <= r; ++a) {
        int divisor = gcd(a, n.mod_int(a));
        if (divisor > 1 && big_int(divisor) < n) {
            return false;
        }
    }

    if (n <= big_int(r)) {
        return true;
    }

    int phi_r = euler_phi(r);
    int limit = max(1, static_cast<int>(floor(sqrt(static_cast<double>(phi_r)) * static_cast<double>(log2_n))));

    for (int a = 1; a <= limit; ++a) {
        if (!check_polynomial_identity(n, r, a)) {
            return false;
        }
    }

    return true;
}
