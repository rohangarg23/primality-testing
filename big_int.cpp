#include "big_int.h"

#include <algorithm>
#include <iomanip>
#include <sstream>
#include <stdexcept>

using namespace std;

void big_int::trim() {
    while (a.size() > 1 && a.back() == 0) {
        a.pop_back();
    }
    if (a.empty()) {
        a.push_back(0);
    }
}

int big_int::block_to_int(const string& s) {
    int num = 0;
    for (char ch : s) {
        num = num * 10 + (ch - '0');
    }
    return num;
}

big_int::big_int() : a(1, 0) {}

big_int::big_int(long long value) {
    if (value == 0) {
        a.push_back(0);
        return;
    }
    while (value > 0) {
        a.push_back(static_cast<int>(value % base));
        value /= base;
    }
}

big_int::big_int(const string& s) {
    a.clear();
    for (int i = static_cast<int>(s.size()); i > 0; i -= digits) {
        int l = max(0, i - digits);
        a.push_back(block_to_int(s.substr(l, i - l)));
    }
    trim();
}

big_int big_int::from_hex(const string& hex) {
    big_int result(0);

    int start = 0;
    if (hex.size() >= 2 && hex[0] == '0' && (hex[1] == 'x' || hex[1] == 'X')) {
        start = 2;
    }

    for (int i = start; i < static_cast<int>(hex.size()); ++i) {
        char ch = hex[i];
        int value = 0;
        if (ch >= '0' && ch <= '9') {
            value = ch - '0';
        } else if (ch >= 'a' && ch <= 'f') {
            value = ch - 'a' + 10;
        } else if (ch >= 'A' && ch <= 'F') {
            value = ch - 'A' + 10;
        } else {
            continue;
        }

        result = result * 16;
        result = result + big_int(value);
    }

    result.trim();
    return result;
}

bool big_int::is_zero() const {
    return a.size() == 1 && a[0] == 0;
}

bool big_int::is_odd() const {
    return a[0] & 1;
}

string big_int::to_string() const {
    stringstream ss;
    ss << a.back();
    for (int i = static_cast<int>(a.size()) - 2; i >= 0; --i) {
        ss << setw(digits) << setfill('0') << a[i];
    }
    return ss.str();
}

size_t big_int::bit_length() const {
    big_int temp = *this;
    size_t bits = 0;
    while (!temp.is_zero()) {
        temp = temp.div2();
        ++bits;
    }
    return bits;
}

ostream& operator<<(ostream& out, const big_int& value) {
    out << value.to_string();
    return out;
}

int big_int::compare(const big_int& other) const {
    if (a.size() != other.a.size()) {
        return a.size() < other.a.size() ? -1 : 1;
    }
    for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
        if (a[i] != other.a[i]) {
            return a[i] < other.a[i] ? -1 : 1;
        }
    }
    return 0;
}

bool big_int::operator<(const big_int& other) const { return compare(other) < 0; }
bool big_int::operator>(const big_int& other) const { return compare(other) > 0; }
bool big_int::operator<=(const big_int& other) const { return compare(other) <= 0; }
bool big_int::operator>=(const big_int& other) const { return compare(other) >= 0; }
bool big_int::operator==(const big_int& other) const { return a == other.a; }
bool big_int::operator!=(const big_int& other) const { return !(*this == other); }

big_int big_int::operator+(const big_int& other) const {
    big_int res;
    int n = max(a.size(), other.a.size());
    res.a.assign(n, 0);

    long long carry = 0;
    for (int i = 0; i < n; ++i) {
        long long sum = carry;
        if (i < static_cast<int>(a.size())) sum += a[i];
        if (i < static_cast<int>(other.a.size())) sum += other.a[i];
        res.a[i] = static_cast<int>(sum % base);
        carry = sum / base;
    }
    if (carry) {
        res.a.push_back(static_cast<int>(carry));
    }
    res.trim();
    return res;
}

