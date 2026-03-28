#ifndef BIG_INT_H
#define BIG_INT_H

#include <iosfwd>
#include <cstddef>
#include <string>
#include <utility>
#include <vector>

class big_int {
    static const int base = 1000000000;
    static const int digits = 9;
    std::vector<int> a;

    void trim();
    static int block_to_int(const std::string& s);

public:
    big_int();
    explicit big_int(long long value);
    explicit big_int(const std::string& s);
    static big_int from_hex(const std::string& hex);

    bool is_zero() const;
    bool is_odd() const;
    std::string to_string() const;
    std::size_t bit_length() const;
    int compare(const big_int& other) const;
    int mod_int(int m) const;
    std::pair<big_int, big_int> divmod(const big_int& v) const;
    big_int ordinary_mod(const big_int& other) const;
    big_int div2() const;

    static big_int fast_mod(const big_int& value, const big_int& mod);

    bool operator<(const big_int& other) const;
    bool operator>(const big_int& other) const;
    bool operator<=(const big_int& other) const;
    bool operator>=(const big_int& other) const;
    bool operator==(const big_int& other) const;
    bool operator!=(const big_int& other) const;

    big_int operator+(const big_int& other) const;
    big_int operator-(const big_int& other) const;
    big_int operator*(int m) const;
    big_int operator*(const big_int& other) const;
    big_int operator/(const big_int& other) const;

    friend std::ostream& operator<<(std::ostream& out, const big_int& value);
};

#endif
