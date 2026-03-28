#ifndef MILLER_RABIN_H
#define MILLER_RABIN_H

#include "big_int.h"

big_int modular_multiply_ordinary(const big_int& a, const big_int& b, const big_int& mod);
big_int modular_multiply_fast(const big_int& a, const big_int& b, const big_int& mod);
big_int modular_power(big_int base, big_int exponent, const big_int& mod, bool use_fast_mod);
bool miller_rabin(const big_int& n, bool use_fast_mod);

#endif