big_int big_int::operator-(const big_int& other) const {
    big_int res;
    res.a.assign(a.size(), 0);

    long long borrow = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        long long cur = a[i] - borrow - (i < static_cast<int>(other.a.size()) ? other.a[i] : 0LL);
        if (cur < 0) {
            cur += base;
            borrow = 1;
        } else {
            borrow = 0;
        }
        res.a[i] = static_cast<int>(cur);
    }
    res.trim();
    return res;
}

big_int big_int::operator*(int m) const {
    if (m == 0 || is_zero()) {
        return big_int(0);
    }

    big_int res;
    res.a.assign(a.size(), 0);
    long long carry = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        long long cur = 1LL * a[i] * m + carry;
        res.a[i] = static_cast<int>(cur % base);
        carry = cur / base;
    }
    while (carry > 0) {
        res.a.push_back(static_cast<int>(carry % base));
        carry /= base;
    }
    res.trim();
    return res;
}

big_int big_int::operator*(const big_int& other) const {
    if (is_zero() || other.is_zero()) {
        return big_int(0);
    }

    big_int res;
    res.a.assign(a.size() + other.a.size(), 0);
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        long long carry = 0;
        for (int j = 0; j < static_cast<int>(other.a.size()) || carry > 0; ++j) {
            long long cur = res.a[i + j] + carry;
            if (j < static_cast<int>(other.a.size())) {
                cur += 1LL * a[i] * other.a[j];
            }
            res.a[i + j] = static_cast<int>(cur % base);
            carry = cur / base;
        }
    }
    res.trim();
    return res;
}

big_int big_int::div2() const {
    big_int res;
    res.a.assign(a.size(), 0);
    long long carry = 0;
    for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
        long long cur = a[i] + carry * base;
        res.a[i] = static_cast<int>(cur / 2);
        carry = cur % 2;
    }
    res.trim();
    return res;
}

int big_int::mod_int(int m) const {
    long long rem = 0;
    for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
        rem = (rem * base + a[i]) % m;
    }
    return static_cast<int>(rem);
}

pair<big_int, big_int> big_int::divmod(const big_int& v) const {
    if (v.is_zero()) {
        throw runtime_error("division by zero");
    }

    big_int res;
    big_int cur(0);
    res.a.assign(a.size(), 0);

    for (int i = static_cast<int>(a.size()) - 1; i >= 0; --i) {
        cur.a.insert(cur.a.begin(), a[i]);
        cur.trim();

        int l = 0;
        int r = base - 1;
        int x = 0;
        while (l <= r) {
            int m = l + (r - l) / 2;
            big_int t = v * m;
            if (t <= cur) {
                x = m;
                l = m + 1;
            } else {
                r = m - 1;
            }
        }

        res.a[i] = x;
        cur = cur - (v * x);
    }

    res.trim();
    cur.trim();
    return {res, cur};
}

big_int big_int::operator/(const big_int& other) const {
    return divmod(other).first;
}

big_int big_int::ordinary_mod(const big_int& other) const {
    return divmod(other).second;
}

big_int big_int::fast_mod(const big_int& value, const big_int& mod) {
    if (mod.is_zero()) {
        throw runtime_error("modulo by zero");
    }

    big_int result = value;
    while (result >= mod) {
        int shift = static_cast<int>(result.a.size()) - static_cast<int>(mod.a.size());
        big_int candidate;
        candidate.a.assign(shift, 0);
        candidate.a.insert(candidate.a.end(), mod.a.begin(), mod.a.end());
        candidate.trim();

        if (candidate > result) {
            --shift;
            candidate.a.assign(shift, 0);
            candidate.a.insert(candidate.a.end(), mod.a.begin(), mod.a.end());
            candidate.trim();
        }

        long long low = 1;
        long long high = base - 1;
        long long best = 1;
        while (low <= high) {
            long long mid = (low + high) / 2;
            big_int scaled = candidate * static_cast<int>(mid);
            if (scaled <= result) {
                best = mid;
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }

        result = result - (candidate * static_cast<int>(best));
    }
    result.trim();
    return result;
}
